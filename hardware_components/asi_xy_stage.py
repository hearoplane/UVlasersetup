'''
Created on Sep 30, 2014

@author:  DZiegler  dominik@scubaprobe.com 

GUI interface of the ASI xy-stage. (e.g. Joystick)
'''

from . import HardwareComponent
import math
from time import sleep
import numpy as np
import ctypes 

try:
    from equipment.asi_xy_stage import ASIXYStage
except Exception as err:
    print "Cannot load required modules for ASI xy-stage:", err

ASIPort = 'COM9'

class ASIXYStageComponent(HardwareComponent): #object-->HardwareComponent
    name = 'ASI xy-stage'
    
    def setup(self):
        self.debug = False
        self.backlash = 0.2 # anti-backlash movement [mm]
        self.backlashZ = 0.5 # anti-backlash movement Z [mm]
        
        #Add logged quantities
        self.asiStage_connectivity = self.add_logged_quantity(name = "ASI stage connectivity", dtype=bool, ro=False)
        self.posX = self.add_logged_quantity(name = 'x', 
                                              initial = 0,
                                              dtype=float, fmt='%10.1f', ro=False,
                                              unit='um',
                                              vmin=-1e10, vmax=1e10)
        self.posY = self.add_logged_quantity('y', dtype=float, unit='um', ro=False)
        self.posZ = self.add_logged_quantity('z', dtype=float, unit='um', ro=False)
        self.joystick_step = self.add_logged_quantity(name = 'Joystick step', initial=100, dtype=float, ro=False, unit = 'um', vmin=0.1, vmax=100000)
        self.Zjoystick_step = self.add_logged_quantity(name = 'Z Joystick step', initial=100, dtype=float, ro=False, unit = 'um', vmin=0.1, vmax=100000)
               
        #connect to custom gui - NOTE:  these are not disconnected!
        self.asiStage_connectivity.connect_bidir_to_widget(self.gui.ui.ASI_stage_connected_checkBox)
        self.joystick_step.connect_bidir_to_widget(self.gui.ui.ASI_XY_stage_steps_doubleSpinBox)
        self.gui.ui.ASI_XY_stage_joystick_left_toolButton.clicked.connect(self.joystick_step_left)
        self.gui.ui.ASI_XY_stage_joystick_right_toolButton.clicked.connect(self.joystick_step_right)
        self.gui.ui.ASI_XY_stage_joystick_down_toolButton.clicked.connect(self.joystick_step_down)
        self.gui.ui.ASI_XY_stage_joystick_up_toolButton.clicked.connect(self.joystick_step_up)
        self.gui.ui.ASI_XY_stage_gotoOrigin_pushButton.clicked.connect(self.gotoOriginXY)
        self.gui.ui.ASI_XY_stage_storePosition_pushButton.clicked.connect(self.storePosition)
        self.gui.ui.ASI_XY_stage_gotoStoredPosition_pushButton.clicked.connect(self.gotoStoredPosition)
        self.gui.ui.ASI_stage_setOrigin_pushButton.clicked.connect(self.setOrigin)
        self.posX.connect_bidir_to_widget(self.gui.ui.ASI_stage_posX_doubleSpinBox)
        self.posY.connect_bidir_to_widget(self.gui.ui.ASI_stage_posY_doubleSpinBox)
        self.posZ.connect_bidir_to_widget(self.gui.ui.ASI_stage_posZ_doubleSpinBox)
        #self.gui.ui.ASI_stop_pushButton.clicked.connect(self.ASI_stop)
        #self.gui.ui.ASI_stage_goto_Filter1.clicked.connect(self.gotoFilter1)
        #self.gui.ui.ASI_stage_goto_Filter2.clicked.connect(self.gotoFilter2) 
        #self.gui.ui.ASI_stage_goto_Filter3.clicked.connect(self.gotoFilter3) 
        #self.gui.ui.ASI_stage_goto_Filter4.clicked.connect(self.gotoFilter4)
        #self.gui.ui.ASI_stage_goto_Filter5.clicked.connect(self.gotoFilter5) 
        #self.gui.ui.ASI_stage_goto_Filter6.clicked.connect(self.gotoFilter6)
        #self.gui.ui.ASI_stage_goto_Filter7.clicked.connect(self.gotoFilter7)
        self.Zjoystick_step.connect_bidir_to_widget(self.gui.ui.ASI_Z_stage_steps_doubleSpinBox)
        self.gui.ui.ASI_Z_stage_joystick_up_toolButton.clicked.connect(self.Zjoystick_step_up)
        self.gui.ui.ASI_Z_stage_joystick_down_toolButton.clicked.connect(self.Zjoystick_step_down)
        self.gui.ui.ASI_Z_stage_storePosition_pushButton.clicked.connect(self.storeZPosition)
        self.gui.ui.ASI_Z_stage_gotoStoredPosition_pushButton.clicked.connect(self.gotoStoredZPosition)
        self.gui.ui.ASI_Z_stage_gotoOrigin_pushButton.clicked.connect(self.gotoOriginZ)
        self.gui.ui.ASI_Z_stage_gotoUnloadPosition_pushButton.clicked.connect(self.gotoUnloadPosition)
        self.gui.ui.ASI_Z_stage_goBackToBox_pushButton.clicked.connect(self.goBackToBoxPosition)
        self.gui.ui.ASI_Spiral_startSpiral_pushButton.clicked.connect(self.popupCheck)

    def connect(self):
        if self.debug: print "connecting to ASI xy-stage"
        
        # Open connection to hardware
        self.stage = ASIXYStage(port=ASIPort, debug=self.debug)
                      
        # connect logged quantities
        self.posX.hardware_read_func = self.stage.getPosX
        self.posX.hardware_set_func =  self.stage.moveToX
        self.posY.hardware_read_func = self.stage.getPosY
        self.posY.hardware_set_func =  self.stage.moveToY
        self.posZ.hardware_read_func = self.stage.getPosZ
        self.posZ.hardware_set_func =  self.stage.moveToZ
                    
        # connect Buttons     
        self.posX.read_from_hardware()
        self.posY.read_from_hardware()
        self.posZ.read_from_hardware()   
        
        print 'connected to ',self.name

    def disconnect(self):
        # disconnect logged quantities from hardware
        #disconnect hardware
        try: 
            self.stage.close()
            self.gui.ui.ASI_stage_connected_checkBox.setChecked(False)
            del self.stage
        except:
            print "Could not disconnect"
            #self.gui.ui.ASI_stage_connected_checkBox.setChecked(True)
        # clean up hardware object  
        print 'disconnected ',self.name    
     
    def joystick_step_left(self):      
        if self.gui.ui.ASI_stage_backlash_checkBox.isChecked():
            self.stage.setBacklashXY(self.backlash, self.backlash)
            self.stage.moveRelX(self.joystick_step.val)
            self.stage.setBacklashXY(0, 0)
        else:
            self.stage.moveRelX(self.joystick_step.val)
        self.posX.read_from_hardware()

    def joystick_step_right(self):
        if self.gui.ui.ASI_stage_backlash_checkBox.isChecked():
            self.stage.setBacklashXY(self.backlash, self.backlash)
            self.stage.moveRelX(-self.joystick_step.val)
        else:
            self.stage.setBacklashXY(0, 0)
            self.stage.moveRelX(-self.joystick_step.val)
        self.posX.read_from_hardware()
        
    def joystick_step_down(self):
        if self.gui.ui.ASI_stage_backlash_checkBox.isChecked():
            self.stage.setBacklashXY(self.backlash, self.backlash)
            self.compensateTilt(self.joystick_step.val)
            self.stage.moveRelY(-self.joystick_step.val)
        else:
            self.stage.setBacklashXY(0, 0)
            self.compensateTilt(self.joystick_step.val)
            self.stage.moveRelY(-self.joystick_step.val)
        self.posY.read_from_hardware()
    
    def joystick_step_up(self):
        if self.gui.ui.ASI_stage_backlash_checkBox.isChecked():
            self.stage.setBacklashXY(self.backlash, self.backlash)
            self.stage.moveRelY(self.joystick_step.val)
            self.compensateTilt(-self.joystick_step.val)
            self.stage.setBacklashXY(0, 0)
        else:
            self.stage.moveRelY(self.joystick_step.val)
            self.compensateTilt(-self.joystick_step.val)
        self.posY.read_from_hardware()
    
        
    def compensateTilt(self,ystep):
        if self.gui.ui.ASI_stage_CompensateTilt_checkBox.isChecked():
            self.tiltangle= self.gui.ui.ASI_stage_stageTilt_doubleSpinBox.value()  
            zstep=ystep*np.tan(self.tiltangle/180*np.pi)
            print "Z correction is ", zstep, " micro meters"
            self.stage.moveRelZ(zstep)
            self.posZ.read_from_hardware()
        # ASI_stage_stageTilt_doubleSpinBox
    
    def Zjoystick_step_up(self):
        if self.gui.ui.ASI_Z_stage_backlash_checkBox.isChecked():
            self.stage.setBacklashZ(self.backlashZ)
            self.stage.moveRelZ(self.Zjoystick_step.val)
            self.stage.setBacklashZ(0)
        else:
            self.stage.moveRelZ(self.Zjoystick_step.val)
        self.posZ.read_from_hardware()
       
    def Zjoystick_step_down(self):
        if self.gui.ui.ASI_Z_stage_backlash_checkBox.isChecked():
            self.stage.setBacklashZ(self.backlashZ)
            self.stage.moveRelZ(-self.Zjoystick_step.val)
            self.stage.setBacklashZ(0)
        else:
            self.stage.moveRelZ(-self.Zjoystick_step.val)
        self.posZ.read_from_hardware()
    
    def moveToXY_mm(self, x, y):
        self.stage.moveToXY(self.stage.c_mm * x, self.stage.c_mm * y)
        #sleep(0.5)
        #self.posX.read_from_hardware() #!remove for faster spiraling
        #sleep(0.5)
        #self.posY.read_from_hardware()
        #sleep(0.5)
   
    def moveToZ_mm(self, z):
        self.stage.moveToZ(self.stage.c_mm * z)
        #sleep(0.5)        
        #self.posZ.read_from_hardware()
    
    def setCurrentPosToXY_mm(self, x, y):
        self.stage.setCurrentPosToXY(self.stage.c_mm * x, self.stage.c_mm * y)
        
    def moveRelXY_mm(self, stepX, stepY):
        print self.stage.c_mm
        if stepY>=0:
            self.compensateTilt(stepY)
            self.stage.moveRelXY(self.stage.c_mm * stepX, self.stage.c_mm * stepY)
        else:
            self.stage.moveRelXY(self.stage.c_mm * stepX, self.stage.c_mm * stepY)
            self.compensateTilt(stepY)
            
    def moveRelXY_mm_backlash(self, stepX, stepY):  
        self.stage.setBacklashXY(self.backlash, self.backlash)
        if stepY>=0:
            self.compensateTilt(stepY)
            self.stage.moveRelXY(self.stage.c_mm * stepX, self.stage.c_mm * stepY)
        else:
            self.stage.moveRelXY(self.stage.c_mm * stepX, self.stage.c_mm * stepY)
            self.compensateTilt(stepY)
        self.stage.setBacklashXY(0.0, 0.0)  

    def moveRelZ_mm(self, stepZ):
        self.stage.moveRelZ(self.stage.c_mm * stepZ)
        sleep(0.5)        
        self.posZ.read_from_hardware()
        
    def moveRelZ_mmNoWait(self, stepZ):
        self.stage.moveRelZ(self.stage.c_mm * stepZ) 
        self.posZ.read_from_hardware()
        
    def getPosXY_mm(self):
        x,y = self.stage.getPosXY()
        return (x/self.stage.c_mm, y/self.stage.c_mm)
    
    def getPosZ_mm(self):
        z = self.stage.getPosZ()
        while z==None:
            print "could not read z-position..."
            sleep(0.05)
            z = self.stage.getPosZ()
        return (z/self.stage.c_mm)
    
    def moveRelXY(self, x,y):
        self.stage.setBacklashXY(self.backlash, self.backlash)
        self.stage.moveRelXY(x,y)
        sleep(0.5)        
        self.posX.read_from_hardware()
        sleep(0.5)
        self.posY.read_from_hardware()
        
    def moveToXY_mm_backlash(self, x, y):
        self.stage.setBacklashXY(self.backlash, self.backlash)
        self.stage.moveToXY(self.stage.c_mm * x, self.stage.c_mm * y)
        self.stage.setBacklashXY(0.0, 0.0)     
        
    def ASI_stop(self):    
        self.stage.stopASI()
    
    def gotoOriginZ(self):
        self.stage.moveToZ(0)
        self.posZ.read_from_hardware()
    
    def gotoOriginXY(self):
        self.stage.moveToXY(0, 0)
        self.posX.read_from_hardware()
        self.posY.read_from_hardware()
        
    def setOrigin(self):
        check5 = ctypes.windll.user32.MessageBoxA(0, "The origin of XY and Z axis will be reset. Only do this if you are 15mm above the sample on the calibration spot in XY. Or if you know what you are doing. Do you wish to Proceed?", "Proceed?", 0x04) #6 Yes, 7 No, 2 cancel
        if check5==6:
            self.stage.setCurrentPosToXY(0., 0., 0.)
            self.stage.writePosToFile()
            self.posX.read_from_hardware()
            self.posY.read_from_hardware()
            self.posZ.read_from_hardware()
        elif check5==7: return

    def storePosition(self):
        self.gui.ui.ASI_stage_storedPosX_doubleSpinBox.setValue(self.stage.getPosX())
        self.gui.ui.ASI_stage_storedPosY_doubleSpinBox.setValue(self.stage.getPosY())

    def gotoStoredPosition(self):
        x = self.gui.ui.ASI_stage_storedPosX_doubleSpinBox.value()
        y = self.gui.ui.ASI_stage_storedPosY_doubleSpinBox.value()
        self.stage.moveToXY(x, y)
        self.posX.read_from_hardware()
        self.posY.read_from_hardware()
        
    def storeZPosition(self):
        self.gui.ui.ASI_stage_storedPosZ_doubleSpinBox.setValue(self.stage.getPosZ())
        
    def gotoStoredZPosition(self):
        Z = self.gui.ui.ASI_stage_storedPosZ_doubleSpinBox.value()
        self.stage.moveToZ(Z)
        self.posZ.read_from_hardware()
    
    def gotoCameraPosition(self): #not used yet
        x,y,z=[3.0, -33.0, -5.0]
        print x,y,z
        self.moveToZ_mm(z)
        self.posZ.read_from_hardware()
        self.moveToXY_mm(x, y)
        self.posX.read_from_hardware()
        self.posY.read_from_hardware()
    
    def gotoUnloadPosition(self):
        #unload position in mm
        self.xtemp=self.posX.read_from_hardware()
        self.ytemp=self.posY.read_from_hardware()
        self.ztemp=self.posZ.read_from_hardware()
        x=40
        y=-30
        z=0
        
        self.moveToZ_mm(z)
        self.posZ.read_from_hardware()
        self.moveToXY_mm(x, y)
        self.posX.read_from_hardware()
        self.posY.read_from_hardware()
        return self.xtemp, self.ytemp, self.ztemp
    
    def goBackToBoxPosition(self):
        try:
            self.x=int(self.xtemp)
            self.y=int(self.ytemp)
            print "x, y are ", self.x, self.y
        except:
            self.x,self.y=0,0
        self.stage.moveToXY(self.x, self.y)
        self.posX.read_from_hardware()
        self.posY.read_from_hardware()    
        
    def gotoFilter1(self):
        self.stage.moveFWto(5)
        
    def gotoFilter2(self):
        self.stage.moveFWto(6)
        
    def gotoFilter3(self):
        self.stage.moveFWto(7) 
        
    def gotoFilter4(self):
        self.stage.moveFWto(8)
    
    def gotoFilter5(self):
        self.stage.moveFWto(1)
        
    def gotoFilter6(self):
        self.stage.moveFWto(2)    
        
    def gotoFilter7(self):
        self.stage.moveFWto(3)          
    
    def popupCheck(self):
        already_retracted= ctypes.windll.user32.MessageBoxA(0, "Are your sure you want to cut with the ASI XY stage? It might take few minutes to complete.", "Question?", 3) #6 Yes, 7 No 2 cancel
        if already_retracted==6: #Yes,
            ##self.markButton(self.gui.ui.ASI_Spiral_startSpiral_pushButton, on=True) 
            self.startSpiralCutting()
            return
        elif already_retracted==7: #No Need to move.
            ##self.markButton(self.gui.ui.ASI_Spiral_startSpiral_pushButton, on=False)       
            return 
        elif already_retracted==2: 
            ##self.markButton(self.gui.ui.ASI_Spiral_startSpiral_pushButton, on=False)       
            return 
