# 2014-03-27

import sys, os
import time
import datetime
import numpy as np
import collections

from PySide import QtCore, QtGui, QtUiTools

import matplotlib
matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar2

from matplotlib.figure import Figure



from equipment.mcl_nanodrive import MCLNanoDrive
#from equipment.crystaltech_dds import CrystalTechDDS
from equipment.thorlabs_pm100d import ThorlabsPM100D
from equipment.ocean_optics_seabreeze import OceanOpticsSpectrometer
#from equipment.acton_spec import ActonSpectrometer

from hardware_components.picoharp import PicoHarpHardwareComponent
from hardware_components.apd_counter import APDCounterHardwareComponent
from hardware_components.andor_ccd import AndorCCDHardwareComponent
from hardware_components.acton_spec import ActonSpectrometerHardwareComponent
from hardware_components.flip_mirror import FlipMirrorHardwareComponent

from measurement_components.ple import PLEPointMeasurement, PLE2DScanMeasurement
from measurement_components.trpl import PicoHarpMeasurement, TRPLScanMeasurement
from measurement_components.apd_confocal import APDOptimizerMeasurement, APDConfocalScanMeasurement
from measurement_components.andor_ccd_readout import AndorCCDReadout, AndorCCDReadBackground
from measurement_components.hyperspectral import SpectrumScan2DMeasurement
from measurement_components.power_scan import PowerScanContinuous

from logged_quantity import LoggedQuantity

# MCL axis translation

MCL_AXIS_ID = dict(X = 2, Y = 1, Z = 3)


HAXIS = "X"
#FOR LATERAL SCAN
#VAXIS = "Y"
#FOR DEPTH SCAN
VAXIS = "Z"

HAXIS_ID = MCL_AXIS_ID[HAXIS] 
VAXIS_ID = MCL_AXIS_ID[VAXIS]


TIMER_MS = 1000    

HARDWARE_DEBUG = False


