import numpy as np

N = 5   # interpolation polynomial order

### Z values, in micron
Z = np.array( [
    0,
    3.7,
    8,
    13,
    21.7,
    24,
    36,
    46,
    60,
    74,
    95,
    120,
    157,
    187
	 
] )

### current values, in mA
I = np.array( [

 	0,    
	30,
	50,
	66.4,
	86,
	100,
	125,
	142,
	158,
	172,
	188,
	200,
	213,
	220

] )


X = ( Z - Z.min() ) / ( Z.max() - Z.min())      #map the range Z range from 0.0 to 1.0

fit = np.polyfit(X, I, N)   # fit with the Nth order polynomial

p = np.poly1d(fit)  # get the polynomian coefficients

### put the coefficients in ascending order p0, p1, ... pN, as 32-bit float required for the Arduino Mega
coeffs = np.flip( p ).astype(np.float32)   
                    

### print a string that can be copy/pasted in the Arduino Mega source code
print( "float polynomial_coeffs[] = { " , end='') 
print( *coeffs, sep = ', ' , end='')
print( " };" )