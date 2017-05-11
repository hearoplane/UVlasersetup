import numpy as np
import pandas as pd
import os
import image_registration as ir
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import cv2
from time import sleep
from skimage import img_as_ubyte
from copy import deepcopy

def rotateImage(image, angle):#parameter angel in degrees 
    #print image[0]
    angle=float(angle)
    height,width=image.shape[0],image.shape[1]
    newwidth=float(width)*np.cos(angle/180*np.pi)+float(height)*np.sin(angle/180*np.pi)
    borderw= int(np.abs((newwidth-float(width))/2))
    newheight=float(height)*np.cos(angle/180*np.pi)+float(width)*np.sin(angle/180*np.pi)
    borderh= int(np.abs((newheight-float(height))/2))
    image_ = cv2.copyMakeBorder(image,borderh,borderh,borderw,borderw, cv2.BORDER_REPLICATE)
    height_, width_= image_.shape[0],image_.shape[1]
    image_center = (width/2+borderw, height/2+borderh)#rotation center
    rot_mat = cv2.getRotationMatrix2D(image_center,angle, 1)
    result = cv2.warpAffine(image_, rot_mat, (width_,height_), flags=cv2.INTER_LINEAR)
    result= result[borderh:height_-borderh,borderw:width_-borderw]
    return result


im = cv2.imread("B642_ScubaE_C1.png") 
img = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
h,w = img.shape[:2]
        
bkg =  np.array([np.mean(im[:h/7,:,0]), np.mean(im[:h/7,:,1]), np.mean(im[:h/7,:,2])])
img_contrast =  np.sum(np.abs(im-bkg), axis=2)
img_contrast /= np.max(img_contrast)
img_contrast = img_as_ubyte(img_contrast)
img_contrast_rot = rotateImage(img_as_ubyte(img_contrast), 2.3)

plt.imshow(img_contrast_rot)
plt.show()
plt.clf()

tl = np.array([330,370])
br = tl + np.array([320,320])

plt.imsave('Scuba_E_template.png', img_contrast_rot[tl[1]:br[1],tl[0]:br[0]], cmap=plt.cm.gray)

cv2.rectangle(img_contrast_rot,(tl[0],tl[1]), (br[0],br[1]), 255, 5)
cv2.circle(img_contrast_rot,(tl[0]+160,tl[1]+217), 10, (255), 10)

plt.imshow(img_contrast_rot)
plt.show()
plt.clf()

plt.imshow(img_contrast_rot[tl[1]:br[1],tl[0]:br[0]])
plt.show()
plt.clf()

