import numpy as np
import time
from .measurement import Measurement 


def ijk_generator(dims, axis_order=(0,1,2)):
    """3D zig-zag scan pattern generator with arbitrary fast axis order"""

    ax0, ax1, ax2 = axis_order
    
    for i_ax0 in range( dims[ax0] ):
        zig_or_zag0 = (1,-1)[i_ax0 % 2]
        for i_ax1 in range( dims[ax1] )[::zig_or_zag0]:
            zig_or_zag1 = (1,-1)[(i_ax0+i_ax1) % 2]
            for i_ax2 in range( dims[ax2] )[::zig_or_zag1]:
            
                ijk = [0,0,0]
                ijk[ax0] = i_ax0
                ijk[ax1] = i_ax1
                ijk[ax2] = i_ax2
                
                yield tuple(ijk)
    return
 
class Base3DScan(Measurement):
    
    def setup(self):
        
        self.display_update_period = 0.1 #seconds

        #connect events        
        self.int_time = self.gui.apd_counter_hc.int_time
        
        # local logged quantities
        lq_params = dict(dtype=float, vmin=-1,vmax=100, ro=False, unit='um' )
        self.x0 = self.add_logged_quantity('x0',  initial=25, **lq_params  )
        self.x1 = self.add_logged_quantity('x1',  initial=45, **lq_params  )
        self.y0 = self.add_logged_quantity('y0',  initial=25, **lq_params  )
        self.y1 = self.add_logged_quantity('y1',  initial=45, **lq_params  )
        self.z0 = self.add_logged_quantity('z0',  initial=15, **lq_params  )
        self.z1 = self.add_logged_quantity('z1',  initial=35, **lq_params  )

        self.dx = self.add_logged_quantity('dx', initial=1, **lq_params)
        self.dy = self.add_logged_quantity('dy', initial=1, **lq_params)
        self.dz = self.add_logged_quantity('dz', initial=1, **lq_params)
        
        
        scan_order_choices = "XYZ YXZ YZX XZY ZXY YXZ YZX ZYX".split()
        scan_order_choices = zip(scan_order_choices, scan_order_choices)
        
        self.axis_scan_order = self.add_logged_quantity('axis_scan_order', dtype=str, initial="XYZ",
                                                        choices = scan_order_choices)
        
        # connect to gui        
        
        self.scan_specific_setup()
    
    def scan_specific_setup(self):
        "subclass this function to setup additional logged quantities and gui connections"
        # logged quantities
        # connect events
        raise NotImplementedError()
        
    def setup_figure(self):
        #2D scan area
        raise NotImplementedError()
    
    def pre_scan_setup(self):
        raise NotImplementedError()
        # hardware
        # create data arrays
        # update figure
    
    def collect_pixel(self, i,j,k):
        # collect data
        # store in arrays        
        raise NotImplementedError()


    def scan_specific_savedict(self):
        "override to add specific data to the save file. should return a dictionary"
        return dict()

    def _run(self):
        # Hardware 
        self.stage = self.gui.mcl_xyz_stage_hc
        self.nanodrive = self.stage.nanodrive
        
        # Data arrays
        self.x_array = np.arange(self.x0.val, self.x1.val, self.dx.val, dtype=float)
        self.y_array = np.arange(self.y0.val, self.y1.val, self.dy.val, dtype=float)
        self.z_array = np.arange(self.z0.val, self.z1.val, self.dz.val, dtype=float)
        
        self.Nx = len(self.x_array)
        self.Ny = len(self.y_array)
        self.Nz = len(self.z_array)
        
        #self.range_extent = [self.h0.val, self.h1.val, self.v0.val, self.v1.val]

        #self.corners =  [self.h_array[0], self.h_array[-1], self.v_array[0], self.v_array[-1]]
        
        #self.imshow_extent = [self.h_array[ 0] - 0.5*self.dh.val,
        #                      self.h_array[-1] + 0.5*self.dh.val,
        #                      self.v_array[ 0] - 0.5*self.dv.val,
        #                      self.v_array[-1] + 0.5*self.dv.val]
        
        #scan specific setup
        self.pre_scan_setup()
                
        # TODO Stop other timers?!
        
        print "scanning"
        
        print "Acquiring %i pixels" % (self.Nx*self.Ny*self.Nz)
                
        try:
            x_axis_id = self.stage.x_axis_id
            y_axis_id = self.stage.y_axis_id
            z_axis_id = self.stage.z_axis_id
            
            ax_trans = dict(X=0, Y=1, Z=2)
            axis_scan_order_ids = [ax_trans[ax] for ax in self.axis_scan_order.val]
            
            print "axis_scan_order", self.axis_scan_order.val
            print "axis_scan_order_ids", axis_scan_order_ids
            
            ijk_list = list(ijk_generator((self.Nx, self.Ny, self.Nz), axis_scan_order_ids[::-1]))
            
            # move slowly to start position
            i,j,k = ijk_list[0]
            start_pos = [self.x_array[i], self.y_array[j],self.z_array[k]]
            self.nanodrive.set_pos_slow(*start_pos)
            
            self.ijk_previous = ijk_list[0]
            
            self.read_stage_position()          

            # Scan!            
            time0 = time.time()
            
            
            for iii, ijk in enumerate(ijk_list):
            
                if self.interrupt_measurement_called:
                    break            
                
                #previous ijk
                ip, jp, kp = self.ijk_previous
    
                # new ijk
                i,j,k = ijk
                
                print ijk
                   
                # move stage
                if i != ip:
                    x = self.x_array[i]
                    self.nanodrive.set_pos_ax( x , self.stage.x_axis_id )
                if j != jp:
                    y = self.y_array[j]
                    self.nanodrive.set_pos_ax( y , self.stage.y_axis_id )
                if k != kp:
                    z = self.z_array[k]
                    self.nanodrive.set_pos_ax( z , self.stage.z_axis_id )

                # collect data
                self.collect_pixel(i, j, k)            
    
                # print out info
                if ((i + j + k) % 10) == 0 :
                    print ijk
                    t_now = time.time()
                    pixel_time = (t_now - time0)*0.1
                    print "sec per pixel:", pixel_time, "| time remaining (s)",  ( ((self.Nx*self.Ny*self.Nz) - iii)*pixel_time )
                    time0 = t_now
                    
                # read stage position every pixel
                self.read_stage_position()    
                
                #get ready for next pixel
                self.ijk_previous = ijk
      
        #scanning done
        #except Exception as err:
        #    self.interrupt()
        #    raise err
        finally:
            #save  data file
            save_dict = {
                     'x_array': self.x_array,
                     'y_array': self.y_array,
                     'z_array': self.z_array,
                     'Nx': self.Nx,
                     'Ny': self.Ny,
                     'Nz': self.Nz,
                     }               

            save_dict.update(self.scan_specific_savedict())
                    
            for lqname,lq in self.gui.logged_quantities.items():
                save_dict[lqname] = lq.val
            
            for hc in self.gui.hardware_components.values():
                for lqname,lq in hc.logged_quantities.items():
                    save_dict[hc.name + "_" + lqname] = lq.val
            
            for lqname,lq in self.logged_quantities.items():
                save_dict[self.name +"_"+ lqname] = lq.val
    
            self.fname = "%i_%s.npz" % (time.time(), self.name)
            np.savez_compressed(self.fname, **save_dict)
            print self.name, "saved:", self.fname

            if not self.interrupt_measurement_called:
                self.measurement_sucessfully_completed.emit()
            else:
                pass

    def read_stage_position(self):
        self.stage.x_position.read_from_hardware()
        self.stage.y_position.read_from_hardware()
        self.stage.z_position.read_from_hardware()
        