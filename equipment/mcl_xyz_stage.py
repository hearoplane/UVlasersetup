import ctypes
from ctypes import c_int, c_byte, c_ubyte, c_short, c_double, cdll, pointer, byref
import time
import os
import platform
import numpy as np

print platform.architecture()
if platform.architecture()[0] == '64bit':
    madlib_path = os.path.abspath(os.path.join(os.path.dirname(__file__),"mcl_64bit/MADLib.dll"))
else:
    madlib_path = os.path.abspath(os.path.join(os.path.dirname(__file__),"MADLib.dll"))
    wdapilib_path = os.path.abspath(os.path.join(os.path.dirname(__file__),"wdapi1010.dll"))
    wdapidll = cdll.LoadLibrary(wdapilib_path)
print "loading DLL:", repr(madlib_path)
madlib = cdll.LoadLibrary(madlib_path)
madlib.MCL_SingleReadZ.restype = c_double
madlib.MCL_SingleReadN.restype = c_double
madlib.MCL_MonitorZ.restype = c_double
madlib.MCL_MonitorN.restype = c_double
madlib.MCL_ReadEncoderZ.restype = c_double
madlib.MCL_GetCalibration.restype = c_double

class MCLProductInformation(ctypes.Structure):
    _pack_ = 1 # important for field alignment
    _fields_ = [
        ("axis_bitmap",     c_ubyte),    #//bitmap of available axis
        ("ADC_resolution",  c_short), #//# of bits of resolution
        #("pad", c_byte),
        ("DAC_resolution",  c_short), #//# of bits of resolution
        ("Product_id",      c_short),   
        ("FirmwareVersion", c_short),
        ("FirmwareProfile", c_short),]
    def print_info(self):
        print "MCL Product Information"
        for fieldname, fieldtype in self._fields_:
            fieldval = self.__getattribute__(fieldname)
            print "\t", fieldname, "\t\t", fieldval, "\t\t", bin(fieldval) 
 
class MCLStage(object):
    def __init__(self, debug=False):
        self.debug = debug
        self.MCL_ERROR_CODES = {
                                0: "MCL_SUCCESS",
                                -1: "MCL_GENERAL_ERROR",
                                -2: "MCL_DEV_ERROR",
                                -3: "MCL_DEV_NOT_ATTACHED",
                                -4: "MCL_USAGE_ERROR",
                                -5: "MCL_DEV_NOT_READY",
                                -6: "MCL_ARGUMENT_ERROR",
                                -7: "MCL_INVALID_AXIS",
                                -8: "MCL_INVALID_HANDLE"
                                }
        self._handle = madlib.MCL_InitHandle()
        if self.debug: print "handle:", hex(self._handle)
        if not self._handle:
            print "MCLNanoDrive failed to grab device handle ", hex(self._handle)
        self.prodinfo = MCLProductInformation()
        madlib.MCL_GetProductInfo(byref(self.prodinfo), self._handle)
        if self.debug: self.prodinfo.print_info()
        
        self.num_axes = 0
        self.pos = dict()
        self.cal = dict()
        for axnum, axbitmap in [(1, 0b001), (2, 0b010), (3, 0b100)]:
            axvalid = bool(self.prodinfo.axis_bitmap & axbitmap)
            if debug: print axnum, "axbitmap:", bin(axbitmap), "axvalid", axvalid
            if not axvalid:
                if debug: print "No axis %s, skipping" % str(axnum)
                continue
            self.num_axes += 1
            
            self.cal[axnum] = madlib.MCL_GetCalibration(axnum, self._handle)
            if debug: print "cal axes %s: %g" % (str(axnum), self.cal[axnum])
            self.pos[axnum] = self.get_pos_ax(axnum)
            if debug: print "pos axes %s: %g" % (str(axnum), self.pos[axnum])
        
    def close(self):
        madlib.MCL_ReleaseHandle(self._handle)
        
    def set_pos_ax(self, pos, axis):
        #if self.debug: print "set_pos_ax", axis, pos
        assert 1 <= axis <= self.num_axes, "incompatible axis number"
        assert 0 <= pos <= self.cal[axis], "target position is out of bounds"
        self.handle_err(madlib.MCL_SingleWriteN(c_double(pos), axis, self._handle))   
        
    def get_pos_ax(self, axis):
        pos = float(madlib.MCL_SingleReadN(axis, self._handle))
        if self.debug: print "get_pos_ax", axis, pos
        return pos        
        
    def handle_err(self, retcode):
        if retcode < 0:
            raise IOError(self.MCL_ERROR_CODES[retcode])
        return retcode
         
if __name__ == '__main__':
    
    """
    print "MCL nanodrive test"
    
    nanodrive = MCLStage(debug=False)
    
    for x,y,z in [ (0,25,0), (0,50,50), (0,25,0), (0,50,50), (0,25,0), (0,50,50)]:
        print "moving to ", x,y,z
        nanodrive.set_pos_ax(x,1)
        nanodrive.set_pos_ax(y,2)
        nanodrive.set_pos_ax(z,3)
        time.sleep(nanodrive.step_duration)
        x1 = nanodrive.get_pos_ax(1)
        y1 = nanodrive.get_pos_ax(2)
        z1 = nanodrive.get_pos_ax(3)
        print "moved to ", x1, y1,z1   

    nanodrive.close()
    """
