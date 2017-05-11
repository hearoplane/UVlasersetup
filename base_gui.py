'''
Created on Jul 23, 2014
DZiegler  dominik@scubaprobe.com 
 
'''
import sys, os
import time
import datetime
import numpy as np
import collections
from PySide import QtCore, QtGui, QtUiTools
import matplotlib
matplotlib.use('QT4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar2
from matplotlib.figure import Figure
from logged_quantity import LoggedQuantity

class BaseGUI(object):
    ui_filename = None
    
    def __init__(self):
        self.logged_quantities = collections.OrderedDict()
        self.hardware_components = collections.OrderedDict()
        self.measurement_components = collections.OrderedDict()
        self.figs = collections.OrderedDict()

        # Load Qt UI from .ui file
        ui_loader = QtUiTools.QUiLoader()
        ui_file = QtCore.QFile(self.ui_filename)
        ui_file.open(QtCore.QFile.ReadOnly); 
        self.ui = ui_loader.load(ui_file)
        ui_file.close()
        
        # Run the subclass setup function
        self.setup()
        # Setup the figures         
        for name, measure in self.measurement_components.items():
            print "setting up figures for", name, "measurement", measure.name
            measure.setup_figure()    
            
        self.obj = object

        self.Timer = QtCore.QTimer()
        self.Timer.timeout.connect(self.firefly_hc.refreshVideoStream)
        self.Timer.start(50)  #Snapping image every 50ms
 
    def add_logged_quantity(self, name, **kwargs):
        lq = LoggedQuantity(name=name, **kwargs)
        self.logged_quantities[name] = lq
        return lq

    def add_hardware_component(self,hc):
        self.hardware_components[hc.name] = hc
        return hc
    
    def add_measurement_component(self, measure):
        assert not measure.name in self.measurement_components.keys()
        self.measurement_components[measure.name] = measure
        return measure
    
    def __del__ ( self ): 
        self.ui = None

    def show(self): 
        #self.ui.exec_()
        self.ui.show()
        
    def add_figure(self, name, widget, toolbar=True):
            """creates a matplotlib figure attaches it to the qwidget specified
            (widget needs to have a layout set (preferably verticalLayout) 
            adds a figure to self.figs"""
            print "---adding figure", name, widget
            if name in self.figs:
                return self.figs[name]
            else:
                fig = Figure()
                fig.patch.set_facecolor('w')
                canvas = FigureCanvas(fig)
                widget.layout().addWidget(canvas)
                if toolbar:
                    nav = NavigationToolbar2(canvas, self.ui)
                    widget.layout().addWidget(nav)
                canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
                canvas.setFocus()
                self.figs[name] = fig
                return fig

    def setup(self):
        """ Override to add Hardware and Measurement Components"""
        raise NotImplementedError()    
    
if __name__ == '__main__':
    pass
#     app = QtGui.QApplication(sys.argv)
#     app.setApplicationName("CL Microscope Control Application")
#     
#     gui = CLMicroscopeGUI()
#     gui.show()
#     
#     sys.exit(app.exec_())