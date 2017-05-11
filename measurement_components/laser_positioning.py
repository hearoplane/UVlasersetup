'''
Created on Jan 6, 2015

@author: dziegler
'''

import numpy as np
import time
from scipy.special import erf
from scipy.optimize import curve_fit

from .measurement import Measurement

class Scan(Measurement):
    name= "Scan"
    display_update_period = 0.2 #seconds
    
    def setup(self):        
        #connect events
        self.gui.ui.LeverDetection_scan_pushButton.clicked.connect(self.start)
        
    def acquireDataAndMoveLine(self, scan_width, alpha):
        self.gui.lever_detection.ps.runBlock()
        time.sleep(0.25)
        # zero-backlash-move
        self.gui.lever_detection.moveRelXY_mm(-scan_width*np.cos(alpha),
                                              -scan_width*np.sin(alpha))
        if self.gui.lever_detection.ps.isReady() == True:
            print "Recording time too short."
        while self.gui.lever_detection.ps.isReady() == False:
            time.sleep(0.01)
            
        self.sum_sweep = self.gui.lever_detection.ps.getDataV(self.channel, numSamples=self.N_samples, startIndex=0,
                                                              downSampleRatio=1, downSampleMode=1, segmentIndex=0,
                                                              returnOverflow=False, exceptOverflow=True,
                                                              dataV=None, dataRaw=None)
                                                              
        self.plot_sweep = True
        
#         self.gui.lever_detection.ps.stop()
        
    def initializeDataAcquisitionForSweep(self):
        self.channel = "B"
        coupling = "DC"
        f_s_des = 2000  # desired sampling rate [Hz]
        calib = 10  # calibration constant
        rec_time = calib * self.scan_width/self.gui.stage_hc.stage.v_max_x    # [s]
        VRange = 20
        
        self.f_sampling, self.N_samples = \
            self.gui.lever_detection.initializePicoScope(rec_time, f_s_des, self.channel, coupling, VRange)
    
    def sweepWidth(self, alpha):
        self.plot_measure = False
        x,y = self.gui.lever_detection.getPosXY_mm()
        x_start_line = x + (self.scan_width/2)*np.cos(alpha)
        y_start_line = y + (self.scan_width/2)*np.sin(alpha)
        self.gui.lever_detection.moveToXY_mm(x_start_line, y_start_line)

        self.acquireDataAndMoveLine(self.scan_width, alpha)

        self.gui.lever_detection.moveToXY_mm(x,y)        
        
    def scanWidth(self, scan_width, step, alpha):
        channel = "B"
        coupling = "DC"
        rec_time = 0.01
        VRange = 20
        f_s_des = 1800
#         daq = self.gui.lever_detection.initializeZI()
        f_sampling, N_samples = \
            self.gui.lever_detection.initializePicoScope(rec_time, f_s_des, channel, coupling, VRange)
            
        x,y = self.gui.lever_detection.getPosXY_mm()
        self.x_start_line = x + (scan_width/2)*np.cos(alpha)
        self.y_start_line = y + (scan_width/2)*np.sin(alpha)
        
        N = int(scan_width/step) + 1
        self.sum_signal = []
        self.dist_vec = np.linspace(0, scan_width, N)
        for i in xrange(N):
            self.gui.lever_detection.moveToXY_mm_backlash(self.x_start_line-self.dist_vec[i]*np.cos(alpha),
                                                          self.y_start_line-self.dist_vec[i]*np.sin(alpha))
            self.gui.lever_detection.acquireDataPicoScope(channel, f_sampling, N_samples)
