
import os
import json
import sys 
import glob 
import numpy as np
import math as mt
import cv2
import random

import matplotlib.pyplot as plt

from utils import u_readYAMLFile, u_mkdir, u_listFileAll, u_getPath
from toolz import interleave
from scipy.spatial import ConvexHull

################################################################################
#feat extraction from video
def featTrackletMatrix(file, type):
    centers         = []
    
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
def featTracklet(file, step, divx, divy, img, depth, type):
    centers         = []
    trajectories    = []
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
################################################################################
# fitting center points
def pointVectorFill(points, size):
    numc = len(points)
    if numc == size:
        return points

    # filling if less than size
    if numc < size :
        
        nmiss = size - numc 
        
        #inc_rate = 2
        while nmiss > 0:
            pos         = 0
            newpoints   = [] 
            
            while ( pos < (len(points)-1) ) and ( nmiss > 0 ):
                
                newpoints.append ( 
                                    ( 
                                        (points[pos][0] + points[pos+1][0]) /2 ,
                                        (points[pos][1] + points[pos+1][1]) /2
                                    )
                                 )
                nmiss   -= 1
                pos     += 1
            
            #inc_rate   += 1
            points      = list(interleave([points, newpoints]))
            
        #plt.plot(x,y,'ro')
        #for p in points:
        #    plt.plot(p[0], p[1], 'bx')

        #plt.show()
        

        return points
    #...........................................................................
    # selecting significant points..............................................
    else:
        x = []
        y = []
        for p in points:
            x.append(p[0])
            y.append(p[1]) 

        plt.plot(x,y,'ro')
        #plt.show()

        #...................first derivative....................................
        slopes      = [0]
        ch_points   = [(0,0)]
        for i in range(1,len(x)):
            xdif    = x[i] - x[i-1]
            ydif    = y[i] - y[i-1]
            slope   = ydif / (xdif + 1e-10)
            slopes.append(slope)
            ch_points.append((i,slope))

        #plt.plot(range(len(x)),slopes)
        #plt.show()

        #.......................second derivative...............................
        ddx = [0]
        for i in range(1, len(slopes)):
            ddx.append(abs(slopes[i-1]-slopes[i]))
        
        #plt.plot(range(len(ddx)), ddx)
        c = sorted(range(len(ddx)), key=lambda k: ddx[k])
        c.reverse()
        c =  [0] + c[:(size-1)]

        if not (numc - 1) in c:
            c[size-1] = (numc - 1)

        c = sorted(c)
       
        new_points = []
        for i in c:
            new_points.append( points[i] )
    
        #plt.plot(x,y,'ro')
        #for i in range(size):
        #    plt.plot(x[c[i]], y[c[i]], 'bx')
        
        #plt.show()
        return new_points
   
 ################################################################################
################################################################################
'''
histogram image
file = tracking file
type = yml | prop
'''
def featTrackletHistoImage(file, type, size):
    
    
    centers = featTrackletMatrix(file, type)
    numc    = len(centers)

    #filling or selecting the centers to normalize the center number
    centers = pointVectorFill (centers, size)
    
    #...........................................................................
    nori        = 8
    nradius     = 12                            #image cannot exceed 4096
    binflat     = nori * nradius
       
    #binori      = 360 / nori
    
    radius_mat  = np.zeros( (size, size) )
    angles_mat  = np.zeros( (size, size) )

    #for each candidate point 
    posi        = 0 
    for i in range(size):
        posj    = 0
        for j in range(size):
            if not i == j:
                histo   = np.zeros( (1, binflat) )

                yside   = centers[i][1] - centers [j][1] 
                xside   = centers[i][0] - centers [j][0]

                radius  = mt.sqrt( (xside * xside) + ( yside * yside))
                angle   = mt.atan2( yside, xside) * 180 / mt.pi

                #if angle <  0:
                #    angle += 360

                
                radius_mat[posi][posj] = mt.log2(radius+(1e-10))
                angles_mat[posi][posj] = angle 

                
            posj += 1
        posi += 1
    
    
    #img2 = plt.imshow(radius_mat)              
    #plt.show()
    #img1 = plt.imshow(angles_mat)              
    #plt.show()
    

    #cv2.imshow('d', vari)
    #cv2.imshow('y:/outtest.png', an)
    #cv2.waitKey()

    return [radius_mat, angles_mat], numc, centers

