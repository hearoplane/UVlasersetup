import numpy as np
import time
from PySide import QtCore

from .measurement import Measurement 
from measurement_components.base_3d_scan import Base3DScan
 

class APDOptimizerMeasurement(Measurement):

    name = "apd_optimizer"

    def setup(self):        
        self.display_update_period = 0.1 #seconds

        self.OPTIMIZE_HISTORY_LEN = 500

        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0

        #connect events
        self.gui.ui.apd_optimize_startstop_checkBox.stateChanged.connect(self.start_stop)
        #self.measurement_state_changed[bool].connect(self.gui.ui.apd_optimize_timer_checkBox.setChecked)

    def setup_figure(self):
        # APD Optimize Figure ########################
        self.fig_opt = self.gui.add_figure('opt', self.gui.ui.plot_optimize_widget)
        self.ax_opt = self.fig_opt.add_subplot(111)
        
        self.optimize_ii = 0
        self.optimize_line, = self.ax_opt.plot(self.optimize_history)
        self.optimize_current_pos = self.ax_opt.axvline(self.optimize_ii, color='r')


    def _run(self):
        self.apd_counter_hc = self.gui.apd_counter_hc
        self.apd_count_rate = self.apd_counter_hc.apd_count_rate


        while not self.interrupt_measurement_called:
            self.apd_count_rate.read_from_hardware()
            #print "in thread:", self.apd_count_rate.val
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN
            
            self.optimize_history[self.optimize_ii] = self.apd_count_rate.val    
        
        #is this right place to put this?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()
    
    @QtCore.Slot()
    def on_display_update_timer(self):        
        ii = self.optimize_ii
        #print "display update", ii, self.optimize_history[ii]

        self.optimize_line.set_ydata(self.optimize_history)
        self.optimize_current_pos.set_xdata((ii,ii))
        if (ii % 2) == 0:
            self.ax_opt.relim()
            self.ax_opt.autoscale_view(scalex=False, scaley=True)

        self.fig_opt.canvas.draw()
        
        Measurement.on_display_update_timer(self)
        
class APDConfocalScanMeasurement(Measurement):
    
    name = "apd_confocal"
    
    def setup(self):
        
        self.display_update_period = 0.1 #seconds

        #connect events
        self.gui.ui.scan_apd_start_pushButton.clicked.connect(self.start)
        self.gui.ui.scan_apd_stop_pushButton.clicked.connect(self.interrupt)
        
        self.int_time = self.gui.apd_counter_hc.int_time
        
        # local logged quantities
        lq_params = dict(dtype=float, vmin=-1,vmax=100, ro=False, unit='um' )
        self.h0 = self.add_logged_quantity('h0',  initial=25, **lq_params  )
        self.h1 = self.add_logged_quantity('h1',  initial=45, **lq_params  )
        self.v0 = self.add_logged_quantity('v0',  initial=25, **lq_params  )
        self.v1 = self.add_logged_quantity('v1',  initial=45, **lq_params  )

        self.dh = self.add_logged_quantity('dh', initial=1, **lq_params)
        self.dv = self.add_logged_quantity('dv', initial=1, **lq_params)
        
        # connect to gui
        self.gui.ui.scan_apd_start_pushButton.clicked.connect(self.start)
        self.gui.ui.scan_apd_stop_pushButton.clicked.connect(self.interrupt)
        
        self.h0.connect_bidir_to_widget(self.gui.ui.h0_doubleSpinBox)
        self.h1.connect_bidir_to_widget(self.gui.ui.h1_doubleSpinBox)
        self.v0.connect_bidir_to_widget(self.gui.ui.v0_doubleSpinBox)
        self.v1.connect_bidir_to_widget(self.gui.ui.v1_doubleSpinBox)
        
        self.dh.connect_bidir_to_widget(self.gui.ui.dh_doubleSpinBox)
        self.dv.connect_bidir_to_widget(self.gui.ui.dv_doubleSpinBox)
        
        
        
    def setup_figure(self):
        #2D scan area
        self.fig2d = self.gui.add_figure('2d', self.gui.ui.plot2d_widget)
        
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.plot([0,1])

        self.ax2d.set_xlim(0, 100)
        self.ax2d.set_ylim(0, 100)
                    
        self.fig2d.canvas.mpl_connect('button_press_event', self.on_fig2d_click)
        
        
    def on_fig2d_click(self, evt):
        
        stage = self.gui.mcl_xyz_stage_hc
        #print evt.xdata, evt.ydata, evt.button, evt.key
        if not self.is_measuring():
            if evt.key == "shift":
                print "moving to ", evt.xdata, evt.ydata
                #self.nanodrive.set_pos_ax(evt.xdata, HAXIS_ID)
                #self.nanodrive.set_pos_ax(evt.ydata, VAXIS_ID)
                
                new_pos = [None,None,None]                
                new_pos[stage.h_axis_id-1] = evt.xdata
                new_pos[stage.v_axis_id-1] = evt.ydata
                
                stage.nanodrive.set_pos_slow(*new_pos)
                stage.read_from_hardware()
    
    def _run(self):
        #hardware 
        self.stage = self.gui.mcl_xyz_stage_hc
        self.nanodrive = self.stage.nanodrive
        self.apd_counter_hc = self.gui.apd_counter_hc
        self.apd_count_rate = self.gui.apd_counter_hc.apd_count_rate

        #get scan parameters: #FIXME should be loggedquantities
