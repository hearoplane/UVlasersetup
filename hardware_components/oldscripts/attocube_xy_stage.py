'''
Created on Jul 24, 2014

@author: Edward Barnard
'''
from . import HardwareComponent
try:
    from equipment.attocube_ecc100 import AttoCubeECC100
except Exception as err:
    print "could not load modules needed for AttoCubeECC100:", err
    

X_AXIS = 0
Y_AXIS = 1
DEVICE_NUM = 0

class AttoCubeXYStage(HardwareComponent):

    def setup(self):
        self.name = 'attocube_xy_stage'
        self.debug = False
        # if attocube pro is activated
        self.pro = False
        
        # Created logged quantities
        self.x_position = self.add_logged_quantity("x_position", 
                                                   dtype=float,
                                                   ro=True,
                                                   vmin=-1e6,
                                                   vmax=1e6,
                                                   unit='nm'
                                                   )
        
        self.x_target_position = self.add_logged_quantity("x_target_position",
                                                         dtype=float,
                                                         ro=False,
                                                         vmin=-1e6,
                                                         vmax=1e6,
                                                         unit='nm')
        
        self.y_position = self.add_logged_quantity("y_position", 
                                                   dtype=float,
                                                   ro=True,
                                                   vmin=-100e6,
                                                   vmax=100e6,
                                                   unit='nm'
                                                   )
        
        self.y_target_position = self.add_logged_quantity("y_target_position",
                                                         dtype=float,
                                                         ro=False,
                                                         vmin=-100e6,
                                                         vmax=100e6,
                                                         unit='nm')
        
        self.x_step_voltage = self.add_logged_quantity("x_step_voltage",
                                                       dtype=float,
                                                       ro=True)
        
        self.y_step_voltage = self.add_logged_quantity("y_step_voltage",
                                                       dtype=float,
                                                       ro=True)
        if self.pro:
            
            self.x_openloop_voltage = self.add_logged_quantity("x_openloop_voltage",
                                                               dtype=float,
                                                               ro=False)
            
            self.y_openloop_voltage = self.add_logged_quantity("y_openloop_voltage",
                                                               dtype=float,
                                                               ro=False)
            
        self.x_frequency = self.add_logged_quantity("x_frequency",
                                                    dtype=float,
                                                    ro=False)
        
        self.y_frequency = self.add_logged_quantity("y_frequency",
                                                    dtype=float,
                                                    ro=False)
        
        self.x_electrically_connected = self.add_logged_quantity("x_electrically_connected", dtype=bool,
                                                               ro=True)
        
        self.y_electrically_connected = self.add_logged_quantity("y_electrically_connected", dtype=bool,
                                                                 ro=True)
        
        self.x_enable_closedloop_axis = self.add_logged_quantity("x_enable_closedloop_axis", dtype=bool,
                                                                 ro=False)
        
        self.y_enable_closedloop_axis = self.add_logged_quantity("y_enable_closedloop_axis", dtype=bool,
                                                                 ro=False)
        
        # need enable boolean lq's
        
        # connect GUI
        # no custom gui yet
        
    def connect(self):
        if self.debug: print "connecting to attocube_xy_stage"
        
        # Open connection to hardware
        self.ecc100 = AttoCubeECC100(device_num=DEVICE_NUM, debug=self.debug)
        
        # Enable Axes
        
        self.ecc100.enable_axis(X_AXIS, enable=True)
        self.ecc100.enable_axis(Y_AXIS, enable=True)
        
        # connect logged quantities
        self.x_position.hardware_read_func = lambda:  self.ecc100.read_position_axis(X_AXIS)
        #self.x_position.hardware_set_func  = lambda x: self.ecc100.set_position_axis(X_AXIS, x)
        
        self.x_target_position.hardware_read_func = lambda: self.ecc100.read_target_position_axis(X_AXIS)
        self.x_target_position.hardware_set_func = lambda x: self.ecc100.write_target_position_axis(X_AXIS, x)
        
        self.y_position.hardware_read_func = lambda:  self.ecc100.read_position_axis(Y_AXIS)
        #self.y_position.hardware_set_func  = lambda y: self.ecc100.set_position_axis(Y_AXIS, y)
        
        self.y_target_position.hardware_read_func = lambda: self.ecc100.read_target_position_axis(Y_AXIS)
        self.y_target_position.hardware_set_func = lambda y: self.ecc100.write_target_position_axis(Y_AXIS, y)
        
        self.x_step_voltage.hardware_read_func = lambda: self.ecc100.read_step_voltage(X_AXIS)
        
        self.y_step_voltage.hardware_read_func = lambda: self.ecc100.read_step_voltage(Y_AXIS)
        
        if self.pro:
            self.x_openloop_voltage.hardware_read_func = lambda: self.ecc100.read_openloop_voltage(X_AXIS)
            self.x_openloop_voltage.hardware_set_func = lambda x: self.ecc100.write_openloop_voltage(X_AXIS, x)
            
            self.y_openloop_voltage.hardware_read_func = lambda: self.ecc100.read_openloop_voltage(Y_AXIS)
            self.y_openloop_voltage.hardware_set_func = lambda y: self.ecc100.write_openloop_voltage(Y_AXIS, y)
        
        self.x_frequency.hardware_read_func = lambda: self.ecc100.read_frequency(X_AXIS)
        self.x_frequency.hardware_set_func = lambda x: self.ecc100.write_frequency(X_AXIS, x)
        
        self.y_frequency.hardware_read_func = lambda: self.ecc100.read_frequency(Y_AXIS)
        self.y_frequency.hardware_set_func = lambda y: self.ecc100.write_frequency(Y_AXIS, y)
        
        
    def disconnect(self):
        

        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        #disconnect hardware
        self.ecc100.close()
        
        # clean up hardware object
        del self.ecc100
        
        