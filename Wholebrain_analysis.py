import numpy as np
from sklearn import linear_model, metrics

class wholeBrain:
    def __init__(self):
        pass


    def calcium_kernel(sample_interval, tau_off):
        # This function is used to calculate the calcium kernel required for the convolution with the binary stimulus trace.
        # sample_interval: sampling rate of the acquisition
        # tau_off: tau off of the used fluorescent reporter 

        #return the calcium kernel

        interval=np.arange(0,30,sample_interval)
        interval=np.hstack((-np.ones(int(30/sample_interval)),interval))
        K_c=(1/tau_off)*np.exp(-interval/tau_off)*(1+np.sign(interval))/2
        K_c=K_c/np.max(K_c)

        return K_c


    def correlation(traces, regressors):
        # This function calculates the Tscores between each cell and the regressor (one or more than one).
        # traces: the fluorescent traces for each cells. You can use the output of the 'cells_extraction' function. Just pay care to remove the first elements of the traces (coordinates)
        # regressors: it accepts a list of multiple regressors or a single array

        # return a list containing the Tscores
        
        clf = linear_model.LinearRegression(fit_intercept=False)
        rows= len(traces[:,0])
        Tscores_int=[]
        Tscores=[]
        if len(regressors)>1:
            for i in range(len(regressors)):
                Tscores_int=[]
                reg=regressors[i].reshape(-1,1)
                for j in range(rows):
                    cell=(traces[j]).reshape(-1,1)
                    coeffs0=clf.fit(reg,cell).coef_ 
                    error=metrics.mean_squared_error(reg,cell)
                    Tscore=np.divide(coeffs0,error)
                    Tscores_int.append(Tscore)

                Tscores.append(Tscores_int)
                print(f'{i/len(regressors)*100} completed')

        elif len(regressors)==1:
            reg=regressors.reshape(-1,1)
            for j in range(rows):
                cell=(traces[j]).reshape(-1,1)
                coeffs0=clf.fit(reg,cell).coef_ 
                error=metrics.mean_squared_error(reg,cell)
                Tscore=np.divide(coeffs0,error)
                Tscores.append(Tscore)

        return Tscores



    def extraction_step(file_path, planes, spacing):
        # See 'cells_extraction' function
        # This function simply opens the various files.npy in the subfolders 'planeX' and returns the median ('med' element inside 'stat.npy') for each ROI

        s=str(planes)
        file_stat=file_path+'plane'+s+'\stat.npy'
        stat=np.load(file_stat, allow_pickle=True)
        file_iscell= file_path+'plane'+s+'\iscell.npy'
        iscell=np.load(file_iscell, allow_pickle=True)
        file_F= file_path+'plane'+s+'\F.npy'
        F=np.load(file_F, allow_pickle=True)

        rows=len(stat)
        med=[]
        for j in range(rows):
            var_00=stat[j]
            var_01=var_00['med']
            med.append(var_01)
        coord_00=np.array(med)
        coord_00=np.append(coord_00,iscell, axis=1)
        coord_00=np.append(coord_00,F, axis=1)
        percentage=0.9                                  #here is defined the threshold for defining cells
        coord_00=coord_00[coord_00[:,2] >percentage]   
        coord_00[:,2]=spacing*planes  
        coord=coord_00

        return coord


    def cells_extraction(file_path, planes, spacing):
        # In the current version of suite2p, the manual labelling performed on the single planes does no influence the total count of cells in the combined planes. 
        # This function (and the other one linked) is meant to extract the cell information from the files of the planes instead of the combined one.
        # file_path: the path to the folder containing the subfolders of the planes
        # planes: the number of the planes subfolders (combined excluded) 
        # spacing: the um between each plane. In this case, we use the mean across all the planes

        # Return a list containing all the cells defined as 'is_cell' in the respective .npy file.
        # For each cell: 
            # the 0 element is the y coordinate;
            # the 1 element is the x coordinate; 
            # the 2 element is the z coordinate (defined in 'spacing');
            # the rest of the elements are the fluorescent traces.

        raw= file_path + 'combined\\F.npy'
        raw=np.load(raw, allow_pickle=True)   
        file_len=len(raw[0])+4  #it could happen that different planes differs of +-1 in lenght. This is used to correct the issue.
        all_cells = np.empty((0, file_len))
        for plane in range(0, planes):
            fixed=wholeBrain.extraction_step(file_path, plane, spacing)
            if len(fixed[0])==file_len:
                print('Appending plane...')
                all_cells = np.append(all_cells, fixed, axis=0)
            else:
                if len(fixed)<file_len:
                    print('Removing last columns from combined:...')
                    all_cells=all_cells[:,:-(file_len-len(fixed[0]))]
                    all_cells = np.append(all_cells, fixed, axis=0)
                    file_len-=1
                else:
                    print('Adding last columns to combined:...')
                    all_cells=all_cells[:,:+(len(fixed[0])-file_len)]
                    all_cells = np.append(all_cells, fixed, axis=0)
                    file_len+=1
                    
        return all_cells


    def correlaton(x,y):
        #Code to map the tseries averaged plane to the z-stack data
        #x: tseries data
        #y: z-stack data
        
        n_planes=30
        n_frames=18000
        initial_frame=300*n_planes
        end_frame=initial_frame+n_frames
        x = np.reshape(x, (-1, 512,  1024))
        y = np.reshape(y, (-1, 512,  1024))
        x=x[initial_frame:end_frame] 

        tseries_plane=[]
        zstack_plane=[]
        for p in range(n_planes):
            seq=[]
            for i in range(p, len(x), n_planes):
                seq.append(x[i])
            seq=np.asarray(seq)
            seq_01=seq.mean(axis=0)
            seq=[]
            scores=[]
            for j in range(len(y)): 
                corr=np.corrcoef(seq_01.ravel(), y[j].ravel())
                scores.append(corr[0,1])
            tseries_plane.append(p)
            zstack_plane.append(np.argmax(scores))
            scores=[]

        final=np.column_stack((tseries_plane,zstack_plane))
            
        return final