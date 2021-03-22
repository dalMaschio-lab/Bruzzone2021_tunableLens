import numpy as np
import pandas as pd

from stytra import Stytra
from stytra.stimulation import Protocol
from stytra.stimulation.stimuli import InterpolatedStimulus, CircleStimulus, TriggerStimulus, DynamicStimulus
from lightparam import Param
from stytra.triggering import Trigger, ZmqTrigger

import serial
import struct


class ArduinoCommStimulus(DynamicStimulus): #mod by Enrico
  
    def __init__(self, frameNumber, port ="/dev/tty.usbmodem14201", baudrate = 38400, timeout = None, **kwargs):
        super().__init__(**kwargs)
        
        self.duration = 0
        
        self.frameNumberToWait = frameNumber
        
        self._pyb = None
        self.com_port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        
    def initialise_external(self, experiment):

        # Initialize serial connection and set it as experiment attribute to make
        # it available for other stimuli:
        self._experiment = experiment
        try:
            self._pyb = getattr(experiment, "_pyb")
        except AttributeError:
            experiment._pyb = serial.Serial(port = self.com_port, baudrate = self.baudrate, timeout = self.timeout)           
            self._pyb = getattr(experiment, "_pyb")
            experiment._pyb.reset_input_buffer()

    def start(self):
        self.duration = 100000000
        #self._pyb.write("b")  # send blinking command at stimulus start
        
        
        
    def update(self):
        receivedFrameNumber = struct.unpack("<I", self._pyb.read(4) )[0]
        print("received " + str(receivedFrameNumber) )
        if (receivedFrameNumber >= self.frameNumberToWait):
            print("trigger")
                            
            self._pyb.write(b'!')
            
            self.duration = self._elapsed
        

        

class LoomingProtocol(Protocol):
    name = "looming_protocol"

    def get_stim_sequence(self):
        interstimulus_duration=160
        starting_radius=0
        final_radius=0.11
        stimulus_duration=2
            

        #We create the sequence of radius
        radius=[starting_radius, final_radius]*15
        radius_def=[]
        for i in radius:
            radius_def.extend([0,i])
            
        #We create the sequence of time
        t=np.arange(1,16).tolist()
        t1=[]
        for i in t:
            t1.extend([i,i,i,i])
            
        tt=[interstimulus_duration,stimulus_duration]*1
        tt1=[]
        for i in tt:
            tt1.extend([i,i])
    
        tt1=np.array(tt1)
        t1=np.array(t1)
        tt2=tt1*t1
        t_def=[]
        for i, val in enumerate(tt2):
            if i==0:
                t_def.extend([tt2[i]])
            else:
                if i%2!=1:
                    t_def.extend([tt2[i]+tt2[i-1]])
                else:
                    t_def.extend([t_def[i-1]])
        t_def.insert(0,0) 
        del t_def[-1]    
 
        looming_stimulus = pd.DataFrame(
               dict(
                   t=t_def,
                    radius=radius_def
                   )
               )            
            
        return [
            ArduinoCommStimulus(0),     
            LoomingStimulus(
                        background_color=(255, 0, 0),
                        circle_color=(0, 0, 0),
                        df_param=looming_stimulus,
                        origin=(0.5,0.5)
                        ) ]


if __name__ == "__main__":
   
    s = Stytra(protocol=LoomingProtocol())
    
    
    s.exp._pyb.close()    # close the serial port

