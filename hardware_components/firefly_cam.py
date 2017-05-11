'''
Created on Feb 19, 2015

@author: DZiegler  dominik@scubaprobe.com  
'''
'''
Created on Feb 17, 2015

@author:  DZiegler  dominik@scubaprobe.com 
'''

import numpy as np
import cv2
from scipy.optimize import minimize
from time import sleep
import ctypes
from . import HardwareComponent
try: import flycapture2 as fc2
except Exception as err: 
    print "Cannot load required modules for Point Grey Cam:", err

class PointGreyCamComponent(HardwareComponent): #object-->HardwareComponent
    name = 'Point Grey Firefly Cam'
    
    def setup(self):        
        #add logged quantities
        self.firefly_cam_connectivity = self.add_logged_quantity(name = "pGray Firefly Camera connectivity", dtype=bool, ro=False)
        with open('equipment/FireFlyCameraCalibration.txt','r') as f:
            try: calib = [float(i) for i in f.read().split("\t")]
            except: calib = [9.,  9., 0.]  #7.37 for 40x objective
        self.cam_scaling_x = self.add_logged_quantity(name='Firefly scaling x ', initial = calib[0], dtype=float, fmt='%1.2f', ro=False, unit='px/um',  vmin=0, vmax=20)
        self.cam_scaling_y = self.add_logged_quantity(name='Firefly scaling y', initial = calib[1], dtype=float, fmt='%1.2f', ro=False, unit='px/um',  vmin=0, vmax=20)
        self.cam_angle_deg = self.add_logged_quantity(name='Firefly angle offset', initial = calib[2], dtype=float, fmt='%2.4f', ro=False, unit='deg',  vmin=-99, vmax=99)
        self.Firefly_save_images = self.add_logged_quantity(name = "Save Firefly images", dtype=bool, ro=False)
        
        #connect to GUI
        self.firefly_cam_connectivity.connect_bidir_to_widget(self.gui.ui.firefly_cam_connected_checkBox)
        self.cam_scaling_x.connect_bidir_to_widget(self.gui.ui.Firefly_cam_scaling_x_doubleSpinBox)
        self.cam_scaling_y.connect_bidir_to_widget(self.gui.ui.Firefly_cam_scaling_y_doubleSpinBox)
        self.cam_angle_deg.connect_bidir_to_widget(self.gui.ui.Firefly_cam_angle_deg_doubleSpinBox)
        self.Firefly_save_images.connect_bidir_to_widget(self.gui.ui.Firefly_save_images_checkBox)
        self.gui.ui.Firefly_SaveImage_pushButton.clicked.connect(self.saveImage)
        self.gui.ui.AutoCalibFireFlyCam_pushButton.clicked.connect(self.CalibrateCamera)
        
        self.setup_figure()
        self.gui.ui.Firefly_videoStream_checkBox.setChecked(True)
        
    def connect(self):
        try:
            if self.debug: print "connecting to Point Grey Cam"
            # Open connection to hardware
            self.cam = self.initializeCamera() 
            self.cam.start_capture()
            self.isready = True
        except: 
            print "maybe camera is still running"
            
        print 'connected to ', self.name
    
    def disconnect(self):
        # disconnect logged quantities from hardware
        #disconnect hardware
        try:self.cam.stop_capture()
        except: print "could not stop Cam"
        self.cam.disconnect()
        
        # clean up hardware object
        del self.cam
        print 'disconnected ', self.name    
    
    def initializeCamera(self):
        cam = fc2.Context()
        num_cam = cam.get_num_of_cameras()
        if num_cam == 0:
            raise ValueError("No Firefly Camera detected.")
        elif num_cam>1:
            print "Warning: Multiple Firefly Cameras detected. First one picked."
        cam.connect(*cam.get_camera_from_index(0))
        #cam.set_video_mode_and_frame_rate(fc2.VIDEOMODE_1280x960Y8, fc2.FRAMERATE_7_5)
        cam.set_video_mode_and_frame_rate(fc2.VIDEOMODE_1280x960Y8, fc2.FRAMERATE_15)
        #cam.set_video_mode_and_frame_rate(fc2.VIDEOMODE_640x480Y8, fc2.FRAMERATE_30)
