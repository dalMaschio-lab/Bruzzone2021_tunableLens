
import numpy as np
import matplotlib.pyplot as plt
#import pyqtgraph as pg    # THIS IS THE LIBRARY TO VISUALIZE SEQUENCE OF IMAGES (T-SERIES OR Z-SERIES)
from scipy import ndimage, stats  #THIS IS THE LIBRARY TO FILTER IMAGES
from sklearn import linear_model #THIS IS THE LIBRARY FOR THE REGRESSION ANALYSIS


raw_path = r'PATH\TO\FILE.raw'
stim_path=r'PATH\TO\STIM.csv'


width = 256 #to check
heigth = 256 #to check
nzplanes = 30 #to check
nchannels = 1  #to check
frame_rate= 30
volume_rate= frame_rate/nzplanes
n_words_to_load = -1  #load  all frames 


my_stim = np.genfromtxt(stim_path, delimiter=',',skip_header=1)
raw = np.memmap(raw_path, dtype=np.uint16, mode='r')  #load the memory map of all data
raw = np.reshape(raw, (-1, nzplanes, nchannels, heigth,  width))


#select one plane and the desired offset to generate a stream
plane=0
offset=1000 # number of Volumes


frames=raw[offset:, plane, 0, :, :]
nframes = np.shape(frames)[0]

#apply a filter to the stream
ker=np.ones((5,1,1))/5
framesdec= ndimage.convolve(frames,ker,mode='reflect')
fig1=plt.figure()
plt.imshow(np.mean(framesdec,axis=0), interpolation='None',cmap='Greys'),plt.title('meanp_'+str(plane)),plt.colorbar()
plt.savefig('mean_'+str(plane)+'.tiff', dpi=300,orientation='portrait', format=None)
plt.close(fig=None)



#show the stream
imv1 = pg.ImageView()
time = np.linspace(0,nframes-1,nframes)
#imv1.setImage(frames,xvals=time)     ##this shows a stream correposnding to one plane as raw data
imv1.setImage(framesdec,xvals=time)        ##this shows a stream correposnding to one plane as filtered data
imv1.show()


toff=1  #in s units, molecule properties for convolution
t=np.linspace(0,15,int(15*volume_rate))
t=np.hstack((-np.ones(int(15*volume_rate)),t))
e=np.exp(-t/toff)*(1+np.sign(t))/2
e=e/np.max(e)
fig2=plt.figure()
plt.plot(e)

time_stim_events=np.nonzero(np.amax(my_stim[:,1:13],axis=1))[0][1::2]
number_stim_events= np.shape(time_stim_events)[0]
stim_duration= 1
reg = np.zeros((np.shape(raw)[0],number_stim_events),dtype=float)
for i in range(number_stim_events):
    reg[int(time_stim_events[i]):int(time_stim_events[i]+stim_duration),i]=1
    reg[:,i]=np.convolve(reg[:,i],e, mode='same')
reg=reg[offset:,:]
fig3=plt.figure()
plt.plot(reg)


datan=framesdec.copy()
clf = linear_model.LinearRegression(fit_intercept=False)
coeffs=np.zeros((number_stim_events,width,heigth))   
Tscores=np.zeros((number_stim_events,width,heigth))    
for j in range(width):
    for k in range(heigth):
        #datan[:,j,k]=np.convolve(np.ones(win),datan[:,j,k],mode='same')/win 
        coeffs[:,j,k]=clf.fit(reg,datan[:,j,k]).coef_
        error=np.sqrt((np.dot((datan[:,j,k]-np.inner(coeffs[:,j,k],reg)),(datan[:,j,k]-np.inner(coeffs[:,j,k],reg)))))
        Tscores[:,j,k]=np.divide(coeffs[:,j,k],error)


for i in range(number_stim_events):
   plt.figure()
   plt.imshow(Tscores[i,:,:], interpolation='None',cmap='YlGn',vmin=0.02,vmax=0.05),plt.title(time_stim_events[i]),plt.colorbar()
   plt.savefig('Tscore_plane_'+str(plane)+'stim_'+str(i)+'.tiff', dpi=300,orientation='portrait', format=None)
   plt.close(fig=None)