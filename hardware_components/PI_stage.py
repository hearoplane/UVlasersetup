'''
Scuba Probe Technologies LLC, 2015
@author:  DZiegler  dominik@scubaprobe.com 
GUI interface of the PI xyz-stage. (e.g. Joystick)
'''

from . import HardwareComponent
import pipython
import math
from time import sleep
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
#from networkx.algorithms.distance_measures import radius

CONTROLLER="E-725"     
STAGE="P-562.3CD"  

class PIStage(HardwareComponent): 
    name = 'PIStage'

    def setup(self):
        self.debug = False
        
        #add Logged Quantities
        self.PIStage_connectivity = self.add_logged_quantity(name="PI Stage connectivity", dtype=bool, ro=False)
        self.PIposX = self.add_logged_quantity(name = 'PI_x', 
                                              initial = 0,
                                              dtype=float, fmt='%10.1f', ro=False,
                                              unit='um',
                                              vmin=-1e10, vmax=1e10)
        self.PIposY = self.add_logged_quantity('PI_y', dtype=float, unit='um', ro=False)
        self.PIposZ = self.add_logged_quantity('PI_z', dtype=float, unit='um', ro=False)
        self.PI_joystick_step = self.add_logged_quantity(name = 'PI Joystick step', initial=10, dtype=float, ro=False, unit = 'um', vmin=0.1, vmax=100000)
        self.PI_Zjoystick_step = self.add_logged_quantity(name = 'PI Z Joystick step', initial=10, dtype=float, ro=False, unit = 'um', vmin=0.1, vmax=100000)
        self.gui.ui.LaserCutter_UseLeverAngles = self.add_logged_quantity(name = "Use Lever Angles", dtype=bool, ro=False)
        #self.gui.ui.PI_HalfCircle_UseAngle=self.add_logged_quantity(name="Half Circles use Angle", dtype=bool, ro=False)
        #self.PI_HalfCircle_UseAngle=self.add_logged_quantity(name= "Half Circle Use Angle", initial = False, dtype=bool, ro=False)
        
        #connect to custom gui - NOTE:  these are not disconnected! 
        self.PIStage_connectivity.connect_bidir_to_widget(self.gui.ui.PIStage_connected_checkBox)
        #self.PIStage_connectivity.hardware_set_func = self.setPIStageConnection
        self.gui.ui.PI_stage_joystick_left_toolButton.clicked.connect(self.PI_joystick_step_left)
        self.gui.ui.PI_stage_joystick_right_toolButton.clicked.connect(self.PI_joystick_step_right)
        self.gui.ui.PI_stage_joystick_down_toolButton.clicked.connect(self.PI_joystick_step_down)
        self.gui.ui.PI_stage_joystick_up_toolButton.clicked.connect(self.PI_joystick_step_up)
        self.gui.ui.PI_Z_stage_joystick_up_toolButton.clicked.connect(self.PI_Zjoystick_step_up)
        self.gui.ui.PI_Z_stage_joystick_down_toolButton.clicked.connect(self.PI_Zjoystick_step_down)                  
        self.gui.ui.PI_stage_gotoCenter_pushButton.clicked.connect(self.PI_gotoCenter)
        #self.gui.ui.PI_stage_setOrigin_pushButton.clicked.connect(self.PI_setOrigin)
        self.gui.ui.PI_stage_gotoStoredPosition_pushButton.clicked.connect(self.PI_gotoStored)
        self.gui.ui.PI_stage_setStoredPosition_pushButton.clicked.connect(self.PI_setStored)
        self.gui.ui.PI_stage_startWaveGenerator_pushButton.clicked.connect(self.PI_startWaveGenerator)
        self.gui.ui.PI_stage_stopWaveGenerator_pushButton.clicked.connect(self.PI_stopWaveGenerator)
        self.PIposX.connect_bidir_to_widget(self.gui.ui.PI_stage_posX_doubleSpinBox)
        self.PIposY.connect_bidir_to_widget(self.gui.ui.PI_stage_posY_doubleSpinBox)
        self.PIposZ.connect_bidir_to_widget(self.gui.ui.PI_stage_posZ_doubleSpinBox)
        self.PI_joystick_step.connect_bidir_to_widget(self.gui.ui.PI_stage_steps_doubleSpinBox)
        self.PI_Zjoystick_step.connect_bidir_to_widget(self.gui.ui.PI_Z_stage_steps_doubleSpinBox)
        self.gui.ui.LaserCutter_UseLeverAngles.connect_bidir_to_widget(self.gui.ui.PI_stage_Window_useLeverOrientation_checkBox)
        self.gui.ui.Circular_startCircular_pushButton.clicked.connect(self.startCircularCutting)
        self.gui.ui.Circular_updatePath_pushButton.clicked.connect(self.updatePath)
        self.gui.ui.Circular_startMultiCircular_pushButton.clicked.connect(self.startMultiCircularCutting)
        self.gui.ui.PI_HalfCircle_Start_pushButton.clicked.connect(self.StartHalfCircles)
        self.gui.ui.PI_HalfCircleZ_Start_pushButton.clicked.connect(self.StartHalfCirclesZ)
        #self.PI_HalfCircle_UseAngle.connect_bidir_to_widget(self.gui.ui.PIStage     
        
    # Connect to controller
    def connect(self):
        if self.debug: print "connecting to PI stage"
        self.gcs = pipython.GCSCommands(CONTROLLER)
        self.gcs.ConnectUSB(114053980)

        # connect logged quantities
        self.PIposX.hardware_read_func = self.getPosPIX
        self.PIposX.hardware_set_func =  self.PI_moveToX
        self.PIposY.hardware_read_func = self.getPosPIY
        self.PIposY.hardware_set_func =  self.PI_moveToY
        self.PIposZ.hardware_read_func = self.getPosPIZ
        self.PIposZ.hardware_set_func =  self.PI_moveToZ
                    
        # connect Buttons     
        self.PIposX.read_from_hardware()
        self.PIposY.read_from_hardware()
        self.PIposZ.read_from_hardware()   
    
        print 'connected to:', self.gcs.qIDN().rstrip()      
    
    def disconnect(self):   
        #disconnect hardware
        self.gcs.CloseConnection()
      
        # clean up hardware object
        del self.gcs
        print 'disconnected ',self.name    

    def setPIStageConnection(self, setTo):
        if setTo ==True: 
            self.connect(self)   
        elif setTo == False:
            try:
                self.disconnect(self)
                #self.gcs.CloseConnection()
                print 'Disconnect from PI Stage'
            except: 
                pass
            
    def PI_joystick_step_left(self):
        axis = self.gcs.axes[0] #this is x axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, self.PI_joystick_step.val) #left and right inverted 
        self.WaitEndofMove()
        self.PIposX.read_from_hardware()
        
    def PI_joystick_step_right(self):
        axis = self.gcs.axes[0] #this is x axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, -self.PI_joystick_step.val) #left and right inverted
        self.WaitEndofMove()
        self.PIposX.read_from_hardware()
    
    def PI_joystick_step_down(self):
        axis = self.gcs.axes[1] #this is y axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, self.PI_joystick_step.val)
        self.WaitEndofMove()
        self.PIposY.read_from_hardware()
    
    def PI_joystick_step_up(self):
        axis = self.gcs.axes[1] #this is y axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, -self.PI_joystick_step.val)
        self.WaitEndofMove()
        self.PIposY.read_from_hardware()
        
    def PI_Zjoystick_step_up(self):
        axis = self.gcs.axes[2] #this is z axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, self.PI_Zjoystick_step.val)
        self.WaitEndofMove()
        self.PIposZ.read_from_hardware()
       
    def PI_Zjoystick_step_down(self):
        axis = self.gcs.axes[2] #this is z axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, -self.PI_Zjoystick_step.val)
        self.WaitEndofMove()
        self.PIposZ.read_from_hardware()
    
    def PI_moveToX(self,target):
        axes = self.gcs.axes[0]
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,target)
        #self.PIposX.read_from_hardware()
        
    def PI_moveRelX(self,stepX):
        axis = self.gcs.axes[0] #this is z axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, stepX)
        self.WaitEndofMove()
        self.PIposX.read_from_hardware()      
        
    def PI_moveToY(self,target):
        axes = self.gcs.axes[1]
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,target)
        #self.PIposY.read_from_hardware()  
              
    def PI_moveRelY(self,stepY):
        axis = self.gcs.axes[1] #this is z axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, stepY)
        self.WaitEndofMove()
        self.PIposY.read_from_hardware()
             
    def PI_moveToZ(self,target):
        axes = self.gcs.axes[2]
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,target)
        #self.PIposZ.read_from_hardware()
        
    def PI_moveRelZ(self,stepZ):
        axis = self.gcs.axes[2] #this is z axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, stepZ)
        self.WaitEndofMove()
        self.PIposZ.read_from_hardware()
    
    def PI_moveRelZ_noWait(self,stepZ):
        axis = self.gcs.axes[2] #this is z axis
        if self.gcs.qSVO(axis)==False:
            self.gcs.SVO(axis,True)
        self.gcs.MVR(axis, stepZ)
        #self.WaitEndofMove()
        self.PIposZ.read_from_hardware()
        
    def PI_gotoCenter(self):
        axes = self.gcs.axes[:3]
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,[100.0,100.0,100.0])
        self.WaitEndofMove()
        self.PIposX.read_from_hardware()
        self.PIposY.read_from_hardware()
        self.PIposZ.read_from_hardware()
    
    def WaitEndofMove(self):
        moving=self.gcs.IsMoving()
        moving=dict(moving)
        #print "waiting for move to finish"
        while True in moving.values():
            #print moving.values()
            moving=self.gcs.IsMoving()
            moving=dict(moving)
        #print "move finished"
        
    def PI_gotoStored(self):
        axes = self.gcs.axes[:3]
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        x=self.gui.ui.PI_stage_storedPosX_doubleSpinBox.value()
        y=self.gui.ui.PI_stage_storedPosY_doubleSpinBox.value()
        z=self.gui.ui.PI_stage_storedPosZ_doubleSpinBox.value()
        self.gcs.MOV(axes,[x,y,z])
        self.WaitEndofMove()
        self.PIposX.read_from_hardware()
        self.PIposY.read_from_hardware()
        self.PIposZ.read_from_hardware()
    
    def PI_setStored(self):
        self.gui.ui.PI_stage_storedPosX_doubleSpinBox.setValue(self.getPosPIX())
        self.gui.ui.PI_stage_storedPosY_doubleSpinBox.setValue(self.getPosPIY())
        self.gui.ui.PI_stage_storedPosZ_doubleSpinBox.setValue(self.getPosPIZ())

    def PI_startWaveGenerator(self):      
