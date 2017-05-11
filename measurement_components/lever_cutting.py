'''
Created on Oct 13, 2014

@author:  DZiegler  dominik@scubaprobe.com 

'''
import cv2
import numpy as np
from .measurement import Measurement
import matplotlib.pyplot as plt
import os
import math
import pickle
from time import sleep, gmtime, strftime
import ctypes  # An included library with Python install.
import datetime
import win32com.client
from skimage.color import rgb2gray
from numpy import arctan
import scipy.misc 

class LeverCutting(Measurement):
    name = "Lever Cutting"
   
    def setup(self):
        self.display_update_period = 0.5 #seconds
        self.lever_vec_sorted = []
        
        #add logged quantities        
        with open('equipment/LaserCurrentPosition.txt','r') as f:
            try: lpos = [float(i) for i in f.read().split("\t")]
            except: 
                ctypes.windll.user32.MessageBoxA(0, "There was a problem loading the laser position from file. Default values loaded.", "Error", 0x0) #6 Yes, 7 No 2 cancel
                lpos = [640, 480]
        
        self.laser_posX = self.add_logged_quantity(name='Laser position x', initial = lpos[0], dtype=int, ro=False, unit='',  vmin=0, vmax=1280)
        self.laser_posY = self.add_logged_quantity(name='Laser position y', initial = lpos[1], dtype=int, ro=False, unit='',  vmin=0, vmax=960)
        
        self.ArrayOfHoles_NHoles = self.add_logged_quantity(name='number of holes', initial = 10, dtype=int, ro=False, unit='',  vmin=1, vmax=200)    
        self.ArrayOfHoles_XYStepSize = self.add_logged_quantity(name='xy step-size', initial = 9., dtype=float, ro=False, unit='um',  vmin=0.1, vmax=200)
        self.ArrayOfHoles_ZStepSize = self.add_logged_quantity(name='z step-size', initial = 9., dtype=float, ro=False, unit='um',  vmin=0.1, vmax=200)
                
        #connect to GUI
        self.gui.ui.LaserCutter_Profile_comboBox.currentIndexChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_UseLeverAngles_checkBox.stateChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_NumIterations_SpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_DiamondModulation_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)       
        self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_DiamondRadius_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_DiamondRadiusIncrement_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_NumPoints_SpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_R0_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_R1_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_R2_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_R3_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_Z0_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_Z1_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_Z2_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_Z3_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_SlopeAngle_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.Circular_nbLoops_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_WindowNLines_SpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_WindowWidth_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
        self.gui.ui.LaserCutter_WindowHeight_doubleSpinBox.valueChanged.connect(self.requestWaveformRefresh)
                
        self.laser_posX.connect_bidir_to_widget(self.gui.ui.LaserCutter_LaserPositionW_doubleSpinBox)
        self.laser_posX.hardware_set_func = self.saveLaserPosition
        self.laser_posY.connect_bidir_to_widget(self.gui.ui.LaserCutter_LaserPositionH_doubleSpinBox) 
        self.laser_posY.hardware_set_func = self.saveLaserPosition
        
        self.gui.ui.LaserCutter_Cut_pushButton.clicked.connect(self.start)
        self.gui.ui.LaserCutter_ArrayOfHoles_pushButton.clicked.connect(self.arrayOfHoles)
        self.gui.ui.LaserCutter_ArrayOfWindows_pushButton.clicked.connect(self.arrayOfWindows)
        self.gui.ui.laser_ONOFF_pushButton.clicked.connect(self.LaserONOFF)

        self.gui.ui.Circular_updatePath_pushButton.clicked.connect(self.plot_ZProfile)

        self.ArrayOfHoles_NHoles.connect_bidir_to_widget(self.gui.ui.ArrayOfHoles_NHoles_SpinBox)
        self.ArrayOfHoles_XYStepSize.connect_bidir_to_widget(self.gui.ui.ArrayOfHoles_XYStepSize_doubleSpinBox)
        self.ArrayOfHoles_ZStepSize.connect_bidir_to_widget(self.gui.ui.ArrayOfHoles_ZStepSize_doubleSpinBox)
        
        self.gui.ui.FindCuttingFocus_pushButton.clicked.connect(self.FindCuttingFocus)
        self.gui.ui.ASI_downToFocus_toolButton.clicked.connect(self.ASI_DownToFocus_down)        

        self.waveform_ready, self.picture_ready, self.picture_displayed, self.start_flag, self.end_flag = False, False, False, True, False
        self.waveform = []  #waveform for video stream overlay

    def requestWaveformRefresh(self, dummy=None):
        self.waveform_ready = False
        
    def refreshWaveform(self, dummy=None):
        profile = self.gui.ui.LaserCutter_Profile_comboBox.currentText() 
        if  profile == 'Diamond':
            self.Diamond(False,False)
        elif profile == 'Spiral':
            self.Spiral(0.,False,False,False)
        elif profile == 'Window':
            self.Window(False, False)
        elif profile == 'None' or profile == 'Array of Holes' or profile == 'Open and Close':
            self.waveform = []
        self.waveform_ready = True

    def testDiamond(self):
        self.Diamond(True,False)
        return
    
    def cutDiamond(self):
        self.Diamond(True,True)
        return

    def calcDiamond(self, iterations, maxpnts, angle, modulation, r, dr):        
        phi=np.zeros(maxpnts)
        Radius=r*np.ones(maxpnts);
        waveform = np.zeros((iterations*(maxpnts),2))
        #Define radius value array according to phi
        for j in range(iterations):
            for k in range(maxpnts):     
                phi[k]= k*2.*np.pi/float(maxpnts)
                if (math.sin(phi[k]+angle)>=0.):
                    Radius[k]=r+float(j)*dr
                    #print "Radius[k]", Radius[k]
                elif (math.sin(phi[k]+angle)<=0.):
                    #Radius[k]=r + 0.2*r*np.sinc((phi[k]-np.pi/2)/np.pi*3) #SINC function
                    Radius[k]=r+float(j)*dr-0.01*modulation*(r+float(j)*dr)*np.fabs(np.sin((phi[k]+angle)*2))  #SIN
                    #print "Radius[k]", Radius[k]
            
            x = Radius*np.cos(phi)
            y = Radius*np.sin(phi)
    
            x = x - (r)*math.sin(angle) #shift waveform
            y = y - (r)*math.cos(angle)
            
            waveform[j*(maxpnts):(j+1)*(maxpnts),:] = np.column_stack((x,y))
        
        waveform = np.roll(waveform,-maxpnts/4+int(angle/(2.*np.pi)*maxpnts),0) #circular roll array to appropriate starting point on curve
        waveform = np.row_stack((waveform, waveform[0,:])) # close curve by adding starting position to end
        return waveform 
    
    def Diamond(self, makeMotion, LaserON):

        if makeMotion==True and LaserON==False:
            iterations=1
        else:
            iterations=self.gui.ui.LaserCutter_NumIterations_SpinBox.value()
        
        modulation=self.gui.ui.LaserCutter_DiamondModulation_doubleSpinBox.value()        
        dr=self.gui.ui.LaserCutter_DiamondRadiusIncrement_doubleSpinBox.value()
        r=self.gui.ui.LaserCutter_DiamondRadius_doubleSpinBox.value()
        maxpnts = self.gui.ui.LaserCutter_NumPoints_SpinBox.value()
        
        if self.gui.ui.LaserCutter_UseLeverAngles_checkBox.isChecked():
            try:
                lever_idx = self.gui.lever_detection.getLeverIndex(self.gui.lever_detection.lever_nb.val)
                angle=self.gui.lever_detection.lever_vec_sorted[lever_idx][2]+np.pi/180.*self.gui.ipevo_hc.cam_angle_deg.val
                # self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.update_value(angle/np.pi*180) # would be nice to update the value in the GUI
            except:
                print "Lever angles unknown"
                angle=np.pi/180.*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
                #self.gui.ui.LaserCutter_UseLeverAngles_checkBox.setChecked(False)
        else:
            angle=np.pi/180.*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()

        waveform_diamond = self.calcDiamond(iterations, maxpnts, angle, modulation, r, dr)
        #scale waveform and store for videostream display
        cam_scaling = np.mean([self.gui.firefly_hc.cam_scaling_x.val, self.gui.firefly_hc.cam_scaling_y.val])
        laser_pos = np.array([self.laser_posX.val, self.laser_posY.val])
        self.waveform = laser_pos + np.int32([cam_scaling*waveform_diamond])
        self.waveform_ready = False

        if makeMotion:
            waveform_diamond[:,0] *= -1.    #flip x
            #obtain start position, calculate waveform
            start_pos = self.gui.MCLstage_hc.get_pos_XY()
            waveform = start_pos + waveform_diamond
            print start_pos
            print waveform[0]
            print waveform[-2]
            #conduct move        
            self.gui.MCLstage_hc.Waveform(waveform, True, LaserON)
            
            #return to starting position
            self.gui.MCLstage_hc.set_pos_XY(start_pos[0], start_pos[1])
            sleep(0.1)
            self.gui.MCLstage_hc.get_pos_XY()
        return    

    def cutWindow(self):
        iterations=self.gui.ui.LaserCutter_NumIterations_SpinBox.value()
        for i in range(iterations):
            self.Window(True, True)
        return

    def calcWindow(self, w, h, Nlines, angle):
        """
        w = width
        h = height
        Nlines = number of lines in y
        angle = orientation angly of window
        """
        dy = h/float(Nlines)
        pnts = np.zeros((Nlines*2,2))
        for i in range(Nlines):
            if (i % 2 ==0): #even
                pnts[2*i,:] = np.array([0,float(i)*dy])
                pnts[2*i+1,:] = np.array([w,float(i)*dy])     
            else: #odd
                pnts[2*i,:] = np.array([w,float(i)*dy])
                pnts[2*i+1,:] = np.array([0,float(i)*dy])
        return pnts
    
    def Window(self, makeMotion, LaserON):
        w  = self.gui.ui.LaserCutter_WindowWidth_doubleSpinBox.value()
        h = self.gui.ui.LaserCutter_WindowHeight_doubleSpinBox.value()
        Nlines = self.gui.ui.LaserCutter_WindowNLines_SpinBox.value()

        if self.gui.ui.LaserCutter_UseLeverAngles_checkBox.isChecked():
            try:
                lever_idx = self.gui.lever_detection.getLeverIndex(self.gui.lever_detection.lever_nb.val)
                angle=self.gui.lever_detection.lever_vec_sorted[lever_idx][2]+np.pi/180.*self.gui.ipevo_hc.cam_angle_deg.val
                # self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.update_value(angle/np.pi*180) # would be nice to update the value in the GUI
            except:
                print "Lever angles unknown"
                angle=np.pi/180.*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
                #self.gui.ui.LaserCutter_UseLeverAngles_checkBox.setChecked(False)
        else:
            angle=np.pi/180.*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
        
        waveform_window = self.calcWindow(w,h,Nlines,angle)
        #scale waveform and store for videostream display
        cam_scaling = np.mean([self.gui.firefly_hc.cam_scaling_x.val, self.gui.firefly_hc.cam_scaling_y.val])
        laser_pos = np.array([self.laser_posX.val, self.laser_posY.val])
        self.waveform = laser_pos + np.int32([cam_scaling*waveform_window])
        self.waveform_ready = False

        if makeMotion:
            waveform_window[:,0] *= -1. #flip along x
            #obtain start position, calculate waveform
            start_pos = self.gui.MCLstage_hc.get_pos_XY()
            waveform = start_pos + waveform_window
            
            #conduct move        
            self.gui.MCLstage_hc.Waveform(waveform, True, LaserON)
            
            #return to starting position
            self.gui.MCLstage_hc.set_pos_XY(start_pos[0], start_pos[1])
            sleep(0.1)
            self.gui.MCLstage_hc.get_pos_XY()
        return

    def arrayOfWindows(self):
        
        r = 8
        c = 8
        
        XStepSize  = 2.*self.gui.ui.LaserCutter_WindowWidth_doubleSpinBox.value()/1000.
        YStepSize = 2.*self.gui.ui.LaserCutter_WindowHeight_doubleSpinBox.value()/1000.
        
        VelStepSize = 5.   #um/s
        FreqStepSize = 50   #Hz
        Fstart = 50
        Vstart = 5.
        xstart, ystart = self.gui.stage_hc.getPosXY_mm()
        
        self.gui.lsarduino_hc.laser_pulseFrequency.update_value(Fstart)
        self.gui.MCLstage_hc.MCLSpeed.update_value(Vstart)
        
        for i in range(r):
            for j in range(c):
                print i,j
                self.gui.stage_hc.moveToXY_mm_backlash(xstart+float(j)*XStepSize, ystart+float(i)*YStepSize)
                self.gui.lsarduino_hc.laser_pulseFrequency.update_value(Fstart+(i)*FreqStepSize)
                self.gui.MCLstage_hc.MCLSpeed.update_value(Vstart+float(j)*VelStepSize)
                self.cutWindow()
                
        #self.gui.stage_hc.moveToXY_mm_backlash(xstart, ystart)
            
    def arrayOfHoles(self):
        xstart, ystart, zstart = self.gui.MCLstage_hc.get_pos_XYZ()
        
        for i in range(self.ArrayOfHoles_NHoles.val):
            self.LaserONOFF()
            self.gui.MCLstage_hc.set_pos_X(xstart+float(i+1)*self.ArrayOfHoles_XYStepSize.val)
            self.gui.MCLstage_hc.set_pos_Z(zstart+float(i+1)*self.ArrayOfHoles_ZStepSize.val)
            print "finished step", i
        
        self.gui.MCLstage_hc.set_pos_XYZ(xstart, ystart, zstart)
        sleep(0.3)
        self.gui.MCLstage_hc.get_pos_XYZ()    
        print "array finished"

    def plot_ZProfile(self):  
        self.fig1 = self.gui.add_figure("Z-R Plot", self.gui.ui.Circular_ZRPlot_groupBox,toolbar=True)
        self.fig1.clear()
                
        # Axes instance == subplot
        self.ax1_1 = self.fig1.add_subplot(1, 2, 1)
        self.ax1_2 = self.fig1.add_subplot(1, 2, 2)
        plt.close('all')

        # Just a figure and one subplot
        self.ax1_1.scatter(self.rplot, self.zplot)
        
        #self.ax1_1.plot(steps, z_r)
        self.ax1_1.plot(self.rplot, self.zplot)
        self.ax1_1.set_title('Radial Profile')
        self.ax1_1.set_xlabel("Radius [um]")
        self.ax1_1.set_ylabel("Height [um]")
        self.ax1_1.set_xlim(0, max(self.rplot)+0.05*(max(self.rplot)-min(self.rplot)))
        self.ax1_1.set_ylim(min(self.zplot)-0.05*(max(self.zplot)), max(self.zplot)+0.05*(max(self.zplot)-min(self.zplot)))

        self.ax1_2.tripcolor(self.waveform_spiral[:,0], self.waveform_spiral[:,1], self.waveform_spiral[:,2])
        self.ax1_2.plot(self.waveform_spiral[:,0], self.waveform_spiral[:,1], 'ko ',ms=2.0)
       
        self.fig1.canvas.draw()
        self.fig1.tight_layout()
        plt.show()  
        return

    def calcSpiral(self,rplot,zplot,slope, angle, nbLoops, numpoints):
        """Calculates XYZ functions vs time. For Spirals
        Calculates R,Phi functions vs time. For Constant linear Velocity Spirals
        @param Radius: Final Radius 
        @param numpoints: number of points
        @param R0-R3 : Radii where height is defined 
        @param Z0-Z3: Corresponding heights
        @param velocity : velocity.
        @param nbLoops: number of lines
        @return : Coordinates x, y, z of new target as list.
        """
        #pnts = np.linspace(0, numpoints, numpoints+1)
        #for donuts
        minRadius = min(rplot)
        maxRadius = max(rplot)
        t=(minRadius/maxRadius)**2*numpoints
        pnts=np.linspace(t,numpoints,numpoints+1)
        r=maxRadius*np.sqrt(pnts/numpoints)
   
        phi=np.sqrt(pnts/numpoints)
        phi=phi-phi[0]
        phi=phi/phi[numpoints]
        phi=phi*2*np.pi*nbLoops
        phi-=np.pi/2+angle
        
        x = r * np.cos(phi)
        y = - r * np.sin(phi)

        z = np.zeros(len(x)) #just to initialize
        for i in range(len(r)):
            if rplot[0] <= r[i] < rplot[1]:
                z[i]=zplot[0]+(zplot[1]-zplot[0])*(r[i]-rplot[0])/(rplot[1]-rplot[0])
            if rplot[1] <= r[i] < rplot[2]:
                z[i]=zplot[1]+(zplot[2]-zplot[1])*(r[i]-rplot[1])/(rplot[2]-rplot[1])
            if rplot[2] <= r[i] <= rplot[3]:
                z[i]=zplot[2]+(zplot[3]-zplot[2])*(r[i]-rplot[2])/(rplot[3]-rplot[2])
        #add slope
        
        z= z-np.sin(slope/180*np.pi)*(y-min(y))
        return [x,y,z]
                
    def MultiSpiralCutting(self):
        iterations1=int(self.gui.ui.Circular_iterations1_doubleSpinBox.value())
        print "Iterations1 is ", iterations1
        iterations2=int(self.gui.ui.Circular_iterations2_doubleSpinBox.value())
        dZ_iter1=self.gui.ui.Circular_dZ_iter1_doubleSpinBox.value() 
        dZ_iter2=self.gui.ui.Circular_dZ_iter2_doubleSpinBox.value()
        
        for x in xrange(0, iterations1):
            self.startCircularCutting(dZ_iter1*(x+1), True, True, True)
        for x in xrange(0, iterations2):
            self.startCircularCutting(dZ_iter1*iterations1+dZ_iter2*(x+1), True, True, True)

    def cutSpiral(self):
        iterations=self.gui.ui.LaserCutter_NumIterations_SpinBox.value()
        for i in range(iterations):
            self.Spiral(0., True, True, True)
        return
        
    def Spiral(self, zoffset, makeMotion, LaserON, plotZProfile):  
        R0=self.gui.ui.Circular_R0_doubleSpinBox.value()
        R1=self.gui.ui.Circular_R1_doubleSpinBox.value()
        R2=self.gui.ui.Circular_R2_doubleSpinBox.value()
        R3=self.gui.ui.Circular_R3_doubleSpinBox.value()
        self.rplot=[R0,R1,R2,R3]
        Z0=self.gui.ui.Circular_Z0_doubleSpinBox.value()
        Z1=self.gui.ui.Circular_Z1_doubleSpinBox.value()
        Z2=self.gui.ui.Circular_Z2_doubleSpinBox.value()
        Z3=self.gui.ui.Circular_Z3_doubleSpinBox.value()
        self.zplot=[Z0,Z0+Z1,Z0+Z2,Z0+Z3]
        maxpnts=self.gui.ui.LaserCutter_NumPoints_SpinBox.value()
        nbLoops=self.gui.ui.Circular_nbLoops_doubleSpinBox.value()
        slope=self.gui.ui.Circular_SlopeAngle_doubleSpinBox.value()      
        
        if self.gui.ui.LaserCutter_UseLeverAngles_checkBox.isChecked():
            try:
                lever_idx = self.gui.lever_detection.getLeverIndex(self.gui.lever_detection.lever_nb.val)
                angle=self.gui.lever_detection.lever_vec_sorted[lever_idx][2]+np.pi/180.*self.gui.ipevo_hc.cam_angle_deg.val
                # self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.update_value(angle/np.pi*180) # would be nice to update the value in the GUI
            except:
                print "Lever angles unknown"
                angle=np.pi/180.*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
                #self.gui.ui.LaserCutter_UseLeverAngles_checkBox.setChecked(False)
        else:
            angle=np.pi/180.*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
        
        [x,y,z]=self.calcSpiral(self.rplot,self.zplot, slope, angle, nbLoops, maxpnts)
        self.waveform_spiral = np.column_stack((-x,y,z))
        cam_scaling = np.mean([self.gui.firefly_hc.cam_scaling_x.val, self.gui.firefly_hc.cam_scaling_y.val])
        laser_pos = np.array([self.laser_posX.val, self.laser_posY.val])
        self.waveform = laser_pos + np.int32([cam_scaling*self.waveform_spiral[:,:2]])
        self.waveform_ready = False
        #if plotZProfile:
        #    self.plot_ZProfile()
        
        if makeMotion:
            [xstart,ystart,zstart] = self.gui.MCLstage_hc.get_pos_XYZ()
            x=x+xstart
            y=y+ystart
            z=-z+zstart+zoffset
                
            if self.gui.ui.Circular_spiralOut_checkBox.isChecked():
                targets = [x,y,z]
            else:
                targets = [x[::-1], y[::-1], z[::-1]]
    
            self.gui.MCLstage_hc.WaveformXYZ(np.column_stack((x,y,z)), True, LaserON)
    
            #returns to start position
            self.gui.MCLstage_hc.set_pos_XYZ(xstart, ystart, zstart)
            sleep(0.1)
            self.gui.MCLstage_hc.get_pos_XYZ()
    
    def saveLaserPosition(self, dummy=None):
        self.waveform_ready = False
        try: 
            f = open('equipment/LaserCurrentPosition.txt','w')
            f.write(str(self.laser_posX.val) + "\t" + str(self.laser_posY.val))
            f.close()
        except:
            print "Could not save laser position to disk" 
    
    def ASI_DownToFocus_down(self):
        check5 = ctypes.windll.user32.MessageBoxA(0, "Are you sure you have the right objective selected?", "Proceed?", 0x04) #6 Yes, 7 No, 2 cancel
        if check5==6:    
            pos=self.gui.ui.ASI_stage_RoughFocusZ_doubleSpinBox.value()/1000.
            self.gui.stage_hc.moveToZ_mm(pos)
        elif check5==7: return
               
    def initializeDataDictionary(self):
        # clear if it already exists
        self.gui.lever_detection.data_dict = {}
        
        # experiment settings
        #self.gui.lever_detection.data_dict['number_of_measurements'] = self.number_of_measurements.val
        #self.gui.lever_detection.data_dict['repositioning'] = self.repositioning.val        
        
        # experiment info
        self.box_name = str(self.gui.ui.Measurements_box_name_lineEdit.text())
        self.experiment_name = str(self.gui.ui.Measurements_experiment_name_lineEdit.text())
        ##self.fluid = str(self.gui.ui.Measurements_fluid_comboBox.currentText())
        #self.notes = str(self.gui.ui.Measurements_notes_textEdit.toPlainText())     
        
        self.date_time = datetime.datetime.now()
        self.gui.lever_detection.data_dict["date_time"] = self.date_time
        self.gui.lever_detection.data_dict['box_name'] =  self.box_name
        self.gui.lever_detection.data_dict['experiment_name'] =  self.experiment_name
        #self.gui.lever_detection.data_dict['fluid'] =  self.fluid
        #self.gui.lever_detection.data_dict['notes'] =  self.notes
        
        self.directory = 'data/' + self.box_name
        self.filename = self.experiment_name + '_' + \
                        self.date_time.strftime('%Y-%m-%d %H-%M-%S')   
                                            
    def storeData(self):
        # update the previously stored data with new values
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
#         else:
#             with open(pathname, 'rb') as handle:
#                 data_dict = pickle.load(handle)
#                 data_dict.update(self.gui.lever_detection.data_dict)
        pathname = os.path.join(self.directory, self.filename+'.pickle')
        with open(pathname, 'wb') as handle:
            # Different protocols available:
            # 0: Ascii, 1: binary (backwards compatible), 2: binary (new style classes)
            pickle.dump(self.gui.lever_detection.data_dict, handle,  protocol=pickle.HIGHEST_PROTOCOL)
        print "Data stored."

    def makebgr_rgb(self,img):
        b,g,r = cv2.split(img)       # get b,g,r
        try:
            self.img_rgb = cv2.merge([r,g,b])     # switch it to rgb
        except:
            print "there is a problem"
        img=np.array(np.array(self.img_rgb).astype('uint8'))
        #img = np.fliplr(self.img_rgb) 
        return img
              
    def show_resized(self, name, img, factor, closeWindow):
        factor = int(factor)
        img_resized = cv2.resize(img,(img.shape[1]/factor, img.shape[0]/factor))
        cv2.imshow(name, img_resized)
        if closeWindow:
            cv2.waitKey(0)
            cv2.destroyAllWindows()
                
    def cropLaserArea(self, img):
        laserposition=[int(self.gui.ui.LaserCutter_LaserPositionH_doubleSpinBox.value()),int(self.gui.ui.LaserCutter_LaserPositionW_doubleSpinBox.value())]
        dimension=int(2*self.gui.ui.LaserCutter_LaserPositionWindow_doubleSpinBox.value())/2 #make sure it is even number
        img=img[laserposition[0]-dimension/2:laserposition[0]+dimension/2, laserposition[1]-dimension/2:laserposition[1]+dimension/2]
        return img
        
    def FindCuttingFocus(self):
        self.zstart= self.gui.MCLstage_hc.get_pos_Z()
        print "zstart is ", self.zstart
        self.retract=self.gui.ui.LaserCutter_Z_stageRetract_doubleSpinBox.value()
        print self.retract
        
        img1 = self.gui.firefly_hc.takePicture()
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img1 = self.cropLaserArea(img1)
        sleep(0.2)
        img1_ = self.gui.firefly_hc.takePicture()
        img1_ = cv2.cvtColor(img1_, cv2.COLOR_BGR2GRAY)
        img1_ = self.cropLaserArea(img1_)
        sleep(0.2)
        img1__ = self.gui.firefly_hc.takePicture()
        img1__ = cv2.cvtColor(img1__, cv2.COLOR_BGR2GRAY)
        img1__ = self.cropLaserArea(img1__)
        
        s = cv2.norm(img1, img1_, cv2.NORM_L1)
        s_ = cv2.norm(img1_, img1__, cv2.NORM_L1)
        s__ = cv2.norm(img1__, img1, cv2.NORM_L1)
        S = np.array([s,s_,s__])
        noise=np.mean(S)
        print "noise is: ", noise
                
        self.stepsize=self.gui.ui.LaserCutter_Z_stage_steps_doubleSpinBox.value()
        self.MaxDistance=self.gui.ui.LaserCutter_Z_stageMaxDistance_doubleSpinBox.value()
        maxstep=int(self.MaxDistance/self.stepsize)
        threshold=self.gui.ui.LaserCutter_Threshold_doubleSpinBox.value()
        
        for x in range(maxstep):    
            #print "next point is", self.zstart-self.retract+(x+1)*self.stepsize
            self.gui.MCLstage_hc.set_pos_Z(self.zstart-self.retract+(x+1)*self.stepsize)
            sleep(0.2)    
            self.znow= self.gui.MCLstage_hc.get_pos_Z()
            
            print "z is now ", self.znow
            self.LaserONOFF()
            self.gui.MCLstage_hc.set_pos_Z(self.zstart)
            #self.gui.PIstage_hc.WaitEndofMove() 
            #self.gui.PIstage_hc.PIposZ.read_from_hardware()
            sleep(0.2)
            img2 = self.gui.firefly_hc.takePicture()
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            img2 = self.cropLaserArea(img2)
            img3 = cv2.absdiff(img2,img1__)

            s = cv2.norm(img1__, img2, cv2.NORM_L1)
            print "The difference between the images is", s
                      
            if s>threshold*noise:
                print "started to cut sample at ", self.znow 
                #move back to where cutting started
                self.gui.MCLstage_hc.set_pos_Z(self.znow) 
                #self.gui.PIstage_hc.PIposZ.read_from_hardware()
                #display cutting difference 
                img4 = cv2.medianBlur(img3,25)
                #img4 = cv2.Canny(img4,5, 50)
                #(contours,_) = cv2.findContours(img4, mode=cv2.cv.CV_RETR_EXTERNAL, method=cv2.cv.CV_CHAIN_APPROX_TC89_L1)
                #img_contours = np.zeros((img4.shape[0],  img4.shape[1], 1), np.uint8)
                #cv2.drawContours(img_contours, contours, -1, cv2.cv.RGB(0,255,0), 4)
                #final = img_contours
                if self.gui.ui.display_images_checkBox.isChecked():
                    #img4=np.fliplr(img4)
                    #cv2.imshow('img4', img4)
                    #cv2.waitKey(0)
                    #cv2.destroyAllWindows()      
                    plt.imshow(img4, cmap='gray')
                    plt.show()
                return
        
        print "reached end"   
            #final = cv2.addWeighted(img_contours,0.5,img2_disp,0.5,0)


    def LaserON(self):
        self.gui.lsarduino_hc.laser_state.hardware_set_func(True)
        return
                            
    def LaserOFF(self):
        self.gui.lsarduino_hc.laser_state.hardware_set_func(False)
        return
    
    def LaserONOFF(self):
        self.gui.lsarduino_hc.laser_state.hardware_set_func(True)
        OnTime=self.gui.ui.laser_pulseTrainDuration.value()
        print "Laser On for ", OnTime, " seconds."
        sleep(OnTime)
        self.gui.lsarduino_hc.laser_state.hardware_set_func(False)

    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.LaserCutter_Cut_pushButton)
            self.start_flag = False
               
        if self.end_flag:
            self.markButton(self.gui.ui.LaserCutter_Cut_pushButton, on=False)
    
    def autosaveImage(self, filename):

        cv2.imwrite(filename, self.gui.firefly_hc.takePicture())
        
        return            
         
    def _run(self):
        print "run lever cutting"
        self.picture_ready, self.picture_displayed, self.start_flag, self.end_flag = False, False, True, False
        
        BoxName = str(self.gui.ui.BoxName_lineEdit.text())
        if BoxName == '':
            BoxName = 'MISC'
        elif os.path.isdir('Firefly_Snapshots/'+BoxName)==False:
            os.mkdir('Firefly_Snapshots/'+BoxName)
        
        chipNum = 'C'+str(int(self.gui.ui.LeverDetection_lever_nb_doubleSpinBox.value()))
        if chipNum == 'C0' or BoxName=='MISC': 
            chipNum = strftime("%Y%m%d_%H%M%S", gmtime())

        self.autosaveImage('Firefly_Snapshots/'+BoxName+'/'+chipNum+'_bc.png')

        #self.initializeDataDictionary()
        #makes cut as indicated by profile scroll-bar
        profile = self.gui.ui.LaserCutter_Profile_comboBox.currentText() 
        LaserON = bool(self.gui.ui.LaserCutter_TestModeActive_checkBox.isChecked()==False)
        if  profile == 'Diamond':
            self.Diamond(True,True)
        elif profile == 'Spiral':
            self.cutSpiral()
        elif profile == 'Window':
            self.cutWindow()
        elif profile == 'Array of Holes':    
            self.arrayOfHoles()
        elif profile == 'Open and Close':
            self.LaserONOFF()    
        elif profile == 'None':
            print "Cutting profile set to 'None', no cut made."

        self.autosaveImage('Firefly_Snapshots/'+BoxName+'/'+chipNum+'_ac.png')

        self.end_flag = True
        sleep(0.1)
        
        #self.gui.ui.progressBar.setValue(100*(1.+float(self.gui.lever_detection.lever_nb.val))/( 1. + float(len(self.gui.lever_detection.lever_vec_sorted))))    
        if self.gui.ui.cut_continue_checkBox.isChecked():
            self.gui.ui.LeverDetection_gotoNextLever_pushButton.click()
        
    