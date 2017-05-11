import numpy as np
import time
from PySide import QtCore

from .measurement import Measurement 

class fastNIScan(Measurement):
    
    name = "fast_NI_scan"
    
    def setup(self):
        
        #  system physical parameters
        self.magRef = 0.114 #  SEM x1 = 114 mm polaroid film
        self.magSEM = 1000 #  default
        
        # local logged quantities
        self.lines = self.add_logged_quantity( 'lines',  initial=256, dtype=int,vmin=8,vmax=2048, ro=False  )
        self.pixels = self.add_logged_quantity( 'pixels',  initial=256, dtype=int,vmin=8,vmax=2048, ro=False  )
        self.magSEM = self.add_logged_quantity( 'SEM magnification',  initial=1000, dtype=int, vmin=75,vmax=1e6, ro=False  )
        self.pixel_clock = self.add_logged_quantity('pixel clock', initial=1.0e4, dtype=float, unit='Hz')
               
        self.display_update_period = 0.3 #seconds
        
        # size, offset, scan angle, scan mode all go here
        self.x_offset = self.y_offset = self.scan_angle = 0.0
        self.scan_mode = 'sawtooth'
        # connect to gui

    def setup_figure(self):
        #2D scan area
        self.fig2d = self.gui.add_figure('2d', self.gui.ui.plot2d_widget)
        
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.plot([0,1])

        self.ax2d.set_xlim(-10, 10) # volts for now
        self.ax2d.set_ylim(-10, 10)

    def _run(self):
        #hardware
        ####
        #self.stage = self.gui.attocube_xy_stage
        self.sem_detector = self.gui.sem_detector
        
        # Get scan parameters
        self.h_array = np.arange(self.h0.val, self.h1.val, self.dh.val, dtype=float)
        self.v_array = np.arange(self.v0.val, self.v1.val, self.dv.val, dtype=float)
        
        self.Nh = len(self.h_array)
        self.Nv = len(self.v_array)
        
        self.extent = [self.h0.val, self.h1.val, self.v0.val, self.v1.val]

        #scan specific setup
        
        # create data arrays
        self.detector_map = np.zeros((self.Nv, self.Nh), dtype=float)
        #update figure
        self.imgplot = self.ax2d.imshow(self.detector_map, 
                                    origin='lower',
                                    vmin=0, vmax=1.5, interpolation='none', 
                                    extent=self.extent)
        self.ax2d.set_xlim(self.h0.val, self.h1.val)
        self.ax2d.set_ylim(self.v0.val, self.v1.val)
        
        
        
        # set up experiment
        # experimental parameters already connected via LoggedQuantities
        
        print "scanning"
        try:
            #v_axis_id = self.stage.v_axis_id
            #h_axis_id = self.stage.h_axis_id
            
            # move slowly to start position
            #start_pos = [None, None,None]
            #start_pos[v_axis_id-1] = self.v_array[0]
            #start_pos[h_axis_id-1] = self.h_array[0]
            #self.nanodrive.set_pos_slow(*start_pos)
            self.stage.y_target_position.update_value(self.v_array[0])
            self.stage.x_target_position.update_value(self.h_array[0])
            time.sleep(1)
            
            # Scan!            
            line_time0 = time.time()
            
            for i_v in range(self.Nv):
                if self.interrupt_measurement_called:
                    break
                self.v_pos = self.v_array[i_v]
                self.stage.y_target_position.update_value(self.v_pos)
                #self.read_stage_position()
                time.sleep(5*self.pixel_time.val)       
    
                if i_v % 2: #odd lines
                    h_line_indicies = range(self.Nh)[::-1]
                else:       #even lines -- traverse in opposite direction
                    h_line_indicies = range(self.Nh)            
    
                for i_h in h_line_indicies:
                    if self.interrupt_measurement_called:
                        break
    
                    #print i_h, i_v
    
                    self.h_pos = self.h_array[i_h]
                    self.stage.x_target_position.update_value(self.h_pos)

                    # settle position
                    time.sleep(self.pixel_time.val)


                    # collect data
                    #self.sem_detector.read_voltage()
                    self.sem_detector.voltage.read_from_hardware()
                    
                    #print i_v, i_h, "V=", self.sem_detector.voltage.val
                    
                    # store in arrays
                    self.detector_map[i_v,i_h] = self.sem_detector.voltage.val
    
                print "line time:", time.time() - line_time0
                print "pixel time:", float(time.time() - line_time0)/self.Nh
                line_time0 = time.time()
                
                # read stage position every line
                self.stage.read_from_hardware()
                
        #scanning done
        #except Exception as err:
        #    self.interrupt()
        #    raise err
        finally:
            #save  data file
            save_dict = {
                     'detector_map': self.detector_map,
                     'h_array': self.h_array,
                     'v_array': self.v_array,
                     'Nv': self.Nv,
                     'Nh': self.Nh,
                     'extent': self.extent,
                    }               

                    
            for lqname,lq in self.gui.logged_quantities.items():
                save_dict[lqname] = lq.val
            
            for hc in self.gui.hardware_components.values():
                for lqname,lq in hc.logged_quantities.items():
                    save_dict[hc.name + "_" + lqname] = lq.val
            
            for lqname,lq in self.logged_quantities.items():
                save_dict[self.name +"_"+ lqname] = lq.val
    
            self.fname = "%i_atto_map.npz" % time.time()
            np.savez_compressed(self.fname, **save_dict)
            print "Atto 2D Scan Saved", self.fname

            if not self.interrupt_measurement_called:
                self.measurement_sucessfully_completed.emit()
            else:
                pass


    def update_display(self):
        #print "updating figure"
        self.imgplot.set_data(self.detector_map[:,:])
        try:
            count_min =  np.percentile(self.detector_map[np.nonzero(self.detector_map)],1)
        except Exception as err:
            count_min = 0
        count_max = np.percentile(self.detector_map,99.999)
        assert count_max > count_min
        self.imgplot.set_clim(count_min, count_max)
        self.imgplot.set_cmap('gray')
        self.fig2d.canvas.draw()
        