#         with pipython.GCSCommands(CONTROLLER) as talk:
#         self.gcs.ConnectUSB(114053980)
        diameter= str(self.gui.ui.PI_WG_Diameter_doubleSpinBox.value())
        numloops=str(int(self.gui.ui.PI_WG_numloops_doubleSpinBox.value()))
        #velocity=str(int(self.gui.ui.PI_WG_Velocity_doubleSpinBox.value()))
        ZAngle=self.gui.ui.PI_WG_Z_angle_doubleSpinBox.value()
        print "angle ", ZAngle
        ZDepth=float(diameter)*(math.tan(ZAngle/180*math.pi)) 
        print "diam ", diameter
        print "depth ", ZDepth
        ZDepth=str(ZDepth)
              
        startposition=[self.getPosPIX(),self.getPosPIY(),self.getPosPIZ()]
        xoffset= str(startposition[0]-float(diameter)/2)
        yoffset= str(startposition[1])
        zoffset= str(startposition[2])
        
        #commandx='WAV 4 X SIN_P 2000 '+diameter+' 100 2000 500 1000'           
        #commandy='WAV 5 X SIN_P 2000 '+diameter+' 85 2000 0 1000'
        #commandz='WAV 6 X SIN_P 2000 '+ZmodulationDepth+' 100 50 20 1000'
                    
        commandx='WAV 4 X SIN_P 2000 '+diameter+' '+xoffset+' 2000 500 1000'
        self.gcs.ReadGCSCommand(commandx) # <SegLength> <Amp> <Offset> <WaveLength> <StartPoint> <CurveCenterPoint>
        self.gcs.ReadGCSCommand('WSL 1 4')  # WSL m n --> send wave n to channel m
                   
        commandy='WAV 5 X SIN_P 2000 '+diameter+' '+yoffset+' 2000 0 1000'
        self.gcs.ReadGCSCommand(commandy)
        self.gcs.ReadGCSCommand('WSL 2 5')
        
        #commandz='WAV 6 X SIN_P 2000 '+ZmodulationDepth+' 100 0 20 1000'
        #if self.gui.lever_cutting.WaveGen_useTilt.val:
        #    commandz='WAV 6 X SIN_P 2000 '+ZDepth+' '+zoffset+' 2000 0 1000'
        #else:
        #    commandz='WAV 6 X SIN_P 2000 0 '+zoffset+' 2000 0 1000'
        commandz='WAV 6 X SIN_P 2000 '+ZDepth+' '+zoffset+' 2000 0 1000'
        self.gcs.ReadGCSCommand(commandz)
        self.gcs.ReadGCSCommand('WSL 3 6')
        
        self.gcs.ReadGCSCommand('WGC 1 '+numloops) #amount of loops all axis will do the same if one is set
        #self.gcs.ReadGCSCommand('WTR 1') #slow down by factor "This gets  object has no attribute 'gsc' error"
        sleep(0.3)
        self.gui.lever_cutting.LaserON()
        sleep(0.05)
        self.gcs.ReadGCSCommand('WGO 1 1 2 1 3 1') #starts Generators 
        totaltime=30*int(numloops)  #30 is the set time for a loop in the wave generator.
        sleep(totaltime)
        self.gui.lever_cutting.LaserOFF()
        
    def PI_stopWaveGenerator(self):
