'''
Created on Jun 27, 2014

@author: Edward Barnard, Dominik Ziegler
'''
import serial
import time

class FlipMirrorArduino(object):
    "Arduino controlled flip mirror"
    
    def __init__(self, port="COM8", debug = False):
        self.port = port
        self.debug = debug
        
        if self.debug: print "FlipMirrorArduino init, port=%s" % self.port
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)
                                 
                                 #baudrate=9600, 
                                 #bytesize=8, parity='N', stopbits=1, 
                                 #xonxoff=0, rtscts=0, timeout=1.0)
        self.ser.flush()
        time.sleep(0.1)
        #self.write_posititon(1)
        #self.read_position()
        self.position=0
    
    def send_cmd(self, cmd):
        assert len(cmd) == 1
        if self.debug: print "send_cmd:", repr(cmd)
        self.ser.write(cmd)

    def ask(self, cmd):
        if self.debug: print "ask:", repr(cmd)
        self.send_cmd(cmd)
        resp = self.ser.read(1)
        if self.debug: print "resp:", repr(resp)
        return resp 

    def write_posititon(self, pos):
        pos = int(pos)
        assert pos in [0,1]
        self.send_cmd(["0","1"][pos])
        self.position = pos
        return self.position
        
    def move_up(self):
        return self.write_posititon(1)

    def move_down(self):
        return self.write_position(0)
    
    def read_position(self):
        resp = self.ask("?")
        if resp == "0":
            self.position = 0
            return self.position
        elif resp == "1":
            self.position = 1
            return self.position
        else:
            raise ValueError("Flip Mirror controller returned %s instead of 0, or 1" % resp)
    
    def close(self):
        self.ser.close()