#             _, s = self.gui.lever_detection.acquireDataZI(daq, rec_time)
            self.sum_signal.append(np.mean(self.gui.lever_detection.s))
            self.plot_measure = True # data ready to be plotted
            
        self.sum_signal = np.array(self.sum_signal)
        
        sum_signal_max_idx = np.argmax(self.sum_signal)
        # store absolute location of maximum
        self.x_max = self.x_start_line - self.dist_vec[sum_signal_max_idx]*np.cos(alpha)
        self.y_max = self.y_start_line - self.dist_vec[sum_signal_max_idx]*np.sin(alpha)
        
        self.gui.lever_detection.moveToXY_mm_backlash(x, y)
        
    def leverDetectedDuringSweep(self, sum_threshold, lever_width):
        # check if ratio between lowest and highest values and is big enough 
        hist, _ = np.histogram(self.sum_sweep, bins=10)
        hist_ratio = float(hist[0])/hist[-1]
        nominal_ratio = len(self.sum_sweep)/(self.f_sampling * lever_width/self.gui.stage_hc.stage.v_max_x)
        print "hist_ratio = %.1f, nominal = %.1f" %(hist_ratio, nominal_ratio/5)
        # checks whether the lever has been detected during sweep
        if max(self.sum_sweep) > sum_threshold and hist_ratio> nominal_ratio/10:
            return True
        else:
            return False
            
        
    def interrupt(self):
        print "measurement", self.name, "interrupt inside scan"
        self.interrupt_measurement_called = True
                
    def _run(self):
        # plot flags, clear subplot
        self.plot_sweep, self.plot_measure, self.button_marked, self.start_flag, self.end_flag = False, False, False, True, False

        self.gui.lever_detection.lever_nb.read_from_hardware()  # in case of manual moves before scan
        lever_nb = self.gui.lever_detection.lever_nb.val
        alpha = self.gui.lever_detection.lever_angle.val
        lever_width = self.gui.lever_detection.nominal_lever_width.val / 1000 # [mm]
        lever_length = self.gui.lever_detection.nominal_lever_length.val / 1000 # [mm]
        sum_threshold = self.gui.lever_detection.sum_threshold.val  # [V]
        
        # define search space
        self.scan_width = 0.5    # [mm]
        scan_length = 0.5   # [mm]
        stepX = lever_width * 1/2.0
        stepY = lever_length / 2
        
        # scan the full search space or until lever is found
        lever_found = False
        M = int(scan_length/stepY) + 1
        dist_vec_y = np.linspace(0, scan_length, M)
        
        x0, y0 = self.gui.lever_detection.getPosXY_mm()   # nominal position after computer vision algorithm

        x_start = x0 + scan_length/2 * np.sin(alpha)
        y_start = y0 - scan_length/2 * np.cos(alpha)
        
        self.initializeDataAcquisitionForSweep()
        for i in xrange(M):
            if not self.interrupt_measurement_called:
                self.gui.lever_detection.moveToXY_mm(x_start - dist_vec_y[i]*np.sin(alpha),
                                                              y_start + dist_vec_y[i]*np.cos(alpha))
                self.sweepWidth(alpha)
                if self.leverDetectedDuringSweep(sum_threshold, lever_width):
                    self.scanWidth(self.scan_width, stepX, alpha)
                    if max(self.sum_signal) > sum_threshold:
                        lever_found = True
                        self.gui.lever_detection.data_dict["sum_sweep"+str(lever_nb)] = self.sum_sweep
                        self.gui.lever_detection.data_dict["sweep_fs"+str(lever_nb)] = self.f_sampling
                        lever_idx = self.gui.lever_detection.getLeverIndex(lever_nb)
                        self.gui.lever_detection.lever_vec_sorted[lever_idx][5] = lever_found
                        # goto Maximum, ready for FineTune                
                        self.gui.lever_detection.moveToXY_mm_backlash(self.x_max, self.y_max)
                        self.gui.lever_detection.updateCurrentLeverPos(self.x_max, self.y_max)
                        break
                    else:
                        # redo sweep further down, because we are at the tip of the lever
                        continue
                        print "scan exception"
        
        if not lever_found:
            print "Lever " + str(lever_nb) + " not found." 
            
        self.end_flag = True

    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.LeverDetection_scan_pushButton)
            self.start_flag = False
        
        if self.plot_sweep:  
            N = len(self.sum_sweep)
            t_sweep = np.linspace(0, (N-1)/self.f_sampling, N)
            self.gui.lever_detection.plotline1_11.set_data(t_sweep[:N], self.sum_sweep[:N])
            # clear fit
            self.gui.lever_detection.plotline1_22.set_data([0,0], [0,0])
            self.gui.lever_detection.plotline1_23.set_data([0,0], [0,0])
                          
            self.gui.lever_detection.ax1_1.set_xlim([0, max(t_sweep)])
            self.gui.lever_detection.ax1_1.set_ylim([min(self.sum_sweep)-max(self.sum_sweep)*0.1, max(self.sum_sweep)*1.1])
            self.gui.lever_detection.ax1_1.relim()          
            self.gui.lever_detection.fig1.canvas.draw()        
        
        if self.plot_measure:
            N = len(self.sum_signal)
            self.gui.lever_detection.plotline1_21.set_data(self.dist_vec[:N] * 1000, self.sum_signal[:N])
                            
            self.gui.lever_detection.ax1_2.set_xlim([0, self.scan_width*1000])
            self.gui.lever_detection.ax1_2.set_ylim([min(self.sum_signal)-max(self.sum_signal)*0.1, max(self.sum_signal)*1.1])
            self.gui.lever_detection.ax1_2.relim()    # updates data limits      
            self.gui.lever_detection.fig1.canvas.draw()
            
        if self.end_flag:
            self.markButton(self.gui.ui.LeverDetection_scan_pushButton, on=False)
         