#         with pipython.GCSCommands(CONTROLLER) as talk:
#         self.gcs.ConnectUSB(114053980)
        self.gcs.ReadGCSCommand('WGO 1 0')
        self.gcs.ReadGCSCommand('WGO 2 0')  
        #talk.ReadGCSCommand('WGO 3 0')
#         self.PIposX.read_from_hardware()
#         self.PIposY.read_from_hardware()
#         self.PIposZ.read_from_hardware()
            
    def getPosPIX(self): #axis is 0 for X, 1 for Y, and 2 for Z
        answer=self.gcs.ReadGCSCommand('POS?')
        answer=answer.split()
        num=float(answer[0][2:-4])
        exp=float(answer[0][-3:])
        positionPI=num*10**exp 
        return positionPI

    def getPosPIY(self): #axis is 0 for X, 1 for Y, and 2 for Z
        answer=self.gcs.ReadGCSCommand('POS?')
        answer=answer.split()
        num=float(answer[1][2:-4])
        exp=float(answer[1][-3:])
        positionPI=num*10**exp 
        return positionPI
    
    def getPosPIZ(self): #axis is 0 for X, 1 for Y, and 2 for Z
        answer=self.gcs.ReadGCSCommand('POS?')
        answer=answer.split()
        num=float(answer[2][2:-4])
        exp=float(answer[2][-3:])
        positionPI=num*10**exp 
        return positionPI
    
    def SingleLine(self):
        startposition=[self.getPosPIX(),self.getPosPIY(),self.getPosPIZ()]
        xstart= str(startposition[0]-float(25))
        ystart= str(startposition[1])
        zstart= str(startposition[2])
        axes = self.gcs.axes[:3]
       
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
        
        startvelocity=self.gui.ui.PI_ArrayofLine_Velocity_doubleSpinBox.value()
        print startvelocity
        self.gcs.ReadGCSCommand('VEL 1 '+str(startvelocity))
        self.gcs.ReadGCSCommand('VEL 2 '+str(startvelocity))
        self.gcs.ReadGCSCommand('VEL 3 '+str(startvelocity))
        
        print startposition[0]
        
        self.gui.lever_cutting.LaserON()
        sleep(0.1)
        xend=str(startposition[0]+float(25))
        self.gcs.MOV(axes,[xend,ystart,zstart])
        self.WaitEndofMove()
        self.gui.lever_cutting.LaserOFF()
        sleep(0.1)
            
        self.gcs.ReadGCSCommand('VEL 1 20000')
        self.gcs.ReadGCSCommand('VEL 2 20000')
        self.gcs.ReadGCSCommand('VEL 3 20000')
        
        xstart=str(startposition[0])
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
        
    def Window(self):
        """Calculate x and y coordinates for a raster scan
        @param h : height (slow scan axis) 
        @param w : width (fast scan axis)
        @param xoffs : Offset of start position for x.
        @param yoffs : Offset of start position for y.
        @param angle : rotation of scan.
        @param nbLines: number of lines
        @param type of scan zig zag or line by line 
        @return : Coordinates x, y of new target as list.
        """
        h=self.gui.ui.LaserCutter_WindowHeight_doubleSpinBox.value()
        w=self.gui.ui.LaserCutter_WindowWidth_doubleSpinBox.value()
        if self.gui.ui.LaserCutter_UseLeverAngles.val:
            try:
                angle=-self.gui.lever_detection.lever_vec_sorted[self.gui.lever_detection.lever_nb.read_from_hardware()-1][2]
                # self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.update_value(angle/np.pi*180) # would be nice to update the value in the GUI
            except:
                print "Lever angles unknown"
                angle=np.pi/180*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
                self.gui.ui.LaserCutter_UseLeverAngles.update_value(False)
        else:
            angle=np.pi/180*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
            
        nbLines=self.gui.ui.LaserCutter_nbLines_doubleSpinBox.value()
        velocity=self.gui.ui.PI_ArrayofLine_Velocity_doubleSpinBox.value() 
        print "velocity", velocity
        #approximation for large nbLines
        maxpnts = 2000
        deltax=w*nbLines*2/maxpnts #approximative distance between two points
        deltatime =deltax/velocity # wait time between two points
        print "deltax ", deltax
        print "deltatime ", deltatime
        pnt=0
    
        #move to start position
        startposition=[self.getPosPIX(),self.getPosPIY(),self.getPosPIZ()]
        
        xstart= str(startposition[0]-float(w/2*math.cos(-angle)))
        ystart= str(startposition[1]+float(w/2*math.sin(-angle))) 
        zstart= str(startposition[2])
        
        axes = self.gcs.axes[:3]
        #move to start position
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
        
        #start cutting 
        self.gui.lever_cutting.LaserON()
        sleep(0.1)
        
        pnts = np.linspace(0, maxpnts, maxpnts+1)
        y = h*pnts/maxpnts
        x = -np.abs(w*signal.sawtooth(2 * np.pi *nbLines* pnts/maxpnts))+w
   
        x = math.cos(angle)*x - math.sin(angle)*y   #To place the cross in the center of the pattern
        y = math.sin(angle)*x + math.cos(angle)*y 
        
        x= x + startposition[0]-w/2*math.cos(angle) #Translate to actual position and place the start in the middle
        y= y + startposition[1]-w/2*math.sin(angle)
        
        axes = self.gcs.axes[:2]

        while pnt < maxpnts+1:
            targets = [x[pnt],y[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
            #print 'targets:', targets
            self.gcs.MOV(axes, targets)
            pnt += 1
            sleep(deltatime)
            
        self.gui.lever_cutting.LaserOFF()
        sleep(0.1)
        
        xstart=str(startposition[0])
        ystart=str(startposition[1])
        zstart=str(startposition[2])
        axes = self.gcs.axes[:3]
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
    
    def updatePath(self):  
        self.fig1 = self.gui.add_figure("Z-R Plot", self.gui.ui.Circular_ZRPlot_groupBox,toolbar=True)
        self.fig1.clear()
        
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
        
        # Axes instance == subplot
        self.ax1_1 = self.fig1.add_subplot(1, 2, 1)
        self.ax1_2 = self.fig1.add_subplot(1, 2, 2)
        plt.close('all')

        # Just a figure and one subplot
        #f, ax1_1 = plt.subplots()
        self.ax1_1.scatter(self.rplot, self.zplot)
        #self.fig1.canvas.draw()
        
        maxpnts=self.gui.ui.Circular_NbPoints_doubleSpinBox.value()
        steps=np.linspace(0,R3,maxpnts)
        #z_r=np.interp(steps, self.rplot, self.zplot)
        #self.ax1_1.plot(steps, z_r)
        self.ax1_1.plot(self.rplot, self.zplot)
        self.ax1_1.set_title('Radial Profile')
        self.ax1_1.set_xlabel("Radius [um]")
        self.ax1_1.set_ylabel("Height [um]")
        self.ax1_1.set_xlim(0, max(self.rplot)+0.05*(max(self.rplot)-min(self.rplot)))
        self.ax1_1.set_ylim(min(self.zplot)-0.05*(max(self.zplot)), max(self.zplot)+0.05*(max(self.zplot)-min(self.zplot)))
        
        
        nbLoops=self.gui.ui.Circular_nbLoops_doubleSpinBox.value()
        [r,phi]=self.CalculateSpiral(min(self.rplot),max(self.rplot), nbLoops, maxpnts)
        [x,y,z]=self.CalculateXYZ(r,phi)

        self.ax1_2.tripcolor(x,y,z)
        self.ax1_2.plot(x,y, 'ko ',ms=2.0)
       
        self.fig1.canvas.draw()
        self.fig1.tight_layout()
        plt.show()  
        return x,y,z
                
    def startMultiCircularCutting(self):
        iterations1=int(self.gui.ui.Circular_iterations1_doubleSpinBox.value())
        print "Iterations1 is ", iterations1
        iterations2=int(self.gui.ui.Circular_iterations2_doubleSpinBox.value())
        dZ_iter1=self.gui.ui.Circular_dZ_iter1_doubleSpinBox.value() 
        dZ_iter2=self.gui.ui.Circular_dZ_iter2_doubleSpinBox.value()
        
        for x in xrange(0, iterations1):
            self.startCircularCutting(dZ_iter1*(x+1))
        for x in xrange(0, iterations2):
            self.startCircularCutting(dZ_iter1*iterations1+dZ_iter2*(x+1))
        
    def startCircularCutting(self,zoffset=None):  
        if zoffset==None: 
            zoffset=0
        print "ZOffset is ", zoffset
        """Cuts a spiral with PI Piezo Stage
        """
        totalTime=self.gui.ui.Circular_TotalTime_doubleSpinBox.value() 
        maxpnts=self.gui.ui.Circular_NbPoints_doubleSpinBox.value() 
        
        [xstart,ystart,zstart]=self.CircularSetOffsets()
        [x,y,z]=self.updatePath()
        
        x=x+xstart
        y=y+ystart
        z=-z+zstart+zoffset
        
        #move to start
        axes = self.gcs.axes[:3]
        targets = [x[len(x)-1],y[len(y)-1],z[len(z)-1]]

        self.gcs.MOV(axes,targets)
        self.WaitEndofMove()
        sleep(0.1)
        #turn laser on. 
        self.gui.lever_cutting.LaserON()
        #sleep(0.05)
        
        deltatime =totalTime/maxpnts # wait time between two points
                ### write an if statement here to pick in or out. 
        
        if self.gui.ui.Circular_spiralOut_checkBox.isChecked():
            pnt=0
            while pnt <maxpnts:
                targets = [x[pnt],y[pnt],z[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
                #print 'targets:', targets
                self.gcs.MOV(axes, targets)
                pnt += 1
                sleep(deltatime)
        else: 
            pnt=maxpnts
            while pnt > 0-1:
                targets = [x[pnt],y[pnt],z[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
                #print 'targets:', targets
                self.gcs.MOV(axes, targets)
                pnt -= 1
                sleep(deltatime)
        #turns laser off when done
        self.gui.lever_cutting.LaserOFF()
        sleep(0.1)
        
        #returns to start position
        axes = self.gcs.axes[:3]
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()

    def CalculateHalfCircle(self, radius, numpoints):
        pnts=np.linspace(0,1,numpoints+1)
        r=np.linspace(radius,radius,numpoints+1)
        phi=pnts*np.pi
        phi=phi-phi[0]

        x =r*np.cos(phi)
        y= r*np.sin(phi)  
        
        if self.gui.ui.PI_HalfCircle_UseAngle_checkBox.isChecked():
            angle=self.gui.ui.PI_HalfCircle_Zangle_doubleSpinBox.value()
            z=-np.sin(angle/180.*np.pi)*y
        else:
            z=0*y
            
        return [x,y,z]
    
    def CalculateHalfCircleZ(self, radius, numpoints):
        pnts=np.linspace(0,1,numpoints+1)
        r=np.linspace(radius,radius,numpoints+1)
        phi=pnts*np.pi
        phi=phi-phi[0]

        y =r*np.cos(phi)
        z =-r*np.sin(phi)  
        
        if self.gui.ui.PI_HalfCircle_UseAngle_checkBox.isChecked():
            angle=self.gui.ui.PI_HalfCircle_Zangle_doubleSpinBox.value()
            x=-np.sin(angle/180*np.pi)*z
        else:
            x=0*z
   
        return [x,y,z]
           
    def StartHalfCirclesZ(self): 
        [xstart,ystart,zstart]=self.CircularSetOffsets() #This only gets current position
        radius=self.gui.ui.PI_HalfCircleZ_Radius_doubleSpinBox.value() 
        totalTime=self.gui.ui.PI_HalfCircleZ_TotalTime_doubleSpinBox.value() 
        maxpnts=self.gui.ui.PI_HalfCircleZ_NbPoints_doubleSpinBox.value() 
        [x,y,z]=self.CalculateHalfCircleZ(radius, maxpnts)
        
        x+=xstart
        y+=ystart
        z=z+zstart+radius
        #plt.plot(z)
        #plt.show() 
        print x[0]
        #move to start
        axes = self.gcs.axes[:3]
        targets = [x[0],y[0],z[0]]

        self.gcs.MOV(axes,targets)
        self.WaitEndofMove()
        sleep(2)
        #turn laser on. 
        self.gui.lever_cutting.LaserON()
        sleep(0.1)
        
        deltatime =totalTime/maxpnts # wait time between two points
        
        ### write an if statement here to pick in or out. 
        
        if self.gui.ui.Circular_spiralOut_checkBox.isChecked():
            pnt=maxpnts
            while pnt > 0-1:
                targets = [x[pnt],y[pnt],z[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
                #print 'targets:', targets
                self.gcs.MOV(axes, targets)
                pnt -= 1
                sleep(deltatime)
        else: 
            pnt=0
            while pnt <maxpnts:
                targets = [x[pnt],y[pnt],z[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
                #print 'targets:', targets
                self.gcs.MOV(axes, targets)
                pnt += 1
                sleep(deltatime)
        #turns laser off when done
        self.gui.lever_cutting.LaserOFF()
        
        #returns to start position
        axes = self.gcs.axes[:3]
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
    
    def StartHalfCircles(self): 
        [xstart,ystart,zstart]=self.CircularSetOffsets()
        radius=self.gui.ui.PI_HalfCircle_Radius_doubleSpinBox.value() 
        totalTime=self.gui.ui.PI_HalfCircle_TotalTime_doubleSpinBox.value() 
        maxpnts=self.gui.ui.PI_HalfCircle_NbPoints_doubleSpinBox.value() 
        [x,y,z]=self.CalculateHalfCircle(radius, maxpnts)
        
        x=x+xstart
        y=y+ystart
        z=-z+zstart
        
        print x[0]
        #move to start
        axes = self.gcs.axes[:3]
        targets = [x[0],y[0],z[0]]

        self.gcs.MOV(axes,targets)
        self.WaitEndofMove()
        sleep(2)
        #turn laser on. 
        self.gui.lever_cutting.LaserON()
        sleep(0.1)
        
        deltatime =totalTime/maxpnts # wait time between two points
    
        ### write an if statement here to pick in or out. 
        
        if self.gui.ui.Circular_spiralOut_checkBox.isChecked():
            pnt=maxpnts
            while pnt > 0-1:
                targets = [x[pnt],y[pnt],z[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
                #print 'targets:', targets
                self.gcs.MOV(axes, targets)
                pnt -= 1
                sleep(deltatime)
        else: 
            pnt=0
            while pnt <maxpnts:
                targets = [x[pnt],y[pnt],z[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
                #print 'targets:', targets
                self.gcs.MOV(axes, targets)
                pnt += 1
                sleep(deltatime)
        #turns laser off when done
        self.gui.lever_cutting.LaserOFF()
        
        #returns to start position
        axes = self.gcs.axes[:3]
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
        
    def CalculateZ(self,r_):
        i = 0
        z= r_ #just to initialize
        rplot=self.rplot
        zplot=self.zplot
        while i <len(r_):
            if rplot[0] <= r_[i] < rplot[1]:
                z[i]=zplot[0]+(zplot[1]-zplot[0])*(r_[i]-rplot[0])/(rplot[1]-rplot[0])
            if rplot[1] <= r_[i] < rplot[2]:
                z[i]=zplot[1]+(zplot[2]-zplot[1])*(r_[i]-rplot[1])/(rplot[2]-rplot[1])
            if rplot[2] <= r_[i] <= rplot[3]:
                z[i]=zplot[2]+(zplot[3]-zplot[2])*(r_[i]-rplot[2])/(rplot[3]-rplot[2])
            #else:
             #   print 'z is not defined'
            i+=1
        return -z
    
    def CalculateSpiral(self,minRadius,maxRadius,nbLoops,numpoints):
        """Calculates R,Phi functions vs time. For Constant linear Velocity Spirals
        @param Radius: Final Radius 
        @param nbLoops: number of lines
        @param numpoints: number of points
        @returns R and Phi of new target as list.
        """
       # pnts = np.linspace(0, numpoints, numpoints+1)
        #for donuts
        t=(minRadius/maxRadius)**2*numpoints
        pnts=np.linspace(t,numpoints,numpoints+1)
        r=maxRadius*np.sqrt(pnts/numpoints)
   
        phi=np.sqrt(pnts/numpoints)
        phi=phi-phi[0]
        phi=phi/phi[numpoints]
        phi=phi*2*np.pi*nbLoops
        phi-=np.pi/2
        #plt.plot(phi)
        #plt.show()
        return [r,phi]

    def CalculateXYZ(self,r,phi):
        """Calculates XYZ functions vs time. For Spirals
        @param R0-R3 : Radii where height is defined 
        @param Z0-Z3: Corresponding heights
        @param velocity : velocity.
        @param nbLoops: number of lines
        @return : Coordinates x, y, z of new target as list.
        """
        x = r * np.cos(phi)
        y= r * np.sin(phi)  
        z= self.CalculateZ(r)  
        
        #add slope
        slopeAngle=self.gui.ui.Circular_SlopeAngle_doubleSpinBox.value()
        z= z-np.sin(slopeAngle/180*np.pi)*(y-min(y))
        return [x,y,z]
        
    def CircularSetOffsets(self):
        #move to start position
        startposition=[self.getPosPIX(),self.getPosPIY(),self.getPosPIZ()]
        xstart= str(startposition[0])
        ystart= str(startposition[1]) 
        zstart= str(startposition[2])
        
        print xstart, ystart, zstart
        
        #self.gui.ui.Circular_Z0_doubleSpinBox.update_value(zstart)
        axes = self.gcs.axes[:3]
        #move to start position
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
        
        xstart=startposition[0]
        ystart=startposition[1]
        zstart=startposition[2]
        return [xstart, ystart, zstart]
    
    def TestDiamond(self):
        self.StartDiamond(True) #starts diamond without cutting
    def Diamond(self):
        self.StartDiamond(False)
        
    def StartDiamond(self,testmodeactive):
        modulation=self.gui.ui.LaserCutter_DiamondModulation_doubleSpinBox.value()
        if testmodeactive:
            iterations=1
        else:
            iterations=self.gui.ui.LaserCutter_DiamondIterations_doubleSpinBox.value()
        
        dr=self.gui.ui.LaserCutter_DiamondRadiusIncrement_doubleSpinBox.value()
        r=self.gui.ui.LaserCutter_DiamondRadius_doubleSpinBox.value()
        
        if self.gui.ui.LaserCutter_UseLeverAngles.val:
            try:
                angle=-self.gui.lever_detection.lever_vec_sorted[self.gui.lever_detection.lever_nb.read_from_hardware()-1][2]
               
                # self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.update_value(angle/np.pi*180) # would be nice to update the value in the GUI
            except:
                print "Lever angles unknown"
                angle=np.pi/180*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
                self.gui.ui.LaserCutter_UseLeverAngles.update_value(False)
        else:
            angle=np.pi/180*self.gui.ui.LaserCutter_angle_deg_doubleSpinBox.value()
        print "Angle is: ", angle*180/(np.pi)    
       #approximation for large nbLines
        maxpnts = self.gui.ui.LaserCutter_DiamondNumPoints_doubleSpinBox.value()
        
        velocity=self.gui.ui.PI_Diamond_Velocity_doubleSpinBox.value() 
        print "velocity", velocity
        #deltax=r*2*np.pi/maxpnts #approximative distance between two points 
        #velo=str(velocity)   
        self.gcs.ReadGCSCommand('VEL 1 '+str(velocity))
        self.gcs.ReadGCSCommand('VEL 2 '+str(velocity))
        self.gcs.ReadGCSCommand('VEL 3 '+str(velocity))
         
        #deltatime =deltax/velocity # wait time between two points
        #deltatime-=0.001 #0.001 is about the time communication with PI stage takes. 
        #if deltatime<0: # deltatime can not be negative 
        #    deltatime=0
        #    print "Deltatime is zero"
        #print "deltax ", deltax
        #print "deltatime ", deltatime
        pnt=0
        k=0
        
        phi=0*np.ones(maxpnts+1)
        Radius=r*np.ones(maxpnts+1);
        
        #move to start position
        startposition=[self.getPosPIX(),self.getPosPIY(),self.getPosPIZ()]
        
        xstart= str(startposition[0])
        ystart= str(startposition[1]) 
        zstart= str(startposition[2])
        
        axes = self.gcs.axes[:3]
        #move to start position
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
    
        j=0
        #Define radius value array according to phi
        while j<iterations:
            j+=1
            k=0
            while k <= maxpnts:     
                phi[k]= k*2*np.pi/maxpnts
                if ((phi[k]>=np.pi) & (phi[k]<2*np.pi)):
                    Radius[k]=r
                    #print "Radius[k]", Radius[k]
                    
                elif ((phi[k]<np.pi) & (phi[k]>=0)):
                    #Radius[k]=r + 0.2*r*np.sinc((phi[k]-np.pi/2)/np.pi*3) #SINC function
                    Radius[k]=r-0.01*modulation*r*np.fabs(np.sin(phi[k]*2))  #SIN
                    #print "Radius[k]", Radius[k]
                k=k+1
            Radius+=j*dr
            
            x = Radius*np.cos(phi)
            y = Radius*np.sin(phi)
    
            x = math.cos(angle)*x - math.sin(angle)*y   #To place the cross in the center of the pattern
            y = math.sin(angle)*x + math.cos(angle)*y 
            
            x = x + startposition[0]+(r+j*dr)*math.sin(angle) #Translate to actual position and place the start in the middle
            y = y + startposition[1]+(r+j*dr)*math.cos(angle)
            
            axes = self.gcs.axes[:2]
            
       
            pnt=0
            while pnt < maxpnts+1:
                
                
                targets = [x[pnt],y[pnt]] #raster(h, r, nbLines, xoffs, yoffs, angle)
                #print 'targets:', targets
                self.gcs.MOV(axes, targets)
                ### maybe the wait end of move can be removed to speed it up. 
                self.WaitEndofMove()
    
                if pnt==0:
                    sleep(0.3)
                    #start cutting
                    if testmodeactive:
                        print "testmode"
                    else:
                        self.gui.lever_cutting.LaserON()
                    sleep(0.1)
                     
                pnt += 1
                #sleep(deltatime)
        
        self.gui.lever_cutting.LaserOFF()
        sleep(0.1)
        
        xstart=str(startposition[0])
        ystart=str(startposition[1])
        zstart=str(startposition[2])
        axes = self.gcs.axes[:3]
        self.gcs.MOV(axes,[xstart,ystart,zstart])
        self.WaitEndofMove()
        
        self.gcs.ReadGCSCommand('VEL 1 20000')
        self.gcs.ReadGCSCommand('VEL 2 20000')
        self.gcs.ReadGCSCommand('VEL 3 20000')
        
              
    def ArrayOfLines(self):
        self.Zstart=self.getPosPIZ()
        print self.Zstart
    
        axes = self.gcs.axes[:3]
        
        if self.gcs.qSVO(axes)==False: self.gcs.SVO(axes,True)
        self.gcs.MOV(axes,[180.0,180.0,self.Zstart])
        self.WaitEndofMove()
        self.PIposZ.read_from_hardware()
        
        startvelocity=self.gui.ui.PI_ArrayofLine_Velocity_doubleSpinBox.value()
        self.gcs.ReadGCSCommand('VEL 2 500')
        distBetweenLines=20
        
        for x in range(0, 5):
            self.gcs.ReadGCSCommand('VEL 1 100')
            self.gcs.MOV(axes,[200.0,200.0-x*distBetweenLines,self.Zstart])
            self.WaitEndofMove()
            velocity=str(startvelocity*(x+1))   
            print velocity
            self.gcs.ReadGCSCommand('VEL 1 '+velocity) 
            self.gui.lever_cutting.LaserON()
            sleep(0.1)
            self.gcs.MOV(axes,[100.0,200.0-x*distBetweenLines,self.Zstart])
            self.WaitEndofMove()   
            self.gui.lever_cutting.LaserOFF()
        
        print "array finished"
        self.gcs.ReadGCSCommand('VEL 1 20000')
        self.gcs.ReadGCSCommand('VEL 2 20000')
        return
    
    def ArrayOfHoles(self):
        Zstart=self.getPosPIZ()
        print Zstart
        for x in range(0, 20):
            self.gui.lever_cutting.LaserON()
            sleep(0.5)
            self.gui.lever_cutting.LaserOFF()
            self.PI_joystick_step_left()
            sleep(0.1)
            self.PI_Zjoystick_step_up()
            sleep(0.1)
            print "finished step", x
            
        for x in range (0, 20):
            self.PI_Zjoystick_step_down()
            sleep(0.1)
            self.PI_joystick_step_right()
            sleep(0.1)
        #self.PI_moveToX(200)
        print "array finished"
        
if __name__ == '__main__':
    pass
    