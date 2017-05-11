from . import HardwareComponent
try:
    from equipment.ni_freq_counter import NI_FreqCounter
except Exception as err:
    print "Cannot load required modules for APDCounter:", err
    
import time

class APDCounterHardwareComponent(HardwareComponent):
    
    def setup(self):
        self.name = "apd_counter"
        self.debug = False
        
        # Create logged quantities
        self.apd_count_rate = self.add_logged_quantity(
                                name = 'apd_count_rate', 
                                initial = 0,
                                dtype=float, fmt="%e", ro=True,
                                unit="Hz",
                                vmin=-1, vmax=1e10)
        self.int_time = self.add_logged_quantity(
                                name = 'int_time',
                                initial=0.1,
                                dtype=float, fmt="%e", ro=False,
                                unit = "sec",
                                vmin = 1e-6, vmax=100)
    def connect(self):
        if self.debug: print "Connecting to APD Counter"
        
        # Open connection to hardware
        self.ni_counter = NI_FreqCounter(debug = self.debug, mode='high_freq')

        # connect logged quantities
        self.apd_count_rate.hardware_read_func = self.read_count_rate

        self.apd_count_rate.updated_text_value.connect(
                                       self.gui.ui.apd_counter_output_lineEdit.setText)


    def disconnect(self):
        #disconnect hardware
        self.ni_counter.close()
        
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        del self.ni_counter
        
    def read_count_rate(self):
        try:
            self.ni_counter.start()
            time.sleep(self.int_time.val)
            self.c0_rate = self.ni_counter.read_average_freq_in_buffer()
        except Exception as E:
            print E
            #self.ni_counter.reset()
        finally:
            self.ni_counter.stop()
        return self.c0_rate
