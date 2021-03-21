
/*	coefficients p0, p1, ..., p5 of the polynomial p0 + p1*t + p2*t^2 + ... + p5*t^5, in this order.
 *	The coordinate t is in the range from 0.0 to 1.0, corresponding to Zmin and Zmax, respectively
 */
float polynomial_coeffs[] = { 6.0905976, 1027.9587, -2939.0461, 5033.7837, -4401.955, 1493.3385 };

const int POLY_ORDER = 5;	// order of polynomial for current interpolation 

const float acquisition_frames_per_second = 30.0;	// Should be set to match the acquisition fps
const int frames_per_volume = 30;	/* number of frames to be counted before resetting the current ramp.
					 * Should be set to the desired number of frames per volume
					 */

const float volume_per_second = acquisition_frames_per_second / frames_per_volume; 	/* number of volumes per second, e.g.: 
				 *	|	acq_frames/sec	|	frames/volume	|	volumes/sec	|
				 *	|		30.0	|		30	|		1.0	|
				 *	|		60.0	|		30	|		2.0	|
				 *	|		30.0	|		15	|		2.0	|
				 *	|		60.0	|		15	|		4.0	|
				 *	|		30.0	|		100	|		0.3	|
				 */
const int TIMEOUT = 1000 * (1 + 1 / volume_per_second);	   /* if not enough frames are counted to cause a reset, 
							    * for a time longer than this timeout, in [ms],		
				 			    * it means that the acquisition has stopped. 
							    * It must be larger than the time required to perfom 
							    * a full volume scan.  
				 			    */
const int BUFSIZE = 16;		/* character buffer size for serial communication, 
				 * must be large enough to contain a ETL driver command
				 */
const int ETL_BAUDRATE = 38400; // baudrate for serial communication with ETL driver via the UART interface. Must be 38400.
const int PC_BAUDRATE = 38400; 	// baudrate for serial communication with PC	
const int POLLING_MILLIS = 3;	/* time period, in [ms], between updating events of the value of ETL driver current.
				 * It must be longer than the time it takes to prepare a command and trasmit it,
				 * and the time required by the ETL driver to process it.
				 * The bottleneck is the serial communication speed at 38400bit/sec: 
				 * a full ETL driver serial command used here has 5 bytes, which takes >~ 1 ms to be transmitted.
				 * The value of 3 ms was found to work well
				 * by checking the serial communication with an oscilloscope. 
				 * The ETL driver responds with an error if a malformed command is sent
				 */
const int MAXCURRENT = 293;	// max value of ETL driver current, in [mA] 
uint8_t dataETL[BUFSIZE];	// character buffer for serial communication with ETL driver
uint8_t dataPC[4];		// character buffer for serial communication with PC via USB

unsigned long originMillis = 0;		// variable to keep track of the time of the last reset, in [ms]
unsigned long previousMillis = 0;	// variable to keep track of the time of the last current update, in [ms]


/*	the following variables are declared volatile because they can be updated at any time by interrupt routines	*/

volatile bool reset = true;	/* boolean flag, used to trigger a reset in the main loop from the Interrupt Service Routine.
				 * It is initialized to true to force a reset at startup. 
				 */
volatile bool serial = false;	/* boolean flag, used to trigger a serial communication in the main loop 
				 * from the Interrupt Service Routine
				 */
volatile uint16_t counterHI = 0;	/* higher bytes of a 32-bit counter value, to keep the count without
					 * overflow for long periods of time
					 */
unsigned long count = 0;		/* 32-bit value used to store the total number 
					 * of counted frames since the beginning of the acquisition 
					 */

int16_t current = 0;			// number in the range 0-4096, representing the value of current to be sent to the ETL driver



