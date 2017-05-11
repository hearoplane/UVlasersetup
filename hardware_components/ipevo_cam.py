'''
Created on Sept 24, 2016

@author: SSedighi  sina@scubaprobe.com  
'''

import numpy as np
import cv2
import image_registration as ir
from scipy.optimize import minimize
import time
import ctypes
from . import HardwareComponent

class IpevoCamComponent(HardwareComponent): #object-->HardwareComponent
    name = 'Ipevo Cam'
    
    def setup(self):        
        #add logged quantities
        self.ipevo_cam_connectivity = self.add_logged_quantity(name = "Ipevo Camera connectivity", dtype=bool, ro=False)
        
        with open('equipment/IpevoCameraCalibration.txt','r') as f:
            try: calib = [float(i) for i in f.read().split("\t")]
            except: 
                ctypes.windll.user32.MessageBoxA(0, "There was a problem loading the ASI Stage Ipevo-Camera Calibration. Default values loaded.", "Error", 0x0) #6 Yes, 7 No 2 cancel
                calib = [-6.83,  -13.17, 28.899, 28.889, 0.0]
        self.cam_offset_x = self.add_logged_quantity(name='Ipevo offset x', initial = calib[0], dtype=float, fmt='%1.2f', ro=False, unit='mm',  vmin=-70, vmax=70)
        self.cam_offset_y = self.add_logged_quantity(name='Ipevo offset y', initial = calib[1], dtype=float, fmt='%1.2f', ro=False, unit='mm',  vmin=-70, vmax=70)
        self.cam_scaling_y = self.add_logged_quantity(name='Ipevo scaling y', initial = calib[2], dtype=float, fmt='%2.4f', ro=False, unit='pxl/mm',  vmin=-99, vmax=99)
        self.cam_scaling_x = self.add_logged_quantity(name='Ipevo scaling x', initial = calib[3], dtype=float, fmt='%2.4f', ro=False, unit='pxl/mm',  vmin=-99, vmax=99)
        self.cam_angle_deg = self.add_logged_quantity(name='Ipevo angle offset', initial = calib[4], dtype=float, fmt='%1.4f', ro=False, unit='deg',  vmin=-180, vmax=180)
        
        #connect to GUI
        self.gui.ui.AutoCalibIpevoCam_pushButton.clicked.connect(self.AutoCalibCam)
        self.ipevo_cam_connectivity.connect_bidir_to_widget(self.gui.ui.ipevo_cam_connected_checkBox)
        self.cam_offset_x.connect_bidir_to_widget(self.gui.ui.Ipevo_cam_offset_x_doubleSpinBox)
        self.cam_offset_y.connect_bidir_to_widget(self.gui.ui.Ipevo_cam_offset_y_doubleSpinBox)
        self.cam_scaling_x.connect_bidir_to_widget(self.gui.ui.Ipevo_cam_scaling_x_doubleSpinBox)
        self.cam_scaling_y.connect_bidir_to_widget(self.gui.ui.Ipevo_cam_scaling_y_doubleSpinBox)
        self.cam_angle_deg.connect_bidir_to_widget(self.gui.ui.Ipevo_cam_angle_deg_doubleSpinBox)
        
        self.frame_w = 3268 # 640, 800, 1024, 1280, 1600, (1920, 2048, 2592), 3264
        self.frame_h = 2448 # 480, 600,  768,  720, 1200, (1080, 1536, 1944) 2448

    def connect(self):
        if self.debug: print "connecting to Ipevo Cam"
        
        # Open connection to hardware
        self.cam = cv2.VideoCapture(0)
        self.ConfigureCameraSettings()
        
        self.cam_offset_x.hardware_set_func = self.gui.lever_detection.gotoUpdatedLeverPos
        self.cam_offset_y.hardware_set_func = self.gui.lever_detection.gotoUpdatedLeverPos
        self.cam_scaling_x.hardware_set_func = self.gui.lever_detection.gotoUpdatedLeverPos
        self.cam_scaling_y.hardware_set_func = self.gui.lever_detection.gotoUpdatedLeverPos
        self.cam_angle_deg.hardware_set_func = self.gui.lever_detection.gotoUpdatedLeverPos
        
        print 'connected to:', self.name   
    
    def disconnect(self):
        # disconnect logged quantities from hardware
        #disconnect hardware
        self.cam.release()
        assert not self.cam.isOpened(), "Could not close Ipevo Cam"
        
        # clean up hardware object
        del self.cam
        print 'disconnected', self.name    
    
    def ConfigureCameraSettings(self):
        assert self.cam.isOpened(), "Ipevo cam could not connect, maybe Presenter is still running"
        self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.frame_w)   # 640, 800, 1024, 1280, 1600, (1920, 2048, 2592) #3264
        self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.frame_h)  # 480, 600,  768,  720, 1200, (1080, 1536, 1944) #2448
        #cap.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, -1)
        #cap.set(cv2.cv.CV_CAP_PROP_CONTRAST, 10)
        #cap.set(cv2.cv.CV_CAP_PROP_SATURATION, 10)       
       
    def takePicture(self):
        assert self.cam.isOpened(), "Ipevo cam is not connected, maybe Presenter is still running"
        ramp_frames = 5     #video capture frames are slightly delayed...
        for i in range(ramp_frames):
            _, temp = self.cam.read()
        ret, camera_capture = self.cam.read()
        #assert img is not None, "Ipevo camera is not connected"
        return camera_capture
    
    def saveCalibration(self):
        try: 
            with open('equipment/IpevoCameraCalibration.txt','w') as f:       
                f.write(str(self.cam_offset_x.val) + "\t" + str(self.cam_offset_y.val) + "\t"
                        + str(self.cam_scaling_x.val) + "\t" + str(self.cam_scaling_y.val) + "\t" 
                        + str(self.cam_angle_deg.val))
            print "Saved Ipevo Cam Calibration Data"
        except:
            print "Could not save Ipevo Cam Calibration data (Error in opening file)"

    def AutoCalibCam(self):
        if not(self.gui.ui.ipevo_cam_connected_checkBox.isChecked()):
            self.gui.ui.firefly_cam_connected_checkBox.setChecked(False)
            self.gui.ui.Firefly_videoStream_checkBox.setChecked(False)
            self.gui.ui.ipevo_cam_connected_checkBox.setChecked(True) 
            revert_to_firefly = True
        else:
            revert_to_firefly = False
            
        self.gui.ui.backlight_state_checkBox.setChecked(True)
        self.gui.lever_detection.moveToTopViewCamPosition()
        TopImg = self.takePicture()
        box_x, box_y, box_w, box_h = self.gui.lever_detection.isolateBox(TopImg)
        self.CalibrateCamera(np.array([box_x,box_y]), np.array([box_x+box_w,box_y+box_h]))
 
        if revert_to_firefly:
            self.gui.ui.ipevo_cam_connected_checkBox.setChecked(False) 
            self.gui.ui.firefly_cam_connected_checkBox.setChecked(True)
            self.gui.ui.Firefly_videoStream_checkBox.setChecked(True)
 
    def CalibrateCamera(self, FOV_TL, FOV_BR):
        def get_pxl_shift(img1,img2):
            img1 = cv2.bilateralFilter(img1,9,75,75)
            img2 = cv2.bilateralFilter(img2,9,75,75)
            yoff, xoff = ir.cross_correlation_shifts(img1,img2)
            return (-yoff,-xoff)
        def costfunc(M, X, Y):
            """
            M[0] = M11 = sx*cos(theta), 
            M[1] = M12 = -sx*sin(theta)
            M[2] = M21 = sy*sin(theta)
            M[3] = M22 = sy*cos(theta)
            X[0] = mm_x
            X[1] = mm_y
            Y[0] = pxl_x
            Y[1] = pxl_y
            """
            T = np.transpose(M.reshape((2,2)))
            Y_calc = np.dot(X,T)
            return np.sum((Y_calc-Y)*(Y_calc-Y))
        
        mm_shifts = [(2.5,0.),(0.,2.5),(-2.5,0.),(0.,-2.5),(2.5,0.),(0.,-2.5),(-2.5,0.),(0.,2.5)]
        pxl_shifts = []
        calib_images = []
        TopImg = self.takePicture()
        calib_images.append(TopImg[FOV_TL[1]:FOV_BR[1],FOV_TL[0]:FOV_BR[0]])
        self.gui.lever_detection.update_figure(calib_images[0])
        for i in range(len(mm_shifts)):
            self.gui.stage_hc.moveRelXY_mm(mm_shifts[i][0], mm_shifts[i][1])
            TopImg = self.takePicture()
            calib_images.append(TopImg[FOV_TL[1]:FOV_BR[1],FOV_TL[0]:FOV_BR[0]])
            self.gui.lever_detection.update_figure(calib_images[i+1])
            pxl_shifts.append(get_pxl_shift(cv2.cvtColor(calib_images[i], cv2.COLOR_RGB2GRAY),cv2.cvtColor(calib_images[i+1], cv2.COLOR_RGB2GRAY)))
            print "move:", mm_shifts[i]
            print "pxl offset:", pxl_shifts[i]
        
        myargs = (np.array(mm_shifts),np.array(pxl_shifts))
        initial_guess = np.random.rand(4)   
        res = minimize(costfunc, initial_guess, args=myargs)
        M = res.x.reshape((2,2))
        U,S,V = np.linalg.svd(M)  #Extract scale components S=[Sx,Sy]
        R = np.dot(U,np.transpose(V))  #Extract rotation matrix = UV'
        
        cam_angle = np.arctan(-R[0][1]/R[0][0]) if abs(R[0][1])<abs(R[0][0]) else np.arctan(-R[0][0]/R[0][1])     #assuming that angle ~ 0 degrees
        cam_scalings = S if abs(R[0][1])<abs(R[0][0]) else S[::-1]
        
        try: 
            self.cam_angle_deg.update_value(180./np.pi*cam_angle)
            self.cam_scaling_x.update_value(cam_scalings[0])
            self.cam_scaling_y.update_value(cam_scalings[1])
            self.saveCalibration()
        except:             
            print "error in camera calibration, most likely the Presenter software is open, not in focus"
        return
              