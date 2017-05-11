'''
Created on Sept 20, 2016

@author: Sina Sedighi
'''
import time
import numpy as np
from . import HardwareComponent
try:
    from equipment.mcl_xyz_stage import MCLStage, MCLProductInformation
except Exception as err:
    print "Cannot load required modules for MCLStage:", err

MCL_AXIS_ID = dict(X = 1, Y = 2, Z = 3)
class MCLStageComponent(HardwareComponent):
    name = 'MCL xyz-stage'
    def setup(self):
        self.debug = True
        
        # Created logged quantities
        self.MCLstage_connectivity = self.add_logged_quantity(name="MCL Stage connectivity", dtype=bool, ro=False)
        self.MCL_XYjoystick_step = self.add_logged_quantity(name = 'MCL XY Joystick step', initial=10, dtype=float, ro=False, unit = 'um', vmin=0.1, vmax=100000)
        self.MCL_Zjoystick_step = self.add_logged_quantity(name = 'MCL Z Joystick step', initial=10, dtype=float, ro=False, unit = 'um', vmin=0.1, vmax=100000)
        lq_params = dict(  dtype=float, ro=False,
                           initial = 0.0,
                           vmin=0.0,
                           vmax=300.,
                           unit='um')
        self.MCLposX = self.add_logged_quantity("x_position", **lq_params)
        self.MCLposY = self.add_logged_quantity("y_position", **lq_params)       
        self.MCLposZ = self.add_logged_quantity("z_position", **lq_params)
        lq_params = dict(unit="um", dtype=float, ro=True, initial=100)
        self.MCLmaxX = self.add_logged_quantity("x_max", **lq_params)
        self.MCLmaxY = self.add_logged_quantity("y_max", **lq_params)
        self.MCLmaxZ = self.add_logged_quantity("z_max", **lq_params)
        self.MCLSpeed = self.add_logged_quantity(name='move_speed',
                                                             initial = 13.,
                                                             unit = "um/s",
                                                             vmin = 1e-4,
                                                             vmax = 1000,
                                                             dtype=float)
        self.MCLsettlingTime = self.add_logged_quantity(name='settling_time',
                                                             initial = 0.100,
                                                             unit = "s",
                                                             vmin = 1e-4,
                                                             vmax = 1000,
                                                             dtype=float)
        self.MCLmaxStepSize = self.add_logged_quantity(name='max_step_size',
                                                             initial = 0.100,
                                                             unit = "um",
                                                             vmin = 1e-4,
                                                             vmax = 1000,
                                                             dtype=float)
        
        # Connect GUI
        self.MCLstage_connectivity.connect_bidir_to_widget(self.gui.ui.MCLstage_connected_checkBox)                                                     
        self.MCLposX.connect_bidir_to_widget(self.gui.ui.MCL_stage_posX_doubleSpinBox)
        self.MCLposY.connect_bidir_to_widget(self.gui.ui.MCL_stage_posY_doubleSpinBox)
        self.MCLposZ.connect_bidir_to_widget(self.gui.ui.MCL_stage_posZ_doubleSpinBox)
        self.MCLSpeed.connect_bidir_to_widget(self.gui.ui.MCL_stage_Speed_doubleSpinBox)
        self.MCLsettlingTime.connect_bidir_to_widget(self.gui.ui.MCL_stage_settlingTime_doubleSpinBox)
        self.MCLmaxStepSize.connect_bidir_to_widget(self.gui.ui.MCL_stage_maxStepSize_doubleSpinBox)
        self.MCL_XYjoystick_step.connect_bidir_to_widget(self.gui.ui.MCL_XY_stage_steps_doubleSpinBox)
        self.MCL_Zjoystick_step.connect_bidir_to_widget(self.gui.ui.MCL_Z_stage_steps_doubleSpinBox)
        self.gui.ui.MCL_stage_joystick_left_toolButton.clicked.connect(self.MCL_joystick_step_left)
        self.gui.ui.MCL_stage_joystick_right_toolButton.clicked.connect(self.MCL_joystick_step_right)
        self.gui.ui.MCL_stage_joystick_down_toolButton.clicked.connect(self.MCL_joystick_step_down)
        self.gui.ui.MCL_stage_joystick_up_toolButton.clicked.connect(self.MCL_joystick_step_up)
        self.gui.ui.MCL_Z_stage_joystick_up_toolButton.clicked.connect(self.MCL_Zjoystick_step_up)
        self.gui.ui.MCL_Z_stage_joystick_down_toolButton.clicked.connect(self.MCL_Zjoystick_step_down)
        self.gui.ui.MCL_stage_gotoCenter_pushButton.clicked.connect(self.MCL_gotoCenter)
        self.gui.ui.MCL_stage_gotoStoredPosition_pushButton.clicked.connect(self.MCL_gotoStored)
        self.gui.ui.MCL_stage_setStoredPosition_pushButton.clicked.connect(self.MCL_setStored)
        
    def connect(self):
        if self.debug: print "connecting to mcl_xyz_stage"
        # Open connection to hardware
        self.nanodrive = MCLStage(debug=self.debug)
        
        # connect logged quantities
        self.MCLposX.hardware_read_func = self.get_pos_X
        self.MCLposX.hardware_set_func =  self.set_pos_X
        self.MCLposY.hardware_read_func = self.get_pos_Y
        self.MCLposY.hardware_set_func =  self.set_pos_Y
        self.MCLposZ.hardware_read_func = self.get_pos_Z
        self.MCLposZ.hardware_set_func =  self.set_pos_Z
        self.MCLmaxX.hardware_read_func = lambda: self.nanodrive.cal[MCL_AXIS_ID["X"]]
        self.MCLmaxY.hardware_read_func = lambda: self.nanodrive.cal[MCL_AXIS_ID["Y"]]
        self.MCLmaxZ.hardware_read_func = lambda: self.nanodrive.cal[MCL_AXIS_ID["Z"]]        
                
        # connect Buttons / update initial values    
        self.MCLposX.read_from_hardware()
        self.MCLposY.read_from_hardware()
        self.MCLposZ.read_from_hardware()   
        self.MCLmaxX.read_from_hardware()
        self.MCLmaxY.read_from_hardware()
        self.MCLmaxZ.read_from_hardware()
        
        print 'connected to:', self.name

    def disconnect(self):      
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        #disconnect hardware
        self.nanodrive.close()
        # clean up hardware object
        del self.nanodrive
        print 'disconnected:', self.name   


    def MCL_joystick_step_left(self):
        self.move_rel_X(-self.MCL_XYjoystick_step.val)
        time.sleep(self.MCLsettlingTime.val)
        self.MCLposX.read_from_hardware()
        
    def MCL_joystick_step_right(self):
        self.move_rel_X(self.MCL_XYjoystick_step.val)
        time.sleep(self.MCLsettlingTime.val)
        self.MCLposX.read_from_hardware()
    
    def MCL_joystick_step_down(self):
        self.move_rel_Y(-self.MCL_XYjoystick_step.val)
        time.sleep(self.MCLsettlingTime.val)
        self.MCLposY.read_from_hardware()
    
    def MCL_joystick_step_up(self):
        self.move_rel_Y(self.MCL_XYjoystick_step.val)
        time.sleep(self.MCLsettlingTime.val)
        self.MCLposY.read_from_hardware()
        
    def MCL_Zjoystick_step_up(self):
        self.move_rel_Z(self.MCL_Zjoystick_step.val)
        time.sleep(self.MCLsettlingTime.val)
        self.MCLposZ.read_from_hardware()
       
    def MCL_Zjoystick_step_down(self):
        self.move_rel_Z(-self.MCL_Zjoystick_step.val)
        time.sleep(self.MCLsettlingTime.val)
        self.MCLposZ.read_from_hardware()
        
    def MCL_gotoCenter(self):
        self.set_pos_XYZ(100., 100., 100.)
        time.sleep(self.MCLsettlingTime.val)
        self.get_pos_XYZ()

    def MCL_gotoStored(self):
        x=self.gui.ui.MCL_stage_storedPosX_doubleSpinBox.value()
        y=self.gui.ui.MCL_stage_storedPosY_doubleSpinBox.value()
        z=self.gui.ui.MCL_stage_storedPosZ_doubleSpinBox.value()
        self.set_pos_XYZ(x,y,z)
        time.sleep(self.MCLsettlingTime.val)
        self.get_pos_XYZ()
    
    def MCL_setStored(self):
        self.gui.ui.MCL_stage_storedPosX_doubleSpinBox.setValue(self.get_pos_X())
        self.gui.ui.MCL_stage_storedPosY_doubleSpinBox.setValue(self.get_pos_Y())
        self.gui.ui.MCL_stage_storedPosZ_doubleSpinBox.setValue(self.get_pos_Z())

    def get_pos_X(self): 
        return self.nanodrive.get_pos_ax(MCL_AXIS_ID['X'])

    def get_pos_Y(self): 
        return self.nanodrive.get_pos_ax(MCL_AXIS_ID['Y'])

    def get_pos_Z(self): 
        return self.nanodrive.get_pos_ax(MCL_AXIS_ID['Z'])

    def get_pos_XY(self):
        self.MCLposX.read_from_hardware()
        self.MCLposY.read_from_hardware()
        return (self.MCLposX.val, self.MCLposY.val)

    def get_pos_XYZ(self):
        self.MCLposX.read_from_hardware()
        self.MCLposY.read_from_hardware()
        self.MCLposZ.read_from_hardware()
        return (self.MCLposX.val, self.MCLposY.val, self.MCLposZ.val)
    
    def set_pos_X(self, target): 
        self.nanodrive.set_pos_ax(target, MCL_AXIS_ID['X'])

    def set_pos_Y(self, target): 
        self.nanodrive.set_pos_ax(target, MCL_AXIS_ID['Y'])

    def set_pos_Z(self, target): 
        self.nanodrive.set_pos_ax(target, MCL_AXIS_ID['Z'])
        
    def set_pos_XY(self, x_target, y_target): 
        self.MCLposX.hardware_set_func(x_target)        
        self.MCLposY.hardware_set_func(y_target)
        
    def set_pos_XYZ(self, x_target, y_target, z_target): 
        self.MCLposX.hardware_set_func(x_target)        
        self.MCLposY.hardware_set_func(y_target)
        self.MCLposZ.hardware_set_func(z_target)     
    
    def move_rel_X(self, step):
        self.set_pos_X(self.get_pos_X()+step)

    def move_rel_Y(self, step):
        self.set_pos_Y(self.get_pos_Y()+step)
    
    def move_rel_Z(self, step):
        self.set_pos_Z(self.get_pos_Z()+step)    
        
    def move_rel_XY(self, x_step, y_step):
        self.set_pos_X(self.get_pos_X()+x_step)
        self.set_pos_Y(self.get_pos_Y()+y_step)    

    def pnt_is_in_bounds(self, x, y):
        return bool(0.< x <self.MCLmaxX and 0. < y < self.MCLmaxY)

    def XYZpnt_is_in_bounds(self, x, y, z):
        return bool(0.< x <self.MCLmaxX and 0. < y < self.MCLmaxY and 0. < y < self.MCLmaxZ)

    def WaveformXYZ(self, waveform, limit_stepSize, LaserON):
        """
        waveform input as list of (x,y,z) tuples (or list of [x,y,z] arrays) containing absolute x,y move positions
        *** Starting position should correspond to waveform[0] ***    
        """
        for x,y,z in waveform:
            assert self.XYZpnt_is_in_bounds(x,y,z), "waveform not in MCL bounds"           
        self.set_pos_X(waveform[0][0])
        self.set_pos_Y(waveform[0][1])
        self.set_pos_Z(waveform[0][2])
        time.sleep(0.2)
            
        n_points = len(waveform)
        waveform = np.asarray(waveform)
        if LaserON:
            self.gui.lsarduino_hc.laser_state.hardware_set_func(True)
        for i in range(n_points-1):
            dx = waveform[i+1][0]-waveform[i][0]
            dy = waveform[i+1][1]-waveform[i][1]
            dz = waveform[i+1][2]-waveform[i][2]
            dist = np.sqrt(dx**2+dy**2+dz**2)
            dt = dist / self.MCLSpeed.val
            
            if limit_stepSize ==True:
                n_steps = int(np.ceil(dist/self.MCLmaxStepSize.val))
            else:
                n_steps = 1
            
            x = np.linspace(waveform[i][0], waveform[i+1][0], n_steps+1, endpoint=True)
            y = np.linspace(waveform[i][1], waveform[i+1][1], n_steps+1, endpoint=True)
            z = np.linspace(waveform[i][2], waveform[i+1][2], n_steps+1, endpoint=True)
            for j in range(1,n_steps+1):
                t1 = time.time()
                self.set_pos_X(x[j])
                self.set_pos_Y(y[j])
                self.set_pos_Z(z[j])
                t2 = time.time()
                time.sleep(max(dt/float(n_steps) - (t2-t1),0))
                
        self.gui.lsarduino_hc.laser_state.hardware_set_func(False)


    def Waveform(self, waveform, limit_stepSize, LaserON):
        """
        waveform input as list of (x,y) tuples (or list of [x,y] arrays) containing absolute x,y move positions
        *** Starting position should correspond to waveform[0] ***    
        """
        for x,y in waveform:
            assert self.pnt_is_in_bounds(x,y), "waveform not in MCL bounds"           
        self.set_pos_X(waveform[0][0])
        self.set_pos_Y(waveform[0][1])
        time.sleep(0.2)
            
        n_points = len(waveform)
        waveform = np.asarray(waveform)
        if LaserON:
            self.gui.lsarduino_hc.laser_state.hardware_set_func(True)
        for i in range(n_points-1):
            dx = waveform[i+1][0]-waveform[i][0]
            dy = waveform[i+1][1]-waveform[i][1]
            dist = np.sqrt(dx**2+dy**2)
            dt = dist / self.MCLSpeed.val
            
            if limit_stepSize ==True:
                n_steps = int(np.ceil(dist/self.MCLmaxStepSize.val))
            else:
                n_steps = 1
            
            x = np.linspace(waveform[i][0], waveform[i+1][0], n_steps+1, endpoint=True)
            y = np.linspace(waveform[i][1], waveform[i+1][1], n_steps+1, endpoint=True)
            for j in range(1,n_steps+1):
                t1 = time.time()
                self.set_pos_X(x[j])
                self.set_pos_Y(y[j])
                t2 = time.time()
                time.sleep(max(dt/float(n_steps) - (t2-t1),0))
                
        self.gui.lsarduino_hc.laser_state.hardware_set_func(False)
        
    def Waveform_Rel(self, waveform, limit_stepSize, LaserON):
        """
        waveform input as list of (x,y) tuples (or list of [x,y] arrays) containing relative delta_x, delta_y move positions (from starting)
        """
        waveform = np.asarray(waveform)
        if waveform[0][0] != 0. or waveform[0][1] != 0.:
            waveform = np.row_stack((np.array([0,0]), waveform))
        self.MCLposX.read_from_hardware()
        self.MCLposY.read_from_hardware()
        self.Waveform(waveform + np.array([self.MCLposX.val,self.MCLposY.val]), limit_stepSize, LaserON)

    
    