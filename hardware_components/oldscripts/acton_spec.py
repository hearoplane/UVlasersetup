'''
Created on May 28, 2014

@author: Edward Barnard
'''
from . import HardwareComponent
try:
    from equipment.acton_spec import ActonSpectrometer
except Exception as err:
    print "Cannot load required modules for ActonSpectrometer:", err
import time
from PySide import QtCore


ACTON_SPEC_PORT = "COM11"

class ActonSpectrometerHardwareComponent(HardwareComponent):
    
    def setup(self):
        self.name = "acton_spectrometer"
        self.debug = False
        
        # Create logged quantities
        self.center_wl = self.add_logged_quantity(
                                name="center_wl",
                                dtype=float, 
                                fmt="%1.3f",
                                ro=True,
                                unit = "nm",
                                vmin=-100, vmax=2000,
                                )

        self.grating = self.add_logged_quantity(
                                name="spec_grating",
                                dtype=str,
                                fmt="%s",
                                ro=True,
                                )



    def connect(self):
        if self.debug: print "connecting to acton_spectrometer"

        # Open connection to hardware
        self.acton_spectrometer = ActonSpectrometer(port=ACTON_SPEC_PORT, debug=True, dummy=False)

        # connect logged quantities
        self.center_wl.hardware_read_func = \
                self.acton_spectrometer.read_wl
        self.grating.hardware_read_func =  \
                self.acton_spectrometer.read_grating_name

        # connect GUI
        self.center_wl.updated_value[float].connect(
                        self.gui.ui.acton_spec_center_wl_doubleSpinBox.setValue)
        self.grating.updated_value[str].connect(
                        self.gui.ui.acton_spec_grating_lineEdit.setText)    


    def disconnect(self):
        #disconnect hardware
        self.acton_spectrometer.close()
        
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        del self.acton_spectrometer
