# -*- coding: utf-8 -*-
"""
Created on Mon Mar 31 11:32:02 2014

@author: lab
"""

from PySide import QtGui
from microscope_gui import MicroscopeGUI
import sys

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("Microscope Control Application")
    
    gui = MicroscopeGUI()
    gui.show()
    
    sys.exit(app.exec_())