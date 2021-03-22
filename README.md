# Bruzzone-et-al.-2021

Repository of the codes used 

**_Arduino.ino_**   
Code for the control of the ETL during volumetric scanning via the Arduino Mega 2560 board.
The source code must be compiled and deployed to the Arduino Mega 2560 board following these steps:
1) Download and install the Arduino IDE, following the instruction on the web site:
<https://www.arduino.cc/en/software>
2) Connect the Arduino Mega to the PC with the USB cable
3) Open the “.ino” file and create a new project if required
4) Select “Tools”&#8594;”Boards”&#8594;”Arduino Mega 2560”
5) If required, modify in the source code the parameters to match the experimental conditions
6) By clicking the upload button, the code is compiled and deployed to the Arduino Mega 2560 board   


**_Mayavi_animation.py_**  
Code to create the mayavi animation of the 'Supplementary Movie S1'. With the same code it is possible to create the images in Figure 5, the corrisponding part is just to uncomment.   
The following script relies on some functions in 'Wholebrain_analysis.py'.


**_RGC_analysis.py_**  
Code to analyse the RGC acquisition data. The script is fed with the data.raw and stimulation.csv and, for the desired plane, it calculate the pixel-wise correlation between the image and the regressor created from the information about the stimulation.   


**_Wholebrain_analysis.py_**  
It contains several functions to extract and analyze the suite2p output.   


**_Polyfit.py_**  
Code for the calculation of the coefficients for the polynomial fitting the measured look-up-table