#         self.cam.set_property()
        return cam    
  
    def saveCalibration(self):
        try: 
            f = open('equipment/FireFlyCameraCalibration.txt','w')
            f.write(str(self.cam_scaling_x.val) + "\t" + str(self.cam_scaling_y.val) + "\t"
                    +str(self.cam_angle_deg.val))
            f.close()
        except:
            print "Could not save Firefly calibration values to disk" 

    def takePicture(self):
        if self.gui.ui.Firefly_videoStream_checkBox.isChecked():
            return self.img_rgb
        else:
            return self.retrieve_buffer()
        
    def retrieve_buffer(self):
        try: 
            raw_img = fc2.Image()
            self.cam.retrieve_buffer(raw_img)
            #img = self.cam.GrabNumPyImage('bgr')
        except:
            print "No open camera found, need to initialize camera and start capture"
            self.cam = self.initializeCamera() 
            #self.cam.stop_capture()
            self.cam.start_capture()
            raw_img = fc2.Image()
            self.cam.retrieve_buffer(raw_img)
            #self.cam.stop_capture() #! when adding a stop the regular camera viewer needs to be reconnected. 
            self.cam.disconnect()
        img = np.array(raw_img)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)
        b,g,r = cv2.split(img_bgr)
        img_rgb=cv2.merge([r,g,b])
        #img=cv2.transpose(img_rgb)
        img=cv2.flip(cv2.transpose(img_rgb), 1)
        #cv2.Flip(timg,timg,flipMode=0)
        return img #cv2.flip(cv2.merge([r,g,b]), 1)

    def saveImage(self):
        filename = str(self.gui.ui.SaveImage_Filename_lineEdit.text())
        r,g,b = cv2.split(self.takePicture())
        image = cv2.merge([b,g,r])
        cv2.imwrite('Firefly_Snapshots/'+filename, image)
        return
                  
    def setup_figure(self):      
        self.FireflyStreamFig = self.gui.add_figure("Firefly Video Stream", self.gui.ui.Firefly_Image_groupBox, toolbar=False)
        self.ax5 = self.FireflyStreamFig.add_subplot(1,1,1)
        self.ax5.set_axis_off()
                    
    def refreshVideoStream(self):
        if self.gui.ui.Firefly_videoStream_checkBox.isChecked():
            #b,g,r = cv2.split(self.gui.firefly_hc.takePicture())       # get b,g,r
            self.img_rgb = self.retrieve_buffer()     
            
            img_rgb_copy = self.img_rgb.copy()
                
            laserposition=(int(self.gui.lever_cutting.laser_posX.val),int(self.gui.lever_cutting.laser_posY.val))
            if self.gui.lever_cutting.waveform_ready == False:
                    self.gui.lever_cutting.refreshWaveform()
                    
            cv2.polylines(img_rgb_copy, self.gui.lever_cutting.waveform, False, (0,255,255), 2)
            cv2.circle(img_rgb_copy, laserposition, 12, (255, 0, 0), thickness=2, lineType=1, shift=0)

            h,w = img_rgb_copy.shape[:2]
            zoom = int(self.gui.ui.VideoStream_Zoom_comboBox.currentText()[0])
            if zoom > 1:
                img_rgb_copy = img_rgb_copy[laserposition[1]-h/(2*zoom):laserposition[1]+h/(2*zoom), laserposition[0]-w/(2*zoom):laserposition[0]+w/(2*zoom), :]
            
            if not hasattr(self, 'img_rgb_imshow'):
                self.img_rgb_imshow = self.ax5.imshow(img_rgb_copy)
            else:
                self.img_rgb_imshow.set_data(img_rgb_copy)
            self.FireflyStreamFig.canvas.draw()       
  
    def CalibrateCamera(self):
        def get_pxl_shift(img1,img2):
            img1 = cv2.bilateralFilter(img1,9,75,75)
            img2 = cv2.bilateralFilter(img2,9,75,75)
            h,w = img2.shape
            #yoff, xoff = ir.cross_correlation_shifts(img1,img2)
            method = eval('cv2.TM_SQDIFF')
            h,w = img1.shape
            template = img1[int(0.15*h):int(0.85*h), int(0.15*w):int(0.85*w)]
            # Apply template Matching
            res = cv2.matchTemplate(img2,template,method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            yoff, xoff = (min_loc[0]-int(0.15*w), min_loc[1]-int(0.15*h))
            return (yoff,-xoff)
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

        um_shifts = [(15.,0.),(0.,15.),(-15.,0.),(0.,-15.), (15.,0.),(0.,-15.),(-15.,0.),(0.,15.), (-15.,0.),(0.,-15.),(15.,0.),(0.,15.), (-15.,0.),(0.,15.),(15.,0.),(0.,-15.)]
        pxl_shifts = []
        calib_images = []
        calib_images.append(self.retrieve_buffer())
        for i in range(len(um_shifts)):
            print "move:", um_shifts[i]
            self.gui.MCLstage_hc.move_rel_XY(um_shifts[i][0], um_shifts[i][1])
            sleep(1)
            calib_images.append(self.retrieve_buffer())
            pxl_shifts.append(get_pxl_shift(cv2.cvtColor(calib_images[i], cv2.COLOR_RGB2GRAY),cv2.cvtColor(calib_images[i+1], cv2.COLOR_RGB2GRAY)))
            print "pxl offset:", pxl_shifts[i]
        
        myargs = (np.array(um_shifts),np.array(pxl_shifts))
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
            print "error in firefly camera calibration, most likely not in focus, or communication error"
        return