ACTON_SPEC_PORT = "COM11"

        
class MicroscopeGUI(object):
    def __del__ ( self ): 
        self.ui = None

    def show(self): 
        #self.ui.exec_()
        self.ui.show()

    def __init__(self):
    
        self.HARDWARE_DEBUG = HARDWARE_DEBUG        
        self.scanning = False
        
        
        self.MCL_AXIS_ID = MCL_AXIS_ID
        self.HAXIS = HAXIS
        self.VAXIS = VAXIS
        self.HAXIS_ID = HAXIS_ID
        self.VAXIS_ID = VAXIS_ID

        self.logged_quantities = collections.OrderedDict()
        self.hardware_components = collections.OrderedDict()
        self.measurement_components = collections.OrderedDict()
        self.figs = collections.OrderedDict()

        # Load Qt UI from .ui file
        ui_loader = QtUiTools.QUiLoader()
        ui_file = QtCore.QFile("microscope_gui.ui")
        ui_file.open(QtCore.QFile.ReadOnly); 
        self.ui = ui_loader.load(ui_file)
        ui_file.close()

        
        # Add hardware components
        print "Adding Hardware Components"
        self.picoharp_hc = self.add_hardware_component(PicoHarpHardwareComponent(self))
        self.apd_counter_hc = self.add_hardware_component(APDCounterHardwareComponent(self))
        self.andor_ccd_hc = self.add_hardware_component(AndorCCDHardwareComponent(self))
        self.acton_spec_hc = self.add_hardware_component(ActonSpectrometerHardwareComponent(self))
        self.flip_mirror_hc = self.add_hardware_component(FlipMirrorHardwareComponent(self))
        self.setup_hardware()

        # Create the measurement objects
        print "Create Measurement objects"
        self.apd_optimizer_measure = self.add_measurement_component(APDOptimizerMeasurement(self))
        self.apd_scan_measure = self.add_measurement_component(APDConfocalScanMeasurement(self))
        self.ple_point_measure = self.add_measurement_component(PLEPointMeasurement(self))
        self.ple2d_measure = self.add_measurement_component(PLE2DScanMeasurement(self))
        self.picoharp_measure = self.add_measurement_component(PicoHarpMeasurement(self))
        self.trpl_scan_measure = self.add_measurement_component(TRPLScanMeasurement(self))
        self.andor_ro_measure = self.add_measurement_component(AndorCCDReadout(self))
        self.andor_bg_measure = self.add_measurement_component(AndorCCDReadBackground(self))
        self.spec_map_measure = self.add_measurement_component(SpectrumScan2DMeasurement(self))
        self.power_scan_measure = self.add_measurement_component(PowerScanContinuous(self))

        # Setup the figures         
        for name, measure in self.measurement_components.items():
            print "setting up figures for", name, "measurement", measure.name
            measure.setup_figure()
        self.setup_figures()

        print "figures:"
        for fig in self.figs:
            print "\t",fig
        print "measurement_components:"
        for m in self.measurement_components:
            print "\t", m


        # events
        self.ui.slow_display_timer_checkBox.stateChanged.connect(self.on_slow_display_timer_checkbox)
        
        self.ui.power_meter_acquire_cont_checkBox.stateChanged.connect(self.on_power_meter_acquire_cont_checkbox)

        self.ui.oo_spec_acquire_cont_checkBox.stateChanged.connect(self.on_oo_spec_acq_cont_checkbox)

        ### timers
        
        self.slow_display_timer = QtCore.QTimer(self.ui)
        self.slow_display_timer.timeout.connect(self.on_slow_display_timer)
    
        self.ui.slow_display_timer_checkBox.setChecked(True)
        
        self.power_meter_acq_cont_timer = QtCore.QTimer(self.ui)
        self.power_meter_acq_cont_timer.timeout.connect(self.on_power_meter_acq_cont_timer)
        
        self.oo_spec_acq_cont_timer = QtCore.QTimer(self.ui)
        self.oo_spec_acq_cont_timer.timeout.connect(self.on_oo_spec_acq_cont_timer)
        
        
    def start_display_timers(self):
        print "start_display_timers"

        
    @QtCore.Slot()
    def stop_display_timers(self):
        print "stop_display_timers"
        self.ui.slow_display_timer_checkBox.setChecked(False)
        self.ui.power_meter_acquire_cont_checkBox.setChecked(False)
        self.ui.oo_spec_acquire_cont_checkBox.setChecked(False)
        QtGui.QApplication.processEvents()


    def add_figure(self,name, widget):
            """creates a matplotlib figure attaches it to the qwidget specified
            (widget needs to have a layout set (preferably verticalLayout) 
            adds a figure to self.figs"""
            print "---adding figure", name, widget
            if name in self.figs:
                return self.figs[name]
            else:
                fig = Figure()
                fig.patch.set_facecolor('w')
                canvas = FigureCanvas(fig)
                nav    = NavigationToolbar2(canvas, self.ui)
                widget.layout().addWidget(canvas)
                widget.layout().addWidget(nav)
                canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
                canvas.setFocus()
                self.figs[name] = fig
                return fig
    
    def add_logged_quantity(self, name, **kwargs):
        lq = LoggedQuantity(name=name, **kwargs)
        self.logged_quantities[name] = lq
        return lq

    def add_hardware_component(self,hc):
        self.hardware_components[hc.name] = hc
        return hc
    
    def add_measurement_component(self, measure):
        assert not measure.name in self.measurement_components.keys()
        self.measurement_components[measure.name] = measure
        return measure

    def setup_figures(self):
        ## OO Spec Figure ###
        
        F = self.fig_oo_spec = self.add_figure('oo_spec', self.ui.oo_spec_plot_widget)
        
        ax = self.oo_spec_ax = F.add_subplot(111)
        self.oo_spec_plotline, = ax.plot(self.oo_spectrometer.wavelengths, self.oo_spectrometer.spectrum)
        ax.set_xlabel("wavelengths (nm)")
        ax.set_ylabel("Laser Spectrum (counts)")
        
    
    def setup_hardware(self):
        

        ######## MCL NanoDrive Stage ###########################################
        print "Initializing MCL stage functionality"
        self.nanodrive = MCLNanoDrive(debug=True)
        self.hmax = self.nanodrive.cal[HAXIS_ID]
        self.vmax = self.nanodrive.cal[VAXIS_ID]
        self.ui.maxdim_label.setText("%s - %s scan. Max: %g x %g um" % (HAXIS, VAXIS, self.hmax, self.vmax) )
        
        
        # Logged Quantities
        self.x_position = self.add_logged_quantity(name = 'x_position', dtype=np.float)
        self.y_position = self.add_logged_quantity(name = 'y_position', dtype=np.float)
        self.z_position = self.add_logged_quantity(name = 'z_position', dtype=np.float)
        
        self.x_position.hardware_set_func = lambda x: self.nanodrive.set_pos_ax_slow(x, MCL_AXIS_ID["X"])
        self.y_position.hardware_set_func = lambda y: self.nanodrive.set_pos_ax_slow(y, MCL_AXIS_ID["Y"])
        self.z_position.hardware_set_func = lambda z: self.nanodrive.set_pos_ax_slow(z, MCL_AXIS_ID["Z"])
        
        
        self.x_position.updated_value.connect(self.ui.cx_doubleSpinBox.setValue)
        self.ui.x_set_lineEdit.returnPressed.connect(self.x_position.update_value)

        self.y_position.updated_value.connect(self.ui.cy_doubleSpinBox.setValue)
        self.ui.y_set_lineEdit.returnPressed.connect(self.y_position.update_value)

        self.z_position.updated_value.connect(self.ui.cz_doubleSpinBox.setValue)
        self.ui.z_set_lineEdit.returnPressed.connect(self.z_position.update_value)
        
        self.nanodrive_move_speed = self.add_logged_quantity(name='nanodrive_move_speed', 
                                                             dtype=np.float, 
                                                             hardware_read_func=self.nanodrive.get_max_speed,
                                                             hardware_set_func = self.nanodrive.set_max_speed)
        self.nanodrive_move_speed.updated_value[float].connect(self.ui.nanodrive_move_slow_doubleSpinBox.setValue)
        self.ui.nanodrive_move_slow_doubleSpinBox.valueChanged[float].connect(self.nanodrive_move_speed.update_value)                                                  
        self.nanodrive_move_speed.read_from_hardware()

        # read and initialize hardware control values
        self.read_stage_position()
                
        ### Power Meter ##########################
        print "Initializing power meter functionality"
        self.power_meter = ThorlabsPM100D(debug=self.HARDWARE_DEBUG)
        
        self.power_meter_wavelength = self.add_logged_quantity('power_meter_wavelength', 
                                                    dtype=int,
                                                    hardware_read_func=self.power_meter.get_wavelength,
                                                    hardware_set_func=self.power_meter.set_wavelength)
        self.power_meter_wavelength.updated_value[float].connect(self.ui.power_meter_wl_doubleSpinBox.setValue )
        self.ui.power_meter_wl_doubleSpinBox.valueChanged[float].connect(self.power_meter_wavelength.update_value)

        print "Reading initial wavelength"       
        self.power_meter_wavelength.read_from_hardware()
    
        self.laser_power = self.add_logged_quantity(name = 'laser_in_power',
                                          fmt='%2.2e W',
                                          dtype=np.float, 
                                          hardware_read_func=self.power_meter.measure_power)
        self.laser_power.updated_text_value.connect(self.ui.power_meter_power_label.setText)
        self.laser_power.read_from_hardware()
        
    
    
        ### AOTF #####################################
        print "Initializing AOTF functionality"
 #       self.dds = CrystalTechDDS(comm="serial", port="COM1", debug=self.HARDWARE_DEBUG)
        
        # Modulation property
