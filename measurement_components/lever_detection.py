'''
Scuba Probe Technologies LLC, 2015
@author: dziegler

'''
import cv2
import copy
import numpy as np
from PySide import QtCore
from .measurement import Measurement
import matplotlib.pyplot as plt
import time
import os
import ctypes  # An included library with Python install.
import win32com.client
from numpy import arctan
from matplotlib.contour import ContourSet

class LeverDetection(Measurement):
    name = "Lever Detection"
  
    def setup(self):
        self.display_update_period = 0.5 #seconds
        self.lever_vec_sorted = []
        self.data_dict = {}
        self.setup_figure()
        self.photo_pos = np.array([+40.0, +0.0, 0.0])

                
        # add logged quantities
        self.lever_nb = self.add_logged_quantity(name = 'Lever number', initial = 0,dtype=int, fmt='%2d', ro=False,unit='', vmin=0, vmax=99)
        self.lever_angle_deg = self.add_logged_quantity(name = 'Lever angle', initial = 0, dtype=float, unit="deg", fmt='%2.1f', ro=True)
        self.number_of_rows = self.add_logged_quantity(name = 'Number of rows', initial = 0,dtype=int, unit="", ro=False)
        self.number_of_columns = self.add_logged_quantity(name = 'Number of columns', initial = 0,dtype=int, unit="", ro=False)
        self.nominal_lever_width = self.add_logged_quantity(name = 'Nominal lever width', initial = 25,dtype=float, fmt='%3.1f', ro=False, unit='um',  vmin=0, vmax=999)
        self.nominal_lever_length = self.add_logged_quantity(name = 'Nominal lever length', initial = 125, dtype=float, fmt='%3.1f', ro=False, unit='um',  vmin=0, vmax=999)
        self.relative_position = self.add_logged_quantity(name = 'Relative position', initial = 0.1, dtype=float, fmt='%0.2f', ro=False, unit='',  vmin=0, vmax=1)
        self.sum_threshold = self.add_logged_quantity(name = 'Sum threshold', initial = 0.6, dtype=float, fmt='%1.2f', ro=False, unit='V',  vmin=0, vmax=999)
        self.display_images = self.add_logged_quantity(name = "Display CV images", dtype=bool, ro=False)
        self.AutoCalibCam = self.add_logged_quantity(name = "Automatically Calibrate Camera", initial = True, dtype=bool, ro=False)
        self.auto_detect_rows_cols = self.add_logged_quantity(name= 'Auto-detect', dtype=bool, initial=True, ro=False)
        
        #connect to custom gui - NOTE:  these are not disconnected!     
        self.gui.ui.LeverDetection_DetectLevers_pushButton.clicked.connect(self.start)
        self.gui.ui.LeverDetection_stop_all_pushButton.clicked.connect(self.stopAll)
        self.gui.ui.LeverDetection_gotoNextLever_pushButton.clicked.connect(self.gotoNextLever)
        # connect logged quantities bidirectionals
        self.lever_nb.connect_bidir_to_widget(self.gui.ui.LeverDetection_lever_nb_doubleSpinBox)
        self.lever_nb.hardware_read_func = self.closestLever
        self.lever_nb.hardware_set_func =  self.gotoLever
        self.lever_angle_deg.connect_bidir_to_widget(self.gui.ui.LeverAngle_doubleSpinBox)
        self.number_of_rows.connect_bidir_to_widget(self.gui.ui.LeverDetection_number_of_rows_doubleSpinBox)
        self.number_of_columns.connect_bidir_to_widget(self.gui.ui.LeverDetection_number_of_columns_doubleSpinBox)
        self.relative_position.connect_bidir_to_widget(self.gui.ui.LeverDetection_relative_laser_position_doubleSpinBox)            
        self.display_images.connect_bidir_to_widget(self.gui.ui.display_images_checkBox)
        self.AutoCalibCam.connect_bidir_to_widget(self.gui.ui.LeverDetection_AutoCalibCam_checkBox)
        self.auto_detect_rows_cols.connect_bidir_to_widget(self.gui.ui.LeverDetection_auto_detect_checkBox)
        
    def stopAll(self):
        for meas_obj in [self.gui.lever_detection, self.gui.scan,
                         self.gui.fineTuneX, self.gui.fineTuneY,
                         self.gui.measureLever, self.gui.fineTuneAll,
                         self.gui.measureAll]:
            meas_obj.interrupt()     
        
    def moveToTopViewCamPosition(self):
        already_retracted = ctypes.windll.user32.MessageBoxA(0, "Will move objective to photo position and center Piezo stage", "Proceed?", 0x0 | 0x01) #6 Yes, 7 No 2 cancel
        if already_retracted==1: #Yes, Already retracted
            self.gui.stage_hc.moveToZ_mm(self.photo_pos[2])
            self.gui.stage_hc.moveToXY_mm(self.photo_pos[0], self.photo_pos[1])            
        elif already_retracted==2: 
            self.end_flag = True       
        return         
  
    def show_resized(self, name, img, factor, closeWindow):
        factor = int(factor)
        img_resized = cv2.resize(img,(img.shape[1]/factor, img.shape[0]/factor))
        cv2.imshow(name, img_resized)
        if closeWindow:
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    def crop_image(self,image,x,y,w,h):
        if len(image.shape)==3:
            return np.array(image[y:y+h,x:x+w,:])
        else:
            return np.array(image[y:y+h,x:x+w])    
         
    def isolateBox(self, image):
        print len(image.shape)
        if len(image.shape)==3:
            ret,thresh = cv2.threshold(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        else:
            ret,thresh = cv2.threshold(image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)        
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        chip_positions = []
        chip_areas = []
        for c in contours:
            if self.is_chip(c):
                M = cv2.moments(c)
                centroid = np.array([int(M['m10']/M['m00']), int(M['m01']/M['m00'])])
                chip_positions.append(centroid)
                chip_areas.append(M['m00'])
        assert len(chip_positions) > 0, "No chips detected..."
        
        chip_positions = np.asarray(chip_positions)
        chip_areas = np.asarray(chip_areas)
        deltax = (np.max(chip_positions[:,0])-np.min(chip_positions[:,0]))
        deltay = (np.max(chip_positions[:,1])-np.min(chip_positions[:,1]))
        chip_width = int(np.sqrt(np.mean(chip_areas)))
        w = deltax + 4*chip_width
        h = deltay + 4*chip_width
        x = np.min(chip_positions[:,0]) - int(2*chip_width)
        y = np.min(chip_positions[:,1]) - int(2*chip_width)
        return x,y,w,h                  

    def is_chip(self, contour):
        hu_mean = np.array([2.11082697e-01, 1.82799986e-02, 9.21592823e-06, 6.01079988e-07, 8.52888697e-13, 2.14478185e-08, -9.50632130e-13])
        hu_std = np.array([4.82291426e-03, 1.95037952e-03, 5.30055288e-06, 4.96603042e-07, 3.44184275e-12, 7.09253405e-08, 3.01636045e-12])

        area = cv2.contourArea(contour)
        hu = cv2.HuMoments(cv2.moments(contour)).flatten()
        hu_dev = (hu-hu_mean)/hu_std #normalized deviation
        hu_err = np.dot(hu_dev,hu_dev) #squared error
        
        return bool((hu_err < 150.) and (500 < area < 20000))

    def findLevers(self):
        def in_hull(p, hull):
            """
            Test if points in `p` are in `hull`
            `p` should be a `NxK` coordinates of `N` points in `K` dimensions
            `hull` is either a scipy.spatial.Delaunay object or the `MxK` array of the 
            coordinates of `M` points in `K`dimensions for which Delaunay triangulation
            will be computed
            """
            from scipy.spatial import Delaunay
            if not isinstance(hull,Delaunay):
                hull = Delaunay(hull)
            return hull.find_simplex(p)>=0
        def find_edge_point(hull, centroid, direction):
            pos = centroid
            i = 1
            while in_hull(pos, hull) == True:
                pos = centroid + np.array([int(round(i*direction[0])), int(round(i*direction[1]))])
                i += 1
            return pos
        def draw_contour_identifiers(image, contour, centroid, eigenVectors, lever_pos):
            majoraxis_pt1 = centroid
            majoraxis_pt2 = centroid+[int(round(100.*eigenVectors[0][0])), int(round(100.*eigenVectors[1][0]))]
            minoraxis_pt1 = centroid-[int(round(50.*eigenVectors[0][1])), int(round(50.*eigenVectors[1][1]))]
            minoraxis_pt2 = centroid+[int(round(50.*eigenVectors[0][1])), int(round(50.*eigenVectors[1][1]))]
            cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)
            cv2.drawContours(image, [np.array([centroid])], -1, (0, 0, 255), 5)
            cv2.drawContours(image, [np.array([lever_pos])], -1, (0, 0, 255), 5)
            cv2.line(image, (majoraxis_pt1[0],majoraxis_pt1[1]), (majoraxis_pt2[0],majoraxis_pt2[1]),(255,0,0), 1)
            cv2.line(image, (minoraxis_pt1[0],minoraxis_pt1[1]), (minoraxis_pt2[0],minoraxis_pt2[1]),(255,0,0), 1)
        
        TopImg_cropped = self.crop_image(self.gui.ipevo_hc.takePicture(), self.box_x, self.box_y, self.box_w, self.box_h)
        imgray = cv2.cvtColor(TopImg_cropped, cv2.COLOR_BGR2GRAY)
        blur = cv2.bilateralFilter(imgray,9,75,75)
        ret,thresh = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        kernel = np.ones((5,5),np.uint8)
        #opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        lever_list = []
        for c in contours:
            try: # identify chip contours by hu_invariant moments / area
                if self.is_chip(c): #normalized square error < cutoff, area > 0.05% of total image
                    # obtain centroids, orientation, and minor/major axis from hull/contour moments
                    M = cv2.moments(c)
                    centroid = np.array([int(M['m10']/M['m00']), int(M['m01']/M['m00'])])
                    cov = np.array([[M['mu20'],M['mu11']],[M['mu11'],M['mu02']]])
                    eigenValues, eigenVectors = np.linalg.eig(cov)
                    idx = eigenValues.argsort()[::-1] #sort eigenvalues in decending order
                    eigenValues = eigenValues[idx]
                    eigenVectors = eigenVectors[:,idx]         
                    lever_angle = -0.5*np.arctan(2.*M['mu11']/(M['mu20']-M['mu02']))
                    lever_pos = find_edge_point(c[:,0], centroid, eigenVectors[:,0])
                    lever_list.append((lever_pos[0],lever_pos[1],lever_angle))
                    draw_contour_identifiers(TopImg_cropped, c, centroid, eigenVectors, lever_pos)
            except ZeroDivisionError: 
                pass
        print lever_list   
        lever_vec_pxl = np.asarray(lever_list)
        self.cam_scalings = np.array([self.gui.ipevo_hc.cam_scaling_x.val, self.gui.ipevo_hc.cam_scaling_y.val])
        self.cam_angle = self.gui.ipevo_hc.cam_angle_deg.val/180.*np.pi
        lever_height = np.mean(self.cam_scalings) * self.gui.ui.LeverDetection_chipLength_doubleSpinBox.value()
        lever_width = np.mean(self.cam_scalings) * self.gui.ui.LeverDetection_chipWidth_doubleSpinBox.value()
        # display images to show steps of the CV algorithm
        if lever_vec_pxl.any():
            # format: (pxl_x, pxl_y, alpha, mm_x, mm_y, lever_found, col_idx, row_idx, lever_nb)
            self.lever_vec_sorted = self.sortLevers(lever_vec_pxl, lever_height, lever_width)
            self.calculateLeverPos()
            self.data_dict["lever_vec_sorted"] = self.lever_vec_sorted
            self.drawLeverNumbers(TopImg_cropped, self.lever_vec_sorted)
            self.gui.auto_focus.lever_vec_sorted = [[]]*len(self.lever_vec_sorted)
            self.gui.lever_align.lever_vec_sorted = [[]]*len(self.lever_vec_sorted)
            self.gui.lever_cutting.lever_vec_sorted = [[]]*len(self.lever_vec_sorted)
        else:
            ctypes.windll.user32.MessageBoxA(0,"No levers were detected! Most likely the camera is not well positioned or out of focus. To set the focus start Presenter and set focus manually to 1.","Uh'Oh", 0x0)
            raise ValueError("No Levers found.")
            
        b,g,r = cv2.split(TopImg_cropped)       # get b,g,r
        self.TopImg = cv2.merge([r,g,b])     # switch it to rgb
        self.update_figure(self.TopImg)
        self.gui.ui.SingleMeasurements_lever_nb_doubleSpinBox.setValue(0) # sets the lever to zero because we are still at imaging position
        print "Find Levers, Done"
               
    def saveBoxImage(self, img, directory, filename, resize_image):
        if resize_image:
            img = cv2.resize(img, (600, 450))
        if not os.path.exists(directory):
                os.makedirs(directory)   
        cv2.imwrite(os.path.join(directory, filename+'.png'), img)
        
    def drawLeverNumbers(self, img, lever_vec_sorted):
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontsize = 3
        color = (255,0, 0)
        thickness = 4
        linetype = cv2.CV_AA
        offset = (-16, -20)
        
        for lever in lever_vec_sorted:
            x, y, _, _, _, _, _, _, lever_nb = lever
            position = (int(x+offset[0]), int(y+offset[1]))
            cv2.putText(img, str(int(lever_nb)), position, font, fontsize, color, thickness, linetype)
        
    def determineNumberOfClusters(self, data, data_range):
        # gap statistic method
        stop_criteria = (cv2.TERM_CRITERIA_MAX_ITER+cv2.TERM_CRITERIA_EPS, 100, 0.01)
        gap= []
        k_range = range(2, len(data))   # gap statistic works bad for a single cluster
        for k in k_range:
            ssd, _, _ = cv2.kmeans(data, k, stop_criteria, 10, cv2.KMEANS_PP_CENTERS)
            
            # Uniform reference distribution 
            ssdUni = 0
            N = 100
            for _ in range(N):
