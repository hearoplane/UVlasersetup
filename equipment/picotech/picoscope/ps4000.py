# This is the instrument-specific file for the PS4000 series of instruments.
# Code is adapted from pico-python by Andreas Amrein <aamrein@lbl.gov>.
#
# pico-python is Copyright (c) 2013-2014 By:
# Colin O'Flynn <coflynn@newae.com>
# Mark Harfouche <mark.harfouche@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
This is the low level driver file for a specific Picoscope.

By this, I mean if parameters want to get passed as strings, they should be
handled by PSBase
All functions here should take things as close to integers as possible, the
only exception here is for array parameters. Array parameters should be passed
in a pythonic way through numpy since the PSBase class should not be aware of
the specifics behind how the clib is called.

The functions should not have any default values as these should be handled
by PSBase.
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import math
# to load the proper dll
import platform

# Do not import or use ill definied data types
# such as short int or long
# use the values specified in the h file
# float is always defined as 32 bits
# double is defined as 64 bits
from ctypes import byref, POINTER, create_string_buffer, c_float, \
    c_int16, c_int32, c_uint32, c_uint16, c_void_p
from ctypes import c_int32 as c_enum

from equipment.picotech.picoscope.picobase import _PicoscopeBase

class PS4000(_PicoscopeBase):
    """The following are low-level functions for the PS4000"""

    LIBNAME = "ps4000"
#     LIBNAME = "C:\\Users\\aamrein\\Code\\foundry_scope\\equipment\\picotech\\ps4000"

    NUM_CHANNELS = 2
    CHANNELS     =  {"A": 0, "B": 1, "MaxChannels": 2}

    CHANNEL_RANGE = [
 #                   {"rangeV":20E-3, "apivalue":1, "rangeStr":"20 mV"},
                    {"rangeV":50E-3, "apivalue":2, "rangeStr":"50 mV"},
                    {"rangeV":100E-3, "apivalue":3, "rangeStr":"100 mV"},
                    {"rangeV":200E-3, "apivalue":4, "rangeStr":"200 mV"},
                    {"rangeV":500E-3, "apivalue":5, "rangeStr":"500 mV"},
                    {"rangeV":1.0, "apivalue":6, "rangeStr":"1 V"},
                    {"rangeV":2.0, "apivalue":7, "rangeStr":"2 V"},
                    {"rangeV":5.0, "apivalue":8, "rangeStr":"5 V"},
                    {"rangeV":10.0, "apivalue":9, "rangeStr":"10 V"},
                    {"rangeV":20.0, "apivalue":10, "rangeStr":"20 V"},
                    ]


    CHANNEL_COUPLINGS = {"DC": 1, "AC": 0}

    #has_sig_gen = True
    WAVE_TYPES = {"Sine": 0, "Square": 1, "Triangle": 2,
                  "RampUp": 3, "RampDown": 4, "DCVoltage": 5}
    
    TIME_UNITS = {"FS":0, "PS":1, "NS":2, "US":3, "MS":4, "S":5}

    MAX_VALUE = 32764
    MIN_VALUE = -32764

    MAX_TIMEBASES = 19
    
    UNIT_INFO_TYPES = {"DriverVersion"          : 0x0,
                       "USBVersion"             : 0x1,
                       "HardwareVersion"        : 0x2,
                       "VarianInfo"             : 0x3,
                       "BatchAndSerial"         : 0x4,
                       "CalDate"                : 0x5,
                       "KernelVersion"          : 0x6}
    
    channelBuffersPtr = [c_void_p(), c_void_p()]
    channelBuffersLen = [0, 0]
    
    
    SIGGEN_TRIGGER_TYPES = {"Rising": 0, "Falling": 1,
                            "GateHigh": 2, "GateLow": 3}
    SIGGEN_TRIGGER_SOURCES = {"None": 0, "ScopeTrig": 1, "AuxIn": 2,
                              "ExtIn": 3, "SoftTrig": 4, "TriggerRaw": 5}

    def __init__(self, serialNumber=None, connect=True):
        """Load DLL etc"""
        if platform.system() == 'Linux':
            from ctypes import cdll
            self.lib = cdll.LoadLibrary("lib" + self.LIBNAME + ".so")
        else:
            from ctypes import windll
            self.lib = windll.LoadLibrary(self.LIBNAME)
            
        super(PS4000, self).__init__(serialNumber, connect)

    def _lowLevelOpenUnit(self, sn):
        c_handle = c_int16()
        if sn is not None:
            raise ValueError("PS4000 doesn't allow to be opened by serial number")

        m = self.lib.ps4000OpenUnit(byref(c_handle))
        