class FineTuneX(Measurement):
    name = "Fine Tune X"
    display_update_period = 0.2 #seconds
    
    def setup(self):
        #connect events
        self.gui.ui.LeverDetection_fine_tune_x_pushButton.clicked.connect(self.start)

    def fitWidth(self, scan_width, alpha, lever_nb):
        x,y = self.gui.lever_detection.getPosXY_mm()
        x_start = x + (scan_width/2)*np.cos(alpha)
        y_start = y + (scan_width/2)*np.sin(alpha)
        
        self.gui.lever_detection.data_dict["sum_signal_x"+str(lever_nb)] = self.gui.scan.sum_signal
        self.gui.lever_detection.data_dict["dist_vec_x"+str(lever_nb)] = self.gui.scan.dist_vec 
        
        # find center of lever (coarse)
        half = (max(self.gui.scan.sum_signal) + min(self.gui.scan.sum_signal)) / 2
        N = len(self.gui.scan.sum_signal)
        idx1 = np.arange(N)[self.gui.scan.sum_signal > half][0]
        idx2 = np.arange(N)[self.gui.scan.sum_signal > half][-1]
        
        edge1 = np.interp(half, self.gui.scan.sum_signal[idx1-1:idx1+1], self.gui.scan.dist_vec[idx1-1:idx1+1])
        edge2 = np.interp(half, self.gui.scan.sum_signal[idx2:idx2+2], self.gui.scan.dist_vec[idx2:idx2+2])
        center = (edge1 + edge2) / 2        
        
        dist_vec_left = self.gui.scan.dist_vec[self.gui.scan.dist_vec <= center]
        dist_vec_right = self.gui.scan.dist_vec[self.gui.scan.dist_vec >= dist_vec_left[-1]]
        sum_signal_left = self.gui.scan.sum_signal[self.gui.scan.dist_vec <= center]
        sum_signal_right = self.gui.scan.sum_signal[self.gui.scan.dist_vec >= dist_vec_left[-1]]            
        
        # find lever edge and laser spot size (error function curve fit)
        def gaussian_CDF_left(x, mu, sigma):
            scale = max(sum_signal_left) - min(sum_signal_left)   # self.noise_mean
            return scale * 0.5 * (1 + erf((x-mu)/(sigma*np.sqrt(2)))) + min(sum_signal_left)
        
        def gaussian_CDF_right(x, mu, sigma):
            scale = max(sum_signal_right) - min(sum_signal_right)   # self.noise_mean
            return scale * 0.5 * (1 + erf((x-mu)/(sigma*np.sqrt(2)))) + min(sum_signal_right)
        
        p_guess_left = (scan_width/2, 0.01)
        p_guess_right = (-scan_width/2, 0.01)
        p_opt_left, _ = curve_fit(gaussian_CDF_left, dist_vec_left, sum_signal_left, p0=p_guess_left)
        p_opt_right, _ = curve_fit(gaussian_CDF_right, -dist_vec_right, sum_signal_right, p0=p_guess_right) # decreasing function -> minus sign
        
        mu_left, sigma_left = p_opt_left
        mu_right, sigma_right = -p_opt_right[0], p_opt_right[1] # decreasing function -> minus sign
        
        self.gui.lever_detection.data_dict['fine_tune_x_fit'+str(lever_nb)] = \
                                                (mu_left, sigma_left, mu_right, sigma_right)
        
        N_points = 100
        self.x_left = np.linspace(dist_vec_left[0], dist_vec_left[-1], N_points)
        self.x_right = np.linspace(dist_vec_right[0], dist_vec_right[-1], N_points)
        self.fit_left = [gaussian_CDF_left(x, mu_left, sigma_left) for x in self.x_left]
        self.fit_right = [gaussian_CDF_right(-x, -mu_right, sigma_right) for x in self.x_right]
        self.plot_fit = True # Fit is ready to be plotted

        # find center of lever using fitted data (mean corresponds to 50% light on lever)
        center_fit = (mu_left + mu_right) / 2   # minus 
        if center_fit<0 or center_fit>scan_width:
            print "rough edges:", edge1*1E3, edge2*1E3
            print "mu", mu_left*1E3, mu_right*1E3
            print "sigma", sigma_left*1E3, sigma_right*1E3
            self.gui.lever_detection.gotoLever(lever_nb)
            raise ValueError("Fit error.")

        x_center = x_start - center_fit*np.cos(alpha)
        y_center = y_start - center_fit*np.sin(alpha)
        
        measured_lever_width = mu_right - mu_left
        sigma = (sigma_left + sigma_right) / 2
        spot_size = 2 * np.sqrt(2*np.log(2)) * sigma    # FWHM
        
        self.gui.lever_detection.lever_width.update_value( measured_lever_width *1000)
        self.gui.lever_detection.spot_size.update_value(spot_size * 1000)
        self.gui.lever_detection.data_dict['spot_size'+str(lever_nb)] = spot_size
        self.gui.lever_detection.data_dict['measured_lever_width'+str(lever_nb)] = measured_lever_width
        
        # update lever position and move there
        self.gui.lever_detection.moveToXY_mm_backlash(x_center, y_center)
        self.gui.lever_detection.updateCurrentLeverPos(x_center, y_center)
        
        # wait for fit to be plotted
        t0 = time.clock()
        while (not self.fit_plotted) and time.clock()-t0 < 3:    
            time.sleep(0.1)
                    
    def _run(self):
        # plot flags, clear figure
        self.gui.scan.plot_measure, self.plot_fit, self.fit_plotted, self.start_flag, self.end_flag = False, False, False, True, False
                
        self.gui.lever_detection.lever_nb.read_from_hardware()
        lever_nb = self.gui.lever_detection.lever_nb.val
        alpha = self.gui.lever_detection.lever_angle.val
        lever_width = self.gui.lever_detection.nominal_lever_width.val / 1000  # [mm]
        
        self.scan_width = 5 * lever_width
        step = lever_width / 6
        
        if not self.interrupt_measurement_called:
            self.gui.scan.scanWidth(self.scan_width, step, alpha)
            self.fitWidth(self.scan_width, alpha, lever_nb)     
            
        self.end_flag = True

    def update_display(self): #!! this function name is used already?? 
        if self.start_flag:
            self.markButton(self.gui.ui.LeverDetection_fine_tune_x_pushButton)
        if self.gui.scan.plot_measure:
            N = len(self.gui.scan.sum_signal)
            self.gui.lever_detection.plotline1_21.set_data(self.gui.scan.dist_vec[:N] * 1000, self.gui.scan.sum_signal[:N])
            # clear fit
            self.gui.lever_detection.plotline1_22.set_data([0,0], [0,0])
            self.gui.lever_detection.plotline1_23.set_data([0,0], [0,0])
            
            if self.plot_fit:
                self.gui.lever_detection.plotline1_22.set_data(self.x_left* 1000, self.fit_left)
                self.gui.lever_detection.plotline1_23.set_data(self.x_right *1000, self.fit_right)
                self.fit_plotted = True
                
            self.gui.lever_detection.ax1_2.set_xlim([0, self.scan_width*1000])
            self.gui.lever_detection.ax1_2.set_ylim([min(self.gui.scan.sum_signal)-max(self.gui.scan.sum_signal)*0.1,
                                                   max(self.gui.scan.sum_signal)*1.1])
            self.gui.lever_detection.ax1_2.relim()    # updates data limits    
