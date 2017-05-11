'''
Created on Jun 27, 2015
@author: Edward Barnard, Dominik Ziegler
'''
import serial
import time
class laserSetupArduino(object):
    "Arduino controlled Shutter, LED intensity, and measurement of photodiode intensity"
    def __init__(self, port, debug = True):
        self.port = port
        self.debug = debug
        if self.debug: print "Laser Setup Arduino init, port=%s" % self.port
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)        #baudrate=9600, bytesize=8, parity='N', stopbits=1, #xonxoff=0, rtscts=0, timeout=1.0
        self.ser.flush()        time.sleep(0.1)        #self.write_posititon(1)        #self.read_position()        
    def close(self):
        self.ser.close()        
    def send_cmd(self, cmd):        assert len(cmd) == 4, "Arduino input must be 4 characters long (with first character being the device id)"        if self.debug: print "send_cmd:", repr(cmd)        self.ser.write(cmd)
    def ask(self, cmd):
        if self.debug: print "ask:", repr(cmd)
        time.sleep(0.1)
        self.send_cmd(cmd)        time.sleep(0.1)
        resp = self.ser.readline()
        if self.debug: print "resp:", repr(resp)
        return resp
    
    def write_LaserON(self, laser_state):
        if laser_state == True:
            self.ask("L001")
        elif laser_state == False:
            self.ask("L000")
            
    def write_LaserPulseFrequency(self, frequency):
        frequency = str(frequency)
        cmd='F'+'0'*(3-len(frequency))+frequency
        return self.ask(cmd)                
    
    def write_BottomIntensity(self, intensity):
        intensity = str(intensity)
        cmd='B'+'0'*(3-len(intensity))+intensity
        return self.ask(cmd) 
    
    def write_TopIntensity(self, intensity):
        intensity = str(intensity)
        cmd='T'+'0'*(3-len(intensity))+intensity
        return self.ask(cmd) 
    
    def write_Backlight(self, backlight_state):
        if backlight_state == True:
            self.ask("S001")
        elif backlight_state == False:
            self.ask("S000")    
          
    def read_LaserIntensity(self):        try:            resp = self.ask("P000")
            self.LaserIntensity = int(resp)
            print self.LaserIntensity            return self.LaserIntensity        except:            raise ValueError("Arduino controller returned %s " % resp)
