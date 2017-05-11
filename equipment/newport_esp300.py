'''
Created on Jan 12, 2015

@author: aamrein

Serial communication with the controller of the Newport ESP300 motion controller.
Controls axes 2 and 3.

'''

import serial
import time


ASIPort = 'COM14'


class ESP300(object):   # new style class
    def __init__(self, port='COM14', debug=False):
        self.port = port
        self.debug = debug
        
        if self.debug: print "Newport ESP300 Initialization"
        self.ser = serial.Serial(port=self.port,
                                 baudrate=19200,
                                 # waiting time for response [s]
                                 timeout=0.1,
                                 bytesize=8, parity='N', 
                                 stopbits=1, xonxoff=0, rtscts=0)
        self.ser.flush()
        
        # configure motors        
        self.setUnitsToMM()
        
        # max speed [mm/s]
        v_max_x = 0.4
        v_max_y = 0.4
        self.setMaxSpeeds(v_max_x, v_max_y)
        
        # speed [mm/s]
        self.speed2 = 0.1
        self.speed3 = 0.1
        self.setSpeeds(self.speed2, self.speed3)

        # acceleration [mm / s^2]
        acc2 = 0.8
        acc3 = 0.8
        self.setAccelerations(acc2, acc3)
        
        print "Opened Newport Esp300 motion controller."
        
    def send_cmd(self, cmd):
        if self.debug: print "Newport ESP300 cmd:", repr(cmd)
        self.ser.write(cmd + '\r')
        
    def ask(self, cmd): # format: '2HW X' -> ':A 355'
        self.send_cmd(cmd)
        resp1 = self.ser.readline()
        if self.debug: print "ASI XY ask resp1:", repr(resp1)
        
        return resp1.strip() # remove whitespace
    
    def setSpeeds(self, ax2, ax3):
        self.send_cmd("2VA" + str(ax2))
        self.send_cmd("3VA" + str(ax3))
    
    def setUnitsToMM(self):
        self.send_cmd("2SN2")
        self.send_cmd("3SN2")
        
    def setMaxSpeeds(self, ax2, ax3):
        self.send_cmd("2VU" + str(ax2))
        self.send_cmd("3VU" + str(ax3))
    
    def setAccelerations(self, ax2, ax3):
        self.send_cmd("2AC" + str(ax2))
        self.send_cmd("3AC" + str(ax3))
        
    def moveToAx2(self, ax2):
        self.send_cmd("2PA" + str(ax2))
        self.wait()
        
    def moveRelAx2(self, step):
        self.send_cmd("2PR" + str(step))
        self.wait()
        
    def moveRelAx3(self, step):
        self.send_cmd("3PR" + str(step))
        self.wait()
        
        
    def moveToAx3(self, ax3):  
        self.send_cmd("3PA" + str(ax3))
        self.wait()
    
    def getPosAx2(self):
        return float(self.ask("2TP"))
    
    def getPosAx3(self):
        return float(self.ask("3TP"))
        
    def wait(self):
        if self.debug: print "wait"
        while self.isBusy():
            time.sleep(self.ser.getTimeout())
            
    def isBusy(self):
        ax2 = self.ask("2MD?")
        ax3 = self.ask("3MD?")
        if int(ax2)==1 and int(ax3)==1:
            return False
        else:
            return True
        
    def close(self):
        self.ser.close()
        print 'Closed Newport ESP300 motion controller.'
        
    def readErrors(self):
        pass
    
    def setLimits(self):
        pass
    
    
        
        