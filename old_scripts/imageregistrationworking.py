#from PIL import Image

#from PIL import shape

import numpy as np
import cv2
import pandas as pd
import image_registration as ir
import matplotlib.pyplot as plt

class ClassyIR(object):

    def __init__(self, img):
        self.img=img
       

def run(self):
    print "run"
    import cv2
    self.img = cv2.imread('ref.tif',0) #0= loads it as grayscale #ref is where we want to have cantilever
    self.img_ = cv2.imread('reftest3.tif',0) #0= loads it as grayscale
    print self.img is None
    rows,cols = self.img.shape

    angle=-11
    M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
    dst = cv2.warpAffine(self.img,M,(cols,rows))

    ccshift=ir.cross_correlation_shifts(self.img,self.img_)
    print ccshift
    correction_mm=(-ccshift[0]/3.85,-ccshift[1]/3.85/2) #dont understand factor 2 here. Output in y seems random. 
    print "The sample needs to move", correction_mm, "Microns"
    #self.img = cv2.imread('ref.tif',0) #0= loads it as grayscale #ref is where we want to have cantilever
    #self.img_ = cv2.imread('reftest3.tif',0) #0= loads it as grayscale
    #rows,cols = self.img.shape

    #angle=-11
    #M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
    #dst = cv2.warpAffine(self.img,M,(cols,rows))

    #ccshift=ir.cross_correlation_shifts(self.img,self.img_)
    #print ccshift
    #correction_mm=(-ccshift[0]/3.85,-ccshift[1]/3.85/2) #dont understand factor 2 here. Output in y seems random. 
    #print "The sample needs to move", correction_mm, "Microns"
    
if __name__ == "__main__":
    run(self)
#cv2.imshow('img',dst)
#cv2.waitKey(0)
#cv2.destroyAllWindows()
