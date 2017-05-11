import numpy as np
import time
import threading
from PySide import QtCore

from .measurement import Measurement 

import matplotlib.gridspec as gridspec 
from time import sleep

ROW0 = 240
ROW1 = 271

class AndorCCDReadout(Measurement):

    name = "andor_ccd_readout"
    
    def setup(self):
        
        self.display_update_period = 0.050 #seconds

        #connect events
        self.gui.ui.andor_ccd_acquire_cont_checkBox.stateChanged.connect(self.start_stop)

    def setup_figure(self):
        #Andor CCD data
        self.fig_ccd_image = self.gui.add_figure('ccd_image', self.gui.ui.plot_andor_ccd_widget)


    def _run(self):
    
        #setup data arrays         
        self.fig_ccd_image.clf()
        gs = gridspec.GridSpec(2,1,height_ratios=[1,4]) 
        self.ax_andor_ccd_spec = self.fig_ccd_image.add_subplot(gs[0])
        self.ax_andor_ccd_image = self.fig_ccd_image.add_subplot(gs[1])
        
        ccd = self.gui.andor_ccd_hc.andor_ccd
        
        width_px = ccd.Nx_ro
        height_px = ccd.Ny_ro
        
        self.andor_ccd_imshow = self.ax_andor_ccd_image.imshow(np.zeros((height_px, width_px),dtype=np.int32) , 
                                                        origin='lower', interpolation='none', aspect='auto')
        
        self.andor_ccd_spec_line, = self.ax_andor_ccd_spec.plot( np.zeros(width_px, dtype=np.int32), 'k-')

        self.ax_andor_ccd_spec.set_xlim(1,width_px)
        #self.ax_andor_ccd_spec.set_xticks(np.arange(1, width_px, int(width_px/10)))
        
        #self.ax_andor_ccd_image.set_xticks(np.arange(1, width_px, int(width_px/10)))
        #self.ax_andor_ccd_image.set_yticks(np.arange(1, height_px, np.max(1, int(height_px/10))))
        
        t_acq = self.gui.andor_ccd_hc.exposure_time.val #in seconds
        
        wait_time = np.min(1.0,np.max(0.05*t_acq, 0.05)) # limit update period to 50ms (in ms) or as slow as 1sec
        
        print "starting acq"
        ccd.start_acquisition()
        
        print "checking..."
        while not self.interrupt_measurement_called:
            stat = ccd.get_status()
            if stat == 'IDLE':
                # grab data
                
                buffer_ = ccd.get_acquired_data()
                
                if self.gui.ui.andor_ccd_bgsub_checkBox.checkState():
                    bg = self.gui.andor_ccd_hc.background
                    if bg is not None:
                        if bg.shape == buffer_.shape:
                            buffer_ = buffer_ - bg
                        else:
                            print "Background not the correct shape", buffer_.shape, bg.shape
                    else:
                        print "No Background available, raw data shown"
                spectra_data = np.average(buffer_, axis=0)
                
                #update figure
                self.andor_ccd_imshow.set_data(buffer_)
                count_min = np.min(buffer_)
                count_max = np.max(buffer_)
                self.andor_ccd_imshow.set_clim(count_min, count_max)
                self.andor_ccd_spec_line.set_ydata(spectra_data)
                self.ax_andor_ccd_spec.relim()
                self.ax_andor_ccd_spec.autoscale_view(scalex=False, scaley=True)
    
                self.fig_ccd_image.canvas.draw()
                # restart acq
                ccd.start_acquisition()
            else:
                sleep(wait_time)            
        # while-loop is complete
        stat = ccd.get_status()
        if stat != 'IDLE':
            ccd.abort_acquisition()
                    
        #is this right place to put this?
        # Signal emission from other threads ok?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()
    
    @QtCore.Slot()
    def on_display_update_timer(self):
        Measurement.on_display_update_timer(self)
        


class AndorCCDReadBackground(Measurement):

    name = "andor_ccd_background"
    
    def setup(self):        
        self.display_update_period = 0.050 #seconds

        #connect events
        self.gui.ui.andor_ccd_acq_bg_pushButton.clicked.connect(self.start)
        self.gui.ui.andor_ccd_abort_bg_pushButton.clicked.connect(self.interrupt)

        
    def setup_figure(self):
        #Andor CCD data
        self.fig_ccd_image = self.gui.add_figure('ccd_image', self.gui.ui.plot_andor_ccd_widget)

    def _run(self):
    
        #setup data arrays         
        self.fig_ccd_image.clf()
        gs = gridspec.GridSpec(2,1,height_ratios=[1,4]) 
        self.ax_andor_ccd_spec = self.fig_ccd_image.add_subplot(gs[0])
        self.ax_andor_ccd_image = self.fig_ccd_image.add_subplot(gs[1])
        
        ccd = self.gui.andor_ccd_hc.andor_ccd
        
        width_px = ccd.Nx_ro
        height_px = ccd.Ny_ro
        
        self.andor_ccd_imshow = self.ax_andor_ccd_image.imshow(np.zeros((height_px, width_px),dtype=np.int32) , 
                                                        origin='lower', interpolation='none', aspect='auto')
        
        self.andor_ccd_spec_line, = self.ax_andor_ccd_spec.plot( np.zeros(width_px, dtype=np.int32), 'k-')

        self.ax_andor_ccd_spec.set_xlim(1,width_px)
        #self.ax_andor_ccd_spec.set_xticks(np.arange(1, width_px, int(width_px/10)))
        
        #self.ax_andor_ccd_image.set_xticks(np.arange(1, width_px, int(width_px/10)))
        #self.ax_andor_ccd_image.set_yticks(np.arange(1, height_px, np.max(1, int(height_px/10))))
        
        t_acq = self.gui.andor_ccd_hc.exposure_time.val #in seconds
        
        wait_time = np.min(1.0,np.max(0.05*t_acq, 0.05)) # limit update period to 50ms (in ms) or as slow as 1sec
        
        print "starting acq"
        ccd.start_acquisition()
        
        while not self.interrupt_measurement_called:
            stat = ccd.get_status()
            if stat == 'IDLE':
                # grab data
                
                buffer_ = ccd.get_acquired_data()
                spectra_data = np.average(buffer_, axis=0)
    
                print buffer_.shape
                #update figure
                self.andor_ccd_imshow.set_data(buffer_)
                count_min = np.min(buffer_)
                count_max = np.max(buffer_)
                self.andor_ccd_imshow.set_clim(count_min, count_max)
                self.andor_ccd_spec_line.set_ydata(spectra_data)
                self.ax_andor_ccd_spec.relim()
                self.ax_andor_ccd_spec.autoscale_view(scalex=False, scaley=True)
    
                self.fig_ccd_image.canvas.draw()
                break
            else:
                sleep(wait_time)            
        # while-loop is complete
        if self.interrupt_measurement_called:
            self.gui.andor_ccd_hc.interrupt_acquisition()
            self.gui.andor_ccd_hc.background = None
        else:
            self.gui.andor_ccd_hc.background = buffer_.copy()
        
        print "Background successfully acquired"
        
        #is this right place to put this?
        # Signal emission from other threads ok?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()
    
    @QtCore.Slot()
    def on_display_update_timer(self):
        Measurement.on_display_update_timer(self)

