'''
Scuba Probe Technologies LLC, 2015
@author: dziegler

'''
import cv2
import numpy as np
import random
import ctypes  # An included library with Python install.
import scipy.misc
from scipy.optimize import curve_fit
from scipy.signal import find_peaks_cwt
from scipy.interpolate import interp1d
from time import sleep
from copy import deepcopy
from .measurement import Measurement
import matplotlib.pyplot as plt
from sklearn import svm
from skimage import img_as_ubyte

class AutoFocus(Measurement):
    name = "AutoFocus"
   
    def setup(self):
        self.display_update_period = 0.5 #seconds
        self.lever_vec_sorted = []
              
        # add logged quantities
        self.AF_save_images=self.add_logged_quantity(name="AF Save images", dtype=bool, ro=False)
        
        #connect to gui
        self.AF_save_images.connect_bidir_to_widget(self.gui.ui.AF_save_images_checkBox)
        self.gui.ui.AutoFocus_pushButton.clicked.connect(self.start)
        self.gui.ui.AutoFocus_Fine_pushButton.clicked.connect(self.Fine_Focus)
        self.gui.ui.AutoFocus_Coarse_pushButton.clicked.connect(self.Coarse_Focus)
                
        self.picture_ready, self.picture_displayed, self.start_flag, self.end_flag = False, False, True, False      
        
    def FindFocus(self, z_step, z_range, z_motion_dir, CenterRange, FocusMetric, MotionStage, LimitFocusRegion, FocusPos, WindowSize):
        print "Finding Focus..."
        Nsteps = int(np.ceil(z_range/z_step))
        
        if MotionStage=='MCL':
            sleeptime=0.1   #pause-time in between each ASI z-step
            if CenterRange:
                self.gui.MCLstage_hc.move_rel_Z(-z_motion_dir*float(Nsteps*z_step)/2.)
                sleep(3*sleeptime)
        elif MotionStage=='ASI':
            sleeptime=0.15   #pause-time in between each ASI z-step
            if CenterRange:
                self.gui.stage_hc.moveRelZ_mmNoWait(-z_motion_dir*float(Nsteps*z_step)/2./1000.)
                sleep(3*sleeptime)
        
        FocusData = np.zeros((Nsteps+1,2))
        for i in range(Nsteps+1):
            if MotionStage=='MCL':
                posZ = self.gui.MCLstage_hc.get_pos_Z()
            elif MotionStage=='ASI':
                #print self.gui.stage_hc.getPosZ_mm()
                posZ = self.gui.stage_hc.getPosZ_mm()*1000.
                #posZ = self.gui.stage_hc.posZ.read_from_hardware()
            
            img = cv2.cvtColor(self.gui.firefly_hc.takePicture(), cv2.COLOR_BGR2GRAY)            
            if LimitFocusRegion:
                img = self.cropWindow(img, FocusPos, WindowSize)
            
            FocusData[i][0] = posZ
            if FocusMetric=='SGMM':
                if LimitFocusRegion:
                    Threshold = 6000.*float(WindowSize)**2/1228800. #full size image 1228800pxls
                else:
                    Threshold = 6000.
                FocusData[i][1] = self.SGMM(img, 3, Threshold)
            elif FocusMetric=='FFT':
                FocusData[i][1] = self.fft_filter(img,6)
            elif FocusMetric=='S':
                FocusData[i][1] = -self.entropy(img)
            print "[Z-Pos, Focus]:", FocusData[i]
        
            if MotionStage=='MCL':
                self.gui.MCLstage_hc.move_rel_Z(z_motion_dir*z_step)
                sleep(sleeptime)
            elif MotionStage=='ASI':
                self.gui.stage_hc.moveRelZ_mmNoWait(z_motion_dir*z_step/1000.)
                sleep(sleeptime)
            
        f = interp1d(FocusData[:,0], FocusData[:,1], kind='cubic')
        x = np.linspace(min(FocusData[:,0]), max(FocusData[:,0]),1000)
        focus_pos = x[np.argmax(f(x))]
        opt_focus = f(focus_pos)
        focus_success = self.success_metric(opt_focus, FocusMetric) 
                
        if MotionStage=='MCL':
            self.gui.MCLstage_hc.set_pos_Z(focus_pos)
        elif MotionStage=='ASI':
            self.gui.stage_hc.moveToZ_mm(focus_pos/1000.)

        sleep(3*sleeptime)

        return opt_focus, focus_success

    def success_metric(self, opt_focus, FocusMetric):
        if FocusMetric == 'FFT':
            SUCCESS = True
        elif FocusMetric == 'SGMM':
            SUCCESS = True
        elif FocusMetric == 'S':
            SUCCESS = True
        return SUCCESS
            
    def Fine_Focus(self):
        print "Start Fine AutoFocus"
        stepsize=self.gui.ui.AutoFocus_Fine_stepsize_doubleSpinBox.value()
        range = stepsize*int(self.gui.ui.AutoFocus_Fine_steps_doubleSpinBox.value())
        
        self.FindFocus(stepsize, range, -1, True, 'SGMM', 'MCL', False, None, None)
    
    def Coarse_Focus(self):
        print "Start Coarse AutoFocus"
        stepsize=self.gui.ui.AutoFocus_Coarse_stepsize_doubleSpinBox.value()
        range=stepsize*int(self.gui.ui.AutoFocus_Coarse_steps_doubleSpinBox.value())
    
        self.FindFocus(stepsize, range, -1, True, 'FFT', 'ASI', False, None, None)
              
    def SGMM(self, img, ksize, T):
        sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize)
        sobely = cv2.Sobel(img,cv2.CV_64F,0,1,ksize)
        sobel_sqrd = sobelx*sobelx + sobely*sobely
        R = np.sum(np.where(sobel_sqrd>T, sobel_sqrd**0.5, 0))
        return R

    def entropy(self,img):
        hist = cv2.calcHist([img],[0],None,[256],[0,256])
        P = hist/np.sum(hist)
        logP = np.log(P)
        logP[logP==-np.inf] = 0
        S = -np.dot(np.transpose(P), logP)    
        return S[0][0]
  
    def fft_filter(self, img, kmax):
        
        fft_shift = np.fft.fftshift(np.fft.fft2(img))
        P = np.abs(fft_shift)**2
        nrows = P.shape[0]
        ncols = P.shape[1]
        P[nrows/2][ncols/2] = 0. #Remove DC component
        
        lfc = 0. 
        for i in range(nrows/2-(kmax+1),nrows/2+(kmax+1)):
            for j in range(ncols/2-(kmax+1), ncols/2+(kmax+1)):
                if (float(nrows)/float(ncols)*(i-nrows/2))**2+(j-ncols/2)**2 <= kmax**2:       
                    lfc += P[i][j]                
        hfc = np.sum(P)-lfc
        return hfc
  
    def cropWindow(self, img, center_pos, window_size):
        window_size -= window_size%2    #force even value 
        return img[center_pos[0]-window_size/2:center_pos[0]+window_size/2, center_pos[1]-window_size/2:center_pos[1]+window_size/2]
  
    def PlotAutoFocus(self, lst):
        #import matplotlib.pyplot as plt
        plt.plot(lst)
        plt.ylabel('Focus')
        plt.show()             
        
    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.AutoFocus_pushButton)
            self.start_flag = False
               
        if self.end_flag:
            self.markButton(self.gui.ui.AutoFocus_pushButton, on=False)
 
    def _run(self):
        print "run Auto-Focus"
        self.picture_ready, self.picture_displayed, self.start_flag, self.end_flag = False, False, True, False
        self.FF_SUCCESS, self.FF_opt_focus, self.CF_SUCCESS, self.CF_opt_focus = False, 0, False, 0
        
        if self.gui.lsarduino_hc.topLED_intensity.val!=30 or self.gui.lsarduino_hc.bottomLED_intensity.val!=0:
            self.gui.lsarduino_hc.topLED_intensity.update_value(30)
            self.gui.lsarduino_hc.bottomLED_intensity.update_value(0)
            sleep(1.2)
        
        #ASI_currentPosZ = self.gui.stage_hc.posZ.read_from_hardware()
        ASI_currentPosZ = self.gui.stage_hc.getPosZ_mm()*1000.
        ASI_roughFocusPosZ = self.gui.ui.ASI_stage_RoughFocusZ_doubleSpinBox.value()
        sweep_range = 3000.
        if int(self.gui.lever_detection.lever_nb.val)==1 or abs(ASI_currentPosZ-ASI_roughFocusPosZ) > 3000:
            check5 = ctypes.windll.user32.MessageBoxA(0, "Commit large Sweep about Rough Focus Position:"+str(ASI_roughFocusPosZ-sweep_range/2)+"<z<"+str(ASI_roughFocusPosZ+sweep_range/2)+"?", "Proceed?", 0x03) #6 Yes, 7 No, 2 cancel
            if check5==6:   #clicked 'yes'    
                self.gui.stage_hc.moveToZ_mm((ASI_roughFocusPosZ+sweep_range/2)/1000.)
                sleep(0.3)
                self.FindFocus(100., sweep_range, -1, False, 'FFT', 'ASI', False, None, None)
            elif check5==2:  #clicked 'cancel'
                self.end_flag = True
                print "Auto-Focus Aborted"
                return None #terminate auto-focus
            
        #Coarse Focus
        self.CF_opt_focus, self.CF_SUCCESS = self.FindFocus(25., 500., -1, True, 'FFT', 'ASI', False, None, None)
    
        #Fine Focus
        self.FF_opt_focus, self.FF_SUCCESS = self.FindFocus(3., 60., -1, True, 'SGMM', 'MCL', False, None, None)
           
        try:
            lever_idx = self.gui.lever_detection.getLeverIndex(self.gui.lever_detection.lever_nb.val)
            self.lever_vec_sorted[lever_idx] = [self.FF_SUCCESS, self.FF_opt_focus, self.CF_SUCCESS, self.CF_opt_focus]
        except:
            print "Could not access lever number/index to store auto-focus data..."
           
        self.end_flag = True
        print "Auto-Focus Done"
                     
        if self.gui.ui.AutoFocus_continue_checkBox.isChecked():
            if self.FF_SUCCESS:
                self.gui.ui.LeverAlign_pushButton.click()
            else:
                self.gui.ui.LeverDetection_gotoNextLever_pushButton.click()
                