# -*- coding: utf-8 -*-
"""
Created on Mon Mar 31 10:46:23 2014

@author: lab
"""

import numpy as np
import time
import threading
from PySide import QtCore
from scipy import interpolate

from .measurement import Measurement 

PM_SAMPLE_NUMBER = 1
UP_AND_DOWN_SWEEP = True

class PLEPointMeasurement(Measurement):
    
    #TODO store information about the acton_spectrometer position and grating
    
    def __init__(self, gui):
        Measurement.__init__(self, gui = gui, name = "ple_point")
        
        self.display_update_period = 0.500 #seconds
        
        self.gui.ui.ple_point_scan_start_pushButton.clicked.connect(self.start)
        self.gui.ui.ple_point_scan_stop_pushButton.clicked.connect(self.interrupt)
    
    def setup_figure(self):
        # AOTF Point Scan Figure ####
        self.fig_aotf_point_scan = self.gui.add_figure('aotf_point_scan', self.gui.ui.aotf_point_scan_plot_groupBox)
        
        self.ax_excite_power = self.fig_aotf_point_scan.add_subplot(221)
        self.ax_excite_power.set_ylabel("power (W)")

        self.ax_laser_spec = self.fig_aotf_point_scan.add_subplot(222)
        self.ax_laser_spec.set_xlabel("wavelenth (nm)")
        
        self.ax_emission_intensity = self.fig_aotf_point_scan.add_subplot(223)
        self.ax_emission_intensity.set_ylabel("Counts")
        
        self.ax_result = self.fig_aotf_point_scan.add_subplot(224)
        self.ax_result.set_xlabel("wavelength (nm)")
        self.ax_result.set_ylabel("intensity 'a.u.'")
        
        for ax in [self.ax_excite_power, self.ax_emission_intensity]:
            ax.set_xlabel("frequency (MHz)")
        
    
    def _run(self):    
        
        # check the type of detector selected in GUI
        use_ccd = self.gui.ui.ple_point_scan_detector_comboBox.currentText() == "Andor CCD"
       
        # Local objects used for measurement
        oospectrometer = self.gui.oo_spectrometer
        if use_ccd:
            ccd = self.gui.andor_ccd_hc.andor_ccd
        else:
            apd_hc = self.gui.apd_counter_hc
       
        
        
       
        # Turn the AOTF modulation on.
        self.gui.aotf_modulation.update_value(True)        

        # CCD setup/initialization               
        self.gui.andor_ccd_hc.shutter_open.update_value(True)
        
        # Wavelengths from the OceanOptics
        self.oo_wavelengths = oospectrometer.wavelengths

        # read current stage position        
        self.gui.read_stage_position()
  
        # List of frequency steps to take based on min, max and step size specified 
        # in the GUI
        freqs1 = np.arange(self.gui.ui.aotf_freq_start_doubleSpinBox.value(),
                          self.gui.ui.aotf_freq_stop_doubleSpinBox.value(),
                          self.gui.ui.aotf_freq_step_doubleSpinBox.value())
        
        # Sweep the frequencies up and down or just up?
        if UP_AND_DOWN_SWEEP:            
            freqs2 = freqs1[::-1]
            self.freqs = np.concatenate((freqs1,freqs2))
        else:
            self.freqs = freqs1

        # Define a local variable for quicker reference.
        freqs = self.freqs
                          
        # Data recorded from the measurement
        self.oo_specs = np.zeros( (len(freqs), len(self.oo_wavelengths)), dtype=int)
        self.oo_wl_maxs = np.zeros( len(freqs), dtype=float)
        self.pm_powers = np.ones( len(freqs), dtype=float)*1e-9
        self.total_emission_intensity = np.zeros( len(freqs), dtype=int)
        self.aotf_modulations = np.zeros(len(freqs), dtype=int)

        if use_ccd:
            self.ccd_specs = np.zeros( (len(freqs), ccd.Nx_ro), dtype=int)
        else:
            self.apd_intensities = np.zeros( (len(freqs), 1), dtype=float)


        # setup figure plotlines
        for ax in [self.ax_excite_power, self.ax_laser_spec, self.ax_emission_intensity, self.ax_result]:
            ax.lines = []
            
        self.excite_power_plotline, = self.ax_excite_power.plot(freqs, np.zeros_like(freqs))                       
        self.laser_spec_plotline, = self.ax_laser_spec.plot(self.oo_wavelengths, 
                                                            np.zeros_like(self.oo_wavelengths, dtype=int))                       
        self.emission_intensity_plotline, = self.ax_emission_intensity.plot(freqs, np.zeros_like(freqs))                       
        self.result_plotline, = self.ax_result.plot(np.zeros_like(freqs), np.zeros_like(freqs))                       
 
        self.spec_wl = 0                 
        
        # Background correct the data?
        if use_ccd:
            do_bgsub = bool(self.gui.ui.andor_ccd_bgsub_checkBox.checkState())
            if do_bgsub:
                do_bgsub = self.gui.andor_ccd_hc.is_background_valid()
            
            if do_bgsub:
                bg = self.gui.andor_ccd_hc.background
            else:
                bg = None
                
            # Figure out a reasonable time to wait to recheck the acquisition
            t_acq = self.gui.andor_ccd_hc.exposure_time.val #in seconds
            wait_time = np.min(1.0,np.max(0.05*t_acq, 0.05))
        
        # Setup complete... start sweep and perform the measurement!
        #print freqs
        for ii, freq in enumerate(freqs):
            print ii, freq
            if self.interrupt_measurement_called:
                break
            
            # Tune the AOTF
            self.gui.aotf_freq.update_value(freq)
            time.sleep(0.020)
            
            try_count = 0
            while True:
                try:
                    if freq > 150:
                        self.gui.aotf_power.update_value(4500)
                    else:
                        self.gui.aotf_power.update_value(2000)
                    time.sleep(0.02)
                    break
                except:
                    try_count = try_count + 1 
                    if try_count > 9:
                        print "Failed to set AOTF power."
                        break
                    time.sleep(0.010)         
            
            # Record laser spectrum from OO 
            oospectrometer.acquire_spectrum()
            oo_spectrum = oospectrometer.spectrum.copy()
            self.oo_specs[ii] = (oo_spectrum)
            
            #compute wavelength of laser
            max_i = oo_spectrum[10:-10].argmax() + 10
            wl = self.oo_wavelengths[max_i]
            self.oo_wl_maxs[ii] = wl
            
            # Set the wavelength correction for the power meter.  Try 10 times before 
            # finally failing.
            self.gui.power_meter_wavelength.update_value(wl)
            
            # Sleep for 10 ms to let power meter finish processing
            time.sleep(0.010)
            
            # Sample the power at least one time from the power meter.
            samp_count = 0
            pm_power = 0.
            for samp in range(0, PM_SAMPLE_NUMBER):
                # Try at least 10 times before ultimately failing
                try_count = 0
                while True:
                    try:
                        pm_power = pm_power + self.gui.laser_power.read_from_hardware(send_signal=True)
                        samp_count = samp_count + 1
                        break 
                    except:
                        try_count = try_count + 1
                        if try_count > 9:
                            break
                        time.sleep(0.010)
             
            if samp_count > 0:              
                pm_power = pm_power/samp_count
            else:
                print "  Failed to read power"
                pm_power = 10000.    
            self.pm_powers[ii] = pm_power
            
            if use_ccd:
                ccd.start_acquisition()
                stat = "ACQUIRING"
                while (stat!= "IDLE") and (not self.interrupt_measurement_called):
                    time.sleep(wait_time)
                    stat = ccd.get_status()
    
                if not self.interrupt_measurement_called:
                    buffer_ = ccd.get_acquired_data()
                    
                    if do_bgsub:
                        buffer_ = buffer_ - bg
                         
                    spectrum = np.sum(buffer_, axis=0)
                    
                    self.ccd_specs[ii] = spectrum
                    self.total_emission_intensity[ii] = spectrum.sum() 
            else: #apd
                self.apd_intensities[ii] = apd_hc.read_count_rate()
                self.total_emission_intensity[ii] = self.apd_intensities[ii]
            
            self.aotf_modulations[ii] = self.gui.aotf_modulation.val
            
            self.ii = ii
                            
        #### END Measurement loop ####        
            
        # If the measurement was interrupted, may need to stop the acqusition        
        if self.interrupt_measurement_called:
                self.gui.andor_ccd_hc.interrupt_acquisition()
                
        # Save the data
        save_dict = {
                     'oo_specs': self.oo_specs,
                     'freqs': freqs,
                     'spec_wl': self.spec_wl,
                     'oo_wavelengths': self.oo_wavelengths,
                     'oo_wl_max': self.oo_wl_maxs,
                     'pm_powers': self.pm_powers,
                     'use_ccd': use_ccd,
                     'aotf_modulations': self.aotf_modulations
                    }

        if use_ccd:
            save_dict.update({
                              'ccd_specs': self.ccd_specs,
                              'do_bgsub': do_bgsub,
                              'bg': bg                     
                              })
        else: # APD
            save_dict.update({
                              'apd_intensities':self.apd_intensities,
                              })
                    
        for lqname,lq in self.gui.logged_quantities.items():
            save_dict[lqname] = lq.val
            
        if use_ccd:
            for lqname,lq in self.gui.andor_ccd_hc.logged_quantities.items():
                save_dict[self.gui.andor_ccd_hc.name + "_" + lqname] = lq.val
        else:
            for lqname,lq in apd_hc.logged_quantities.items():
                save_dict[apd_hc.name + "_" + lqname] = lq.val
                
        for lqname,lq in self.logged_quantities.items():
            save_dict[self.name +"_"+ lqname] = lq.val
        
        np.savez_compressed("%i_ple_scan.npz" % time.time(), **save_dict)

        #if use_ccd:
            # Close the shutter          
        #    self.gui.andor_ccd_hc.shutter_open.update_value(False)
        
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            pass
    
    @QtCore.Slot()
    def start(self):
        self.interrupt_measurement_called = False
        self.acq_thread = threading.Thread(target=self._run)
        self.acq_thread.start()
        self.t_start = time.time()
        self.display_update_timer.start(100)
    
    @QtCore.Slot()
    def interrupt(self):
        self.interrupt_measurement_called = True
        #Make sure display is up to date        
        self.on_display_update_timer() 

    def is_measuring(self):
        return self.acq_thread.is_alive()
        
    
    @QtCore.Slot()
    def on_display_update_timer(self):
        #update figure
        try:
            self.excite_power_plotline.set_ydata(self.pm_powers)
                           
            self.laser_spec_plotline.set_ydata(self.oo_specs[self.ii])
                          
            self.emission_intensity_plotline.set_ydata(self.total_emission_intensity)
            
            self.result_plotline.set_data(self.oo_wl_maxs, self.total_emission_intensity/self.pm_powers)    
            
            for ax in self.fig_aotf_point_scan.axes:
                ax.relim()
                ax.autoscale_view()
            
            self.fig_aotf_point_scan.canvas.draw()        
        except Exception, err:
            pass
            #print "Failed to update figure:", err            
        finally:       
            Measurement.on_display_update_timer(self)