#                 uni = np.float32(np.random.uniform(data_range[0], data_range[1],(len(data))))
                uni = np.float32(np.random.uniform(min(data),max(data),(len(data))))
        #         ssdUni_x+=sum(np.amin([(center-u)**2 for center in centers_x for u in uni_x],axis=0))/N
                s_i,_, _ = cv2.kmeans(uni, k, stop_criteria, 10, cv2.KMEANS_PP_CENTERS)
                ssdUni += s_i / N
            gap.append((ssdUni)-(ssd))

        numberOfClusters = k_range[np.argmax(gap)]
        
        return numberOfClusters

    def sortLevers(self,lever_vec_pxl, lever_height, lever_width):
        # return format: (pxl_x, pxl_y, alpha, mm_x, mm_y, lever_found, col_idx, row_idx, lever_nb)
        pxl_x = np.float32(lever_vec_pxl[:, 0])
        pxl_y = np.float32(lever_vec_pxl[:, 1])
        alpha = lever_vec_pxl[:, 2]
        
        # single row:lever_height
        if self.auto_detect_rows_cols.val==True and max(lever_vec_pxl[:, 1]) - min(lever_vec_pxl[:, 1]) < lever_height:
            lever_list_pxl = [lever for lever in lever_vec_pxl]
            N_cols = len(lever_list_pxl)
            N_rows = 1
            self.number_of_columns.update_value(N_cols)
            self.number_of_rows.update_value(N_rows)
            # one row, only sort in x:
            row_sorted = np.array(sorted(lever_list_pxl, key = lambda item: item[0]))
            
            lever_found = False
            mm_x, mm_y = 0, 0
            data = [(pxl_x[i], pxl_y[i], alpha[i], mm_x, mm_y, lever_found,
                     np.where(row_sorted[:,0]==lever_list_pxl[i][0])[0][0], 0) for i in range(len(pxl_x))]
            lever_vec_sorted = np.array(sorted(data, key=lambda item: (item[7], item[6])))
        
        # single column:
        elif self.auto_detect_rows_cols.val==True and max(lever_vec_pxl[:, 0]) - min(lever_vec_pxl[:, 0]) < lever_width:
            lever_list_pxl = [lever for lever in lever_vec_pxl]
            N_cols = 1
            N_rows = len(lever_list_pxl)
            self.number_of_columns.update_value(N_cols)
            self.number_of_rows.update_value(N_rows)
            # one row, only sort in x:
            col_sorted = np.array(sorted(lever_list_pxl, key = lambda item: item[1]))
            
            lever_found = False
            mm_x, mm_y = 0, 0
            data = [(pxl_x[i], pxl_y[i], alpha[i], mm_x, mm_y, lever_found, 0,
                     np.where(col_sorted[:, 1]==lever_list_pxl[i][1])[0][0]) for i in range(len(pxl_x))]
            lever_vec_sorted = np.array(sorted(data, key=lambda item: (item[7], item[6])))      
        
        else:
            # This algorithms does not work well for single rows or single columns:
            range_x = [0, self.TopImg.shape[1]]
            range_y = [0, self.TopImg.shape[0]]
            
            if self.auto_detect_rows_cols.val==True:
                N_cols = self.determineNumberOfClusters(pxl_x, range_x)
                N_rows = self.determineNumberOfClusters(pxl_y, range_y)
                self.number_of_columns.update_value(N_cols)
                self.number_of_rows.update_value(N_rows)
            else: 
                N_cols = self.number_of_columns.val
                N_rows = self.number_of_rows.val
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER , 100, 0.01)
            _, labels_x, centers_x= cv2.kmeans(pxl_x, N_cols, criteria, 10, cv2.KMEANS_PP_CENTERS)
            _, labels_y, centers_y= cv2.kmeans(pxl_y, N_rows, criteria, 10, cv2.KMEANS_PP_CENTERS)
            
            # sort according to column and row indices
            centers_x_sorted = np.sort(centers_x, axis=0)
            centers_y_sorted = np.sort(centers_y, axis=0)
        
            # default values
            lever_found = False
            mm_x, mm_y = 0, 0
            data = [(pxl_x[i], pxl_y[i], alpha[i], mm_x, mm_y, lever_found, np.where(centers_x_sorted==centers_x[labels_x[i]])[0][0],
                     np.where(centers_y_sorted==centers_y[labels_y[i]])[0][0]) for i in range(len(pxl_x))]
            lever_vec_sorted = np.array(sorted(data, key=lambda item: (item[7], item[6])))
        
        lever_nb = np.array([int(lever[7]*N_cols + lever[6] + 1) for lever in lever_vec_sorted])
        lever_vec_sorted = np.append(lever_vec_sorted,lever_nb.reshape(len(lever_nb),1),1)
        return lever_vec_sorted

    def closestLever(self):
        # returns the number of the closest Lever
        lever_numbers = [int(f) for f in self.lever_vec_sorted[:, 8]]
        x,y = self.gui.stage_hc.getPosXY_mm()
        pos = np.array([x, y])
        distances = [np.linalg.norm(pos-vec[3:5]) for vec in self.lever_vec_sorted]
        return lever_numbers[np.argmin(distances)]
    
    def calculateLeverPos(self):
        self.offsets_mm = np.array([self.gui.ipevo_hc.cam_offset_x.val, self.gui.ipevo_hc.cam_offset_y.val])
        self.cam_scalings = np.array([self.gui.ipevo_hc.cam_scaling_x.val, self.gui.ipevo_hc.cam_scaling_y.val])
        self.cam_angle = self.gui.ipevo_hc.cam_angle_deg.val/180.*np.pi
        h,w = self.gui.ipevo_hc.frame_h, self.gui.ipevo_hc.frame_w
        for i in xrange(len(self.lever_vec_sorted)):
            r_B_L_pxl = np.array([self.box_x+self.lever_vec_sorted[i][0], self.box_y+self.lever_vec_sorted[i][1]]) - np.array([w/2, h/2])
            r_B_mm = self.offsets_mm
            r_L_mm = r_B_mm + self.photoToStage(r_B_L_pxl)
            self.lever_vec_sorted[i][3:5] = r_L_mm

    def photoToStage(self, vecP):
        # change of coordinates
        alpha = self.cam_angle
        vecS = np.array([0, 0], dtype=float)
        vecS[0] = 1./self.cam_scalings[0] * (np.cos(alpha)*vecP[0] + np.sin(alpha)*vecP[1])
        vecS[1] = 1./self.cam_scalings[1] * (-np.sin(alpha)*vecP[0] + np.cos(alpha)*vecP[1])
        return vecS
              
    def gotoUpdatedLeverPos(self, calib_value):
        # function argument is only needed for the function to be used as a hardware set function
        if self.lever_nb.val > 0:  
            self.calculateLeverPos()
            self.gotoLever(self.lever_nb.val) ###!Check why this happens still
        
    def gotoLever(self, i):
        # move objective to lever number i
        self.gui.lever_cutting.waveform_ready = False
        self.gui.MCLstage_hc.set_pos_XY(100.,100.)
        if hasattr(self,'lever_vec_sorted'):
            try:
                lever_idx = self.getLeverIndex(i)
                r_L_mm = self.lever_vec_sorted[lever_idx][3:5]
                _, posynow = self.gui.stage_hc.getPosXY_mm() 
                #print "the current y position is", posynow
                #print "new y position is bigger than current y positon?", posynow>r_L_mm[1]
                if posynow>r_L_mm[1]:
                    self.gui.stage_hc.compensateTilt((posynow-r_L_mm[1])*1000)
                    self.gui.stage_hc.moveToXY_mm(r_L_mm[0], r_L_mm[1])
                else:
                    self.gui.stage_hc.moveToXY_mm(r_L_mm[0], r_L_mm[1])   
                    self.gui.stage_hc.compensateTilt((posynow-r_L_mm[1])*1000)
                
                self.lever_angle_deg.update_value(180./np.pi*self.lever_vec_sorted[lever_idx][2])
                self.lever_nb.read_from_hardware()
                self.lever_angle_deg.read_from_hardware()
                self.gui.ipevo_hc.saveCalibration()
                self.gui.stage_hc.posX.read_from_hardware()
                self.gui.stage_hc.posY.read_from_hardware()
                self.gui.MCLstage_hc.get_pos_XYZ()
            except ValueError:
                print "Lever number not valid."
                self.gui.MCLstage_hc.get_pos_XYZ()
            
    def gotoFirstLever(self):
        lever_idx = 0   # first in terms of lever index
        r_L_mm = self.lever_vec_sorted[lever_idx][3:5]
        self.gui.stage_hc.moveToXY_mm(r_L_mm[0], r_L_mm[1])
        self.lever_nb.read_from_hardware()
        
    def gotoNextLever(self):
        #self.markButton(self.gui.ui.LeverDetection_gotoNextLever_pushButton)
        
        if int(self.lever_nb.val) == 0:
            current_LeverIndex = -1
        else:    
            current_LeverIndex = self.getLeverIndex(int(self.lever_nb.val))
            
        if current_LeverIndex < len(self.lever_vec_sorted[:,8])-1:
            self.gui.MCLstage_hc.set_pos_XYZ(100.,100.,100.)
            next_LeverIndex = current_LeverIndex+1
            self.lever_nb.hardware_set_func(self.lever_vec_sorted[next_LeverIndex, 8]) 
                
            if self.gui.ui.goToNextLever_continue_checkBox.isChecked():
                self.gui.ui.AutoFocus_pushButton.click()
        else:
            print "No More Chips!"
        
        #self.markButton(self.gui.ui.LeverDetection_gotoNextLever_pushButton, on=False)

    def getLeverIndex(self, lever_nb):
        lever_numbers = [int(f) for f in self.lever_vec_sorted[:, 8]]
        if lever_nb not in lever_numbers:
            raise ValueError("Lever number not valid.")
        else:
            lever_idx = next(j for j in xrange(len(lever_numbers)) if lever_numbers[j] == lever_nb)
        return lever_idx
        
    def updateCurrentLeverPos(self, x, y):
        lever_idx = self.getLeverIndex(self.lever_nb.val)
        self.lever_vec_sorted[lever_idx][3:5] = [x, y]
    
    def showAllLevers(self):
        for i in xrange(len(self.lever_vec_sorted)):
            self.gotoLever(i+1)
   
    def setup_figure(self):
        self.fig2 = self.gui.add_figure("Box Image", self.gui.ui.LeverDetection_box_image_groupBox, toolbar=False)
        self.fig2.clear()
        
        # Axes instance == subplot
        self.ax2_1 = self.fig2.add_subplot(1,1,1)
        self.ax2_1.set_axis_off()

    def update_figure(self, image):
        if not hasattr(self, 'TopImg_imshow'):
            self.TopImg_imshow = self.ax2_1.imshow(image)
        else:
            self.TopImg_imshow.set_data(image)
        self.fig2.canvas.draw()
   
    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.LeverDetection_DetectLevers_pushButton)
            self.start_flag = False
           
        if self.end_flag:
            self.markButton(self.gui.ui.LeverDetection_DetectLevers_pushButton, on=False)
        
    def _run(self):
        print "run lever detection"
        # plot, start, and end flags
        
        self.picture_ready, self.picture_displayed, self.start_flag, self.end_flag = False, False, True, False
        
        self.gui.MCLstage_hc.set_pos_XYZ(100.,100.,100.)
        
        if self.lever_nb.val != 0:
            self.lever_nb.update_value(0)
            
        self.gui.ui.backlight_state_checkBox.setChecked(True)
        if self.gui.ui.firefly_cam_connected_checkBox.isChecked():
            self.gui.ui.Firefly_videoStream_checkBox.setChecked(False)
            self.gui.ui.firefly_cam_connected_checkBox.setChecked(False)
        
        self.moveToTopViewCamPosition()
        if self.end_flag == False:
            time.sleep(3)
            
            self.gui.ui.ipevo_cam_connected_checkBox.setChecked(True) 
            time.sleep(3)
            
            self.picture_ready = True
            self.TopImg = self.gui.ipevo_hc.takePicture()
            self.update_figure(self.TopImg)
            self.box_x, self.box_y, self.box_w, self.box_h = self.isolateBox(self.TopImg)
            if self.AutoCalibCam.val:
                self.gui.ipevo_hc.CalibrateCamera(np.array([self.box_x,self.box_y]), np.array([self.box_x+self.box_w,self.box_y+self.box_h]))
        
            if self.end_flag == False:
                self.findLevers()
                self.BoxName = str(self.gui.ui.BoxName_lineEdit.text())
                self.data_dict["Box_Name"]=self.BoxName
                self.saveBoxImage(self.TopImg, "data/"+self.BoxName, "BoxOverview", False)
                                
            self.gui.stage_hc.posX.read_from_hardware()
            time.sleep(0.5)
            self.gui.stage_hc.posY.read_from_hardware()
            time.sleep(0.5)
            self.gui.stage_hc.posZ.read_from_hardware()
            time.sleep(0.5)
        
        self.gui.ui.ipevo_cam_connected_checkBox.setChecked(False) 
        self.gui.ui.firefly_cam_connected_checkBox.setChecked(True)
        self.gui.ui.Firefly_videoStream_checkBox.setChecked(True)
        self.gui.ui.backlight_state_checkBox.setChecked(False)
        self.gui.MCLstage_hc.get_pos_XYZ()
        
        self.start_flag = False    
        self.end_flag = True
        #self.gui.ui.progressBar.setValue(100*(1.)/( 1. + float(len(self.lever_vec_sorted))))
        
        if self.gui.ui.DetectLevers_continue_checkBox.isChecked() and hasattr(self,'lever_vec_sorted'):
            self.gui.ui.LeverDetection_gotoNextLever_pushButton.click()


    
    