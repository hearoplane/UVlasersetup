'''
Created on Jun 27, 2014

@author: Edward Barnard, Dominik Ziegler
'''
from . import HardwareComponent

try:
    from equipment.laserSetupArduino import laserSetupArduino
except Exception as err:
    print "Cannot load required modules for laserSetupArduino:", err

ARDUINO_PORT = "COM13"

class LSArduinoHardwareComponent(HardwareComponent):
    
    def setup(self):
        self.name = 'LSArduino'
        self.debug = True

        # Create logged quantities
        self.arduino_connectivity = self.add_logged_quantity(name = "Arduino connectivity", dtype=bool, ro=False)        
        self.backlight_state = self.add_logged_quantity("backlight_state", dtype=bool)
        self.topLED_intensity=self.add_logged_quantity("topLED_intensity", dtype=int, unit="x", initial = 0, vmin=0, vmax=100)
        self.bottomLED_intensity=self.add_logged_quantity("bottomLED_intensity", dtype=int, unit="x", initial = 0,vmin=0, vmax=100)
        self.laser_intensity = self.add_logged_quantity('laser_intensity', dtype=int, ro=False)
        self.laser_state = self.add_logged_quantity("laser_state", dtype=bool)
        self.laser_pulseFrequency=self.add_logged_quantity("laser_pulse_frequency", dtype=int, unit="Hz", initial = 400,vmin=33, vmax=400)
        
        # connect GUI
        self.arduino_connectivity.connect_bidir_to_widget(self.gui.ui.arduino_connected_checkBox)
        self.backlight_state.connect_bidir_to_widget(self.gui.ui.backlight_state_checkBox)
        self.laser_pulseFrequency.connect_bidir_to_widget(self.gui.ui.laser_pulseFrequency_SpinBox)
        self.topLED_intensity.connect_bidir_to_widget(self.gui.ui.TopLEDIntensity_SpinBox)
        self.bottomLED_intensity.connect_bidir_to_widget(self.gui.ui.BottomLEDIntensity_SpinBox)
        self.laser_intensity.connect_bidir_to_widget(self.gui.ui.laser_intensity_doubleSpinBox)
        self.gui.ui.readPhotoDetector_pushButton.clicked.connect(self.laser_intensity.read_from_hardware)
        
    def connect(self):
        if self.debug: print "connecting to Arduino"
             
        # Open connection to hardware
        self.lsarduino = laserSetupArduino(port=ARDUINO_PORT, debug=True)

        # connect logged quantities to hardware
        self.backlight_state.hardware_set_func = self.lsarduino.write_Backlight
        self.topLED_intensity.hardware_set_func = self.lsarduino.write_TopIntensity
        self.bottomLED_intensity.hardware_set_func = self.lsarduino.write_BottomIntensity
        self.laser_intensity.hardware_read_func = self.lsarduino.read_LaserIntensity
        self.laser_state.hardware_set_func = self.lsarduino.write_LaserON
        self.laser_pulseFrequency.hardware_set_func = self.lsarduino.write_LaserPulseFrequency
        
        print 'connected to', self.name    
        
    def disconnect(self):
        if self.debug: print "disconnecting Arduino"

        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        #disconnect hardware
        self.lsarduino.close()
        
        # clean up hardware object
        del self.lsarduino
        print 'disconnected', self.name
        
    def measureLaserPower(self):
        return