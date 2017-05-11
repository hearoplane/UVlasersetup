'''
Created on Jan 6, 2015

@author: aamrein
'''
import numpy as np
import time
import datetime
import os
import scipy.signal
from scipy.optimize import curve_fit
import pickle

from .measurement import Measurement
from equipment.newport_esp300 import ESP300

class MeasureLever(Measurement):
    name = "Measure Lever"
    display_update_period = 0.2 #seconds
    
    def setup(self):
        # logged quantities
        self.esp300_connectivity = self.add_logged_quantity(name="Newport controller connectivity", dtype=bool, ro=False)
        self.lower_frequency = self.add_logged_quantity(name="Lower frequency", initial=10, dtype=int, fmt='%2d',
                                                           ro=False, unit='kHz', vmin=1, vmax=99)
        self.upper_frequency = self.add_logged_quantity(name="Upper frequency", initial = 400, dtype=int, fmt='%3d',
                                                           ro=False, unit='kHz', vmin=1, vmax=999)
        self.fit_width = self.add_logged_quantity(name="Fit width", initial=30, dtype=int, fmt='%3d',
                                                           ro=False, unit='kHz', vmin=1, vmax=99)
        
        self.number_of_averages = self.add_logged_quantity(name='Number of averages', initial = 10, dtype=int, fmt='%2d',
                                                           ro=False, unit='', vmin=1, vmax=99)
        
        #connect events
        self.gui.ui.LeverDetection_measure_lever_pushButton.clicked.connect(self.start)
        self.gui.ui.LeverDetection_regulate_horizontal_pushButton.clicked.connect(self.regulateHorizontal)
        self.gui.ui.LeverDetection_regulate_vertical_pushButton.clicked.connect(self.regulateVertical)
        
        #self.esp300_connectivity.connect_bidir_to_widget(self.gui.ui.LeverDetection_newport_controller_connected_checkBox)
        #self.esp300_connectivity.hardware_set_func = self.setNewportControllerConnection
        
        self.lower_frequency.connect_bidir_to_widget(self.gui.ui.LeverDetection_lower_frequency_doubleSpinBox)
        self.upper_frequency.connect_bidir_to_widget(self.gui.ui.LeverDetection_upper_frequency_doubleSpinBox)
        self.fit_width.connect_bidir_to_widget(self.gui.ui.LeverDetection_fit_width_doubleSpinBox)
        self.number_of_averages.connect_bidir_to_widget(self.gui.ui.LeverDetection_number_of_averages_doubleSpinBox)
        
        
        
        
    def setNewportControllerConnection(self, setTo):
        if setTo == False:
            self.esp.close()
        else:
            try:
                self.esp = ESP300(debug=False)
            except:  # bad style
                pass # already connected    
        
    def measureNormalizedDeflection(self, defl_channel):
        rec_time = 0.005
        coupling = "DC"
        VRange = 20
        f_s_des = 2000
        f_sampling, N_samples = self.gui.lever_detection.initializePicoScope(rec_time, f_s_des, defl_channel, coupling, VRange)
        self.gui.lever_detection.acquireDataPicoScope(defl_channel, f_sampling, N_samples)
        defl = np.mean(self.gui.lever_detection.s)
        f_sampling, N_samples = self.gui.lever_detection.initializePicoScope(rec_time, f_s_des, "B", coupling, VRange)
        self.gui.lever_detection.acquireDataPicoScope("B", f_sampling, N_samples)
        defl /= np.mean(self.gui.lever_detection.s)
        return defl  
        
    def regulateHorizontal(self):
        self.regulateDeflection(defl_channel="C", axis=2, slope0=10, tol=0.05)
    
    def regulateVertical(self):
        self.regulateDeflection(defl_channel="A", axis=3, slope0=-10, tol=0.05)
        
    def regulateDeflection(self, defl_channel="A" , axis=3, slope0=-10, tol=0.05):
        # Algorithm is designed for a non-normalized deflection signal
        # slope0 must at least have the right sign for the algorithm to work 
        # measure deflection
        
        defl_new = self.measureNormalizedDeflection(defl_channel)
        
        # regulate deflection if not close to zero
        fix_step = 0.1  # [mm]
        min_abs_slope = 7.5 # maximum slope [mm^-1]
        min_abs_step = 0.01 # [mm] too small steps lead to random slope
        
        if abs(defl_new)>tol:
            i = 0
            maxIter = 20
            slope = slope0    # initial guess for slope [mm^-1]
            damping = 0.3   # damping in [0,1]
