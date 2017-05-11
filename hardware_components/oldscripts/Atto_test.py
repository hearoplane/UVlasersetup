'''
Created on Jul 30, 2014

@author: Frank
'''
import time
print 'atto test here'
try:
    from equipment.attocube_ecc100 import AttoCubeECC100
except Exception as err:
    print "could not load modules needed for AttoCubeECC100:", err
    
import winsound

X_AXIS = 0
Y_AXIS = 1

def beep( msec = 100 ):
    print chr(7),
    Freq = 2000 # Set Frequency To 2500 Hertz
    winsound.Beep(Freq,msec)
    
def setup():
    ecc = AttoCubeECC100()
    ecc.enable_axis(X_AXIS, enable=True)
    ecc.enable_axis(Y_AXIS, enable=True)
    return ecc
          
def set_x( x, loop = 50, delay = 0.05, reset = -5):
    #ecc.write_target_position_axis(X_AXIS,reset)
    #time.sleep(delay)
    ecc.write_target_position_axis(X_AXIS,x)
    print 'set position ', x
    pos = 0
    beep()
    for i in range(loop):
        pos += ecc.read_position_axis(X_AXIS)
        time.sleep(delay)
    #print i, pos
    pos /= float(loop)
    print 'mean position ', pos
    return pos


delta = 2
count = 8
wait = 20

ecc = setup()

for i in range(count ):
    set_x( i*delta, wait )
set_x(0)    

for i in range(count/2):
    set_x(delta,wait)
    set_x(0,wait)
ecc.close()
        
        # clean up hardware object

      
if __name__ == '__main__':
    pass