#             self.gui.lever_detection.ax1_2.autoscale_view(scalex=True, scaley=True)       
            self.gui.lever_detection.fig1.canvas.draw()
            
        if self.end_flag:
            self.markButton(self.gui.ui.LeverDetection_fine_tune_x_pushButton, on=False)

class FineTuneY(Measurement):
    name = "Fine Tune Y"
    display_update_period = 0.2 #seconds
    
    def setup(self):
        #connect events
        self.gui.ui.LeverDetection_fine_tune_y_pushButton.clicked.connect(self.start)
        
    def scanLength(self, scan_length, step, alpha, lever_nb):
        x,y = self.gui.lever_detection.getPosXY_mm()
        x_start = x + self.scan_length * (0.9) * np.sin(alpha)
        #0.6 + self.gui.lever_detection.rel_pos_laser[lever_nb-1])
        y_start = y - self.scan_length * (0.9) * np.cos(alpha)
        self.gui.lever_detection.moveToXY_mm_backlash(x_start, y_start)
        
        channel = "B"
        coupling = "DC"
        VRange = 20
        rec_time = 0.01  # [s]
        f_s_des = 1800  # desired sampling rate [Hz]
        f_sampling, N_samples = self.gui.lever_detection.initializePicoScope(rec_time, f_s_des, channel, coupling, VRange)
        N = int(scan_length/step)+1
        self.sum_signal = []