#             esp = ESP300(debug=False)
            if axis==3:
                getPos = self.esp.getPosAx3
                moveRel = self.esp.moveRelAx3
            elif axis==2:
                getPos = self.esp.getPosAx2
                moveRel = self.esp.moveRelAx2
            else:
                raise ValueError("Invalid ESP300 axis number.")
            
            pos_new = getPos()
            while abs(defl_new)>tol and i<maxIter:
                i += 1
#                 print "Deflection %1.3f, slope %1.2f" %(defl_new, slope) 
                if slope*slope0 > 0:    # laser spot hits both halves of the diode
                    slope = max(abs(slope), min_abs_slope) * np.sign(slope)
                    step =  - defl_new / slope * (1-damping)
                else: # not in the linear region (flip sign)
                    step =  -fix_step*np.sign(defl_new)*np.sign(slope0)
   
#                 print "step %1.3f" %step                
                step = np.sign(step) * max(abs(step), min_abs_step)    
                moveRel(step)
                pos_old = pos_new
                pos_new = getPos()  
                defl_old = defl_new
                defl_new = self.measureNormalizedDeflection(defl_channel)
                if pos_new != pos_old:
                    slope = (defl_new-defl_old)/(pos_new-pos_old)
              
        if axis==3: deflection = 'Vertical'
        elif axis==2: deflection = 'Horizontal'
        print deflection, "regulated to %2.1f%%" %(defl_new*100)
    
    def measureSpectrum(self, channel, f_sampling, N_samples, N_average, windowing = False, on_lever=True):
        self.plot_measure = False   # do not plot spectrum on chip
        # number of positive frequencies in spectrum
        if N_samples % 2 == 0: N_pos = N_samples / 2 + 1
        else: N_pos = (N_samples + 1) / 2
            
        self.mag_avg = np.zeros(N_pos)
        print "FFT number:",
        for i in xrange(N_average):
            self.gui.lever_detection.acquireDataPicoScope(channel, f_sampling, N_samples)
            signal = self.gui.lever_detection.s
            if i<N_average-1: print str(i+1)+",",
            else: print i+1
            
            self.f = np.fft.rfftfreq(len(signal), 1/f_sampling)
            if windowing:   # normalized windowed FFT
                w = np.blackman(len(signal))
                self.mag_avg = (i*self.mag_avg+np.abs(np.fft.rfft(w * signal))/np.sqrt(len(signal)))/ (i+1)
            else:   # normalized FFT
                self.mag_avg = (i*self.mag_avg+np.abs(np.fft.rfft(signal))/np.sqrt(len(signal)))/ (i+1)
            if on_lever: self.plot_measure = True    # data ready to be plotted

        return (self.f, self.mag_avg)
    
    def getSpectrum(self, lever_nb, on_lever=True):
        channel = "A"
        coupling = "AC"
        VRange = 0.05   # [V]
        f_s_des = int(5E6) # desired sampling frequency
        rec_time = float(1E6) / f_s_des
        N_average = self.number_of_averages.val  # number of spectrum averages
        f_sampling, N_samples = self.gui.lever_detection.initializePicoScope(rec_time, f_s_des, channel, coupling, VRange)
        f_lever, mag_lever = self.measureSpectrum(channel, f_sampling, N_samples, N_average, windowing=False, on_lever=on_lever)
        self.saveToDict('measurement_datetime'+str(lever_nb), datetime.datetime.now())
        
        return (f_lever, mag_lever)
    
    def measureSum(self, lever_nb):
        rec_time = 0.005        
        channel = "B"
        coupling = "DC"
        VRange = 20
        f_s_des = 2000
        f_sampling, N_samples = self.gui.lever_detection.initializePicoScope(rec_time, f_s_des, channel, coupling, VRange)
        self.gui.lever_detection.acquireDataPicoScope(channel, f_sampling, N_samples)
        sum_lever = np.mean(self.gui.lever_detection.s)
        self.gui.lever_detection.sum_lever.update_value(sum_lever)
        self.saveToDict('sum_lever'+str(lever_nb), sum_lever)
    
    def moveToChip(self, alpha):
        x,y = self.gui.lever_detection.getPosXY_mm()
        Delta = 0.5     # [mm]
        x_target = x - Delta * np.sin(alpha)
        y_target = y + Delta * np.cos(alpha) 
        self.gui.lever_detection.moveToXY_mm_backlash(x_target, y_target)
        
    def detectSpectrumPeak(self, f_lever, mag_lever, mag_chip):
        mag_diff = mag_lever - mag_chip
        mag_diff += 1.1 * np.abs(min(mag_diff))
        
        # eliminate sharp peaks
        Delta_f = np.mean(np.diff(f_lever)) # frequency resolution
        N = int(125 / Delta_f)   # kernel size = 125 Hz
        rect = np.ones(N) / N
        mag_diff_maf = scipy.signal.fftconvolve(mag_diff, rect, 'same') # moving average filtered
        
        # peak in range of interest
        lower = self.lower_frequency.val * 1000
        upper = self.upper_frequency.val * 1000
        idx_peak = np.argmax([mag_diff_maf[i]*(f_lever[i]>lower and f_lever[i]<upper) for i in range(len(f_lever))])
        f_peak = f_lever[idx_peak]
        print f_peak
        
        return f_peak
    
    
    def SOHAmpWhite(self, x, DC, f0, Q, WN):
        f0x = f0 / x
        return np.sqrt((DC*f0x)**2 / ((f0x - 1/f0x)**2 + 1/Q**2) + WN**2)
    
    def fitSpectrum(self, f_lever, mag_lever, f_peak, lever_nb):
        # fit aplitude of simple harmonic oscillator (SOH) driven by white noise (WN)
         
        fit_center = f_peak
        fit_width = self.fit_width.val*1000
        p_guess = (1E-3, fit_center, 150, 1E-3) # initial parameters
        self.f_fit = np.array([x for x in f_lever if (x>fit_center-fit_width/2 and x<fit_center+fit_width/2)])
        mag_fit = np.array([mag_lever[i] for i in range(len(mag_lever)) if 
                            f_lever[i]>fit_center-fit_width/2 and f_lever[i]<fit_center+fit_width/2]) 
        p_opt, corr = curve_fit(self.SOHAmpWhite, self.f_fit,  mag_fit, p0=p_guess)
         
        print "Fit variance", np.diag(corr)
        print 'p_opt', p_opt
        
        DC_fit = p_opt[0]
        f0_fit = p_opt[1]
        Q_fit  = p_opt[2]
        WN_fit = p_opt[3]
        
        SNR = np.sqrt(DC_fit**2*Q_fit**2 + WN_fit**2) / WN_fit
                     
        self.gui.lever_detection.resonance_frequency.update_value(f0_fit / 1000)
        self.gui.lever_detection.quality_factor.update_value(Q_fit)
        self.gui.lever_detection.signal_to_noise_ratio.update_value(SNR)
        
        self.mag_fitted = [self.SOHAmpWhite(x, DC_fit, f0_fit, Q_fit, WN_fit) for x in self.f_fit]
        self.plot_fit = True # Fit ready to be plotted
        
        self.saveToDict('fit_width'+str(lever_nb), fit_width)
        self.saveToDict('spectrum_lever'+str(lever_nb), mag_lever[::100])
        self.saveToDict('f_lever'+str(lever_nb), f_lever[::100])
        self.saveToDict('spectrum_fit'+str(lever_nb), p_opt)
        self.saveToDict('SNR'+str(lever_nb), SNR)
    
    def _run(self):
        # plot flags
        self.plot_measure, self.plot_fit, self.fit_plotted, self.start_flag, self.end_flag = False, False, False, True, False
        self.gui.lever_detection.lever_nb.read_from_hardware()
        lever_nb = self.gui.lever_detection.lever_nb.val
        alpha = self.gui.lever_detection.lever_angle.val
        
        # adjust deflection
        self.regulateVertical()
        self.regulateHorizontal()
        self.regulateVertical()
        
        # measure sum on lever
        self.measureSum(lever_nb)
        
        # measure spectrum of lever
        f_lever, mag_lever = self.getSpectrum(lever_nb, on_lever=True)
        
        # move from lever to chip to obtain reference spectrum
        self.moveToChip(alpha)
        
        # adjust deflection
        self.regulateVertical()
        self.regulateHorizontal()
        self.regulateVertical()
        
        # measure spectrum of lever
        _, mag_chip = self.getSpectrum(lever_nb, on_lever=False)
        
        # go back to Lever
        self.gui.lever_detection.gotoLever(lever_nb)
        
        f_peak = self.detectSpectrumPeak(f_lever, mag_lever, mag_chip)
        
        self.fitSpectrum(f_lever, mag_lever, f_peak, lever_nb)
        
        t0 = time.clock()
        while (not self.fit_plotted) and time.clock()-t0 < 2:
            time.sleep(0.1)
        
        self.end_flag = True
            
    def saveToDict(self, key, val):
        if not key in self.gui.lever_detection.data_dict:
            self.gui.lever_detection.data_dict[key] = [val]
        else:
            self.gui.lever_detection.data_dict[key].append(val)           
    
    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.LeverDetection_measure_lever_pushButton)
        
        if self.plot_measure:
            N_plot = 100
            f_plot = self.f[::N_plot]
            mag_avg_plot = self.mag_avg[::N_plot]
            self.gui.lever_detection.plotline1_41.set_data(f_plot, mag_avg_plot)
            self.gui.lever_detection.ax1_4.set_xlim([min(f_plot), max(f_plot)])
            self.gui.lever_detection.ax1_4.set_ylim([min(mag_avg_plot), max(mag_avg_plot)])
            
        if self.plot_fit:
            N_plot_fit = 10
            f_fit_plot = self.f_fit[::N_plot_fit]
            mag_fit_plot = self.mag_fitted[::N_plot_fit]
            self.gui.lever_detection.plotline1_42.set_data(f_fit_plot, mag_fit_plot)
            self.gui.lever_detection.ax1_4.set_xlim([min(self.f_fit)/10, max(self.f_fit)*10])
            self.gui.lever_detection.ax1_4.set_ylim([min(mag_fit_plot)/5, max(mag_fit_plot)*5])  # in case autoscale fails
            self.fit_plotted = True
                
        self.gui.lever_detection.ax1_4.relim()