#         print('Scope handle number: '+ str(c_handle.value))
        
        self.checkResult(m)
        self.handle = c_handle.value    # handle number 
        self.suggested_time_units = self.TIME_UNITS["NS"]

    def _lowLevelCloseUnit(self):
        m = self.lib.ps4000CloseUnit(c_int16(self.handle))
        self.checkResult(m)
        print("PicoScope 4000 closed.")
        
    def _lowLevelSetChannel(self, chNum, enabled, coupling, VRange, VOffset,
                            BWLimited):
        # VOffset and BWLimited are unused 
        m = self.lib.ps4000SetChannel(c_int16(self.handle), c_enum(chNum),
                                      c_int16(enabled), c_enum(coupling),
                                      c_enum(VRange))
#         VRangeInfo = str(self.CHANNEL_RANGE[VRange-2].get("rangeV"))
#         print("Set voltage range to: [-" +VRangeInfo + "V, " + VRangeInfo + "V]")
        self.checkResult(m)
        
    def _lowLevelStop(self):
        m = self.lib.ps4000Stop(c_int16(self.handle))
        self.checkResult(m)
    
    def _lowLevelGetUnitInfo(self, info):
        s = create_string_buffer(256)
        requiredSize = c_int16(0)

        m = self.lib.ps4000GetUnitInfo(c_int16(self.handle), byref(s),
                                       c_int16(len(s)), byref(requiredSize),
                                       c_enum(info))
        self.checkResult(m)
        if requiredSize.value > len(s):
            s = create_string_buffer(requiredSize.value + 1)
            m = self.lib.ps4000GetUnitInfo(c_int16(self.handle), byref(s),
                                           c_int16(len(s)),
                                           byref(requiredSize), c_enum(info))
            self.checkResult(m)

        # should this bee ascii instead?
        # I think they are equivalent...
        return s.value.decode('utf-8')

    def _lowLevelFlashLed(self, times):
        m = self.lib.ps2000_flash_led(c_int16(self.handle))
        self.checkResult(m)

    def _lowLevelSetSimpleTrigger(self, enabled, trigsrc, threshold_adc,
                                  direction, delay, timeout_ms):      
        
        #TODO: Fix 'auto' which is where trigger occurs in block. Delay is not used
        
        m = self.lib.ps2000_set_trigger(
            c_int16(self.handle), c_enum(trigsrc), c_int16(threshold_adc),
            c_enum(direction), c_int16(0), c_int16(timeout_ms))
        self.checkResult(m)
    
    def _lowLevelRunBlock(self, numPreTrigSamples, numPostTrigSamples,
                          timebase, oversample, segmentIndex):
        timeIndisposedMs = c_int32()
        m = self.lib.ps4000RunBlock(
            c_int16(self.handle), c_uint32(numPreTrigSamples),
            c_uint32(numPostTrigSamples), c_uint32(timebase),
            c_int16(oversample), byref(timeIndisposedMs),
            c_uint16(segmentIndex), c_void_p(), c_void_p())
        self.checkResult(m)