#         daq = self.gui.lever_detection.initializeZI()
        self.dist_vec = np.linspace(0, self.scan_length, N)
        for i in xrange(N):
            self.gui.lever_detection.moveToXY_mm_backlash(x_start - self.dist_vec[i]*np.sin(alpha),
                                                          y_start + self.dist_vec[i]*np.cos(alpha))
#             _, s = self.gui.lever_detection.acquireDataZI(daq, rec_time)
            self.gui.lever_detection.acquireDataPicoScope(channel, f_sampling, N_samples)
            self.sum_signal.append(np.mean(self.gui.lever_detection.s))
            self.plot_measure = True # sum_signal nonempty
            
        self.gui.lever_detection.data_dict["sum_signal_y"+str(lever_nb)] = self.sum_signal
        self.gui.lever_detection.data_dict["dist_vec_y"+str(lever_nb)] = self.dist_vec 
    
    def fitLength(self, scan_length, lever_length, rel_pos, alpha, lever_nb): 
        x,y = self.gui.lever_detection.getPosXY_mm()
        x_start = x + scan_length * (0.9) * np.sin(alpha)
        y_start = y - scan_length * (0.9) * np.cos(alpha) 
        
        # find lever edge and laser spot size (error function curve fit)
        def gaussian_CDF(x, mu, sigma):
            scale = max(self.sum_signal) - min(self.sum_signal)
            return scale * 0.5 * (1 + erf((x-mu)/(sigma*np.sqrt(2)))) + min(self.sum_signal)
        
        p_guess = (scan_length/2, 0.01) # initial parameters
        p_opt, _ = curve_fit(gaussian_CDF, self.dist_vec, self.sum_signal, p0=p_guess) #, p0, sigma, absolute_sigma)
        
        
        self.gui.lever_detection.data_dict["fine_tune_y_fit"+str(lever_nb)] = p_opt
        
        # ready to plot
        N_points = 100
        self.x_plot = np.linspace(self.dist_vec[0], self.dist_vec[-1], N_points)
        self.fit = [gaussian_CDF(x, p_opt[0], p_opt[1]) for x in self.x_plot]
        self.plot_fit = True    # Fit ready to be plotted
        
        edge =  p_opt[0]
        
        if edge>0 and edge<scan_length:
            # update lever position and move there
            x_target = x_start - (edge + rel_pos*lever_length)*np.sin(alpha)
            y_target = y_start + (edge + rel_pos*lever_length)*np.cos(alpha)
            self.gui.lever_detection.moveToXY_mm_backlash(x_target, y_target)
            self.gui.lever_detection.updateCurrentLeverPos(x_target, y_target)
        else:
            print "p_opt =", p_opt   
            print "sum_signal_max=", np.max(self.sum_signal)
            self.gui.lever_detection.gotoLever(lever_nb)
            raise ValueError("Fit error.")
        
        # wait for fit to get plotted by other thread
        t0 = time.clock()
        while (not self.fit_plotted) and time.clock()-t0 < 3:    
            time.sleep(0.1)
        
    def _run(self):
        # plot flags
        self.plot_measure, self.plot_fit, self.fit_plotted, self.start_flag, self.end_flag = False, False, False, True, False
        
        self.gui.lever_detection.lever_nb.read_from_hardware()
        lever_nb = self.gui.lever_detection.lever_nb.val
        alpha = self.gui.lever_detection.lever_angle.val
        lever_length = self.gui.lever_detection.nominal_lever_length.val / 1000    # [mm]
        rel_pos = self.gui.lever_detection.relative_position.val  # [-]
        
        self.scan_length = lever_length*2
        step = self.scan_length / 15
            
        if not self.interrupt_measurement_called:
            self.scanLength(self.scan_length, step, alpha, lever_nb)
            self.fitLength(self.scan_length, lever_length, rel_pos, alpha, lever_nb)
            
        self.end_flag = True
        
    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.LeverDetection_fine_tune_y_pushButton)
        
        if self.plot_measure:
            N = len(self.sum_signal)
            self.gui.lever_detection.plotline1_31.set_data(self.dist_vec[:N] * 1000, self.sum_signal[:N])
            if self.plot_fit:
                self.gui.lever_detection.plotline1_32.set_data(self.x_plot* 1000, self.fit)
                self.fit_plotted = True
                
            self.gui.lever_detection.ax1_3.set_xlim([0, self.scan_length*1000])  # in case autoscale fails
            self.gui.lever_detection.ax1_3.set_ylim([min(self.sum_signal)-max(self.sum_signal)*0.1, max(self.sum_signal)*1.1])  # in case autoscale fails
            self.gui.lever_detection.ax1_3.relim()    # updates data limits
