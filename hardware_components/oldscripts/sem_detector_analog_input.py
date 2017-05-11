from . import HardwareComponent
try:
    from equipment.ni_analog_input import NI_AnalogInput
except Exception as err:
    print "Cannot load required modules for SEM Dector Analog:", err
import time

class SEMDetectorHardwareComponent(HardwareComponent):
    
    def setup(self):
        self.name = "sem_detector_analog"
        self.debug = True
        
        
        # Create Logged quantities
        self.voltage = self.add_logged_quantity(
                                name = 'voltage', 
                                initial = 0,
                                dtype=float, fmt="%e", ro=True,
                                unit="V",
                                vmin=-11, vmax=11)
        """self.int_time = self.add_logged_quantity(
                                name = 'int_time',
                                initial=0.1,
                                dtype=float, fmt="%e", ro=False,
                                unit = "sec",
                                vmin = 1e-6, vmax=100)
        """
        
    def connect(self):
        if self.debug: print "Connecting to SEM Detector Analog"
        
        # Open connection to hardware
        self.ni_analog_in = NI_AnalogInput(input_channel="ADC_BNC/ai0", debug = self.debug)

        # connect logged quantities
        self.voltage.hardware_read_func = self.read_voltage

    def disconnect(self):
        #disconnect hardware
        self.ni_analog_in.close()
        
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        del self.ni_analog_in


    def read_voltage(self):
        try:
            #self.ni_analog_in.start()
            #time.sleep(self.int_time.val)
            #v = self.ni_analog_in.read_average_voltage_in_buffer()
            v = self.ni_analog_in.read_voltage_single()
        except Exception as E:
            print E
            #self.ni_counter.reset()
        finally:
            self.ni_analog_in.stop()
        return v