#         
    def startSpiralCutting(self):  
        """Cuts a spiral with ASI Stage
        """
        
        totalTime=self.gui.ui.ASI_Spiral_TotalTime_doubleSpinBox.value() 
        maxpnts=self.gui.ui.ASI_Spiral_NbPoints_doubleSpinBox.value() 
        nbLoops=self.gui.ui.ASI_Spiral_nbLoops_doubleSpinBox.value()
        R0=self.gui.ui.ASI_Spiral_R0_doubleSpinBox.value()
        R1=self.gui.ui.ASI_Spiral_R1_doubleSpinBox.value()
        #Z0=self.gui.ui.ASI_Spiral_Z0_doubleSpinBox.value()
        #Z1=self.gui.ui.ASI_Spiral_Z1_doubleSpinBox.value()
        [r,phi]=self.CalculateSpiral(R0,R1, nbLoops, maxpnts)
        x,y=self.CalculateXY(r,phi) 
       
        x/=1000 # conversion from um to mm
        y/=1000 
        print x
        [xstart,ystart]=self.getPosXY_mm()
        x+=xstart
        y+=ystart
        #z=np.linspace(Z0,Z1,maxpnts+1)
        #move to start
        self.moveToXY_mm(x[0], y[0])
        sleep(1)
        #turn laser on. 
        self.gui.lever_cutting.LaserON()
        sleep(0.1)
        
        deltatime =totalTime/maxpnts # wait time between two points
        pnt=0
        while pnt < maxpnts+1:
            self.moveToXY_mm(x[pnt], y[pnt])
            #self.gui.PIStage.PI_moveToZ(z[pnt])
            pnt += 1
            sleep(deltatime)
        #turns laser off when done
        self.gui.lever_cutting.LaserOFF()
        sleep(0.1)
        self.moveToXY_mm(xstart, ystart)
        return       
        #self.WaitEndofMove()

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
         
        #plt.plot(phi)
        #plt.show()
        return [r,phi]
 
    def CalculateXY(self,r,phi):
        """Calculates XY functions vs time. For Spirals
        """
        x = r * np.cos(phi)
        y= r * np.sin(phi)        
        return [x,y]
    
