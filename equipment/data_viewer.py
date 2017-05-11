'''
# This file is used to visualize previously measured data.


Created on Jan 28, 2015

@author: aamrein
'''
from PySide import QtCore
import pickle
import os
import numpy as np
import matplotlib.colors as colors
import matplotlib.pyplot as plt

from PySide.QtGui import QFileDialog

# http://matplotlib.org/users/event_handling.html


class SingleMeasurements(QtCore.QObject):
    def __init__(self, gui):                


        QtCore.QObject.__init__(self)

        self.gui = gui
        
        self.setup_figure()
    
        self.gui.ui.SingleMeasurements_load_pushButton.clicked.connect(self.displayData)
        self.gui.ui.SingleMeasurements_lever_nb_doubleSpinBox.valueChanged.connect(self.selectLever)
        
    def setup_figure(self):
            self.fig1 = self.gui.add_figure("Box Table", self.gui.ui.SingleMeasurements_box_table_groupBox)
            self.fig2 = self.gui.add_figure("Fitted Spectra", self.gui.ui.SingleMeasurements_fitted_spectra_groupBox)
            self.fig3 = self.gui.add_figure("Long Term Behavior", self.gui.ui.SingleMeasurements_long_term_groupBox)
            self.AutoAlignDisplay = self.gui.add_figure("AutoAlign", self.gui.ui.AutoAlign_groupBox)
#             self.fig3 = self.gui.add_figure("Box Image", self.gui.ui.SingleMeasurements_box_image_groupBox, toolbar=False)
            self.fig1.clear()
            self.fig2.clear()
            
            # Axes instance == subplot
            self.ax1_1 = self.fig1.add_subplot(2, 1, 1)
            self.ax1_1.set_axis_off()
            self.ax1_2 = self.fig1.add_subplot(2, 1, 2)
            self.ax1_2.set_axis_off()
            self.ax2_1 = self.fig2.add_subplot(1, 1, 1)
            self.ax3_1 = self.fig3.add_subplot(1, 1, 1)
#             self.ax3_1.grid() 
            self.ax3_2 = self.ax3_1.twinx()
            
            # labeling
            self.ax2_1.set_xlabel("Frequency [kHz]")
            self.ax2_1.set_ylabel("Magnitude [V]")
            
            self.ax3_1.set_xlabel(r"Measurement Number $[-]$")
            self.ax3_1.set_ylabel(r"$f\,[\mathrm{kHz}]$",  color='b')
            self.ax3_2.set_ylabel(r"$Q\,[-]$",  color='g')
            
    def showTable(self):
        self.ax1_2.cla()
        N_entries = 3   # number of entries per lever
        labelsize = 11
        textsize = 12
        aspect = 0.1* self.N_cols/ self.N_rows
        
        # Generate some data...
        pattern = np.zeros((self.N_rows*N_entries, self.N_cols))
        cmap = colors.ListedColormap(['white', 'gainsboro'])
        for i in xrange(self.N_rows*N_entries):
            for j in xrange(self.N_cols):
                if (i/N_entries+j)%2 == 0:
                    # same color for each lever
                    pattern[i, j] = 1
                   
        ticks = np.tile(['$f\,[\mathrm{kHz}$]', '$Q$', 'SNR'], self.N_rows)
#         ticks = np.tile(['$f\,[\mathrm{kHz}$]', '$Q$', 'SNR', 'Sum$\,[\mathrm{V}]$',
#                          'Spot size$\,[\mu \mathrm{m}]$','Lever width $[\mathrm{\mu m}]$'], self.N_rows)
        self.ax1_2.matshow(pattern, aspect=aspect, cmap=cmap)
        self.ax1_2.set(title='', xticks=[], xticklabels=ticks,
               yticks=range(N_entries*self.N_rows), yticklabels=ticks)
        self.ax1_2.tick_params(labelsize=labelsize)
        
        key1 = 'spectrum_fit'
        key3 = 'SNR'
