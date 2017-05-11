from . import HardwareComponent
try:
    from equipment.thorlabs_pm100d import ThorlabsPM100D
except Exception as err:
    print "Cannot load required modules for Thorlabs Power meter:", err

class ThorlabsPowerMeter(HardwareComponent):
    
    def setup(self):
        self.name = 'thorlabs_powermeter'
        self.debug = False
        
        # Created logged quantities
        self.wavelength = self.add_logged_quantity(
                                                     name = 'wavelength', 
                                                     unit = "nm",
                                                     dtype = int,
                                                     vmin=0,
                                                     vmax=2000, )
        
        self.power = self.add_logged_quantity(name = 'power', dtype=float, unit="W", vmin=0, vmax = 10, ro=True)
        # connect GUI
        self.wavelength.connect_bidir_to_widget(self.gui.ui.power_meter_wl_doubleSpinBox)
        
    def connect(self):
        if self.debug: print "connecting to thorlabs_powermeter"
        
        # Open connection to hardware                        
        self.power_meter = ThorlabsPM100D(debug=self.debug)
        
        #Connect lq
        self.wavelength.hardware_read_func = self.power_meter.get_wavelength
        self.wavelength.hardware_set_func  = self.power_meter.set_wavelength
        
        self.power.hardware_read_func = self.power_meter.measure_power

    def disconnect(self):
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        #disconnect hardware
        self.power_meter.close()
        
        # clean up hardware object
        del self.power_meter
                