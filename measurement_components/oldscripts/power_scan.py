'''
Created on Jun 19, 2014

@author: Edward Barnard
'''
import numpy as np
import time
import threading

from .measurement import Measurement 

PM_SAMPLE_NUMBER = 1

class PowerScanContinuous(Measurement):
    
    name = "power_scan"
    
    def setup(self):
        
        self.display_update_period = 0.050 #seconds
        
        self.gui.ui.power_scan_cont_start_pushButton.clicked.connect(self.start)
        self.gui.ui.power_scan_interrupt_pushButton.clicked.connect(self.interrupt)
        
        # Data arrays
        self.pm_powers = []
        self.out_powers = []
        self.specs = []
        self.ii = 0
        
        self.bg_sub = True
        
        self.detector = 'CCD'


    def setup_figure(self):
        self.fig = self.gui.add_figure('power_scan', self.gui.ui.power_scan_plot_widget)
        self.fig.clf()
        
        self.ax_power = self.fig.add_subplot(212)
        self.ax_spec  = self.fig.add_subplot(211)
        
        self.power_plotline, = self.ax_power.plot([1],[1],'o-')
        self.spec_plotline, = self.ax_spec.plot(np.arange(512), np.zeros(512))
        
    def _run(self):

        self.detector = 'APD'
        #Setup hardware
        if self.detector == 'CCD':
            ccd = self.andor_ccd = self.gui.andor_ccd_hc.andor_ccd
        elif self.detector == 'APD':
            self.apd_counter_hc = self.gui.apd_counter_hc
            self.apd_count_rate = self.gui.apd_counter_hc.apd_count_rate


        t_acq = self.gui.andor_ccd_hc.exposure_time.val #in seconds
        wait_time = 0.05 # wait between check if ccd is done acquisition

    
        # Data arrays
        self.pm_powers = []
        self.out_powers = []
        self.specs = []
        
        try:
            self.ii = 0
            while not self.interrupt_measurement_called:
        
                if self.detector == 'CCD':
                    # start CCD measurement while power meter is acquiring
                    ccd.start_acquisition()

        
                # Sample the power at least one time from the power meter.
                samp_count = 0
                pm_power = 0.0
                for samp in range(0, PM_SAMPLE_NUMBER):
                    # Try at least 10 times before ultimately failing
                    try_count = 0
                    while True:
                        try:
                            pm_power = pm_power + self.gui.thorlabs_powermeter_hc.power.read_from_hardware(send_signal=True)
                            samp_count = samp_count + 1
                            break 
                        except Exception as err:
                            try_count = try_count + 1
                            if try_count > 9:
                                print "failed to collect power meter sample:", err
                                break
                            time.sleep(0.010)
                 
                if samp_count > 0:              
                    pm_power = pm_power/samp_count
                else:
                    print "  Failed to read power"
                    pm_power = 10000.  
                    
                # Store in array  
                self.pm_powers.append(pm_power)
                
                
                # grab spectrum
                #ccd.start_acquisition()
                if self.detector == 'CCD':
                    stat = ccd.get_status()
                    print "stat", stat
                    while stat == 'ACQUIRING':
                        time.sleep(wait_time)            
                        stat = ccd.get_status()
                        if self.interrupt_measurement_called:
                            break
    
                    if stat == 'IDLE':
                        # grab spec data
                        buffer_ = ccd.get_acquired_data()
                        
                        if self.bg_sub:
                            bg = self.gui.andor_ccd_hc.background
                            if bg is not None:
                                if bg.shape == buffer_.shape:
                                    buffer_ = buffer_ - bg
                                else:
                                    print "Background not the correct shape", buffer_.shape, bg.shape
                            else:
                                print "No Background available, raw data shown"
                        self.spectrum_data = np.average(buffer_, axis=0)
                        
                    else:
                        raise ValueError("andor_ccd status should be 'IDLE', is '%s'" % stat)            
                            
                                      
                    # store spectrum in array
                    self.specs.append( self.spectrum_data )
                    self.out_powers.append( np.sum(self.spectrum_data)) 
                
                # grab apd count?
                elif self.detector == 'APD':
                    self.apd_count_rate.read_from_hardware()
                    self.out_powers.append( self.apd_count_rate.val )
                
                if self.ii % 10 == 0:
                    print self.ii, self.pm_powers[-1], self.out_powers[-1]
                
                self.ii += 1
        finally:
            #save data file
            save_dict = {
                         'pm_powers': self.pm_powers,
                         'out_powers': self.out_powers,
                         'N': self.ii,
                         'spectra': self.specs,
                         'bg_spec': self.gui.andor_ccd_hc.background,
                         'detector': self.detector,
                         }
            for lqname,lq in self.gui.logged_quantities.items():
                save_dict[lqname] = lq.val
            
            for hc in self.gui.hardware_components.values():
                for lqname,lq in hc.logged_quantities.items():
                    save_dict[hc.name + "_" + lqname] = lq.val
            
            for lqname,lq in self.logged_quantities.items():
                save_dict[self.name +"_"+ lqname] = lq.val

            self.fname = "%i_power_scan.npz" % time.time()
            np.savez_compressed(self.fname, **save_dict)
            print "Power Scan Saved", self.fname

            if not self.interrupt_measurement_called:
                self.measurement_sucessfully_completed.emit()
            else:
                pass
    
    
    def update_display(self):        
        #print "updating figure"
        self.power_plotline.set_data(self.pm_powers[:self.ii], self.out_powers[:self.ii])
        self.ax_power.relim()
        self.ax_power.autoscale_view(scalex=True, scaley=True)
        if self.detector == 'CCD':
            self.spec_plotline.set_ydata(self.specs[-1])
            self.ax_spec.relim()
            self.ax_spec.autoscale_view(scalex=False, scaley=True)

        self.fig.canvas.draw()