#         key4 = 'sum_lever'
#         key5 = 'spot_size'
#         key6 = 'measured_lever_width'
        for (i, j), _ in np.ndenumerate(pattern):
            lever_nb = j+1+i/N_entries*self.N_cols
            if i % N_entries == 0 and key1+str(lever_nb) in self.data_dict:
                val = self.data_dict[key1+str(lever_nb)][-1][1]
                self.ax1_2.annotate('{:.5g}'.format(val/1000), (j,i), ha='center', va='center', size=textsize)
            elif i % N_entries == 1 and key1+str(lever_nb) in self.data_dict:
                val = self.data_dict[key1+str(lever_nb)][-1][2]
                self.ax1_2.annotate('{:.3g}'.format(val), (j,i), ha='center', va='center', size=textsize)
            elif i % N_entries == 2 and key3+str(lever_nb) in self.data_dict:
                val = self.data_dict[key3+str(lever_nb)][-1]
                self.ax1_2.annotate('{:.3g}'.format(val), (j,i), ha='center', va='center', size=textsize)
#             elif i % N_entries == 3 and key4+str(lever_nb) in self.data_dict:
#                 val = self.data_dict[key4+str(lever_nb)][-1]
#                 self.ax1_2.annotate('{:3.1g}'.format(val), (j,i), ha='center', va='center', size=textsize)
#             elif i % N_entries == 4 and key5+str(lever_nb) in self.data_dict:
#                 val = self.data_dict[key5+str(lever_nb)]
#                 self.ax1_2.annotate('{:3.1g}'.format(val*1000), (j,i), ha='center', va='center', size=textsize)
#             elif i % N_entries == 5 and key6+str(lever_nb) in self.data_dict:
#                 val = self.data_dict[key6+str(lever_nb)]
#                 self.ax1_2.annotate('{:.1g}'.format(val*1000), (j,i), ha='center', va='center', size=textsize)
           
        self.fig1.tight_layout()
        self.fig1.canvas.draw()
            
    def selectLever(self):
        lever_nb = int(self.gui.ui.SingleMeasurements_lever_nb_doubleSpinBox.value())
        
        key = "spot_size"+str(lever_nb)
        if key in self.data_dict:
            self.gui.ui.SingleMeasurements_spot_size_doubleSpinBox.setValue(self.data_dict[key]*1000)
        else:
            self.gui.ui.SingleMeasurements_spot_size_doubleSpinBox.setValue(0)
            
            
        key = "measured_lever_width"+str(lever_nb)
        if key in self.data_dict:
            self.gui.ui.SingleMeasurements_lever_width_doubleSpinBox.setValue(self.data_dict[key]*1000)
        else:
            self.gui.ui.SingleMeasurements_lever_width_doubleSpinBox.setValue(0)
            
        
        key = "sum_lever"+str(lever_nb)
        if key in self.data_dict:
            self.gui.ui.SingleMeasurements_sum_lever_doubleSpinBox.setValue(self.data_dict[key][-1])
        else:
            self.gui.ui.SingleMeasurements_sum_lever_doubleSpinBox.setValue(0)
              
        key = "spectrum_fit"+str(lever_nb)
        if key in self.data_dict:
            f = self.data_dict[key][-1][1]
            Q = self.data_dict[key][-1][2]
            SNR = self.data_dict["SNR"+str(lever_nb)][-1]
            self.gui.ui.SingleMeasurements_fitted_f_doubleSpinBox.setValue(f/1000)
            self.gui.ui.SingleMeasurements_fitted_Q_doubleSpinBox.setValue(Q)
            self.gui.ui.SingleMeasurements_fitted_SNR_doubleSpinBox.setValue(SNR)
        else:
            self.gui.ui.SingleMeasurements_fitted_f_doubleSpinBox.setValue(0)
            self.gui.ui.SingleMeasurements_fitted_Q_doubleSpinBox.setValue(0)
            self.gui.ui.SingleMeasurements_fitted_SNR_doubleSpinBox.setValue(0)
        
        for i, line in enumerate(self.spectrum_plotline_list):
            if i+1 == lever_nb:
                plt.setp(line, color='r', linewidth=2.0)  
            else:
                plt.setp(line, color='b', linewidth=1.0)
        
        key = "sum_sweep"+str(lever_nb)
        if key in self.data_dict:
            sum_sweep = self.data_dict[key]
            f_sampling = self.data_dict['sweep_fs'+str(lever_nb)]
            N = len(sum_sweep)
            t_sweep = np.linspace(0, (N-1)/f_sampling, N)
            self.gui.lever_detection.plotline1_11.set_data(t_sweep, sum_sweep)
            self.gui.lever_detection.ax1_1.set_xlim([0, max(t_sweep)])
            self.gui.lever_detection.ax1_1.set_ylim([min(sum_sweep)-max(sum_sweep)*0.1, max(sum_sweep)*1.1])  
            
        else:
            self.gui.lever_detection.ax1_1.cla()
            
        key = "sum_signal_x"+str(lever_nb)
        if key in self.data_dict:
            sum_signal = self.data_dict[key]
            dist_vec = self.data_dict["dist_vec_x"+str(lever_nb)]
            self.gui.lever_detection.plotline1_21.set_data(dist_vec*1000, sum_signal)
            self.gui.lever_detection.ax1_2.set_xlim([0, max(dist_vec)*1000])
            self.gui.lever_detection.ax1_2.set_ylim([min(sum_signal)-max(sum_signal)*0.1, max(sum_signal)*1.1])
        else:
            self.gui.lever_detection.ax1_2.cla()
         
        key = "sum_signal_y"+str(lever_nb)
        if key in self.data_dict:
            sum_signal = self.data_dict[key]
            dist_vec = self.data_dict["dist_vec_y"+str(lever_nb)]
            self.gui.lever_detection.plotline1_31.set_data(dist_vec*1000, sum_signal)
            self.gui.lever_detection.ax1_3.set_xlim([0, max(dist_vec)*1000])  # in case autoscale fails
            self.gui.lever_detection.ax1_3.set_ylim([min(sum_signal)-max(sum_signal)*0.1, max(sum_signal)*1.1]) 
        else:
            self.gui.lever_detection.ax1_3.cla()
        
        key = 'spectrum_lever'+str(lever_nb)
        if key in self.data_dict:
            magnitude = self.data_dict[key][-1]
            f_plot = self.data_dict["f_lever"+str(lever_nb)][-1]
            self.gui.lever_detection.plotline1_41.set_data(f_plot, magnitude) 
            self.gui.lever_detection.ax1_4.set_xlim([min(f_plot), max(f_plot)])
            self.gui.lever_detection.ax1_4.set_ylim([min(magnitude), max(magnitude)])
        else:
            self.gui.lever_detection.ax1_4.cla()
               
        self.fig2.canvas.draw()
        self.gui.lever_detection.fig1.canvas.draw()
    
    def plotSpectrumFits(self):
        self.ax2_1.cla()
        self.spectrum_plotline_list = []        
        
        for i in xrange(self.N_cols*self.N_rows):
            key = "spectrum_fit" + str(i+1)
            if key in self.data_dict:
                fit_width = self.data_dict['fit_width'+str(i+1)][-1]
                p = self.data_dict['spectrum_fit' + str(i+1)][-1]
                f = np.linspace(p[1]-fit_width/2, p[1]+fit_width/2, 500)
                mag_fitted = [self.gui.measureLever.SOHAmpWhite(x, p[0], p[1], p[2], p[3]) for x in f]
                self.spectrum_plotline_list.append(self.ax2_1.loglog(f/1000, mag_fitted, 'b'))
            else: 
                self.spectrum_plotline_list.append(self.ax2_1.loglog([1,1], [1,1]))
                
        self.ax2_1.set_xlim([10, 500])
        self.fig2.tight_layout()
        self.fig2.canvas.draw()
        
    def loadData(self, path=None):
        if path is None:
            path = QFileDialog.getOpenFileName()[0]
        with open(os.path.join(path), "rb" ) as handle:
            box_image_path =  os.path.splitext(handle.name)[0]
            self.data_dict = pickle.load(handle)
         
        lever_vec_sorted = self.data_dict["lever_vec_sorted"]
        self.lever_numbers = [int(i) for i in lever_vec_sorted[:, 8]]
        self.N_cols = int(max(lever_vec_sorted[:,6]) + 1)
        self.N_rows = int(max(lever_vec_sorted[:,7]) + 1)
        
        # display box image
        box_image = plt.imread(box_image_path+'.png')
        self.ax1_1.imshow(box_image)
        self.fig1.canvas.draw()
        self.gui.lever_detection.ax2_1.imshow(box_image)
        self.gui.lever_detection.fig1.canvas.draw()
        
    def displayAverageValues(self):
        key1 = "spectrum_fit"
        key2 = 'SNR'
        key3 = 'sum_lever'
        f_list, Q_list, SNR_list, sum_list = [], [], [], []
        for i in xrange(self.N_cols*self.N_rows):
            if key1+str(i+1) in self.data_dict:
                f = self.data_dict[key1+str(i+1)][-1][1]
                Q = self.data_dict[key1+str(i+1)][-1][2]
                f_list.append(f)
                Q_list.append(Q)
            if key2+str(i+1) in self.data_dict:
                SNR = self.data_dict[key2+str(i+1)][-1]
                SNR_list.append(SNR)
            if key3+str(i+1) in self.data_dict:
                sum_lever = self.data_dict[key3+str(i+1)][-1]
                sum_list.append(sum_lever)
        f_array = np.asarray(f_list)
        sum_array = np.asarray(sum_list)
        Q_array = np.asarray(Q_list)
        SNR_array = np.asarray(SNR_list)
        self.gui.ui.SingleMeasurements_average_f_doubleSpinBox.setValue(np.mean(f_array)/1000)
        self.gui.ui.SingleMeasurements_std_f_doubleSpinBox.setValue(np.std(f_array)/1000)
        self.gui.ui.SingleMeasurements_average_Q_doubleSpinBox.setValue(np.mean(Q_array))
        self.gui.ui.SingleMeasurements_std_Q_doubleSpinBox.setValue(np.std(Q_array))
        self.gui.ui.SingleMeasurements_average_SNR_doubleSpinBox.setValue(np.mean(SNR_array))
        self.gui.ui.SingleMeasurements_std_SNR_doubleSpinBox.setValue(np.std(SNR_array))
        self.gui.ui.SingleMeasurements_average_sum_doubleSpinBox.setValue(np.mean(sum_array))
        self.gui.ui.SingleMeasurements_std_sum_doubleSpinBox.setValue(np.std(sum_array))        
            
    def plotLongTerm(self):
        self.ax3_1.cla()
        self.ax3_2.cla()
        self.long_term_f_plotline_list = []
        self.long_term_Q_plotline_list = []      
        
        for i in xrange(self.N_cols*self.N_rows):
            key = "spectrum_fit" + str(i+1)
            if key in self.data_dict:
                p_list = self.data_dict['spectrum_fit' + str(i+1)]
                f_array = np.array([p[1] for p in p_list])
                Q_array = np.array([p[2] for p in p_list])
                meas_nb = np.arange(len(f_array))
                print str(i+1), "f", f_array/1000, "Q", Q_array
                self.long_term_f_plotline_list.append(self.ax3_1.plot(meas_nb, f_array / 1000,'bo-'))
                self.long_term_Q_plotline_list.append(self.ax3_2.plot(meas_nb, Q_array, 'go-'))                             
            else: 
                self.long_term_f_plotline_list.append(self.ax3_1.plot([0,0], [0,0], 'b'))
                self.long_term_Q_plotline_list.append(self.ax3_2.plot([0,0], [0,0], 'g'))
                
        self.fig3.tight_layout()
        self.fig3.canvas.draw()

             
    def displayData(self, path=None):
        # load Data (automatically close file)
        
        self.loadData(path=path)
        self.displayAverageValues()
        
        self.showTable()
        
        self.plotSpectrumFits()
        
        self.plotLongTerm()
        

#         for val in d.itervalues():
#     print val