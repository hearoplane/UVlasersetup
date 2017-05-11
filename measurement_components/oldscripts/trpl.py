# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 09:21:07 2014

@author: esbarnard
"""
import numpy as np
import time
from PySide import QtCore

from .measurement import Measurement 
from .base_3d_scan import Base3DScan
from numpy import histogram


class PicoHarpMeasurement(Measurement):    
    name = "picoharp_live"
    
    def setup(self):
        self.display_update_period = 0.1 #seconds
        
        #connect events
        self.gui.ui.picoharp_acquire_one_pushButton.clicked.connect(self.start)
        self.gui.ui.picoharp_interrupt_pushButton.clicked.connect(self.interrupt)
    
    def setup_figure(self):
        self.fig = self.gui.add_figure("picoharp_live", self.gui.ui.picoharp_plot_widget)
                    
        self.ax = self.fig.add_subplot(111)
        self.plotline, = self.ax.semilogy([0,20], [1,65535])
        self.ax.set_ylim(1e-1,1e5)
        self.ax.set_xlabel("Time (ns)")
        self.ax.set_ylabel("Counts")
    
    def _run(self):
        ph = self.picoharp = self.gui.picoharp_hc.picoharp
        #: type: ph: PicoHarp300
        
        self.plotline.set_xdata(ph.time_array*1e-3)
        sleep_time = np.min((np.max(0.1*ph.Tacq*1e-3, 0.010), 0.100)) # check every 1/10 of Tacq with limits of 10ms and 100ms
        print "sleep_time", sleep_time, np.max(0.1*ph.Tacq*1e-3, 0.010)
        
        ph.start_histogram()
        while not ph.check_done_scanning():
            if self.interrupt_measurement_called:
                break
            ph.read_histogram_data()
            time.sleep(sleep_time)

        ph.stop_histogram()
        ph.read_histogram_data()
        
        save_dict = {
                     'time_histogram': ph.histogram_data,
                     'time_array': ph.time_array
                    }               

                    
        for lqname,lq in self.gui.logged_quantities.items():
            save_dict[lqname] = lq.val
            
        for lqname,lq in self.gui.picoharp_hc.logged_quantities.items():
            save_dict[self.gui.picoharp_hc.name + "_" + lqname] = lq.val
            
        for lqname,lq in self.logged_quantities.items():
            save_dict[self.name +"_"+ lqname] = lq.val

        self.fname = "%i_picoharp.npz" % time.time()
        np.savez_compressed(self.fname, **save_dict)
        print "TRPL Picoharp Saved", self.fname
                
        #is this right place to put this?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()        

               
    @QtCore.Slot()
    def on_display_update_timer(self):
        try:
            ph = self.picoharp
            self.plotline.set_ydata(ph.histogram_data)
            self.fig.canvas.draw()
        finally:
            Measurement.on_display_update_timer(self)
        
 
class PicoHarpPowerWheelMeasurement(Measurement):
    
    name = "picoharp_live"
    
    def setup(self):
        self.display_update_period = 0.1 #seconds
        
        #connect events
        self.gui.ui.power_wheel_start_pushButton.clicked.connect(self.start)
        self.gui.ui.power_wheel_interrupt_pushButton.clicked.connect(self.interrupt)
        
        self.power_wheel_steps = self.add_logged_quantity("power_wheel_steps", dtype=int, unit='deg', vmin=0, vmax=+8000, ro=False)
        self.power_wheel_steps.connect_bidir_to_widget(self.gui.ui.power_wheel_steps_doubleSpinBox)

        self.power_wheel_delta = self.add_logged_quantity("power_wheel_delta", dtype=int, unit='', vmin=-8000, vmax=+8000, ro=False)
        self.power_wheel_steps.connect_bidir_to_widget(self.gui.ui.power_wheel_delta_doubleSpinBox)


        self.stored_histogram_channels = self.add_logged_quantity("stored_histogram_channels", dtype=int, vmin=1, vmax=2**16)
        self.stored_histogram_channels.connect_bidir_to_widget(
                                           self.gui.ui.power_wheel_channels_doubleSpinBox)
        
        self.stored_histogram_channels.update_value(1000)   
    
    def setup_figure(self):
        self.fig = self.gui.add_figure("picoharp_live", self.gui.ui.picoharp_plot_widget)
                    
        self.ax = self.fig.add_subplot(111)
        self.plotline, = self.ax.semilogy([0,20], [1,65535])
        self.ax.set_ylim(1e-1,1e5)
        self.ax.set_xlabel("Time (ns)")
        self.ax.set_ylabel("Counts")
    
    def _run(self):

        ph = self.picoharp = self.gui.picoharp_hc.picoharp

        pw = self.power_wheel = self.gui.power_wheel_arduino_hc.power_wheel_arduino_hc
        
        pw_steps = self.power_wheel_steps.val
        pw_delta = self.power_wheel_delta.val
        pw_motor_steps = pw_steps*pw_delta
        #: type: ph: PicoHarp300
        
        self.plotline.set_xdata(ph.time_array*1e-3)
        sleep_time = np.min((np.max(0.1*ph.Tacq*1e-3, 0.010), 0.100)) # check every 1/10 of Tacq with limits of 10ms and 100ms
        print "sleep_time", sleep_time, np.max(0.1*ph.Tacq*1e-3, 0.010)
        
                  

        N = self.stored_histogram_channels.val
        self.time_trace= np.zeros(pw_steps,N)
        self.power = np.zeros(pw_steps)
            
            
        for ii in range(pw_steps+1):
                
            # collect data
            ph.start_histogram()
            while not ph.check_done_scanning():
                ph.read_histogram_data()
                time.sleep(sleep_time)  
            ph.stop_histogram()
            ph.read_histogram_data()


            # make a step
            pw.write_steps(pw_motor_steps)                                      
        
            # store in arrays
            self.time_trace[ii,:] = ph.histogram_data[0:N]

            
            
                
        save_dict = {
                     'time_trace': self.time_trace,
                     'time_array': self.time_array,
                     'power': self.power
                     } 
    
                
                
            
                
                           

                    
        for lqname,lq in self.gui.logged_quantities.items():
            save_dict[lqname] = lq.val
            
        for lqname,lq in self.gui.picoharp_hc.logged_quantities.items():
            save_dict[self.gui.picoharp_hc.name + "_" + lqname] = lq.val
            
        for lqname,lq in self.logged_quantities.items():
            save_dict[self.name +"_"+ lqname] = lq.val

        self.fname = "%i_picoharp.npz" % time.time()
        np.savez_compressed(self.fname, **save_dict)
        print "TRPL Picoharp Saved", self.fname
                
        #is this right place to put this?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()        

               
    @QtCore.Slot()
    def on_display_update_timer(self):
        try:
            ph = self.picoharp
            self.plotline.set_ydata(ph.histogram_data)
            self.fig.canvas.draw()
        finally:
            Measurement.on_display_update_timer(self)
        
        

class TRPLScanMeasurement(Measurement):
    
    name = "trpl_scan"

    def setup(self):
        print "setup TRPLScanMeasurement"
                
        self.display_update_period = 0.1 #seconds
        
        # local logged quantities
        lq_params = dict(dtype=float, vmin=-1,vmax=100, ro=False, unit='um' )
        self.h0 = self.add_logged_quantity('h0',  initial=25, **lq_params  )
        self.h1 = self.add_logged_quantity('h1',  initial=45, **lq_params  )
        self.v0 = self.add_logged_quantity('v0',  initial=25, **lq_params  )
        self.v1 = self.add_logged_quantity('v1',  initial=45, **lq_params  )

        self.dh = self.add_logged_quantity('dh', initial=1, **lq_params)
        self.dv = self.add_logged_quantity('dv', initial=1, **lq_params)

        self.stored_histogram_channels = self.add_logged_quantity("stored_histogram_channels", dtype=int, vmin=1, vmax=2**16)

        # connect to gui        
        self.h0.connect_bidir_to_widget(self.gui.ui.h0_doubleSpinBox)
        self.h1.connect_bidir_to_widget(self.gui.ui.h1_doubleSpinBox)
        self.v0.connect_bidir_to_widget(self.gui.ui.v0_doubleSpinBox)
        self.v1.connect_bidir_to_widget(self.gui.ui.v1_doubleSpinBox)
        
        self.dh.connect_bidir_to_widget(self.gui.ui.dh_doubleSpinBox)
        self.dv.connect_bidir_to_widget(self.gui.ui.dv_doubleSpinBox)
        
        #connect events
        self.gui.ui.trpl_map_start_pushButton.clicked.connect(self.start)
        self.gui.ui.trpl_map_interrupt_pushButton.clicked.connect(self.interrupt)
        
        self.stored_histogram_channels.connect_bidir_to_widget(
                                           self.gui.ui.trpl_map_stored_channels_doubleSpinBox)
        
        self.stored_histogram_channels.update_value(1000)
    
    def setup_figure(self):
        print "TRPLSCan figure"
        self.fig = self.gui.add_figure("trpl_map", self.gui.ui.trpl_map_plot_widget)
        self.ax_time = self.fig.add_subplot(211)
        self.ax_time.set_xlabel("Time (ns)")
        self.time_trace_plotline, = self.ax_time.semilogy([0,20], [0,65535])
        self.ax_time.set_ylim(1e-1,1e5)
        
        #self.fig.canvas.draw()

        self.aximg = self.fig.add_subplot(212)
        self.aximg.set_xlim(0, 100)
        self.aximg.set_ylim(0, 100)

        #self.fig.canvas.draw()

    
    def _run(self):
        # Setup try-block
        #hardware
        self.stage = self.gui.mcl_xyz_stage_hc
        self.nanodrive = self.stage.nanodrive
        ph = self.picoharp = self.gui.picoharp_hc.picoharp

        #get scan parameters:

        self.h_array = np.arange(self.h0.val, self.h1.val, self.dh.val, dtype=float)
        self.v_array = np.arange(self.v0.val, self.v1.val, self.dv.val, dtype=float)
        
        self.Nh = len(self.h_array)
        self.Nv = len(self.v_array)
        
        self.extent = [self.h0.val, self.h1.val, self.v0.val, self.v1.val]


        # TRPL scan specific setup
        sleep_time = np.min(np.max(0.1*ph.Tacq*1e-3, 0.010), 0.100) # check every 1/10 of Tacq with limits of 10ms and 100ms

        
        #create data arrays
        self.integrated_count_map = np.zeros((self.Nv, self.Nh), dtype=int)
        self.time_trace_map = np.zeros( (self.Nv, self.Nh, self.stored_histogram_channels.val), dtype=int)
        
        self.time_array = ph.time_array[0:self.stored_histogram_channels.val]*1e-3
        #update figure
        self.time_trace_plotline.set_xdata(self.time_array)

        self.imgplot = self.aximg.imshow(self.integrated_count_map, 
                                    origin='lower',
                                    vmin=1e4, vmax=1e5, interpolation='nearest', 
                                    extent=self.extent)

        # set up experiment
        # experimental parameters already connected via LoggedQuantities
        
        # TODO Stop other timers?!

        print "scanning"
        try:
            v_axis_id = self.stage.v_axis_id
            h_axis_id = self.stage.h_axis_id

            # move slowly to start position
            start_pos = [None, None,None]
            start_pos[v_axis_id-1] = self.v_array[0]
            start_pos[h_axis_id-1] = self.h_array[0]
            self.nanodrive.set_pos_slow(*start_pos)            
            
            # Scan!            
            line_time0 = time.time()
            
            for i_v in range(self.Nv):
                self.v_pos = self.v_array[i_v]
                self.nanodrive.set_pos_ax(self.v_pos, v_axis_id)
                #self.read_stage_position()       
    
                if i_v % 2: #odd lines
                    h_line_indicies = range(self.Nh)[::-1]
                else:       #even lines -- traverse in opposite direction
                    h_line_indicies = range(self.Nh)            
    
                for i_h in h_line_indicies:
                    if self.interrupt_measurement_called:
                        break
    
                    print i_h, i_v
    
                    self.h_pos = self.h_array[i_h]
                    self.nanodrive.set_pos_ax(self.h_pos, h_axis_id)    
                    
                    # collect data
                    ph.start_histogram()
                    while not ph.check_done_scanning():
                        ph.read_histogram_data()
                        time.sleep(sleep_time)  
                    ph.stop_histogram()
                    ph.read_histogram_data()
                                      
                    # store in arrays
                    N = self.stored_histogram_channels.val
                    self.time_trace_map[i_v,i_h,:] = ph.histogram_data[0:N]
                    self.integrated_count_map[i_v,i_h] = np.sum(self.time_trace_map[i_v,i_h])
    
                print "line time:", time.time() - line_time0
                print "pixel time:", float(time.time() - line_time0)/self.Nh
                line_time0 = time.time()
                
                # read stage position every line
                self.stage.x_position.read_from_hardware()
                self.stage.y_position.read_from_hardware()
                self.stage.z_position.read_from_hardware()

                
            #scanning done
        #except Exception as err:
        #    self.interrupt()
        #    raise err
        finally:
            #save  data file
            save_dict = {
                     'time_trace_map': self.time_trace_map,
                     'integrated_count_map': self.integrated_count_map,
                     'h_array': self.h_array,
                     'v_array': self.v_array,
                     'Nv': self.Nv,
                     'Nh': self.Nh,
                     'extent': self.extent,
                     'time_array': self.time_array
                    }               

                    
            for lqname,lq in self.gui.logged_quantities.items():
                save_dict[lqname] = lq.val
                
            for lqname,lq in self.gui.picoharp_hc.logged_quantities.items():
                save_dict[self.gui.picoharp_hc.name + "_" + lqname] = lq.val
                
            for lqname,lq in self.logged_quantities.items():
                save_dict[self.name +"_"+ lqname] = lq.val
    
            self.fname = "%i_trpl_map.npz" % time.time()
            np.savez_compressed(self.fname, **save_dict)
            print "TRPL Scan Saved", self.fname

            if not self.interrupt_measurement_called:
                self.measurement_sucessfully_completed.emit()
            else:
                pass

    
    def update_display(self):
        self.time_trace_plotline.set_ydata(1+self.picoharp.histogram_data[0:self.stored_histogram_channels.val])
        
        C = self.integrated_count_map
        self.imgplot.set_data(C)
        
        try:
            count_min =  np.min(C[np.nonzero(C)])
        except Exception:
            count_min = 0
        count_max = np.max(self.integrated_count_map)
        self.imgplot.set_clim(count_min, count_max + 1)
        
        self.fig.canvas.draw()
        
        
class TRPLScan3DMeasurement(Base3DScan):
    
    name = "trpl_scan3d"
    
    def scan_specific_setup(self):
        self.stored_histogram_channels = self.add_logged_quantity("stored_histogram_channels", dtype=int, vmin=1, vmax=2**16, initial=4000)
        
    def setup_figure(self):
        pass
    
    def pre_scan_setup(self):
        #hardware
        ph = self.picoharp = self.gui.picoharp_hc.picoharp
        
        # TRPL scan specific setup
        self.sleep_time = np.min(np.max(0.1*ph.Tacq*1e-3, 0.010), 0.100) # check every 1/10 of Tacq with limits of 10ms and 100ms

        #create data arrays
        self.integrated_count_map = np.zeros((self.Nz, self.Ny, self.Nx), dtype=int)
        print "size of time_trace_map %e" %  (self.Nx* self.Ny * self.Nz * self.stored_histogram_channels.val)

        self.time_trace_map = np.zeros( (self.Nz, self.Ny, self.Nx, self.stored_histogram_channels.val),dtype=np.uint16)
        
        self.time_array = ph.time_array[0:self.stored_histogram_channels.val]*1e-3
        #update figure
        #self.time_trace_plotline.set_xdata(self.time_array)    
        
        
    def collect_pixel(self, i, j, k):
        ph = self.picoharp
        # collect data
        ph.start_histogram()
        while not ph.check_done_scanning():
            ph.read_histogram_data()
            time.sleep(self.sleep_time)  
        ph.stop_histogram()
        ph.read_histogram_data()
                          
        # store in arrays
        N = self.stored_histogram_channels.val
        self.time_trace_map[k,j,i,:] = ph.histogram_data[0:N]
        self.integrated_count_map[k,j,i] = np.sum(self.time_trace_map[k,j,i])

    def scan_specific_savedict(self):
        return dict( integrated_count_map=self.integrated_count_map,
                     time_trace_map = self.time_trace_map,
                     time_array = self.time_array,
                     )
        
    def update_display(self):
        pass
