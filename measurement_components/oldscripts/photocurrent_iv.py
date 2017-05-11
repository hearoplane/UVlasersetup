'''
Created on Sep 8, 2014

@author: Edward Barnard and Benedikt Ursprung
'''

from .measurement import Measurement 
import time
import numpy as np

class PhotocurrentIVMeasurement(Measurement):
    
    name = "photocurrrent_iv"
    
    def setup(self):
        self.display_update_period = 0.1 #seconds
        
        
        # logged quantities
        self.source_voltage_min = self.add_logged_quantity("source_voltage_min", dtype=float, unit='V', vmin=-5, vmax=5, ro=False)
        self.source_voltage_max = self.add_logged_quantity("source_voltage_max", dtype=float, unit='V', vmin=-5, vmax=5, ro=False)
        self.source_voltage_steps = self.add_logged_quantity("source_voltage_steps", dtype=int, initial = 10, vmin=1, vmax=1000, ro=False)           
        
        self.source_voltage_min.connect_bidir_to_widget(self.gui.ui.photocurrent_iv_vmin_doubleSpinBox)
        self.source_voltage_max.connect_bidir_to_widget(self.gui.ui.photocurrent_iv_vmax_doubleSpinBox)
        self.source_voltage_steps.connect_bidir_to_widget(self.gui.ui.photocurrent_iv_steps_doubleSpinBox)
        #connect events
        self.gui.ui.photocurrent_iv_start_pushButton.clicked.connect(self.start)

    
    def setup_figure(self):
        self.fig = self.gui.add_figure("photocurrent_iv", self.gui.ui.photocurrent_iv_plot_groupBox)
                    
        self.ax = self.fig.add_subplot(111)
        self.plotline, = self.ax.plot([0,1], [0,0])
        #self.ax.set_ylim(1e-1,1e5)
        self.ax.set_xlabel("Voltage (V)")
        self.ax.set_ylabel("Current (Amps)")
    


    def _run(self):
        self.keithley_hc = self.gui.keithley_sourcemeter_hc
        K1 = self.keithley = self.keithley_hc.keithley
        
        K1.resetA()
        K1.setAutoranges_A()
        K1.switchV_A_on()
        I,V = K1.measureIV_A(self.source_voltage_steps.val, 
                             Vmin=self.source_voltage_min.val, 
                             Vmax = self.source_voltage_max.val, 
                             KeithleyADCIntTime=1, delay=0)
        
        K1.switchV_A_off()
        
        self.Iarray = I
        self.Varray = V
        
        self.update_display()
        
        #save some data
        save_dict = {
                     'I': self.Iarray,
                     'V': self.Varray
                     }
        self.fname = "%i_photocurrent_iv.npz" % time.time()
        np.savez_compressed(self.fname, **save_dict)
        print "photocurrent_iv Saved", self.fname
        
        
    def update_display(self):
        self.plotline.set_data(self.Varray,self.Iarray)
        self.ax.relim()
        self.ax.autoscale_view(scalex=True, scaley=True)            
        self.fig.canvas.draw()
          