#        self.aotf_modulation = self.add_logged_quantity(name="aotf_modulation", dtype=bool, hardware_set_func=self.dds.set_modulation)
#        self.aotf_modulation.updated_value[bool].connect(self.ui.aotf_mod_enable_checkBox.setChecked)
#        self.ui.aotf_mod_enable_checkBox.stateChanged.connect(self.aotf_modulation.update_value)
#        self.aotf_modulation.update_value(True)
        
        # Frequency property
        # TODO:  only works on channel 0!
#        self.aotf_freq = self.add_logged_quantity(name="aotf_freq", 
#                                        dtype=np.float, 
 #                                       hardware_read_func=self.dds.get_frequency,
#                                        hardware_set_func=self.dds.set_frequency,
#                                        fmt = '%f')
#        self.aotf_freq.updated_value[float].connect(self.ui.atof_freq_doubleSpinBox.setValue)
#        self.ui.atof_freq_doubleSpinBox.valueChanged[float].connect(self.aotf_freq.update_value)
#        self.ui.aotf_freq_set_lineEdit.returnPressed.connect(self.aotf_freq.update_value)
#        self.aotf_freq.read_from_hardware()
        
        # Power property
        # TODO:  only works on channel 0!
#        self.aotf_power = self.add_logged_quantity(name="aotf_power", 
#                                         dtype=np.int, 
#                                         hardware_read_func=self.dds.get_amplitude,
#                                        hardware_set_func=self.dds.set_amplitude)
#        self.aotf_power.updated_value[float].connect(self.ui.aotf_power_doubleSpinBox.setValue)
#        self.ui.aotf_power_doubleSpinBox.valueChanged.connect(self.aotf_power.update_value)
#        self.aotf_power.read_from_hardware()
        
        
        ### OO Spec ####################################
        print "Initializing OceanOptics spectrometer functionality"
        self.oo_spectrometer = 	OceanOpticsSpectrometer(debug=self.HARDWARE_DEBUG)
        self.oo_spec_int_time = self.add_logged_quantity(name="oo_spec_int_time", dtype=float,
                                                hardware_set_func=self.oo_spectrometer.set_integration_time_sec)
        self.ui.oo_spec_int_time_doubleSpinBox.valueChanged[float].connect(self.oo_spec_int_time.update_value)
        self.oo_spec_int_time.updated_value[float].connect(self.ui.oo_spec_int_time_doubleSpinBox.setValue)
        self.oo_spec_int_time.update_value(0.1)
        self.oo_spectrometer.start_threaded_acquisition()
        
        
        
    
    # Hardware Read functions
    def read_stage_position(self):
        self.stage_pos = self.nanodrive.get_pos()
        self.x_position.update_value(self.stage_pos[MCL_AXIS_ID["X"]-1], update_hardware=False)
        self.y_position.update_value(self.stage_pos[MCL_AXIS_ID["Y"]-1], update_hardware=False)
        self.z_position.update_value(self.stage_pos[MCL_AXIS_ID["Z"]-1], update_hardware=False)
        return self.stage_pos
    
    # GUI Functions
    @QtCore.Slot()
    def on_clearfig(self):
        self.fig2d.clf()
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.plot([0,1])    
        # update figure
        self.ax2d.set_xlim(0, self.hmax)
        self.ax2d.set_ylim(0, self.vmax)
        self.fig2d.canvas.draw()
        


    @QtCore.Slot()
    def on_slow_display_timer_checkbox(self, enable):
        if enable:
            self.slow_display_timer.start(TIMER_MS)
        else:
            self.slow_display_timer.stop()
        
    # Timer callbacks
    @QtCore.Slot()
    def on_slow_display_timer(self):
        self.read_stage_position()
        #self.read_ni_countrate(int_time = 0.01)
                
        #Update the temperature reading for the CCD
        
        if self.andor_ccd_hc.is_connected:
            ccd = self.andor_ccd_hc
            if (ccd.status.read_from_hardware() == 'IDLE'):
                ccd.temperature.read_from_hardware()

    
    @QtCore.Slot()
    def on_oo_spec_acq_cont_checkbox(self,enable):
        if enable:
            # limit update period to 50ms (in ms) or as slow as 1sec
            #timer_period = np.min(1.0,np.max(0.05*self.oo_spec_int_time.val,0.05)) * 1000. 
            self.oo_spec_acq_cont_timer.start(0.050)
        else:
            self.oo_spec_acq_cont_timer.stop()
        
        
    @QtCore.Slot()
    def on_oo_spec_acq_cont_timer(self):    
        # Check to see if a spectrum is available from the Ocean Optics spec
        if self.oo_spectrometer.is_threaded_acquisition_complete():
            self.oospec_update_figure()
            self.oo_spectrometer.start_threaded_acquisition()   
    
    def oospec_update_figure(self):
        F = self.fig_oo_spec
        ax = self.oo_spec_ax
        self.oo_spectrometer.spectrum[:10]=np.nan
        self.oo_spectrometer.spectrum[-10:]=np.nan
        self.oo_spec_plotline.set_ydata(self.oo_spectrometer.spectrum)
        ax.relim()
        ax.autoscale_view(scalex=False, scaley=True)
        F.canvas.draw()       

    @QtCore.Slot(bool)
    def on_power_meter_acquire_cont_checkbox(self,enable):
        if enable:
            self.power_meter_acq_cont_timer.start(100)
        else:
            self.power_meter_acq_cont_timer.stop()

    @QtCore.Slot()
    def on_power_meter_acq_cont_timer(self):
        
        #read power
        self.laser_power.read_from_hardware()
    
        
    
