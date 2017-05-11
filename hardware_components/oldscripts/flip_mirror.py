'''
Created on Jun 27, 2014

@author: Edward Barnard
'''
from . import HardwareComponent

try:
    from equipment.flip_mirror_arduino import FlipMirrorArduino
except Exception as err:
    print "Cannot load required modules for FlipMirrorArduino:", err


FLIP_MIRROR_PORT = "COM3"

class FlipMirrorHardwareComponent(HardwareComponent):
    
    def setup(self):
        self.name = 'flip_mirror'
        self.debug = False
        
        # Create logged quantities        
        self.flip_mirror_position = self.add_logged_quantity("mirror_position", dtype=bool,
                                                                choices = [
                                                                        ("Spectrometer", 0),
                                                                        ("APD", 1)]
                                                             )

        # connect GUI
        self.flip_mirror_position.connect_bidir_to_widget(self.gui.ui.flip_mirror_checkBox)
        
    def connect(self):
        if self.debug: print "connecting to flip mirror arduino"
        
        # Open connection to hardware
        self.flip_mirror = FlipMirrorArduino(port=FLIP_MIRROR_PORT, debug=True)

        # connect logged quantities
        self.flip_mirror_position.hardware_read_func = \
                self.flip_mirror.read_position
        self.flip_mirror_position.hardware_set_func = \
                self.flip_mirror.write_posititon
        

        
        
    def disconnect(self):
        
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        #disconnect hardware
        self.flip_mirror.close()
        
        # clean up hardware object
        del self.flip_mirror