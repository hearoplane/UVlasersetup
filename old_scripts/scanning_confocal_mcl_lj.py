'''
Created on June 17, 2013

@author: esbarnard
'''
import sys, os
import time
import datetime
import numpy as np
from PySide import QtCore, QtGui, QtUiTools

import matplotlib
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar2

from matplotlib.figure import Figure

from equipment import MCLNanoDrive
from equipment import labjack_counter


XAXIS_ID = 2
YAXIS_ID = 1
ZAXIS_ID = 3

HAXIS_ID = 2 # "y"-axis in nanodrive
#FOR LATERAL SCAN
VAXIS_ID = 1 # "x"-axis in nanodrive

#FOR DEPTH SCAN
#VAXIS_ID = 3 # "z"-axis in nanodrive

TIMER_MS = 1000

HARDWARE_DEBUG = False

OPTIMIZE_HISTORY_LEN = 100

class LoggedQuantity(QtCore.QObject):

    updated_value = QtCore.Signal( (float,),(int,)  )
    updated_text_value = QtCore.Signal(str)

    def __init__(self, name=None, dtype=np.float, hardware_read_func=None, hardware_set_func=None, initial=0, fmt="%g"):
        super(LoggedQuantity, self).__init__()
        
        self.name = name
        self.dtype = dtype
        self.val = dtype(initial)
        self.hardware_read_func = hardware_read_func
        self.hardware_set_func = hardware_set_func
        self.fmt = fmt
        
    def read_from_hardware():
        if self.hardware_read_func:
            self.hardware_read_func()
    

    @QtCore.Slot(str)
    @QtCore.Slot(float)
    @QtCore.Slot(int)
    @QtCore.Slot()
    def update_value(self, new_val=None, update_hardware=True, send_signal=True):
        #print "called update_value"
        if new_val == None:
            new_val = self.sender().text()
        self.val = self.dtype(new_val)
        if update_hardware and self.hardware_set_func:
            self.hardware_set_func(self.val)   
        if send_signal:
            self.send_display_updates()
            
    def send_display_updates(self):
        self.updated_value.emit(self.val)
        self.updated_text_value.emit( self.fmt % self.val )        


"""class ScanThread(QThread):
    
    data_ready_signal   = QtCore.Signal()
    scan_complete_signal = QtCore.Signal()
    

    def DOWENEED__init__(self, parent = None):
        super(ScanThread, self).DOWENEED__init__(parent)
        print parent
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            pass
            
        print "start scan"
        
        self.scanning = True
        
        # get scan parameters:
        self.h0 = ui.h0_doubleSpinBox.value()
        self.h1 = ui.h1_doubleSpinBox.value()
        self.v0 = ui.v0_doubleSpinBox.value()
        self.v1 = ui.v1_doubleSpinBox.value()
    
        self.dh = 1e-3*ui.dh_spinBox.value()
        self.dv = 1e-3*ui.dv_spinBox.value()
    
    
    
    
    def stop(self, wait=False):
        self.running = False
        if wait:
            self.wait()
            
"""

            
    
