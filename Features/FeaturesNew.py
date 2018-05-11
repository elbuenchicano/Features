#Feature Detector

import os
import json
import sys 
import glob 
import numpy as np
import math as mt
import cv2
import matplotlib.pyplot as plt

from utils import *
from functions import featTracklet, featTrackletHistoImage

def saveList(path, flist1, flist2, flist3, flist4, token=''):

    flist1 = sorted(flist1, key = u_stringSplitByNumbers)
    
    if flist2 is not None:
        if len(flist2) > 1:
            flist2 = sorted(flist2, key = u_stringSplitByNumbers)
            flist3 = sorted(flist3, key = u_stringSplitByNumbers)
            flist4 = sorted(flist4, key = u_stringSplitByNumbers)

            u_saveList2File(path + '/' + token + 'angular.lst', flist1)
            u_saveList2File(path + '/' + token + 'radial.lst', flist2)
            u_saveList2File(path + '/' + token + 'numc.lst', flist3)
            u_saveList2File(path + '/' + token + 'centers.lst', flist4)
    else:
        u_saveList2File(path + '/' + token + 'trajec_image.lst', flist1)


################################################################################
#feat extraction from video 
def featVideoFile(general, individual):
    config  = general [ general['type'] ]
    step    = config['step']
    img_sze = config['img_sze']
    depth   = config['depth']
    i_flag  = config['i_flag']
    
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

    out_imgs    = []

    # 0 for combined 1 for individual
    if i_flag == 0:
        img = np.ones((img_sze, img_sze, depth), dtype = "uint8") * 255
        for file in glob.glob(path + '/*' + token):
            featTracklet(file, step, divx, divy, img, depth, type)
        fbase = os.path.basename(dataf)
        out_img = path + '/' + os.path.splitext(fbase)[0] + '_d'+str(depth)+'.png'
        cv2.imwrite(out_img, img)
        out_imgs.append(out_img)
        print('Write file:' , out_img)
    
    else:
        fbase = os.path.basename(dataf)
        for file in glob.glob(path + '/*' + token):
            img = np.ones((img_sze, img_sze, depth), dtype = "uint8") * 255
            featTracklet(file, step, divx, divy, img, depth, type)
            out_img = os.path.splitext(file)[0] + '_d'+str(depth)+'i.png'
            cv2.imwrite(out_img, img)
            out_imgs.append(out_img)
            print('Write file:' , out_img)

    return out_imgs, None, None, None
    
    ################################################################################
#feat extraction from video 
def featVideoFileMatrix(general, individual):

    config      = general[ general['type'] ]
    npoints     = config['npoints']
    
    dataf       = individual["file"]
    filetype    = (os.path.splitext(dataf)[1] == '.yml')

    # true for yml 
    if filetype:
        data    = u_readYAMLFile(dataf)
    else:
        data    = json.load(open(dataf))

    path    = data['video_out_path']
    token   = data['tracklet_token']

    names_angular   = []
    names_radial    = []
    numc_list       = []
    names_centers   = []

    for file in glob.glob(path + '/*' + token):
        print ('Examining file: ', file)
        imgs, numc, centers  = featTrackletHistoImage(file, filetype, npoints)
        
        name = os.path.splitext(file)[0].replace('\\', '/')
        out_img_radius  = name + '_mtR.png'
        out_img_angle   = name + '_mtA.png'
        out_info        = name + '.tinf'
        centers_file    = name + '.ft'

        numc_dict   = {
            "n_vertex"          : numc
        }

        u_saveDict2File(out_info, numc_dict)        
        u_saveArrayTuple2File(centers_file, centers)
        cv2.imwrite(out_img_radius, imgs[0])
        cv2.imwrite(out_img_angle, imgs[1])
        print('Saving file: ' , out_img_radius) 
        print('Saving file: ' , out_img_angle) 
        
        names_angular.append(out_img_angle)
        names_radial.append(out_img_radius)
        numc_list.append(str(numc))
        names_centers.append(centers_file)


            
    return names_angular, names_radial, numc_list, names_centers
        
################################################################################
#feat extraction from folder
def entireFolder(general, individual):
    
    path    = individual["path"]
    token   = individual["token"]
    type    = general["type"]

    out_type= { 'image'  : featVideoFile,
                'matrix' : featVideoFileMatrix}

    flist1 = []
    flist2 = []
    numc_l = []
    cent_f = []
    #walking for specific token
    for root, dirs, files in os.walk(path): 
        for file in files:
            if file.endswith(token):
                print('=============================================')
                print('Conf. file: ', file)
                ind = { 'file': root+ '/' + file }
                a1, a2, cl, cf  = out_type[type] (general, ind)
                flist1          = flist1 + a1
                if a2 is not None:
                    flist2 = flist2 + a2
                    numc_l = numc_l + cl
                    cent_f = cent_f + cf
                base = file.split('.')[0]
                
                #saveList(root.replace('\\', '/'), a1, a2, cl, cf)

    saveList(path, flist1, flist2, numc_l, cent_f)

################################################################################
#feat extraction from folder
def fromfilelist(general, individual):
    
    path    = individual["path"]
    out_    = individual["out_lst"]

    type    = general["type"]

    out_type= { 'image'  : featVideoFile,
                'matrix' : featVideoFileMatrix}

    flist1 = []
    flist2 = []
    numc_l = []    
    cent_f = []

    f = open(path)
    #walking for specific token
    for file in f: 
        if len(file) == 0:
            continue
        print('=============================================')
        file        = file.strip()
        print('Conf. file: ', file)
        ind         = { 'file'  : file }
        a1, a2, cl, cf = out_type[type] (general, ind)
        flist1 = flist1 + a1
        if a2 is not None:
            flist2  = flist2 + a2
            numc_l  = numc_l + cl
            cent_f  = cent_f + cf
       
        base = os.path.basename(file).split('.')[0] + '_'
        saveList(out_, a1, a2, cl, cf, base)
    
    saveList(out_, flist1, flist2, numc_l, cent_f)

################################################################################
################################################################################
################################ Main controler ################################
def _main():

    funcdict = {'entire_folder'         : entireFolder,
                'filelist_propt'        : fromfilelist,
                'tracklets_path'        : featVideoFile,
                'tracklets_path_matrix' : featVideoFileMatrix}
                #'format_name' : formatName ,
                #'same_name': sameName}

    conf    = u_getPath('confNew.json')
    confs   = json.load(open(conf))

    #...........................................................................
    funcdict[confs['source_type']]( general = confs['general'], 
                                    individual = confs[confs['source_type']])
   
################################################################################
################################################################################
############################### MAIN ###########################################
if __name__ == '__main__':
    _main()

