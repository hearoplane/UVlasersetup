# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 09:25:48 2014

@author: esbarnard
"""

from PySide import QtCore, QtGui
import threading
import time
from logged_quantity import LoggedQuantity
from collections import OrderedDict
import pyqtgraph as pg


class Measurement(QtCore.QObject):
    
    measurement_sucessfully_completed = QtCore.Signal(()) # signal sent when full measurement is complete
    measurement_interrupted = QtCore.Signal(()) # signal sent when  measurement is complete due to an interruption
    measurement_state_changed = QtCore.Signal(bool) # signal sent when measurement started or stopped
    
    def __init__(self, gui):
        """type gui: MicroscopeGUI
        """
        
        QtCore.QObject.__init__(self)

        self.gui = gui
        
        self.display_update_period = 0.05 # seconds  #!Was 0.5
        self.display_update_timer = QtCore.QTimer(self.gui.ui)
        self.display_update_timer.timeout.connect(self.on_display_update_timer)
        self.acq_thread = None
        
        self.logged_quantities = OrderedDict()
        self.operations = OrderedDict()

        self.add_operation("start", self.start)
        self.add_operation("interrupt", self.interrupt)
        
        self.setup()
        
        self._add_control_widgets_to_measurements_tab()

    def setup(self):
        "Override this to set up logged quantites and gui connections"
        """Runs during DOWENEED__init__, before the hardware connection is established
        Should generate desired LoggedQuantities"""
        raise NotImplementedError()
        
    def setup_figure(self):
        print "Empty setup_figure called"
        pass

    def _run(self):
        raise NotImplementedError("Measurement _run not defined")
    
    @QtCore.Slot()
    def start(self):
        print "measurement", self.name, "start"
        self.interrupt_measurement_called = False
        if (self.acq_thread is not None) and self.is_measuring():
            raise RuntimeError("Cannot start a new measurement while still measuring")
        self.acq_thread = threading.Thread(target=self._run)
        # TODO Stop Display Timers
#         try:
#             self.gui.stop_display_timers()
#         except Exception as err:
#             print "failed to stop_display_timers", err
        self.measurement_state_changed.emit(True)
        self.acq_thread.start()
        self.t_start = time.time()
        self.display_update_timer.start(self.display_update_period*1000)
    
    @QtCore.Slot()
    def interrupt(self):
        print "measurement", self.name, "interrupt"
        self.interrupt_measurement_called = True
        #Make sure display is up to date        
        #self.on_display_update_timer()

    def start_stop(self, start):
        print self.name, "start_stop", start
        if start:
            self.start()
        else:
            self.interrupt()

    def markButton(self, button, on=True):
        if on:
            button.setStyleSheet("background-color: rgb(142,203,232)")
        else:
            button.setStyleSheet("background-color: none")
        
        
    def is_measuring(self):
        return self.acq_thread.is_alive()
        
    
    def update_display(self):
        "Override this function to provide figure updates when the display timer runs"
        pass
    
    @QtCore.Slot()
    def on_display_update_timer(self):
        #update figure
        try:
            self.update_display()
        except Exception, err:
            print self.name, "Failed to update figure:", err            
        finally:
            if not self.is_measuring():
                self.display_update_timer.stop()

    def add_logged_quantity(self, name, **kwargs):
        lq = LoggedQuantity(name=name, **kwargs)
        self.logged_quantities[name] = lq
        return lq
    
    def add_operation(self, name, op_func):
        """type name: str
           type op_func: QtCore.Slot
        """
        self.operations[name] = op_func   
    

    def _add_control_widgets_to_measurements_tab(self):
        cwidget = self.gui.ui.measurements_tab_scrollArea_content_widget
        
        self.controls_groupBox = QtGui.QGroupBox(self.name)
        self.controls_formLayout = QtGui.QFormLayout()
        self.controls_groupBox.setLayout(self.controls_formLayout)

        cwidget.layout().addWidget(self.controls_groupBox)
        
        #self.start_measurement_checkBox = QtGui.QCheckBox("Connect to Hardware")
        #self.controls_formLayout.addRow("Connect", self.connect_hardware_checkBox)
        
        
        self.control_widgets = OrderedDict()
        for lqname, lq in self.logged_quantities.items():
            #: :type lq: LoggedQuantity
            if lq.choices is not None:
                widget = QtGui.QComboBox()
            elif lq.dtype in [int, float]:
                #widget = QtGui.QDoubleSpinBox()
                widget = pg.SpinBox()
            elif lq.dtype in [bool]:
                widget = QtGui.QCheckBox()  
            elif lq.dtype in [str]:
                widget = QtGui.QLineEdit()
            lq.connect_bidir_to_widget(widget)

            # Add to formlayout
            self.controls_formLayout.addRow(lqname, widget)
            self.control_widgets[lqname] = widget
            
            
        self.op_buttons = OrderedDict()
        for op_name, op_func in self.operations.items(): 
            op_button = QtGui.QPushButton(op_name)
            op_button.clicked.connect(op_func)
            self.controls_formLayout.addRow(op_name, op_button)
            
