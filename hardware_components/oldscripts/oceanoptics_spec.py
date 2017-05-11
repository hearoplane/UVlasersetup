#         print "Initializing OceanOptics spectrometer functionality"
#         self.oo_spectrometer =     OceanOpticsSpectrometer(debug=self.HARDWARE_DEBUG)
#         self.oo_spec_int_time = self.add_logged_quantity(name="oo_spec_int_time", dtype=float,
#                                                 hardware_set_func=self.oo_spectrometer.set_integration_time_sec)
#         self.ui.oo_spec_int_time_doubleSpinBox.valueChanged[float].connect(self.oo_spec_int_time.update_value)
#         self.oo_spec_int_time.updated_value[float].connect(self.ui.oo_spec_int_time_doubleSpinBox.setValue)
#         self.oo_spec_int_time.update_value(0.1)
#         self.oo_spectrometer.start_threaded_acquisition()


from . import HardwareComponent
try:
    from equipment.ocean_optics_seabreeze import OceanOpticsSpectrometer
except Exception as err:
    print "Cannot load required modules for OceanOptics Spectrometer:", err

class OceanOpticsSpectrometerHC(HardwareComponent):
    
    def setup(self):
        self.name = 'ocean_optics_spectrometer'
        self.debug = False
        
        # Create logged quantities
        self.oo_spec_int_time = self.add_logged_quantity(
                                            name="oo_spec_int_time", 
                                            dtype=float,
                                            ro = False,
                                            vmin = 0.0001,
                                            vmax = 1000,
                                            unit = 'sec',
                                            intial = 0.1,
                                            )


        #connect GUI
       #self.oo_spec_int_time.connect_
       
       
       #ui.oo_spec_int_time_doubleSpinBox.valueChanged[float].connect(self.oo_spec_int_time.update_value)

    def connect(self):

        #connect to hardware        
        self.oo_spectrometer = OceanOpticsSpectrometer(debug=self.debug)
        
        
        # Connect logged quantities to hardware
        self.oo_spec_int_time.hardware_set_func=self.oo_spectrometer.set_integration_time_sec

    def disconnect(self):
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        #disconnect hardware
        self.oo_spectrometer.close()
        
        # clean up hardware object
        del self.oo_spectrometer
        