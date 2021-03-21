
import numpy as np
from sklearn import preprocessing
import matplotlib.pyplot as plt
import scipy as sc
from sklearn import linear_model, metrics, preprocessing 
from mayavi import mlab
from tvtk.api import tvtk
from Wholebrain_analysis import wholeBrain

file_path=r'PATH\TO\SUBFOLDERS'
planes=30
spacing=6

all_cells=wholeBrain.cells_extraction(file_path, planes, spacing)   #see function in 'wholebrain_analysis.py'

stim=(([1]*17)+([0]*150))*15+([0]*154) 
regressor=np.convolve(np.array(stim), wholeBrain.calcium_kernel(1,4), mode='same').reshape(1,-1)    #see function in 'wholebrain_analysis.py'

Tscores=wholeBrain.correlation(all_cells[:,2375:], regressor)


percentile=0.95
threshold=np.quantile(Tscores,percentile)
s0=[Tscores[i] if Tscores[i]>threshold else np.asarray([0]) for i in range(len(Tscores))]


traces_percentile=[s0[i] for i in range(len(s0)) if s0[i]!=0]
all_cells_percentile=np.asarray([all_cells[i, :3] for i in range(len(all_cells)) if s0[i]>threshold])
activity_percentile=np.asarray([sc.stats.zscore(all_cells[i, 3:]) for i in range(len(all_cells)) if s0[i]>threshold])


###-------uncomment to subdivide the identified cells by clusters-------###
#-then you have to create other mlab 3dpoints for the respective clusters-#

#clusters_file=np.loadtxt('PATH\TO\THE\CLUSTERS.txt')    
#count=0
#clusters=clusters_file.astype(int)
#s_clusters=[]
#for i in range(len(s0)):
#    if s0[i]!=0:
#        s_clusters.append(clusters[count])
#        count+=1
#    else:
#        s_clusters.append(5)   #5 is a random number

#s_clusters=np.asarray(s_clusters)
#all_cells_clusters=(all_cells[:,0],all_cells[:,1],all_cells[:,2],s_clusters)
#all_cells_clusters=np.asarray(all_cells_clusters).T
#all_cells_clusters=all_cells_clusters+activity_percentile

#all_all=np.asarray([all_cells_clusters[i] for i in range(len(all_cells_clusters)) if all_cells_clusters[:,3][i]==5]) #no clusters
#all_cluster0=np.asarray([all_cells_clusters[i] for i in range(len(all_cells_clusters)) if all_cells_clusters[:,3][i]==0])  #cluser 0
#all_cluster1=np.asarray([all_cells_clusters[i] for i in range(len(all_cells_clusters)) if all_cells_clusters[:,3][i]==1])  #cluser 1
#all_cluster2=np.asarray([all_cells_clusters[i] for i in range(len(all_cells_clusters)) if all_cells_clusters[:,3][i]==2])  #cluser 2
#all_cluster3=np.asarray([all_cells_clusters[i] for i in range(len(allall_cells_clusters)) if all_cells_clusters[:,3][i]==3])   #cluser 3

# all_clusters0=np.asarray([all_cluster0[i] for i in range(len(all_cluster0))])
# all_clusters1=np.asarray([all_cluster1[i] for i in range(len(all_cluster1))])
# all_clusters2=np.asarray([all_cluster2[i] for i in range(len(all_cluster2))])
# all_clusters3=np.asarray([all_cluster3[i] for i in range(len(all_cluster3))])


mlab.figure(size = (1024,1080),
             bgcolor = (1,1,1), fgcolor = (0.8, 0.8, 0.8))

all_cells_mayavi=mlab.points3d(all_cells[:,0], all_cells[:,1],all_cells[:,2], all_cells[:,3],  scale_factor=6, scale_mode='none', color=(0.99, 0.99, 0.99), opacity=0.05)
cells_percentile=mlab.points3d(all_cells_percentile[:,0], all_cells_percentile[:,1], all_cells_percentile[:,2], activity_percentile[:,0], scale_factor=6, scale_mode='none', colormap='Greens', vmin=-2, vmax=5)

all_cells_mayavi.actor.actor.rotate_y(360)
all_cells_mayavi.actor.actor.rotate_z(180)
all_cells_mayavi.actor.actor.rotate_x(0)

cells_percentile.actor.actor.rotate_y(360)
cells_percentile.actor.actor.rotate_z(180)
cells_percentile.actor.actor.rotate_x(0)

ms1 = cells_percentile.mlab_source


import os
out_path = 'OUTPUT\PATH'
out_path = os.path.abspath(out_path)
fps = 1
prefix = 'framex'
ext = '.png'
padding = len(str(len(all_cells[0])))

@mlab.animate()
def anim():
    for i in range(1000):
        print(i)
        s1=activity_percentile[:,i] 
        ms1.trait_set(scalars=s1)
        f = mlab.gcf()
        f.scene.movie_maker.record = True
        zeros = '0'*(padding - len(all_cells[0]))
        #filename = os.path.join(out_path, '{}_{}{}{}'.format(prefix, zeros, i, ext))
        #mlab.savefig(filename=filename)
        yield    
anim()
mlab.show()


    
    
    
    

    
 






