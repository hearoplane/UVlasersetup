import visa
import time

TRIES_BEFORE_FAILURE = 10
RETRY_SLEEP_TIME = 0.010  # in seconds

class ThorlabsPM100D(object):
    """
    Thorlabs PM100D power meter
    
    uses the PyVISA 1.5 library to communicate over USB.
    """

    
    def __init__(self, port="USB0::0x1313::0x8078::P0005750::INSTR", debug=False):
    
        self.port = port
        self.debug = debug

        self.visa_resource_manager = visa.ResourceManager()
    
        if debug: self.visa_resource_manager.list_resources()
    
        self.pm = self.visa_resource_manager.get_instrument(port)
    
        self.idn = self.ask("*IDN?")
        
        self.sensor_idn = self.ask("SYST:SENS:IDN?")
        
        self.write("CONF:POW") # set to power meaurement

        self.wavelength_min = float(self.ask("SENS:CORR:WAV? MIN"))
        self.wavelength_max = float(self.ask("SENS:CORR:WAV? MAX"))
        self.get_wavelength()
        
        self.get_attenuation_dB()
        
        self.write("SENS:POW:UNIT W") # set to Watts
        self.power_unit = self.ask("SENS:POW:UNIT?")

        self.write("SENS:POW:RANG:AUTO ON") # turn on auto range

        self.auto_range = bool(self.ask("SENS:POW:RANG:AUTO?"))
        
        self.get_average_count()
        
        self.get_power_range()        
        self.measure_power()
        self.measure_frequency()
        
        
    
    def ask(self, cmd):
        if self.debug: print "PM100D ask ", repr(cmd)
        resp = self.pm.ask(cmd)
        if self.debug: print "PM100D resp --->", repr(resp)
        return resp
    
    def write(self, cmd):
        if self.debug: print "PM100D write", repr(cmd)
        resp = self.pm.write(cmd)
        if self.debug: print "PM100D written --->", repr(resp)
        
    def get_wavelength(self):
        try_count = 0
        while True:
            try:
                self.wl = float(self.ask("SENS:CORR:WAV?"))
                if self.debug: print "wl:", repr(self.wl)
                break
            except:
                if try_count > 9:
                    print "Failed to get wavelength."
                    break
                else:
                    time.sleep(RETRY_SLEEP_TIME)  #take a rest..
                    try_count = try_count + 1
                    print "trying to get the wavelength again.."
        return self.wl
    
    def set_wavelength(self, wl):
        try_count = 0
        while True:
            try:
                self.write("SENS:CORR:WAV %f" % wl)
                time.sleep(0.005) # Sleep for 5 ms before rereading the wl.
                break
            except:
                if try_count > 9:
                    print "Failed to set wavelength."
                    time.sleep(0.005) # Sleep for 5 ms before rereading the wl.
                    break
                else:
                    time.sleep(RETRY_SLEEP_TIME)  #take a rest..
                    try_count = try_count + 1
                    print "trying to set wavelength again.."

        return self.get_wavelength()
    
    def get_attenuation_dB(self):
        # in dB (range for 60db to -60db) gain or attenuation, default 0 dB
        self.attenuation_dB = float( self.ask("SENS:CORR:LOSS:INP:MAGN?") )
        if self.debug: print "attenuation_dB", self.attenuation_dB
        return self.attenuation_dB

    
    def get_average_count(self):
        """each measurement is approximately 3 ms.
        returns the number of measurements
        the result is averaged over"""
        self.average_count = int( self.ask("SENS:AVER:COUNt?") )
        if self.debug: print "average count:", self.average_count
        return self.average_count
    
    def set_average_count(self, cnt):
        """each measurement is approximately 3 ms.
        sets the number of measurements
        the result is averaged over"""
        self.write("SENS:AVER:COUNT %i" % cnt)
        return self.get_average_count()
            
    
    def measure_power(self):
        self.power = float(self.ask("MEAS:POW?"))
        if self.debug: print "power:", self.power
        return self.power
        
    def get_power_range(self):
        self.power_range = self.ask("SENS:POW:RANG?") # CHECK RANGE
        if self.debug: print "power_range", self.power_range
        return self.power_range
    
    def measure_frequency(self):
        self.frequency = self.ask("MEAS:FREQ?")
        if self.debug: print "frequency", self.frequency
        return self.frequency

    def close(self):
        return self.pm.close()

if __name__ == '__main__':
    
    power_meter = ThorlabsPM100D(debug=True)
    power_meter.get_wavelength()
    power_meter.get_average_count()
    power_meter.measure_power()