#Feature Detector

import os
import json
import sys 
import glob 
import numpy as np
import math as mt
import cv2

import matplotlib.pyplot as plt



from utils import u_readYAMLFile, u_mkdir, u_listFileAll, u_getPath
################################################################################
#feat extraction from video
def featTrackletMatrix(file, type):
    centers    = []
    
    if type:
        with open(file) as f:
            for line in f:
                inner_list = [elt.strip() for elt in line.split(',')]
                           
                x,y,w,h    = [float(x) for x in inner_list[1].split()]
                xc  = x + w/2
                xc  = x + w/2
                centers.append( (int(xc), int(y)) ) 

            
    else:
        with open(file) as f:
            for line in f:
                inner_list = [elt.strip() for elt in line.split(',')]
                
                x,y        = [float(x) for x in inner_list[1].split()]
                centers.append( (int(x), int(y)) ) 

    return centers

################################################################################
#feat extraction from video
def featTracklet(file, type):
    centers    = []
    
    if type:
        with open(file) as f:
            for line in f:
                inner_list = [elt.strip() for elt in line.split(',')]
                           
                x,y,w,h    = [float(x) for x in inner_list[1].split()]
                xc  = x + w/2
                xc  = x + w/2
                centers.append( (int(xc), int(y)) ) 

            
    else:
        with open(file) as f:
            for line in f:
                inner_list = [elt.strip() for elt in line.split(',')]
                
                x,y        = [float(x) for x in inner_list[1].split()]
                centers.append( (int(x), int(y)) ) 
    
    #computing flow and painting map

    
    for i in range(step, len(centers)):
        t_  = centers[i-step]
        t   = centers[i]
        
        opposite    = t_[1] - t[1]
        adjacent    = t_[0] - t[0]
        magnitude   = mt.sqrt( adjacent*adjacent + opposite*opposite )
        angle       = mt.atan2( opposite, adjacent) * 180 / mt.pi
        if angle < 0 : angle += 360
        trajectories.append((angle, magnitude))

        #drawing line
        pt_ =  (int(t_[0]/divx), int(t_[1]/divy))
        pt  =  (int(t[0]/divx), int(t[1]/divy))

        cv2.line(img, pt_, pt, (127,0,0), thickness=3, lineType=8, shift=0)
        
        if depth > 1:
            cv2.line(img, pt_, pt, (0,(angle/360)*255,0), thickness=3, lineType=8, shift=0)
            cv2.line(img, pt_, pt, (0,0,(magnitude/70)*255), thickness=3, lineType=8, shift=0)
        
 
 ################################################################################
#feat extraction from video 
def featVideoFile(general, individual):
    step    = general['step']
    img_sze = general['img_sze']
    depth   = general['depth']
    i_flag  = general['i_flag']
    
    dataf   = individual["file"]

    ext     = os.path.splitext(dataf)[1]
    type    = ext == '.yml' 

    # true for yml 
    if type:
        data    = u_readYAMLFile(dataf)
    else:
        data    = json.load(open(dataf))

    path    = data['video_out_path']
    w       = data['video_w']
    h       = data['video_h']
    token   = data['tracklet_token']

    #values to quantize the resultant image
    divx    = w/img_sze
    divy    = h/img_sze

    if i_flag == 0:
        img = np.ones((img_sze, img_sze, depth), dtype = "uint8") * 255
        for file in glob.glob(path + '/*' + token):
            featTracklet(file, step, divx, divy, img, depth, type)
        fbase = os.path.basename(dataf)
        out_img = path + '/' + os.path.splitext(fbase)[0] + '_d'+str(depth)+'.png'
        cv2.imwrite(out_img, img)
        print('Write file:' , out_img)
    
    else:
        fbase = os.path.basename(dataf)
        for file in glob.glob(path + '/*' + token):
            img = np.ones((img_sze, img_sze, depth), dtype = "uint8") * 255
            featTracklet(file, step, divx, divy, img, depth, type)
            out_img = os.path.splitext(file)[0] + '_d'+str(depth)+'i.png'
            cv2.imwrite(out_img, img)
            print('Write file:' , out_img)

    
    ################################################################################
#feat extraction from video 
def featVideoFileMatrix(general, individual):
    step    = general['step']
    img_sze = general['img_sze']
    depth   = general['depth']
    i_flag  = general['i_flag']
    
    dataf   = individual["file"]
    

    filetype    = (os.path.splitext(dataf)[1] == '.yml')

    # true for yml 
    if filetype:
        data    = u_readYAMLFile(dataf)
    else:
        data    = json.load(open(dataf))

    path    = data['video_out_path']
    token   = data['tracklet_token']

    for file in glob.glob(path + '/*' + token):
        centers = featTrackletMatrix(file, filetype)
        tam     = len(centers)
        vari    = np.zeros((tam,tam))
        

        
        for i in range(tam):
            for j in range(i + 1, tam):
                
                # computing slope between point 
                #slope = ( centers[i][1] - centers [j][1] ) / (( centers[i][0] - centers [j][0] ) + 1e-8)
                angle =  mt.atan2( ( centers[i][1] - centers [j][1] ) , ( centers[i][0] - centers [j][0] ))
                
                #vari[i][j] = slope
                #vari[j][i] = slope
                
                vari[i][j] = angle
                vari[j][i] = angle
        
        img = plt.imshow(vari)              
        plt.show()
        #cv2.imshow('d', vari)
        #cv2.waitKey()

        m = vari.max()
        print (m)
        #vari = vari / m

        #vari = vari * 255


        #out_img = os.path.splitext(file)[0] + 'd_'+str(depth)+'_i_matrix.png'
        #cv2.imwrite(out_img, vari)
        #print('Write file:' , out_img) 
        
        



################################################################################
#feat extraction from folder
def entireFolder(general, individual):
    
    path    = individual["path"]
    token   = individual["token"]
    type    = general["type"]

    out_type= { 'image'        : featVideoFile,
                'matrix' : featVideoFileMatrix}

    #walking for specific token
    for root, dirs, files in os.walk(path): 
        for file in files:
            if file.endswith(token):
                print('Conf. file: ', file)
                ind = { 'file': root+ '/' + file }
                out_type[type] (general, ind)


################################################################################
################################################################################
################################ Main controler ################################
def _main():

    funcdict = {'entire_folder'          : entireFolder,
                'tracklets_path'        : featVideoFile,
                'tracklets_path_matrix' : featVideoFileMatrix}
                #'format_name' : formatName ,
                #'same_name': sameName}

    conf    = u_getPath('conf.json')
    confs   = json.load(open(conf))

    #...........................................................................
    funcdict[confs['source_type']]( general = confs['general'], 
                                    individual = confs[confs['source_type']])
   
################################################################################
################################################################################
############################### MAIN ###########################################
if __name__ == '__main__':
    _main()
