'''
Created on Sep 18, 2014

@author: Benedikt Ursprung
'''

from . import HardwareComponent

try:
    from equipment.thorlabs_optical_chopper import ThorlabsOpticalChopper
except Exception as err:
    print "Cannot load required modules for Thorlabs Optical Chopper:", err


ThorlabsOpticalChopperPort = 'COM4'


class ThorlabsOpticalChopperComponent(HardwareComponent): #object-->HardwareComponent
    
    name = 'thorlabs_optical_chopper'
    debug = False
    
    
    
    def setup(self):
        self.debug = True
        
        self.freq = self.add_logged_quantity('chopp_frequency', dtype=int, unit='Hz', ro=False)        
        self.freq.connect_bidir_to_widget(self.gui.ui.photocurrent2D_chopp_frequency_doubleSpinBox)

        self.spinning = self.add_logged_quantity('spinning', dtype=bool, unit='Hz', ro=False)        
        self.spinning.connect_bidir_to_widget(self.gui.ui.photocurrent2D_spinning_checkBox)
        
        
        
    def connect(self):
        if self.debug: print "connecting to thorlabs optical chopper"
        
        
        # Open connection to hardware
        self.thorlabs_optical_chopper = ThorlabsOpticalChopper(port=ThorlabsOpticalChopperPort, debug=True)
        
    
        # connect logged quantities
        self.freq.hardware_set_func = \
            self.thorlabs_optical_chopper.write_freq
            
        self.freq.hardware_read_func = \
            self.thorlabs_optical_chopper.read_freq
        
        self.spinning.hardware_set_func = \
            self.thorlabs_optical_chopper.enable
            
        self.spinning.hardware_read_func = \
            self.thorlabs_optical_chopper.read_enable
            
        print 'connected to ',self.name
    


    def disconnect(self):

        # disconnect logged quantities from hardware
    
    
        #disconnect hardware

        self.thorlabs_optical_chopper.close()
        
        # clean up hardware object
        del self.thorlabs_optical_chopper
        
        print 'disconnected ',self.name
        