MASK_2D_WITH_APD_MAP = True
MASK_INT_THRESHOLD = 1.e2

class PLE2DScanMeasurement(Measurement):

    #TODO store information about the acton_spectrometer position and grating
    
    def __init__(self, gui):
        Measurement.__init__(self, gui = gui, name = "ple2d")
        
        self.display_update_period = 0.500 #seconds
        
        self.gui.ui.ple2d_start_pushButton.clicked.connect(self.start)
        self.gui.ui.ple2d_stop_pushButton.clicked.connect(self.interrupt)
    
            
    def setup_figure(self):
        # AOTF Point Scan Figure ####
        self.fig2d = self.gui.add_figure('ple2d', self.gui.ui.ple2d_plot_groupBox)
        
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.plot([0,1])

        self.ax2d.set_xlim(0, self.gui.hmax)
        self.ax2d.set_ylim(0, self.gui.vmax)

    
    def _run(self):
        #hardware 
        self.nanodrive = self.gui.nanodrive

        #get scan parameters:
        self.h0 = self.gui.ui.h0_doubleSpinBox.value()
        self.h1 = self.gui.ui.h1_doubleSpinBox.value()
        self.v0 = self.gui.ui.v0_doubleSpinBox.value()
        self.v1 = self.gui.ui.v1_doubleSpinBox.value()
    
        self.dh = 1e-3*self.gui.ui.dh_spinBox.value()
        self.dv = 1e-3*self.gui.ui.dv_spinBox.value()

        self.h_array = np.arange(self.h0, self.h1, self.dh, dtype=float)
        self.v_array = np.arange(self.v0, self.v1, self.dv, dtype=float)
        
        self.Nh = len(self.h_array)
        self.Nv = len(self.v_array)
        
        self.extent = [self.h0, self.h1, self.v0, self.v1]

        #scan specific setup
        
        
        # create data arrays
        self.visual_map = np.zeros((self.Nv, self.Nh), dtype=float)
        #update figure
        self.imgplot = self.ax2d.imshow(self.visual_map, 
                                    origin='lower',
                                    vmin=1e4, vmax=1e5, interpolation='nearest', 
                                    extent=self.extent)
        
        # set up experiment
        # experimental parameters already connected via LoggedQuantities
        
        if MASK_2D_WITH_APD_MAP:
            apd_h_array = self.gui.apd_scan_measure.h_array
            apd_v_array = self.gui.apd_scan_measure.v_array
            apd_map = self.gui.apd_scan_measure.count_rate_map
            apd_extent = self.gui.apd_scan_measure.extent
            # 2D interpolation function is confusing.  Must have everything as x-y,
            apd_map_interp_func = interpolate.interp2d(apd_h_array, apd_v_array, apd_map)

        print "scanning PLE 2D"
        try:
            start_pos = [None, None,None]
            start_pos[self.gui.VAXIS_ID-1] = self.v_array[0]
            start_pos[self.gui.HAXIS_ID-1] = self.h_array[0]
            
            self.nanodrive.set_pos_slow(*start_pos)
            
            # Scan!            
            line_time0 = time.time()
            
            for i_v in range(self.Nv):
                self.v_pos = self.v_array[i_v]
                self.nanodrive.set_pos_ax(self.v_pos, self.gui.VAXIS_ID)
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
                    self.nanodrive.set_pos_ax(self.h_pos, self.gui.HAXIS_ID)    
                    
                    # Determine whether or not to collect data at this poision
                    if MASK_2D_WITH_APD_MAP:
                        if ((apd_extent[0] <= self.h_pos <= apd_extent[1]) and 
                            (apd_extent[2] <= self.v_pos <= apd_extent[3])):
                            
                            print self.h_pos, self.v_pos,  apd_map_interp_func(self.h_pos, self.v_pos)
                            if (apd_map_interp_func(self.h_pos, self.v_pos) >= MASK_INT_THRESHOLD):
                                collect_data = True
                                print "measuring point"
                            else:
                                print "skipping point"
                                collect_data = False
                            
                        else:
                            # outside of APD map...don't collect data.
                            print "out of range!"
                            collect_data = False 
                    else:
                        collect_data = True
                    
                    if collect_data:
                        ple_point_measure = self.gui.ple_point_measure
                        ple_point_measure.start()
                        while ple_point_measure.is_measuring():
                            time.sleep(0.1)
                            if self.interrupt_measurement_called:
                                ple_point_measure.interrupt()
    
                        if not self.interrupt_measurement_called:                                  
                            # store in arrays
                            self.visual_map[i_v,i_h] = np.sum(ple_point_measure.total_emission_intensity)
                    else:
                        time.sleep(0.010)  # sleep for 10 ms so we don't crash the stage
                        self.visual_map[i_v,i_h] = -1


        #scanning done
        except Exception as err:
            self.interrupt()
            raise err
        finally:
            print "PLE 2D done"
            # saving data goes here -->.

            save_dict = {
                     'visual_map': self.visual_map,
                     'h_array': self.h_array,
                     'v_array': self.v_array,
                     'dh': self.dh,
                     'dv': self.dv,
                     'Nv': self.Nv,
                     'Nh': self.Nh,
                     'extent': self.extent
                    }               
            np.savez_compressed("%i_ple_2D_scan.npz" % time.time(), **save_dict)

            if not self.interrupt_measurement_called:
                self.measurement_sucessfully_completed.emit()
            else:
                pass
        

    @QtCore.Slot()
    def on_display_update_timer(self):        
        try:
            #print "updating figure"
            self.imgplot.set_data(self.visual_map)
            try:
                count_min =  np.min(self.visual_map[np.nonzero(self.visual_map)])
            except Exception as err:
                count_min = 0
            count_max = np.percentile(self.visual_map,99.)
            assert count_max > count_min
            self.imgplot.set_clim(count_min, count_max + 1)
            self.fig2d.canvas.draw()
        except Exception, err:
            print "Failed to update figure:", err            
        finally:       
            Measurement.on_display_update_timer(self)

    