#         self.h0 = self.gui.ui.h0_doubleSpinBox.value()
#         self.h1 = self.gui.ui.h1_doubleSpinBox.value()
#         self.v0 = self.gui.ui.v0_doubleSpinBox.value()
#         self.v1 = self.gui.ui.v1_doubleSpinBox.value()
    
#         self.dh = 1e-3*self.gui.ui.dh_spinBox.value()
#         self.dv = 1e-3*self.gui.ui.dv_spinBox.value()

        self.h_array = np.arange(self.h0.val, self.h1.val, self.dh.val, dtype=float)
        self.v_array = np.arange(self.v0.val, self.v1.val, self.dv.val, dtype=float)
        
        self.Nh = len(self.h_array)
        self.Nv = len(self.v_array)
        
        self.extent = [self.h0.val, self.h1.val, self.v0.val, self.v1.val]

        #scan specific setup
        
        
        # create data arrays
        self.count_rate_map = np.zeros((self.Nv, self.Nh), dtype=float)
        #update figure
        self.imgplot = self.ax2d.imshow(self.count_rate_map, 
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
                    self.apd_count_rate.read_from_hardware()
                                      
                    # store in arrays
                    self.count_rate_map[i_v,i_h] = self.apd_count_rate.val
    
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
                     'count_rate_map': self.count_rate_map,
                     'h_array': self.h_array,
                     'v_array': self.v_array,
                     'Nv': self.Nv,
                     'Nh': self.Nh,
                     'extent': self.extent,
                     'int_time': self.int_time.val,
                    }               

                    
            for lqname,lq in self.gui.logged_quantities.items():
                save_dict[lqname] = lq.val
            
            for hc in self.gui.hardware_components.values():
                for lqname,lq in hc.logged_quantities.items():
                    save_dict[hc.name + "_" + lqname] = lq.val
            
            for lqname,lq in self.logged_quantities.items():
                save_dict[self.name +"_"+ lqname] = lq.val
    
            self.fname = "%i_apd_map.npz" % time.time()
            np.savez_compressed(self.fname, **save_dict)
            print "APD 2D Scan Saved", self.fname

            if not self.interrupt_measurement_called:
                self.measurement_sucessfully_completed.emit()
            else:
                pass


    def update_display(self):
        #print "updating figure"
        self.imgplot.set_data(self.count_rate_map)
        try:
            count_min =  np.min(self.count_rate_map[np.nonzero(self.count_rate_map)])
        except Exception as err:
            count_min = 0
        count_max = np.percentile(self.count_rate_map,99.)
        assert count_max > count_min
        self.imgplot.set_clim(count_min, count_max + 1)
        self.fig2d.canvas.draw()


class APDConfocalScan3DMeasurement(Base3DScan):

    name = "apd_confocal_scan3d"
    
    def scan_specific_setup(self):
        
        self.int_time = self.gui.apd_counter_hc.int_time

    def setup_figure(self):
        pass
    
    def pre_scan_setup(self):
        #hardware 
        self.apd_counter_hc = self.gui.apd_counter_hc
        self.apd_count_rate = self.gui.apd_counter_hc.apd_count_rate

        #scan specific setup
        
        # create data arrays
        self.count_rate_map = np.zeros((self.Nz, self.Ny, self.Nx), dtype=float)
        #update figure
    
    def collect_pixel(self, i, j, k):
        # collect data
        self.apd_count_rate.read_from_hardware()
                          
        # store in arrays
        self.count_rate_map[k,j,i] = self.apd_count_rate.val
    
    def scan_specific_savedict(self):
        return {'count_rate_map': self.count_rate_map}
        
    def update_display(self):
        pass