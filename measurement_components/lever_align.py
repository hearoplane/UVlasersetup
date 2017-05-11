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

class LeverAlign(Measurement):
    name = "LeverAlign"
   
    def setup(self):
        self.display_update_period = 0.5 #seconds
        self.lever_vec_sorted = []      
        # add logged quantities
        
        #connect to gui
        self.gui.ui.LeverAlign_pushButton.clicked.connect(self.start)
        self.gui.ui.SnapPatch_pushButton.clicked.connect(self.makePatchImage)
        self.gui.ui.LeverType_comboBox.currentIndexChanged.connect(self.updateTemplate)  
        #self.picture_ready, self.picture_displayed, self.start_flag, self.end_flag = False, False, True, False  

    def setup_figure(self):
        self.ManualAlignFig = self.gui.add_figure("Lever Alignment", self.gui.ui.AlignLever_image_groupBox, toolbar=False)
        self.ax1 = self.ManualAlignFig.add_subplot(1,1,1)
        self.ax1.set_axis_off()

        self.updateTemplate()
        
    def update_figure(self, image):
        if not hasattr(self, 'patchwork_imshow'):
            self.patchwork_imshow = self.ax1.imshow(image)
        else:
            self.patchwork_imshow.set_data(image)
        self.ManualAlignFig.canvas.draw() 

    
    def updateTemplate(self, dummy=None):
        chipType = self.gui.ui.LeverType_comboBox.currentText()
        if  chipType == 'Shielded NSC':
            self.template = cv2.imread('templates/ShieldedNSC_template.png', 0)
            self.template_info = {"target_align": np.array([146,193]), "neck_length_pxl":200, "cut_profile":"Diamond", "cut_params":[]}
            #self.tp_dict = {"image":cv2.imread('templates/ShieldedNSC_template.png', 0), 
            #                "target_align": np.array([146,193]), 
            #                "nom_dims_pxl":{"neck_length":200, "neck_width": 100},
            #                "nom_cut_params":{"profile":"Diamond", "radius":12., "mod":15}}
        elif chipType == 'NSC 19':
            self.template = cv2.imread('templates/NSC19_template.png', 0)
            self.template_info = {"target_align": np.array([177,240]), "neck_length_pxl":200, "cut_profile":"Diamond", "cut_params":[]}
        elif chipType == 'Scuba E':
            self.template = cv2.imread('templates/ScubaE_template.png', 0)
            self.template_info = {"target_align": np.array([157,217]), "neck_length_pxl":100, "cut_profile":"Diamond", "cut_params":[]}
        elif chipType == 'Scuba EP':
            self.template = cv2.imread('templates/ScubaEP_template.png', 0)
            self.template_info = {"target_align": np.array([170,240]), "neck_length_pxl":100, "cut_profile":"Diamond", "cut_params":[]}
        elif chipType == 'Scuba A':
            self.template = cv2.imread('templates/ScubaA_template.png', 0)
            self.template_info = {"target_align": np.array([183,270]), "neck_length_pxl":100, "cut_profile":"Diamond", "cut_params":[]}
        
        self.update_figure(cv2.cvtColor(self.template,cv2.COLOR_GRAY2RGB))
    
    def CA_success_metric(self, TM_corr):
        return TM_corr > 0.6    
        
    def LeverCoarseAlign(self):
        numrowcol = numrowcol=int(self.gui.ui.SnapPatch_NumColRow_doubleSpinBox.value())
        im = self.makePatchImage()   
        h,w = im.shape[:2]
        
        labels, centers = self.segmentColors(im,3, False)
        bkg_label = int(round(np.mean(labels[:50,:])))
        bkg_color = centers[bkg_label]
        
        img_contrast =  np.sum(np.abs(im-bkg_color), axis=2)
        img_contrast /= np.max(img_contrast)
        img_contrast = img_as_ubyte(img_contrast)
        
        #Template for object matching
        template = cv2.resize(self.template, (0,0), fx=1./float(numrowcol), fy=1./float(numrowcol))
        th,tw = template.shape[:2]
        template_target = np.array([int(round(self.template_info["target_align"][0]/float(numrowcol))), int(round(self.template_info["target_align"][1]/float(numrowcol)))])
        
        try:
            lever_idx = self.gui.lever_detection.getLeverIndex(self.gui.lever_detection.lever_nb.val)
            self.lever_angle_deg = 180./np.pi*self.gui.lever_detection.lever_vec_sorted[lever_idx][2]+self.gui.ipevo_hc.cam_angle_deg.val
            print "Using lever angle from chip detection... lever angle (firefly reference) =", self.lever_angle_deg
            img_contrast_rot = self.rotateImage(img_contrast, -self.lever_angle_deg)
            [corr, top_left, bottom_right] = self.templateMatch(img_contrast_rot, template)
        except:
            print "could not access lever angle, sweep max rotation range"
            angle_deg_initialGuess = 0.
            angle_deg_range = 16.
            angle_deg_delta = 0.2
            [img_contrast_rot, corr, rotation_deg, top_left, bottom_right] = self.templateMatch_w_rotation(img_contrast, template, angle_deg_initialGuess, angle_deg_range, angle_deg_delta, True)
            self.lever_angle_deg = -rotation_deg
        
        laser_pos = (int(self.gui.lever_cutting.laser_posX.val),int(self.gui.lever_cutting.laser_posY.val))        
        target_pos = np.array([top_left[0]+template_target[0], top_left[1]+template_target[1]])    
        vecP1 = np.array([(target_pos[0]-w/2)*numrowcol, (target_pos[1]-h/2)*numrowcol])
        vecP2 = np.array([(laser_pos[0]-w/2), (laser_pos[1]-h/2)])
        #vecP2 = np.array([0.,0.])
        vecR_mm = self.photoToStage(vecP1-vecP2, self.lever_angle_deg/180.*np.pi+self.cam_angle)
        self.gui.stage_hc.moveRelXY_mm_backlash(vecR_mm[0],vecR_mm[1])      
                    
        img_contrast_rot = cv2.cvtColor(img_contrast_rot, cv2.COLOR_GRAY2RGB)       
        cv2.rectangle(img_contrast_rot,top_left, bottom_right, (255,0,0), 10)
        cv2.circle(img_contrast_rot,(target_pos[0],target_pos[1]), 3, (255,0,0), 10)
        self.update_figure(img_contrast_rot)
    
        return self.CA_success_metric(corr), corr
    
    def FA_success_metric(self, TM_corr):
        return TM_corr > 0.88
            
    def LeverFineAlign(self): 
        print "Fine Lever Align"
        sleep(0.1)
        im = self.gui.firefly_hc.takePicture() 
        img = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        h,w = img.shape[:2]
        
        bkg =  np.array([np.mean(im[:h/7,:,0]), np.mean(im[:h/7,:,1]), np.mean(im[:h/7,:,2])])
        img_contrast =  np.sum(np.abs(im-bkg), axis=2)
        img_contrast /= np.max(img_contrast)
        img_contrast = img_as_ubyte(img_contrast)
        
        template = self.template
        th,tw = template.shape[:2]
        template_target = self.template_info["target_align"].copy()
        
        angle_deg_initialGuess = -self.lever_angle_deg
        angle_deg_range = 4.
        angle_deg_delta = 0.2
        [img_contrast_rot, TM_corr, self.lever_angle_deg, top_left, bottom_right] = self.templateMatch_w_rotation(img_contrast, template, angle_deg_initialGuess, angle_deg_range, angle_deg_delta, True)
        laserposition=(int(self.gui.lever_cutting.laser_posX.val),int(self.gui.lever_cutting.laser_posY.val))
        
        vecP1 = np.array([w/2,h/2])-np.array([top_left[0]+template_target[0], top_left[1]+template_target[1]])
        vecR1_mm = self.photoToStage(vecP1, self.lever_angle_deg/180.*np.pi+self.cam_angle)
        vecR1_um = vecR1_mm*1000.
        
        vecP2 = np.array([w/2,h/2])-np.array([laserposition[0],laserposition[1]])
        vecR2_mm = self.photoToStage(vecP2, self.cam_angle)
        vecR2_um = vecR2_mm*1000.
               
        target_dev = np.array([vecR1_um[0]-vecR2_um[0],-vecR1_um[1]+vecR2_um[1]])
        
        if abs(target_dev[0])<90. and abs(target_dev[1])<90.: 
            self.gui.MCLstage_hc.move_rel_XY(target_dev[0], target_dev[1])
        else:
            "Coarse Alignment Error, required Fine Align displacement out of range"
        
        img_contrast_rot = cv2.cvtColor(img_contrast_rot, cv2.COLOR_GRAY2RGB)       
        cv2.rectangle(img_contrast_rot,top_left, bottom_right, (255,0,0), 10)
        cv2.circle(img_contrast_rot,(top_left[0]+template_target[0],top_left[1]+template_target[1]), 10, (255,0,0), 10)
        self.update_figure(img_contrast_rot)
        
        return self.success_metric(TM_corr), TM_corr
    
    def extract_lever_width(self, align_to_center):
        #MAKE SURE IMAGE IS TAKEN USING BOTTOM ILLUMINATION ONLY       
        im = self.gui.firefly_hc.takePicture() 
        img = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        h,w = img.shape[:2]
        laserpos=(int(self.gui.lever_cutting.laser_posX.val),int(self.gui.lever_cutting.laser_posY.val))
        
        theta = -np.pi/180.*self.lever_angle_deg
        R = np.array([[np.cos(theta),np.sin(theta)],[-np.sin(theta),np.cos(theta)]])
        laserpos_rot = np.array([w/2,h/2])+np.dot(R,(laserpos[0]-w/2,laserpos[1]-h/2))
        img_rot = self.rotateImage(img, -self.lever_angle_deg)
        
        cw,ch = 600, self.template_info["neck_length_pxl"]
        tl = (int(laserpos_rot[0])-cw/2,int(laserpos_rot[1]))
        br = (int(laserpos_rot[0])+cw/2,int(laserpos_rot[1])+ch)
        
        img_rot_crop = img_rot[tl[1]:br[1], tl[0]:br[0]]
        img_rot_crop = (255-img_rot_crop)
        
        histx = np.sum(img_rot_crop, 0)
        lv_avg = np.mean(histx[cw/2-cw/10:cw/2+cw/10])
        bkg_avg = np.mean(histx[:cw/6])
        
        i=0
        while histx[i] < bkg_avg+0.7*(lv_avg-bkg_avg):
            i+=1
        edgeLoc_1 = i
        
        i=cw-1
        while histx[i] < bkg_avg+0.7*(lv_avg-bkg_avg):
            i-=1
        edgeLoc_2 = i
                
        lever_width_pxl = (edgeLoc_2-edgeLoc_1)
        pxl_per_um = np.mean(self.cam_scalings)/1000.
        lever_width_um = float(lever_width_pxl)/pxl_per_um
        print "lever width [um]:", lever_width_um
        print "lever width [pxls]", lever_width_pxl
        
        cut_radius_pxl = int(0.30*(edgeLoc_2-edgeLoc_1))
        
        if align_to_center:
            vecP1 = np.array([int(cw/2),0])-np.array([int(0.5*(edgeLoc_1+edgeLoc_2)), 0])
            vecR1_mm = self.photoToStage(np.array([5,0]), 0.)#self.lever_angle_deg/180.*np.pi+self.cam_angle)
            vecR1_um = vecR1_mm*1000.
           
            target_dev = np.array([vecR1_um[0],-vecR1_um[1]])
        
            if abs(target_dev[0])<90. and abs(target_dev[1])<90.: 
                self.gui.MCLstage_hc.move_rel_XY(target_dev[0], target_dev[1])
            else:
                "Coarse Alignment Error, required Fine Align displacement out of range"
            
        img_rot = cv2.cvtColor(img_rot, cv2.COLOR_GRAY2RGB)
        cv2.line(img_rot, (tl[0]+edgeLoc_1,0), (tl[0]+edgeLoc_1,h), (255,0,0), 13)                     
        cv2.line(img_rot, (tl[0]+edgeLoc_2,0), (tl[0]+edgeLoc_2,h), (255,0,0), 13)
        cv2.circle(img_rot,(tl[0]+(edgeLoc_1+edgeLoc_2)/2,int(laserpos_rot[1])-cut_radius_pxl), cut_radius_pxl, (255,0,0), 12)
        #cv2.rectangle(img_rot,(tl[0]+edgeLoc_1,tl[1]), (tl[0]+edgeLoc_2,br[1]), 255, 5)
        self.update_figure(img_rot)

        return lever_width_pxl, lever_width_um
        
    def templateMatch_w_rotation(self, img, template, angle_deg_initialGuess, angle_deg_range, angle_deg_delta, returnOptImg=False):
        corr_data = np.zeros((int(angle_deg_range/angle_deg_delta)+1,2))        
        for i in range(int(angle_deg_range/angle_deg_delta)+1):
            angle_deg = angle_deg_initialGuess-angle_deg_range/2. + float(i)*angle_deg_delta
            result = self.templateMatch(self.rotateImage(img,angle_deg), template) 
            corr_data[i][0] = angle_deg
            corr_data[i][1] = result[0]
            print corr_data[i]
        f = interp1d(corr_data[:,0], corr_data[:,1], kind='cubic')
        x = np.linspace(min(corr_data[:,0]), max(corr_data[:,0]),1000)
        opt_angle_deg = x[np.argmax(f(x))]
        opt_img = self.rotateImage(img, opt_angle_deg)
        opt_result = self.templateMatch(opt_img, template)
        print "optimal angle:", opt_angle_deg
        if returnOptImg:
            return [opt_img, opt_result[0], -opt_angle_deg, opt_result[1], opt_result[2]]
        else:
            return [opt_result[0], -opt_angle_deg, opt_result[1], opt_result[2]]
        
    def templateMatch(self, img, template):
        h,w = img.shape[:2]
        th,tw = template.shape[:2]
        res = cv2.matchTemplate(img,template,eval('cv2.TM_CCORR_NORMED'))
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        bottom_right = (top_left[0] + tw, top_left[1] + th)
        return [max_val,top_left, bottom_right]

    def rotateImage(self,image, angle):#parameter angel in degrees 
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

    def photoToStage(self, vecP, alpha):
        # change of coordinates
        vecS = np.array([0, 0], dtype=float)
        vecS[0] = 1./self.cam_scalings[0] * (np.cos(alpha)*vecP[0] + np.sin(alpha)*vecP[1])
        vecS[1] = 1./self.cam_scalings[1] * (-np.sin(alpha)*vecP[0] + np.cos(alpha)*vecP[1])
        return vecS

    def movetoLaser(self,tipposition):
        distX=(tipposition[0]-self.gui.ui.LaserCutter_LaserPositionW_doubleSpinBox.value())/self.gui.ui.Firefly_cam_scaling_x_doubleSpinBox.value()
        distY=(tipposition[1]-self.gui.ui.LaserCutter_LaserPositionH_doubleSpinBox.value())/self.gui.ui.Firefly_cam_scaling_y_doubleSpinBox.value()
        print "x, y Distance from Laser Position [um]: ", distX,distY

        if np.abs(distX)<=50. and np.abs(distY)<=50.:
            self.gui.MCLstage_hc.move_rel_X(distX)             
            self.gui.MCLstage_hc.move_rel_Y(-distY)
            #self.movetoLaser(tipposition)
            print "positioned within 50um"
            #self.gui.lever_cutting.snapNewImage()
            #print "updated Fine Image"
            return
        
        elif np.abs(distX)<=300. and np.abs(distY)<=200.:
            print "Use ASI stage to approach"
            self.gui.MCLstage_hc.move_rel_X(distX,distY)
            tipposition=self.startAlign(displayPlots=False)
            #self.movetoLaser(tipposition) #do the alignment again
            return
        else:
            print "Could not move to cantilever"  
        return

    def makePatchImage(self):
        print "Creating Patch Image"
        
        temp = self.gui.firefly_hc.takePicture()
        h,w = temp.shape[0],temp.shape[1]
        #xstep=float(w)/self.gui.firefly_hc.cam_scaling_x.val/1000.
        #ystep=float(h)/self.gui.firefly_hc.cam_scaling_y.val/1000.
        cam_scaling = 0.5*1000.*(self.gui.firefly_hc.cam_scaling_x.val + self.gui.firefly_hc.cam_scaling_y.val)
        xstep = float(w) / cam_scaling
        ystep = float(h) / cam_scaling
        print xstep, ystep
        numrowcol=int(self.gui.ui.SnapPatch_NumColRow_doubleSpinBox.value())
        
        waittime=0.3
        typical_scaling = 4.
        #if abs(self.gui.firefly_hc.cam_scaling_x.val-typical_scaling) <1.0 and abs(self.gui.firefly_hc.cam_scaling_y.val-typical_scaling) < 1.0:
        if 1==1:
            self.patchwork = np.zeros((numrowcol*h, numrowcol*w, 3), np.uint8)
            self.gui.stage_hc.moveRelXY_mm_backlash(-(numrowcol/2)*xstep, -(numrowcol/2)*ystep)
            sleep(waittime)
            x_start, y_start = self.gui.stage_hc.getPosXY_mm()
            sleep(waittime)
            for i in range(numrowcol):
                for j in range(numrowcol):
                    self.gui.stage_hc.moveToXY_mm_backlash(x_start+j*xstep, y_start+i*ystep)
                    sleep(waittime)
                    self.patchwork[i*h:(i+1)*h, (j)*w:(j+1)*w, :] = self.gui.firefly_hc.takePicture()
            self.gui.stage_hc.moveToXY_mm_backlash(x_start+numrowcol/2*xstep, y_start+numrowcol/2*ystep)
            sleep(waittime)
            
            self.patchwork = cv2.resize(self.patchwork, (w, h))
            self.update_figure(self.patchwork)
            return self.patchwork
    
    def cropLaserArea(self, img):
        laserposition=[int(self.gui.ui.LaserCutter_LaserPositionH_doubleSpinBox.value()),int(self.gui.ui.LaserCutter_LaserPositionW_doubleSpinBox.value())]
        dimension=200
        img=img[laserposition[0]-dimension/2:laserposition[0]+dimension/2, laserposition[1]-dimension/2:laserposition[1]+dimension/2]
        return img

    def segmentColors(self, image, K, returnSegmentedImage=False):
        # reshape image to (nxm,3) vector array
        Z = image.reshape((-1,3))
        # convert to np.float32
        Z = np.float32(Z)
        # define criteria, number of clusters(K) and apply kmeans()
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        ret, labels, centers = cv2.kmeans(Z, K, criteria, 10, 0)
        labels = labels.reshape((image.shape[:2]))    
        
        if returnSegmentedImage==False:
            return labels, centers
        else:
            for i in range(K):
                image[labels==i+1] = centers[i]
            return image, labels, centers    

    def fitEdge_SVM(self, labels, bkg_label):
        h,w = labels.shape[:2]
        mask = np.ones((labels.shape[:2]), np.uint8)*255
        mask[labels==bkg_label] = 0    
        X = np.zeros((h*w,2))
        X[:np.sum(mask>0),:] = np.column_stack(np.nonzero(mask))
        X[np.sum(mask>0):,:] = np.column_stack(np.nonzero(mask==0))
        X = np.column_stack((np.ones(h*w),X))
        Y = np.zeros(h*w)
        Y[:np.sum(mask>0)] = 1
        Y[np.sum(mask>0):] = 0
        clf = svm.LinearSVC(dual=False)
        clf.fit(X, Y)
        edge_angle_deg = np.arctan(clf.coef_[0][2]/clf.coef_[0][1])*180./np.pi
        y_edge = int((1.-clf.coef_[0][0]-float(w/2)*clf.coef_[0][2])/clf.coef_[0][1])        
        return edge_angle_deg, y_edge

    def LeverCoarseAlign_old(self):
        numrowcol = numrowcol=int(self.gui.ui.SnapPatch_NumColRow_doubleSpinBox.value())
        im = self.makePatchImage()   
        self.cam_angle = self.gui.firefly_hc.cam_angle_deg.val/180.*np.pi
        self.cam_scalings = 1000.*np.array([self.gui.firefly_hc.cam_scaling_x.val,self.gui.firefly_hc.cam_scaling_y.val])
        h,w = im.shape[:2]
        
        Z = im.reshape((-1,3))
        # convert to np.float32
        Z = np.float32(Z)
        # define criteria, number of clusters(K) and apply kmeans()
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 3
        #ret,label,center=cv2.kmeans(Z,K,None,criteria,10,cv2.KMEANS_RANDOM_CENTERS)
        ret, label, center = cv2.kmeans(Z, K, criteria, 10, 0)
        label = label.reshape((im.shape[:2]))
        bkg_label = int(round(np.mean(label[:50,:])))
        bkg_color = center[bkg_label]
        mask = np.ones((im.shape[:2]), np.uint8)*255
        mask[label==bkg_label] = 0    
        X = np.zeros((h*w,2))
        X[:np.sum(mask>0),:] = np.column_stack(np.nonzero(mask))
        X[np.sum(mask>0):,:] = np.column_stack(np.nonzero(mask==0))
        X = np.column_stack((np.ones(h*w),X))
        Y = np.zeros(h*w)
        Y[:np.sum(mask>0)] = 1
        Y[np.sum(mask>0):] = 0
        
        clf = svm.LinearSVC(dual=False)
        clf.fit(X, Y)
        self.lever_angle_deg = np.arctan(clf.coef_[0][2]/clf.coef_[0][1])*180./np.pi
        print 'angle: ', self.lever_angle_deg
        #y_edge = int((1.-clf.coef_[0][0]-float(w/2)*clf.coef_[0][2])/clf.coef_[0][1])

        mask = self.rotateImage(mask, -self.lever_angle_deg)
        histy = np.sum(mask,axis=1)
        histx = np.sum(mask,axis=0)

        def func(X,a,b,c,d,e,f):
            return a/(1.+np.exp((b-X)/c)) + d/(1.+np.exp((e-X)/f))         
        x = np.linspace(0,h-1,h)
        popt, pcov = curve_fit(func, x, histy, bounds=(0, [np.max(histy)/10., h/2, 50, np.max(histy), h, 50]))
        fit = func(x, popt[0], popt[1], popt[2], popt[3], popt[4], popt[5])
        lever_y = int(popt[1])
        lever_x = np.argmax(np.convolve(histx, np.ones(13), 'same')) 
        print 'histogram'
        print lever_x, lever_y
        
        vecP = np.array([(lever_x-w/2)*numrowcol, (lever_y-h/2)*numrowcol])
        vecR_mm = self.photoToStage(vecP, -self.lever_angle_deg/180.*np.pi+self.cam_angle)
        self.gui.stage_hc.moveRelXY_mm_backlash(vecR_mm[0],vecR_mm[1])      
                    
        #cv2.line(mask, (0,y_edge), (w,y_edge), (255), 10)     
        cv2.circle(mask,(lever_x,lever_y), 100, (255), 10)
        self.update_figure(mask)
                
    def numpyandresize(self,img):
        img=np.array(np.array(img).astype('float'))
        img = scipy.misc.imresize(img, 0.1)
        img = np.fliplr(img) 
        return img
    
    #find contours 
    def findcontours(self,imgrot__):
        #print img[0]
        _,mask1 = cv2.threshold(imgrot__,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        _,mask1 = cv2.threshold(mask1, 127, 255, cv2.THRESH_BINARY_INV)
          
        # remove pixels of big levers
        kernel_size = (15, 15)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        mask4 = cv2.morphologyEx(mask1, cv2.MORPH_OPEN, kernel)
            
            # Find external contours
        (contours, _) = cv2.findContours(mask4.copy(), mode=cv2.cv.CV_RETR_EXTERNAL,method=cv2.cv.CV_CHAIN_APPROX_SIMPLE)
        img_contours = np.zeros((mask1.shape[0],  mask1.shape[1], 3), np.uint8)
        cv2.drawContours(img_contours, contours, -1, cv2.cv.RGB(255,255,255), 2)
        #print "found ", len(contours) ,"contours"
        return img_contours,contours[-1] #pick longest contour not just first
    
    def findposition(self,contours,image, displayPlots):
        length=len(contours)
        xvalues=[]
        yvalues=[]
        for x in xrange(0,length):
            xvalues.append(int(contours[x][0][0]))
            yvalues.append(int(contours[x][0][-1]))
    
    #calculate histograms width
        binsize=3
        height,width=image.shape[0],image.shape[1]
        nbBinsW=int(width/binsize)
        histW, bin_edgesW = np.histogram(xvalues, nbBinsW)
        bin_centresW = (bin_edgesW[:-1] + bin_edgesW[1:])/2
    
    #calculate histograms width
        binsize=3
        nbBinsH=int(height/binsize)
        histH, bin_edgesH = np.histogram(yvalues, nbBinsH)
        bin_centresH = (bin_edgesH[:-1] + bin_edgesH[1:])/2
    
    # pH is the initial guess for the fitting coefficients (A, mu and sigma above)
        indexH= [i for i, j in enumerate(histH) if j == max(histH)]
        pH = [max(histH), bin_edgesH[int(indexH[0])],20] #Takes the first point if several max are equal
        try: coeffH,_ = curve_fit(self.gauss, bin_centresH, histH, p0=pH)
        except: coeffH= [0,0,0]; print "H fit failed"
        indexW1= [i for i, j in enumerate(histW) if j == max(histW)]
        pW1 = [max(histW), bin_edgesW[int(indexW1[0])],20] #Takes the first point if several max are equal
        try: coeffW1, _ = curve_fit(self.gauss, bin_centresW, histW, p0=pW1)
        except: coeffW1=[0,0,0]; print "W1 fit failed"; self.WFitErrors+=1
    #Takes the first point if several max are equal
        
    #set to zero the highest peak. 
        histW2=deepcopy(histW)
        lowsidefirstpeak=int((coeffW1[1]-4*coeffW1[2])/width*len(histW2))
        highsidefirstpeak=int((coeffW1[1]+4*coeffW1[2])/width*len(histW2))
    #Cut away the first peak.    
        histW2[lowsidefirstpeak:highsidefirstpeak]=0 
    
        indexW2= [i for i, j in enumerate(histW2) if j == max(histW2)]
        pW2 = [max(histW2), bin_edgesW[int(indexW2[0])],20]
        try: coeffW2, _ = curve_fit(self.gauss, bin_centresW, histW, p0=pW2)
        except: coeffW2=[0,0,0]; print "W2 fit failed";self.WFitErrors+=1
        leverwidth=np.abs(coeffW1[1]-coeffW2[1])
        #print "leverwidth: ", leverwidth
        PosHStartLever = bin_centresH[[i for i, j in enumerate(histH) if j != 0][0]] #finds position of all non zero elements
        leverlength=np.abs(PosHStartLever-coeffH[1])
        #print "leverlenght:", leverlength
        
        #if self.gui.ui.display_images_checkBox.isChecked() and displayPlots==True: 
        #    self.plothistos(bin_centresW, bin_centresH, histW, histH, coeffW1, coeffW2, coeffH, image)
            
        #a fitted sigma of <10 is good. Starting with 20 seems good too. 
        return coeffW1, coeffW2, coeffH, bin_centresW, bin_centresH, histW, histH, leverwidth, leverlength
    
    # Define model function to be used to fit to the data above:
    def gauss(self,x, *p):
        A, mu, sigma = p
        return A*np.exp(-(x-mu)**2/(2.*sigma**2))
    
    def plothistos(self,bin_centresW_, bin_centresH_, histW_, histH_, coeffW1_, coeffW2_, coeffH_, image_):
    #  fitted curve in Width or X
        hist_fitW1 = self.gauss(bin_centresW_, *coeffW1_)
    # fitted curve in Width or X
        hist_fitW2 = self.gauss(bin_centresW_, *coeffW2_)
    # fitted curve in Height or Y
        hist_fitH = self.gauss(bin_centresH_, *coeffH_) 
        
        plt.subplot(2,2,1),plt.imshow(image_, cmap='gray')
        plt.title('Image')
        
        plt.subplot(2,2,2)
        plt.plot(histH_, bin_centresH_, label='Y data')
        plt.plot(hist_fitH, bin_centresH_, label='Fitted data')
        plt.ylim(image_.shape[0],0)
    
        plt.subplot(2,2,3)
        plt.plot(bin_centresW_, histW_, label='X data')
        plt.plot(bin_centresW_, hist_fitW1, label='Fitted data 1')
        plt.plot(bin_centresW_, hist_fitW2, label='Fitted data 2')
        plt.xlim(0,image_.shape[1])
        plt.show()
        plt.close()

    def findexactangle(self,img_,angleminmax,steps,displayPlots):  #I rotate full image it would be more efficient to only rotate the contours
        angles=[]
        sigmas=[]
        leverwidths=[]
        leverlengths=[]
        #imgoverl_=deepcopy(img_)
        #plt.subplot(1,1,1),plt.imshow(imgoverl_,cmap = 'gray')
        #plt.title('Image Contour'), plt.xticks([]), plt.yticks([])
        #plt.show()
            
        for x in xrange(-angleminmax,angleminmax,steps):
            angle=0.1*x #+/-5 Degrees
            imgrot_=self.rotateImage(img_, angle)
            imgrotcont_,contours_=self.findcontours(imgrot_)
            #imgoverl_ = cv2.add(imgrot_,imgrotcont_
            #plt.subplot(1,1,1),plt.imshow(imgoverl_,cmap = 'gray')
            #plt.title('Image Contour'), plt.xticks([]), plt.yticks([])
            #plt.show()
            
            (_,_,coeffH,_,_,_,_,leverwidth,leverlength)=self.findposition(contours_,imgrotcont_,displayPlots=False)
            #print "angle is: ",angle
            #print "sigma is:", coeffH[2]
            sigma=coeffH[2]
            angles.append(angle)
            sigmas.append(sigma)
            leverwidths.append(leverwidth)
            leverlengths.append(leverlength)
        #if self.gui.ui.display_images_checkBox.isChecked() and displayPlots==True: 
        #    plt.subplot(1,1,1),plt.plot(angles, sigmas, label='Best Angle')
        #    plt.plot(angles, leverwidths, label='Lever Width')
        #    plt.plot(angles, leverlengths, label='Lever Length')
        #    plt.ylim((0,300))
        #    plt.show()
        #    plt.close()
        try:
            sigmamin_index=[i for i,j in enumerate(sigmas) if j==min(x for x in sigmas if x != 0)] #finds position of smallest non zero element
        except:
            print "Lever not found"
            return
        print sigmamin_index
        bestangle=angles[sigmamin_index[0]]
        return bestangle
    
    def update_display(self):
        
        if self.start_flag:
            self.markButton(self.gui.ui.LeverAlign_pushButton)
            self.start_flag = False
               
        if self.end_flag:
            self.markButton(self.gui.ui.LeverAlign_pushButton, on=False)
            
    def _run(self):
        print "run lever align"
        self.picture_ready, self.picture_displayed, self.start_flag, self.end_flag = False, False, True, False
        self.lever_align_success = False
        
        self.cam_angle = self.gui.firefly_hc.cam_angle_deg.val/180.*np.pi
        self.cam_scalings = 1000.*np.array([self.gui.firefly_hc.cam_scaling_x.val,self.gui.firefly_hc.cam_scaling_y.val])
        
        if self.gui.lsarduino_hc.topLED_intensity.val!=30 or self.gui.lsarduino_hc.bottomLED_intensity.val!=0:
            self.gui.lsarduino_hc.topLED_intensity.update_value(30)
            self.gui.lsarduino_hc.bottomLED_intensity.update_value(0)
            sleep(1.2)
        
        self.updateTemplate()
        
        self.CA_SUCCESS, self.CA_TM_corr = self.LeverCoarseAlign()
        
        self.FA_SUCCESS, self.FA_TM_corr = self.LeverFineAlign()
        
        laserposition=[int(self.gui.ui.LaserCutter_LaserPositionH_doubleSpinBox.value()),int(self.gui.ui.LaserCutter_LaserPositionW_doubleSpinBox.value())]
        windowSize = 200        
        self.cFF_Focus, self.cFF_Focus_SUCCESS = self.gui.auto_focus.FindFocus(1.0, 24., -1, True, 'SGMM', 'MCL', True, laserposition, windowSize)
        
        if self.FA_SUCCESS:
            self.gui.lsarduino_hc.topLED_intensity.update_value(0)
            self.gui.lsarduino_hc.bottomLED_intensity.update_value(100)
            sleep(1.0)
            
            self.lever_width_pxl, self.lever_width_um = self.extract_lever_width(False)
            
            self.gui.lsarduino_hc.topLED_intensity.update_value(30)
            self.gui.lsarduino_hc.bottomLED_intensity.update_value(0)
            sleep(0.5)
        else:
            self.lever_width_pxl = 0
            self.lever_width_um = 0
 
        #re-focus with smaller window centered about laser positi
        self.end_flag = True
        print "Lever Align Done"
        
        try:
            lever_idx = self.gui.lever_detection.getLeverIndex(self.gui.lever_detection.lever_nb.val)
            self.lever_vec_sorted[lever_idx] = [self.lever_angle_deg, self.TM_corr, self.lever_align_success, self.lever_width_pxl, self.lever_width_um]
        except:
            print "Could not access lever number/index to store alignment data..."
            
        if self.gui.ui.LeverAlign_continue_checkBox.isChecked():
            self.gui.ui.LaserCutter_Cut_pushButton.click()
        