void setup() {	// |SETUP|
  // setup code, it is run only at the beginning, when the Arduino boots or is reset:


	noInterrupts();		// disable all interrupts while configuring  


	pinMode(  47, INPUT);	/* configure the pin 47 on the Arduino Mega board as input, 
				 * this corresponds to the T5 pin of the ATmega2560, which is
				 * the input to the 16-bit Timer/Counter 5.
				 * there are other four Timer/Counter-s available, 
				 * but their inputs T1, T2 ..., T4 are not exposed as pins in the Arduino Mega board
				 */

	/*	TCNT5 is a 16-bit register containing the current count of the Timer/Counter 5,		 
	 *	when this count reaches the value of the OCR5A register, an interrupt is triggered, which is 
	 *	handled by the code implementing in the  "ISR (TIMER5_COMPA_vect)" routine.			
	 *	When the value of TCNT5 overflows, the corresponding interrupt is handled by the "ISR(TIMER5_OVF_vect)" routine
	 */
 	
	TCCR5A = 0;				/* the register TCCR5A, together with TCCR5B, configures the operation
						 * of the Timer/Counter 5. Here we set it in normal mode
						 */

	TCCR5A |= ~bit(COM5A1) & bit(COM5A0);   /* enable toggle mode on compare match on OC5A pin, 
						 * which corresponds to pin 46 on Arduino mega board.
						 * not required, but can be usefull for debugging purposes,
						 * if the pin is enable as output.
						 */
	TCCR5B = 0; 
	TCCR5B |= bit(CS52) | bit(CS51) | bit(CS50);   // clock source on T5 pin, rising edge  
	//TCCR5B |= bit(CS52) | bit(CS51) | ~bit(CS50);   // clock source on T5 pin, falling edge  

	TIMSK5 = 0;				// the register TIMSK5 configures interrupts of the Timer/Counter 5.
	TIMSK5 |= bit(OCIE5A);                  // enable output compare A match interrupt 
	TIMSK5 |= bit(TOIE5);			// enable overflow interrupt


	OCR5A = frames_per_volume;		// initialize the match register

	TCNT5 = 0;				// initialize the value of the Timer/Counter 5

	interrupts();				// re-enable interrupts


	Serial.begin(PC_BAUDRATE);		/* enable serial communication with PC, via USB.
						 * We use it to periodically send the number of counted frames to the PC.
						 * Not required, but can be useful to syncronize other software in the PC 
						 * with acquisition.
						 */

	Serial1.begin(ETL_BAUDRATE);   		/* USART serial communication with ETL driver, on UART interface 1.
						 * The TX/RX pins are 18 and 19, respectively, in the Arduino mega board.
						 * The baudrate 38400 is required by the ETL driver.  
						 */
	
	Serial1.write("Start");     		/* sends a command to the ETL driver. 
						 * The command "Start" resets the driver and, among other things,
						 * sets the current to 0 mA
						 */
}	// end of |SETUP|					

