
import numpy as np
import image_registration as ir
from scipy import misc
from skimage.color import rgb2gray

im1 = np.array(np.array(misc.imread('reg.tif')).astype('float'))#[::-1,:])#y is reversed
im2 = np.array(np.array(misc.imread('regtest.tif')).astype('float'))
im1=rgb2gray(im1)
im2=rgb2gray(im2)

#the cross_correlation_shifts will tell how many pixels off in x and y the one image is from the other
ccshift=ir.cross_correlation_shifts(im1,im2)

print ccshift