#         self.gui.lever_detection.ax1_4.autoscale_view(scalex=True, scaley=True)            
        self.gui.lever_detection.fig1.canvas.draw()
        
        if self.end_flag:
            self.markButton(self.gui.ui.LeverDetection_measure_lever_pushButton, on=False)

class MeasureAll(Measurement):
    name = "Measure All"
    display_update_period = 0.2 # seconds
    
    def setup(self):
        self.gui.ui.SingleMeasurements_measure_all_pushButton.clicked.connect(self.start)
        
        self.number_of_measurements = self.add_logged_quantity(name='Number of measurements', initial = 1, dtype=int, fmt='%2d',
                                                           ro=False, unit='', vmin=1, vmax=99)
        self.repositioning = self.add_logged_quantity(name = "Repositioning", dtype=bool, initial=False, ro=False)
        
        self.number_of_measurements.connect_bidir_to_widget(self.gui.ui.Measurements_number_of_measurements_doubleSpinBox)
        self.repositioning.connect_bidir_to_widget(self.gui.ui.Measurements_repositioning_checkBox)
        
    def interrupt(self):
        print "Measurement", self.name, "interrupt"
        self.interrupt_measurement_called = True
        
    def initializeDataDictionary(self):
        # clear if it already exists
        self.gui.lever_detection.data_dict = {}
        
        # long term measurements?
        self.gui.lever_detection.data_dict['long_term'] = False
        
        # read experiment info
        self.gui.lever_detection.box_name = str(self.gui.ui.SingleMeasurements_box_name_lineEdit.text())
        self.gui.lever_detection.experiment_name = str(self.gui.ui.SingleMeasurements_experiment_name_lineEdit.text())
        self.gui.lever_detection.fluid = str(self.gui.ui.SingleMeasurements_fluid_lineEdit.text())
        self.gui.lever_detection.notes = str(self.gui.ui.SingleMeasurements_notes_lineEdit.text())     
        
        self.gui.lever_detection.date_time = datetime.datetime.now()
        self.gui.lever_detection.data_dict["date_time"] = self.gui.lever_detection.date_time
        self.gui.lever_detection.data_dict['box_name'] =  self.gui.lever_detection.box_name
        self.gui.lever_detection.data_dict['experiment_name'] =  self.gui.lever_detection.experiment_name
        self.gui.lever_detection.data_dict['fluid'] =  self.gui.lever_detection.fluid
        self.gui.lever_detection.data_dict['notes'] =  self.gui.lever_detection.notes
        
        self.gui.lever_detection.directory = 'data/' + self.gui.lever_detection.box_name
        self.gui.lever_detection.filename = self.gui.lever_detection.experiment_name + '_' + \
                                            self.gui.lever_detection.fluid + '_' + \
                                            self.gui.lever_detection.date_time.strftime('%Y-%m-%d %H-%M-%S')   
                                            
    def storeData(self):
        # is updating necessary or does overwriting the job? 
        #    pathname = os.path.join(self.gui.lever_detection.directory, self.gui.lever_detection.filename+'.pickle')
        #    with open(pathname, 'rb') as handle:
        #        data_dict = pickle.load(handle)
        #    data_dict.update(self.gui.lever_detection.data_dict)
    
        
        if not os.path.exists(self.gui.lever_detection.directory):
                os.makedirs(self.gui.lever_detection.directory)   
        with open(os.path.join(self.gui.lever_detection.directory,
                               self.gui.lever_detection.filename+'.pickle'), 'wb') as handle:
            # Different protocols available:
            # 0: Ascii, 1: binary (backwards compatible), 2: binary (new style classes)
            pickle.dump(self.gui.lever_detection.data_dict, handle,  protocol=pickle.HIGHEST_PROTOCOL)
            
        print "Data stored."
        
    def _run(self):
        self.start_flag, self.end_flag = True, False
        
        self.initializeDataDictionary()
        
        if not self.interrupt_measurement_called:
            self.gui.lever_detection.start()
            self.mode = 0
            while self.gui.lever_detection.is_measuring():
                time.sleep(0.1)
            time.sleep(1)
            
        self.gui.lever_detection.saveBoxImage(self.gui.lever_detection.img1_copy,
                                              self.gui.lever_detection.directory,
                                              self.gui.lever_detection.filename)

        lever_numbers = [int(f) for f in self.gui.lever_detection.lever_vec_sorted[:, 8]]
        for n in xrange(self.number_of_measurements.val):
            for i in lever_numbers[:1]:
                if not self.interrupt_measurement_called:
                    self.mode = 1
                    self.gui.lever_detection.gotoLever(i)
                    time.sleep(1) 
                if n==0 or self.repositioning.val: 
                    if not self.interrupt_measurement_called:   
                        self.gui.scan.start()
                        self.mode = 2
                        while self.gui.scan.is_measuring():
                            time.sleep(0.1)
                        time.sleep(1)
                        
                    lever_idx = self.gui.lever_detection.getLeverIndex(i)
                    lever_found = self.gui.lever_detection.lever_vec_sorted[lever_idx][5]
                        
                    if lever_found:
                        if not self.interrupt_measurement_called:   
                            self.gui.fineTuneY.start()
                            self.mode = 3
                            while self.gui.fineTuneY.is_measuring():
                                time.sleep(0.1)
                            time.sleep(1)
                        
                        if not self.interrupt_measurement_called:   
                            self.gui.fineTuneX.start()
                            self.mode = 4
                            while self.gui.fineTuneX.is_measuring():
                                time.sleep(0.1)
                            time.sleep(1)
                        
                if not self.interrupt_measurement_called:   
                    self.gui.measureLever.start()
                    self.mode = 5
                    while self.gui.measureLever.is_measuring():
                        time.sleep(0.1)
                    time.sleep(1)
                    
        self.storeData()
        
        self.end_flag = True
                
    def update_display(self):
        if self.start_flag:
            self.markButton(self.gui.ui.SingleMeasurements_measure_all_pushButton)
            self.start_flag = False
        if self.mode == 0:
            self.gui.lever_detection.update_display()
        elif self.mode == 2:
            self.gui.scan.update_display()
        elif self.mode == 3:
            self.gui.fineTuneY.update_display()
        elif self.mode == 4:
            self.gui.fineTuneX.update_display()
        elif self.mode == 5:
            self.gui.measureLever.update_display()
            
        if self.end_flag:
            self.gui.singleMeasurements.displayData(path=os.path.join(self.gui.lever_detection.directory,
                               self.gui.lever_detection.filename+'.pickle'))
            self.gui.ui.SingleMeasurements_lever_nb_doubleSpinBox.setValue(self.gui.lever_detection.lever_nb.val)
            self.gui.singleMeasurements.selectLever()
            self.markButton(self.gui.ui.SingleMeasurements_measure_all_pushButton, on=False)
            
    