class ScanningConfocalUI:
    def __del__ ( self ): 
        self.ui = None

    def show(self): 
        #self.ui.exec_()
        self.ui.show()

    def __init__(self):
        ui_loader = QtUiTools.QUiLoader()
        print os.path.join(__file__,"scanning_confocal_mcl_lj.ui")
        ui_file = QtCore.QFile("scanning_confocal_mcl_lj.ui")
        ui_file.open(QtCore.QFile.ReadOnly); 
        self.ui = ui_loader.load(ui_file)
        ui_file.close()

        self.HARDWARE_DEBUG = HARDWARE_DEBUG
        
        self.fig2d = Figure()
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.plot([0,1])
        self.canvas2d = FigureCanvas(self.fig2d)
        self.ui.plot2D_verticalLayout.addWidget(self.canvas2d)
        self.navtoolbar_plot2d = NavigationToolbar2(self.canvas2d, self.ui)
        self.ui.plot2D_verticalLayout.addWidget( self.navtoolbar_plot2d )


        self.fig_opt = Figure()
        self.ax_opt = self.fig_opt.add_subplot(111)
        
        self.canvas_opt = FigureCanvas(self.fig_opt)
        self.ui.plot_optimize_verticalLayout.addWidget(self.canvas_opt)
        self.navtoolbar_plot_opt = NavigationToolbar2(self.canvas_opt, self.ui)
        self.ui.plot_optimize_verticalLayout.addWidget( self.navtoolbar_plot_opt )

        self.optimize_history = np.zeros(OPTIMIZE_HISTORY_LEN, dtype=np.float)
        self.optimize_ii = 0
        self.optimize_line, = self.ax_opt.plot(self.optimize_history)
        self.optimize_current_pos = self.ax_opt.axvline(self.optimize_ii, color='r')

        ##################### hardware #########################################
        
        self.scanning = False

        ######## MCL NanoDrive Stage ###########################################
        self.nanodrive = MCLNanoDrive(debug=self.HARDWARE_DEBUG)
        try:
            self.hmax = self.nanodrive.cal[HAXIS_ID]
            self.vmax = self.nanodrive.cal[VAXIS_ID]
            self.ui.maxdim_label.setText("max: %g x %g um" % (self.hmax, self.vmax) )
        except Exception as e:
            print e
            self.ui.maxdim_label.setText("max: ? x ? um")
        
        
        # Logged Quantities
        self.x_position = LoggedQuantity(name = 'x_position', dtype=np.float)
        self.y_position = LoggedQuantity(name = 'y_position', dtype=np.float)
        self.z_position = LoggedQuantity(name = 'z_position', dtype=np.float)
        
        
        #self.x_position.updated_value.connect(self.ui.cx_lcdNumber.display)
        self.x_position.updated_value.connect(self.ui.cx_doubleSpinBox.setValue)
        self.ui.x_set_lineEdit.returnPressed.connect(self.x_position.update_value)

        #self.y_position.updated_value.connect(self.ui.cy_lcdNumber.display)
        self.y_position.updated_value.connect(self.ui.cy_doubleSpinBox.setValue)
        self.ui.y_set_lineEdit.returnPressed.connect(self.y_position.update_value)

        #self.z_position.updated_value.connect(self.ui.cz_lcdNumber.display)
        self.z_position.updated_value.connect(self.ui.cz_doubleSpinBox.setValue)
        self.ui.z_set_lineEdit.returnPressed.connect(self.z_position.update_value)


        self.x_position.hardware_set_func = lambda x: self.nanodrive.set_pos_ax(x, XAXIS_ID)
        self.y_position.hardware_set_func = lambda y: self.nanodrive.set_pos_ax(y, YAXIS_ID)
        self.z_position.hardware_set_func = lambda z: self.nanodrive.set_pos_ax(z, ZAXIS_ID)
        

        ####### LabJack (apd) counter readout ##################################
        self.lj_counter = labjack_counter.LabJackCounter()

        self.apd_count_rate = LoggedQuantity(name = 'apd_count_rate', dtype=np.float, fmt="%e")

        self.apd_count_rate.updated_text_value.connect(self.ui.apd_counter_output_lineEdit.setText)

        ########################################################################        

        self.read_from_hardware()

        self.update_display()

        # update figure
        self.ax2d.set_xlim(0, self.hmax)
        self.ax2d.set_ylim(0, self.vmax)

        # events

        self.ui.scan_start_pushButton.clicked.connect(self.on_scan_start)
        self.ui.scan_stop_pushButton.clicked.connect(self.on_scan_stop)

        self.ui.fast_update_checkBox.stateChanged.connect(self.on_fast_timer_checkbox)

        self.ui.clearfig_pushButton.clicked.connect(self.on_clearfig)

        ### timers
        
        self.timer = QtCore.QTimer(self.ui)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(TIMER_MS)
        
        self.fast_timer = QtCore.QTimer(self.ui)
        self.fast_timer.timeout.connect(self.on_fast_timer)
        
        self.display_update_when_scanning_timer = QtCore.QTimer(self.ui)
        self.display_update_when_scanning_timer.timeout.connect(self.on_display_update_when_scanning_timer)

        
        
    @QtCore.Slot()
    def on_clearfig(self):
        self.fig2d.clf()
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.plot([0,1])    
        # update figure
        self.ax2d.set_xlim(0, self.hmax)
        self.ax2d.set_ylim(0, self.vmax)
        self.fig2d.canvas.draw()

        
    def read_from_hardware(self):
        self.stage_pos = self.nanodrive.get_pos()
        self.c0_rate = self.lj_counter.read_rates()[0]

    def update_display(self):
        self.x_position.update_value(self.stage_pos[XAXIS_ID-1], update_hardware=False)
        self.y_position.update_value(self.stage_pos[YAXIS_ID-1], update_hardware=False)
        self.z_position.update_value(self.stage_pos[ZAXIS_ID-1], update_hardware=False)
        self.apd_count_rate.update_value(self.c0_rate)

    @QtCore.Slot()
    def on_timer(self):
        self.read_from_hardware()
        self.update_display()

    @QtCore.Slot()
    def on_fast_timer(self):
        self.c0_rate = self.lj_counter.read_rates()[0]
        self.apd_count_rate.update_value(self.c0_rate)
        #print self.c0_rate
        
        
        self.optimize_ii += 1
        self.optimize_ii %= OPTIMIZE_HISTORY_LEN
        ii = self.optimize_ii
        
        self.optimize_history[ii] = self.c0_rate
        self.optimize_line.set_ydata(self.optimize_history)
        self.optimize_current_pos.set_xdata((ii,ii))
        if (ii % 10) == 0:
            self.ax_opt.relim()
            self.ax_opt.autoscale_view(scalex=False, scaley=True)
        
        #print "redraw"
        self.fig_opt.canvas.draw()
            
    @QtCore.Slot(bool)
    def on_fast_timer_checkbox(self, fast_timer_enable):
        if fast_timer_enable:
            self.fast_timer.start(100)
            print "fast timer start"
        else:
            self.fast_timer.stop()
            print "fast timer stop"        

    @QtCore.Slot()            
    def on_scan_start(self):
        print "start scan"
        
        self.scanning = True
        
        QtGui.QApplication.processEvents()

        #get scan parameters:
        self.h0 = self.ui.h0_doubleSpinBox.value()
        self.h1 = self.ui.h1_doubleSpinBox.value()
        self.v0 = self.ui.v0_doubleSpinBox.value()
        self.v1 = self.ui.v1_doubleSpinBox.value()
    
        self.dh = 1e-3*self.ui.dh_spinBox.value()
        self.dv = 1e-3*self.ui.dv_spinBox.value()

        self.h_array = np.arange(self.h0, self.h1, self.dh, dtype=float)
        self.v_array = np.arange(self.v0, self.v1, self.dv, dtype=float)
        
        self.Nh = len(self.h_array)
        self.Nv = len(self.v_array)
        
        self.pixel_time = self.ui.pixel_time_doubleSpinBox.value()
        
        
        ### create data arrays
        self.count_rate_map = np.zeros((self.Nv, self.Nh), dtype=np.float)
        
        print "shape:", self.count_rate_map.shape
        
        print "Nh, Nv", self.Nh, self.Nv    

        ### update figure
        self.ax_2d_img = self.ax2d.imshow(self.count_rate_map, 
                                    origin='lower',
                                    vmin=1e4, vmax=1e5, interpolation='nearest', 
                                    extent=[self.h0, self.h1, self.v0, self.v1])
        self.fig2d.canvas.draw()
        
        
        self.timer.stop() #stop the normal timer
        
        #display_timer_update = 0.5*self.pixel_time*1e3
        #if display_timer_update < 200
        
        self.display_update_when_scanning_timer.start(100)
        
        # Scan!            
        line_time0 = time.time()
        for i_v in range(self.Nv):
            if not self.scanning:
                break
            self.v_pos = self.v_array[i_v]
            self.nanodrive.set_pos_ax(self.v_pos, VAXIS_ID)
            self.read_from_hardware()
            
            print "line time:", time.time() - line_time0
            print "pixel time:", float(time.time() - line_time0)/self.Nh
            line_time0 = time.time()
            
            if i_v % 2: #odd lines
                h_line_indicies = range(self.Nh)
            else:       #even lines -- traverse in oposite direction
                h_line_indicies = range(self.Nh)[::-1]
            
            
            for i_h in h_line_indicies:
                if not self.scanning:
                    break
                self.h_pos = self.h_array[i_h]
                self.nanodrive.set_pos_ax(self.h_pos, XAXIS_ID)
                
                
                time0 = time.time()
                while time.time() - time0 < self.pixel_time:
                    QtGui.QApplication.processEvents() #release       
                
                counts = self.lj_counter.read_rates()
                #self.count_rate_map[i_v,i_h] = counts[-1] # grab integration time for now
                self.c0_rate = counts[0]
                self.count_rate_map[i_v,i_h] = self.c0_rate # grab count0 rate
                
                """self.ccd.start_acquisition()
                stat = "ACQUIRING"
                while stat!= "IDLE":
                    wx_yielded_sleep(self.ccd.exposure_time * 0.25)
                    stati, stat = self.ccd.get_status()
                self.ccd.get_acquired_data()
                
                spectrum = np.sum(self.ccd.buffer[ROW0:ROW1], axis=0)
                
                self.spectrum_map[jj,ii,:] = spectrum
                
                self.integrated_count_map[jj,ii] = sum(spectrum)
                """

   
        self.on_scan_stop()
        
        
    @QtCore.Slot()            
    def on_scan_stop(self):
        print "on_scan_stop"
        self.scanning = False
        self.update_display()

        self.timer.start() #restart the normal timer
        self.display_update_when_scanning_timer.stop()

        # clean up after scan
        self.ax_2d_img.set_data(self.count_rate_map)
        self.fig2d.canvas.draw()
        self.update_display()
        self.scanning = False
        print "scanning done"
    
        """
        print "saving data..."
        t0 = time.time()
        #np.savetxt("%i_confocal_scan.csv" % t0, 
        #           self.integrated_count_map, delimiter=',')
        
        save_params = ["spectrum_map", "x0", "x1", "y0", "y1",
                       "Nx", "Ny", 
                       "x_array", "y_array",
                       "dx", "dy", "integrated_count_map"]
        save_dict = dict()
        for key in save_params:
            save_dict[key] = getattr(self, key)
        

        for key in ["XAXIS_ID", "YAXIS_ID","HARDWARE_DEBUG","ANDOR_HFLIP","ANDOR_VFLIP","ANDOR_AD_CHAN","ROW0","ROW1"]:
            save_dict[key] = globals()[key]
        
        for key in ["wl", "gratings", "grating"]:
            save_dict["spec_"+key] = getattr(self.spec, key)
        
        for key in ["exposure_time", "em_gain", "temperature", "ad_chan", "ro_mode", "Nx", "Ny"]:
            save_dict["andor_"+key] = getattr(self.ccd, key)
            
        
        save_dict["time_saved"] = t0
        
        np.savez_compressed("%i_spec_map.npz" % t0, **save_dict)
        print "data saved"
        """


    
    @QtCore.Slot()
    def on_display_update_when_scanning_timer(self):
        # update display
        try:
            self.update_display()
        except Exception, err:
            print "Failed to update_display", err
        
        try:
            #self.spec_plotline.set_ydata(spectrum)
            #self.ax_speclive.relim()
            #self.ax_speclive.autoscale_view(tight=None, scalex=False, scaley=True)
            #self.fig2.canvas.draw()
            pass
        except Exception as err:
            print "Failed to update spectrum plot", err
        
        try:
            #print "updating figure"
            #self.read_from_hardware()
            self.ax_2d_img.set_data(self.count_rate_map)
            try:
                count_min =  np.min(self.count_rate_map[np.nonzero(self.count_rate_map)])
            except Exception as err:
                count_min = 0
            count_max = np.max(self.count_rate_map)
            self.ax_2d_img.set_clim(count_min, count_max + 1)
            self.fig2d.canvas.draw()
        except Exception, err:
            print "Failed to update figure:", err    
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("ScanningConfocalApp")
    
    gui = ScanningConfocalUI()
    gui.show()
    
    sys.exit(app.exec_())
    