#!/usr/bin python
# -*- coding: utf-8 -*-
"""Command two axes of a PI controller in a raster scan motion.
"""

__version__ = '1.0.0.0'

import math
import numpy as np
from time import sleep
from scipy import signal
import matplotlib.pyplot as plt
from pipython import GCSCommands

def main():
    """Calculate x and y coordinates for a raster scan
    @param h : height (slow scan axis) 
    @param w : width (fast scan axis)
    @param xoffs : Offset of start position for x.
    @param yoffs : Offset of start position for y.
    @param angle : rotation of scan.
    @param nbLines: number of lines
    @param type of scan zig zag or line by line 
    @return : Coordinates x, y of new target as list.
    """
    deltatime = 1  # waits 1ms between two points
    h, w = 15,50
    angle=-0.332 #rads
    nbLines=10
    xoffs = 5.0  # offset of start position for x
    yoffs = 5.0  # offset of start position for y
    maxpnts = 2000
    pnt=0
    pnts = np.linspace(0, 1, maxpnts)
    x = w* signal.sawtooth(2 * np.pi * nbLines * pnts)
    x = np.abs(x)
    plt.plot(pnts, x)
    
    y = h*pnts/maxpnts
    plt.plot(pnts, y)
    
    x = math.cos(angle)*x + math.sin(angle)*y + xoffs
    y = math.sin(angle)*x + math.cos(angle)*y + yoffs
    
    with GCSCommands() as gcs:
        gcs.InterfaceSetupDlg()
        axes = gcs.axes[:2]
        while pnt < maxpnts:
            targets = [x[pnt],y[pnt]] #raster(h, w, nbLines, xoffs, yoffs, angle)
            print 'targets:', targets
            gcs.MOV(axes, targets)
            pnt += 1
            sleep(deltatime)

if __name__ == "__main__":
    main()