#         print("RunBlock info")
#         print("handle", self.handle, "numPreTrigSamples", numPreTrigSamples, "numPostTrigSamples", numPostTrigSamples)
#         print("timbase", timebase, "oversample", oversample, "timeIndisposedMs", timeIndisposedMs.value, "segmentIndex", segmentIndex )
        return timeIndisposedMs.value

    def _lowLevelIsReady(self):
        ready = c_int16()
        m = self.lib.ps4000IsReady(c_int16(self.handle), byref(ready))
        self.checkResult(m)
        if ready.value:
            return True
        else:
            return False
 
    def _lowLevelGetTimebase(self, tb, noSamples, oversample, segmentIndex):
        """ Return (timeIntervalSeconds, maxSamples). """
        maxSamples = c_int32()
        sampleRate = c_float()  # [ns]

        m = self.lib.ps4000GetTimebase2(c_int16(self.handle), c_uint32(tb),
                                        c_uint32(noSamples), byref(sampleRate),
                                        c_int16(oversample), byref(maxSamples),
                                        c_uint16(segmentIndex))
        self.checkResult(m)

        return (sampleRate.value / 1.0E9, maxSamples.value)

    def getTimeBaseNum(self, sampleTimeS):
        """ Sample time in seconds to timebase as int for API calls. """
        maxSampleTime = (((2 ** 30 - 1) - 2) / 31.25E6)
        if sampleTimeS < 64E-9:
            # Low
            timebase = math.floor(math.log(sampleTimeS * 250E6, 2))
            timebase = max(timebase, 0)
        else:
            # High (max 2^30-1)
            if sampleTimeS > maxSampleTime:
                sampleTimeS = maxSampleTime

            timebase = math.floor((sampleTimeS * 31.25E6) + 2)

        # is this cast needed?
        timebase = int(timebase)
#         print("timebase, sampleTimeS", timebase, sampleTimeS)
        return timebase
    
    def getTimestepFromTimebase(self, timebase):
        """ Return sampling time as seconds. """
        if timebase < 4:
            # Low
            dt = 2. ** timebase / 250E6
        else:
            # High
            dt = (timebase - 2.) / 31.25E6
        return dt
        
  
    def _lowLevelSetDataBuffer(self, channel, data, downSampleMode, segmentIndex):
        """
        data should be a numpy array.

        Be sure to call _lowLevelClearDataBuffer
        when you are done with the data array
        or else subsequent calls to GetValue will still use the same array.

        segmentIndex is unused, but required by other versions of the API (eg PS5000a)

        """
        dataPtr = data.ctypes.data_as(POINTER(c_int16))
        numSamples = len(data)

        m = self.lib.ps4000SetDataBuffer(c_int16(self.handle), c_enum(channel),
                                         dataPtr, c_int32(numSamples))
        self.checkResult(m)

    def _lowLevelClearDataBuffer(self, channel, segmentIndex):
        self.channelBuffersPtr[channel] = c_void_p()
        self.channelBuffersLen[channel] = 0
    
    def _lowLevelGetValues(self, numSamples, startIndex, downSampleRatio,
                           downSampleMode, segmentIndex):
        numSamplesReturned = c_uint32()
        numSamplesReturned.value = numSamples
        overflow = c_int16()
        m = self.lib.ps4000GetValues(
            c_int16(self.handle), c_uint32(startIndex),
            byref(numSamplesReturned), c_uint32(downSampleRatio),
            c_enum(downSampleMode), c_uint16(segmentIndex),
            byref(overflow))
        self.checkResult(m)
        return (numSamplesReturned.value, overflow.value)

    def _lowLevelSetSigGenBuiltInSimple(self, offsetVoltage, pkToPk, waveType,
                                        frequency, shots, triggerType,
                                        triggerSource):
        m = self.lib.ps2000_set_sig_gen_built_in(
            c_int16(self.handle),
            c_int32(int(offsetVoltage * 1000000)),
            c_int32(int(pkToPk        * 1000000)),
            c_int16(waveType),
            c_float(frequency), c_float(frequency),
            c_float(0), c_float(0), c_enum(0), c_uint32(0))
        self.checkResult(m)
