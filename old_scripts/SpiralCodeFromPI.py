#!/usr/bin python
# -*- coding: utf-8 -*-
"""Command two axes of a PI controller in a spiraled motion.
"""

__version__ = '1.0.0.0'

import math
from time import sleep

from pipython import GCSCommands


def spiral(a, phi, xoffs=0., yoffs=0.):
    """Calculate x and y coordinates for an archimedean spiral r(phi) = a * phi.
    @param a : Defines spacing of the spiral.
    @param phi : Current angle.
    @param xoffs : Offset of start position for x.
    @param yoffs : Offset of start position for y.
    @return : Coordinates x, y of new target as list.
    """
    radius = a * phi
    x = radius * math.cos(phi) + xoffs
    y = radius * math.sin(phi) + yoffs
    return [x, y]


def main():
    """Connect a PI controller and command its first and second axis in a spiraled motion.
    """
    maxphi = 4 * math.pi  # total travel range, e.g. 4 * pi means two rounds
    deltaphi = 0.1  # change in angle from one iteration to the next
    deltatime = 0.05  # change in time from one iteration to the next
    spacing = 0.1  # spacing of the spiral, i.e. parameter "a" in r(phi) = a * phi
    xoffs = 5.0  # offset of start position for x
    yoffs = 5.0  # offset of start position for y
    phi = 0.
    with GCSCommands() as gcs:
        gcs.InterfaceSetupDlg()
        axes = gcs.axes[:2]
        while phi < maxphi:
            targets = spiral(spacing, phi, xoffs, yoffs)
            print 'targets:', targets
            gcs.MOV(axes, targets)
            phi += deltaphi
            sleep(deltatime)


if __name__ == "__main__":
    main()