#             self.gui.lever_detection.ax1_3.autoscale_view(scalex=True, scaley=True)            
            self.gui.lever_detection.fig1.canvas.draw()
            
        if self.end_flag:
            self.markButton(self.gui.ui.LeverDetection_fine_tune_y_pushButton, on=False)
            
class FineTuneAll(Measurement):
    name = "Fine Tune All"
    display_update_period = 0.2 # seconds
    
    def setup(self):
        self.gui.ui.LeverDetection_fine_tune_all_pushButton.clicked.connect(self.start)
        
    def interrupt(self):
        print "Measurement", self.name, "interrupt"
        self.interrupt_measurement_called = True
        
    def _run(self):
        self.start_flag, self.end_flag = True, False
        lever_numbers = [int(f) for f in self.gui.lever_detection.lever_vec_sorted[:, 8]]
        for i in lever_numbers:
            if not self.interrupt_measurement_called:
                self.mode = 0
                self.gui.lever_detection.gotoLever(i)
                time.sleep(1)
             
            if not self.interrupt_measurement_called:   
                self.gui.scan.start()
                self.mode = 1
                while self.gui.scan.is_measuring():
                    time.sleep(0.1)
                time.sleep(1)
                
            lever_idx = self.gui.lever_detection.getLeverIndex(i)
            lever_found = self.gui.lever_detection.lever_vec_sorted[lever_idx][5]
                
            if lever_found:
                if not self.interrupt_measurement_called:   
                    self.gui.fineTuneY.start()
                    self.mode = 2
                    while self.gui.fineTuneY.is_measuring():
                        time.sleep(0.1)
                    time.sleep(1)
                
                if not self.interrupt_measurement_called:   
                    self.gui.fineTuneX.start()
                    self.mode = 3
                    while self.gui.fineTuneX.is_measuring():
                        time.sleep(0.1)
                    time.sleep(1)
        
        self.end_flag = True        
            
    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.LeverDetection_fine_tune_all_pushButton)
            self.start_flag = False
        if self.mode == 1:
            self.gui.scan.update_display()
        elif self.mode == 2:
            self.gui.fineTuneY.update_display()
        elif self.mode == 3:
            self.gui.fineTuneX.update_display()
        if self.end_flag:
            self.markButton(self.gui.ui.LeverDetection_fine_tune_all_pushButton, on=False)