class AndorCCDReadSingle(Measurement):

    name = "andor_ccd_readsingle"
    
    def setup(self):        
        self.display_update_period = 0.050 #seconds

        #connect events
        #self.gui.ui.andor_ccd_acq_bg_pushButton.clicked.connect(self.start)
        #self.gui.ui.andor_ccd_abort_bg_pushButton.clicked.connect(self.interrupt)

        
    def setup_figure(self):
        #Andor CCD data
        self.fig_ccd_image = self.gui.add_figure('ccd_image', self.gui.ui.plot_andor_ccd_widget)

    def _run(self):
    
        #setup data arrays         
        self.fig_ccd_image.clf()
        gs = gridspec.GridSpec(2,1,height_ratios=[1,4]) 
        self.ax_andor_ccd_spec = self.fig_ccd_image.add_subplot(gs[0])
        self.ax_andor_ccd_image = self.fig_ccd_image.add_subplot(gs[1])
        
        ccd = self.gui.andor_ccd_hc.andor_ccd
        
        width_px = ccd.Nx_ro
        height_px = ccd.Ny_ro
        
        self.andor_ccd_imshow = self.ax_andor_ccd_image.imshow(np.zeros((height_px, width_px),dtype=np.int32) , 
                                                        origin='lower', interpolation='none', aspect='auto')
        
        self.andor_ccd_spec_line, = self.ax_andor_ccd_spec.plot( np.zeros(width_px, dtype=np.int32), 'k-')

        self.ax_andor_ccd_spec.set_xlim(1,width_px)
        #self.ax_andor_ccd_spec.set_xticks(np.arange(1, width_px, int(width_px/10)))
        
        #self.ax_andor_ccd_image.set_xticks(np.arange(1, width_px, int(width_px/10)))
        #self.ax_andor_ccd_image.set_yticks(np.arange(1, height_px, np.max(1, int(height_px/10))))
        
        t_acq = self.gui.andor_ccd_hc.exposure_time.val #in seconds
        
        wait_time = np.min(1.0,np.max(0.05*t_acq, 0.05)) # limit update period to 50ms (in ms) or as slow as 1sec
        
        print "starting acq"
        ccd.start_acquisition()
        
        while not self.interrupt_measurement_called:
            stat = ccd.get_status()
            if stat == 'IDLE':
                # grab data
                
                buffer_ = ccd.get_acquired_data()
                spectra_data = np.average(buffer_, axis=0)
    
                print buffer_.shape
                #update figure
                self.andor_ccd_imshow.set_data(buffer_)
                count_min = np.min(buffer_)
                count_max = np.max(buffer_)
                self.andor_ccd_imshow.set_clim(count_min, count_max)
                self.andor_ccd_spec_line.set_ydata(spectra_data)
                self.ax_andor_ccd_spec.relim()
                self.ax_andor_ccd_spec.autoscale_view(scalex=False, scaley=True)
    
                self.fig_ccd_image.canvas.draw()
                break
            else:
                sleep(wait_time)            
        # while-loop is complete
        if self.interrupt_measurement_called:
            self.gui.andor_ccd_hc.interrupt_acquisition()
            self.spectrum = None
        else:
            self.spectrum = buffer_.copy()
        
        save_dict = {
                 'spectrum': self.spectrum,
                    }               
                
        for lqname,lq in self.gui.logged_quantities.items():
            save_dict[lqname] = lq.val
        
        for hc in self.gui.hardware_components.values():
            for lqname,lq in hc.logged_quantities.items():
                save_dict[hc.name + "_" + lqname] = lq.val
        
        for lqname,lq in self.logged_quantities.items():
            save_dict[self.name +"_"+ lqname] = lq.val

        self.fname = "%i_%s.npz" % (time.time(), self.name)
        np.savez_compressed(self.fname, **save_dict)
        print self.name, "saved:", self.fname

        print "Andor CCD single acq successfully acquired"
        
        #is this right place to put this?
        # Signal emission from other threads ok?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()
    
    @QtCore.Slot()
    def on_display_update_timer(self):
        Measurement.on_display_update_timer(self)