void loop() {  // |LOOP|
  // loop code. This is the main code which is run repeatedly.

	unsigned long currentMillis = millis();		// reads the current time in milliseconds from the internal timer
	
	count = ((unsigned long) counterHI << 16) + TCNT5;	// compute the value of counted frames by merging the high and low bytes
  	
	if (reset || (count == 0) ) {	/* |RESET| conditional
					 * This is executed anytime a reset signal is triggered by the interrupt,
					 * or when the count is zero which mean the acquisition has not started yet.
					 */
 		reset = false;
		originMillis = currentMillis;		// sync the reference time to the present time
		previousMillis = currentMillis;
	}  // end of |RESET| conditional



	if (serial) {	/* |SERIAL| conditional
			 * This is executed when the serial signal is triggered by the interrupt. 
			 */
		serial = false;

		/*	prepare the serial buffer	*/
		dataPC[3] = counterHI >> 8;   // high byte
		dataPC[2] = counterHI & 0xFF;  // low byte
		dataPC[1] = TCNT5 >> 8;   // high byte
		dataPC[0] = TCNT5 & 0xFF;  // low byte 

		Serial.write(dataPC, 4);	/* send to PC the counter value (current frame number)
						 * as a 4 bytes, 32-bit unsigned integer. Little-endian.
						 */
	}  // end of |SERIAL| conditional

	if ((currentMillis >= previousMillis + POLLING_MILLIS) && count ) {	/* |UPDATE| conditional
									 	 * This is executed every POLLING_MILLIS ms,
										 * but ONLY if the acquisition is running,
										 * i.e. count > 0
										 */
   
		previousMillis = currentMillis;
  
		int16_t dt = currentMillis - originMillis;	/* dt is the time, in ms, since the last reset, 
								 * i.e. the beginning of the current ramp. During acquisition
								 * this quantity should never exceed the time it takes to perform 								  * the full Zscan, since it restarts from zero at every reset.
								 * When the acquisition stops, however, there are no more resets
								 * and dt keeps increasing. 
								 * This is handled in the |TIMEOUT| conditional.
								 */
    		/*	compute the polynomial I(t) = p0 * t^0 + p1 * t^1 + p2 * t^2 + ... * p5 * t^5  	
		 *	the coordinate t is in the range from 0.0 to 1.0, corresponding to Zmin and Zmax, respectively
		 */
		float t = float(dt) / 1000 *   volume_per_second;	/* the coordinate t ranges from 0 to 1 */
           
		float x = 1.0;		// x = t^0

		float I = x * polynomial_coeffs[0];	// partial sum:   p0 * t^0
    
		for (int i = 1; i <= POLY_ORDER; i++){		// perform the rest of the sum
      			x *= float(t);				// x = t^i
			I += x * polynomial_coeffs[i];	
            	}

		if (t <= 1.0) {						/* if t > 1 means that we are going in TIMEOUT, 
									 * in that case we keep the last computed value of current
									 */
			current = I / MAXCURRENT * 4096;		/* rescale the current in the range 0-4096, 
									 * as required by the ETL driver
									 */
		}
		if (dt > TIMEOUT) {		/* |TIMEOUT| conditional
						 * when dt exceeds TIMEOUT it means the acquisition has stopped, so we must
						 * get ready for a new, independent acquisition. In particular, the value of the
						 * counter and the current must be reset to zero. The other code is basically the
						 * the same as in the setup() routine
						 */
			noInterrupts();	

			current = 0;					
			counterHI = 0;
			count = 0;

			TCNT5 = 0;				// initialize the initial count
 	
			TCCR5A = 0;			
			TCCR5A |= ~bit(COM5A1) & bit(COM5A0);   
			TCCR5B = 0; 
			TCCR5B |= bit(CS52) | bit(CS51) | bit(CS50);   
			TIMSK5 = 0;				
			TIMSK5 |= bit(OCIE5A);                  
			TIMSK5 |= bit(TOIE5);		

			OCR5A = frames_per_volume;		// initialize the match register

			interrupts();				// re-enable interrupts

		} 	// end of |TIMEOUT| conditional

		/*	prepare a command to be sent to the ETL driver. The command to update the value of the current 
		 *	is composed of the characters 'A', 'w', followed by a two-bytes 16 bit integer number ranging 
		 *	from 0 for 0 current, to 4096, for max current. Finally, a Cyclic Redundancy Check byte is added.	
		 */
 

		int NBYTES = 0;		// just an index to enqueue characters in the "dataETL" buffer one at a time
		
		dataETL[NBYTES++] = 0x41;  // ASCII 'A'		
		dataETL[NBYTES++] = 0x77;  // ASCII 'w'		 
		dataETL[NBYTES++] = current >> 8;   // high byte	 
		dataETL[NBYTES++] = current & 0xFF;  // low byte	 

		/* 	compute the CRC byte based on the previous bytes in the dataETL buffer	 */
		uint16_t crc = 0;

		for (int i = 0; i < NBYTES; i++) {    // outer for
  
			crc ^= dataETL[i];
 			for (int j = 0; j < 8; ++j) { // inner for
				if (crc & 1)
					crc = (crc >> 1) ^ 0xA001;
				else
					crc = (crc >> 1);
			}  // end of inner for
		} // end of outer for


		dataETL[NBYTES++] = crc & 0xFF;		// add the CRC byte to the buffer
		dataETL[NBYTES++] = crc >> 8;

		Serial1.write(dataETL, NBYTES);		// send the serial command to the ETL driver
     
	}  // end of |UPDATE| conditional




}  // end of |LOOP|





ISR (TIMER5_COMPA_vect) {  	/* implementation of INTERRUPT SERVICE ROUTINE for Timer Compare Match A 
				 * This is executed every time the TCNT5 value reaches the OCR5A target value.
				 */
	OCR5A += frames_per_volume;	// increase the target value 
	reset = true;			// trigger a reset signal in the main loop
	serial = true;			// trigger a serial signal in the main loop
}

ISR(TIMER5_OVF_vect) {	/* implementation of INTERRUPT SERVICE ROUTINE for Overflow.
 			 * This happens when TCNT5 count reaches 2^16 = 65536 and restarts from zero. 
			 * With an acquisition speed of 30 frames per second this happens about every 36 minutes.
			 * We keep track of the total count by increasing another 16-bit variable counterHI,
			 * which together with TCNT5 represents a 32-bit unsigned integer. This overflows in more than 4 years.
			 */
	counterHI++;

}
