'''
Created on Jul 27, 2014

@author: Edward Barnard
'''
from . import HardwareComponent
try:
    from equipment.mcl_nanodrive import MCLNanoDrive
except Exception as err:
    print "Cannot load required modules for MclXYZStage:", err



class MclXYZStage(HardwareComponent):
    
    MCL_AXIS_ID = dict(X = 2, Y = 1, Z = 3)

    
    def setup(self):
        self.name = 'mcl_xyz_stage'
        self.debug = True
        
        # Created logged quantities
        lq_params = dict(  dtype=float, ro=True,
                           initial = -1,
                           vmin=-1,
                           vmax=100,
                           unit='um')
        self.x_position = self.add_logged_quantity("x_position", **lq_params)
        self.y_position = self.add_logged_quantity("y_position", **lq_params)       
        self.z_position = self.add_logged_quantity("z_position", **lq_params)
        
        lq_params = dict(  dtype=float, ro=False,
                           initial = -1,
                           vmin=-1,
                           vmax=100,
                           unit='um')
        self.x_target = self.add_logged_quantity("x_target", **lq_params)
        self.y_target = self.add_logged_quantity("y_target", **lq_params)       
        self.z_target = self.add_logged_quantity("z_target", **lq_params)        
        
        
        lq_params = dict(unit="um", dtype=float, ro=True, initial=100)
        self.x_max = self.add_logged_quantity("x_max", **lq_params)
        self.y_max = self.add_logged_quantity("y_max", **lq_params)
        self.z_max = self.add_logged_quantity("z_max", **lq_params)

        lq_params = dict(dtype=str, choices=[("X","X"), ("Y","Y"),("Z","Z")])
        self.h_axis = self.add_logged_quantity("h_axis", initial="X", **lq_params)
        self.v_axis = self.add_logged_quantity("v_axis", initial="Y", **lq_params)
        
        self.move_speed = self.add_logged_quantity(name='move_speed',
                                                             initial = 1.0,
                                                             unit = "um/s",
                                                             vmin = 1e-4,
                                                             vmax = 1000,
                                                             dtype=float)        
        
        # connect GUI
        self.x_position.updated_value.connect(self.gui.ui.cx_doubleSpinBox.setValue)
        self.gui.ui.x_set_lineEdit.returnPressed.connect(self.x_position.update_value)

        self.y_position.updated_value.connect(self.gui.ui.cy_doubleSpinBox.setValue)
        self.gui.ui.y_set_lineEdit.returnPressed.connect(self.y_position.update_value)

        self.z_position.updated_value.connect(self.gui.ui.cz_doubleSpinBox.setValue)
        self.gui.ui.z_set_lineEdit.returnPressed.connect(self.z_position.update_value)
        
        self.move_speed.connect_bidir_to_widget(
                                  self.gui.ui.nanodrive_move_slow_doubleSpinBox)
        
    def connect(self):
        if self.debug: print "connecting to mcl_xyz_stage"
        
        # Open connection to hardware
        self.nanodrive = MCLNanoDrive(debug=self.debug)
        
        # connect logged quantities
        self.x_target.hardware_set_func  = \
            lambda x: self.nanodrive.set_pos_ax_slow(x, self.MCL_AXIS_ID["X"])
        self.y_target.hardware_set_func  = \
            lambda y: self.nanodrive.set_pos_ax_slow(y, self.MCL_AXIS_ID["Y"])
        self.z_target.hardware_set_func  = \
            lambda z: self.nanodrive.set_pos_ax_slow(z, self.MCL_AXIS_ID["Z"])

        self.x_position.hardware_read_func = \
            lambda: self.nanodrive.get_pos_ax(self.MCL_AXIS_ID["X"])
        self.y_position.hardware_read_func = \
            lambda: self.nanodrive.get_pos_ax(self.MCL_AXIS_ID["Y"])
        self.z_position.hardware_read_func = \
            lambda: self.nanodrive.get_pos_ax(self.MCL_AXIS_ID["Z"])
            
            
        self.x_max.hardware_read_func = lambda: self.nanodrive.cal[self.MCL_AXIS_ID["X"]]
        self.y_max.hardware_read_func = lambda: self.nanodrive.cal[self.MCL_AXIS_ID["Y"]]
        self.z_max.hardware_read_func = lambda: self.nanodrive.cal[self.MCL_AXIS_ID["Z"]]
        
        self.move_speed.hardware_read_func = self.nanodrive.get_max_speed
        self.move_speed.hardware_set_func =  self.nanodrive.set_max_speed

    def disconnect(self):
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        #disconnect hardware
        self.nanodrive.close()
        
        # clean up hardware object
        del self.nanodrive
        
    @property
    def v_axis_id(self):
        return self.MCL_AXIS_ID[self.v_axis.val]
    
    @property
    def h_axis_id(self):
        return self.MCL_AXIS_ID[self.h_axis.val]
    
    @property
    def x_axis_id(self):
        return self.MCL_AXIS_ID["X"]
    
    @property
    def y_axis_id(self):
        return self.MCL_AXIS_ID["Y"]
    
    @property
    def z_axis_id(self):
        return self.MCL_AXIS_ID["Z"]
    