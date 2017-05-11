# -*- coding: utf-8
#
# Colin O'Flynn, Copyright (C) 2013. All Rights Reserved. <coflynn@newae.com>
#
import math
import time
import inspect
import numpy as np
# from picoscope import ps4000
from equipment.picotech.picoscope import ps4000
from equipment.picotech.picoscope import ps5000a

import matplotlib.pyplot as plt
import scipy.fftpack
import scipy

def fft(signal, freq):
    Mag = abs(scipy.fft(signal))
    freqs =  scipy.fftpack.fftfreq(len(signal), 1/freq)

    Mag = Mag[0:len(freqs)/2]   # positive frequencies
    freqs = freqs[0:len(freqs)/2]

    return (freqs, Mag)

def examplePS6000():    
    fig=plt.figure()
    plt.ion()    # interactive mode
     
    print "Attempting to open..."
    ps = ps4000.PS4000()
 
    #Example of simple capture
    channel = "A"
    ps.setChannel(channel, "AC", 50E-3)
    f_sampling, max_sample = ps.setSamplingFrequency(250E3, 4096)  # sampling and record_length
    print "Sampling @ %f MHz, %d samples"%(f_sampling/1E6, max_sample)
  
    blockdata = np.array(0)
  
    for i in range(0, 10):
        ps.runBlock()
        while(ps.isReady() == False): time.sleep(0.01)
  
        print "Sampling Done"
        data = ps.getDataV(channel, 4096)
        blockdata = np.append(blockdata, data)
  
        #Simple FFT
        print "FFT In Progress"
        [freqs, FFTdb] = fft(data, f_sampling)
        plt.clf()
        plt.plot(freqs, FFTdb)        
        plt.draw()
  
        start = (i - 5) * 4096
        if start < 0:
            start = 0
        #Spectrum Graph, keeps growing
        plt.clf()
        plt.specgram(blockdata[start:], NFFT=4096, Fs=f_sampling, noverlap=512)
        plt.xlabel('Measurement #')
        plt.ylabel('Frequency (Hz)')
        plt.draw()
     
    ps.close()
    plt.show()
                    
                   
def examplePS4000():
    print "Attempting to open..."
    ps = ps4000.PS4000()

    #Example of simple capture
    channel = "B"
    N_s_des = 100 
    f_s_des = 100
#     ps.setChannel(channel, "AC", 50E-3)
    ps.setChannel(channel=channel, coupling="AC", VRange=10, VOffset=0.0, enabled=True,
                   BWLimited=False, probeAttenuation=1.0)
    f_sampling, max_sample = ps.setSamplingFrequency(f_s_des, N_s_des)  # sampling and record_length
    Nsamples = min(max_sample, N_s_des)
    print "Sampling @ %.3f kHz, MaxSamples %d , Nsamples %d" %(f_sampling/1E3, max_sample, Nsamples)
    
    ps.runBlock()
    while(ps.isReady() == False):
        time.sleep(0.01)
    print "Sampling Done"
    data = ps.getDataV(channel, numSamples= Nsamples, startIndex=0, downSampleRatio=1, downSampleMode=0,
                 segmentIndex=0, returnOverflow=False, exceptOverflow=True, dataV=None, dataRaw=None)
    
    #Simple FFT
    [freqs, Mag] = fft(data, f_sampling)
    
    fig1 = plt.figure()
    plt.clf()
    ax1 = fig1.add_subplot(211)
    ax1.plot(data)
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude [V]')  
    
    
    ax2 = fig1.add_subplot(212)
    f = np.fft.rfftfreq(len(data), 1/f_sampling)
    mag = np.abs(np.fft.rfft(data))
    ax2.loglog(f, mag)
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amplitude [V]')  
    
    plt.show()
    
def examplePS5000():
    print "Attempting to open..."
    ps = ps5000a.PS5000a()

    #Example of simple capture
    channel = "A"
    N_s_des = int(10000) 
    f_s_des = 10000
    VRange = 0.1
#     ps.setChannel(channel, "AC", 50E-3)
    ps.setChannel(channel=channel, coupling="AC", VRange=VRange, VOffset=0.0, enabled=True,
                   BWLimited=False, probeAttenuation=1.0)
    f_sampling, max_sample = ps.setSamplingFrequency(f_s_des, N_s_des)  # sampling and record_length
    Nsamples = min(N_s_des, max_sample)
    print "Sampling @ %.3f kHz, MaxSamples %d, Nsamples %d "%(f_sampling/1E3, max_sample, Nsamples) 
    
    ps.runBlock()
    while(ps.isReady() == False):
        time.sleep(0.01)
    print "Sampling Done"
    data = ps.getDataV(channel, numSamples=Nsamples, startIndex=0, downSampleRatio=1, downSampleMode=0,
                 segmentIndex=0, returnOverflow=False, exceptOverflow=True, dataV=None, dataRaw=None)

    fig1 = plt.figure()
    plt.clf()
    ax1 = fig1.add_subplot(211)
    ax1.plot(data)
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude [V]')  
    
    
    ax2 = fig1.add_subplot(212)
    f = np.fft.rfftfreq(len(data), 1/f_sampling)
    mag = np.abs(np.fft.rfft(data))
    ax2.loglog(f, mag)
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amplitude [V]')  
    
    plt.show()
          
          
if __name__ == "__main__":
#     examplePS6000()
#     examplePS4000()
    examplePS5000()
