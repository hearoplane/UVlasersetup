from collections import namedtuple
import numpy as np
from equipment.mcl_nanodrive import MCLNanoDrive
from equipment.ni_freq_counter import NI_FreqCounter
import time

xyz_tuple = namedtuple('xyz', 'x y z')


class Confocal3DScanNI(object):

    INPUT_PARAM_NAMES = """x0 x1 dx y0 y1 dy z0 z1 dz
                    t_exposure
                    axis_scan_order mcl_axis_translation""".split()
                    
    
    def __init__(self, **params):
     
        for p in self.INPUT_PARAM_NAMES :
            setattr(self, p, params[p])
        
        self.x_array = np.arange(self.x0, self.x1, self.dx, dtype=float)
        self.y_array = np.arange(self.y0, self.y1, self.dy, dtype=float)
        self.z_array = np.arange(self.z0, self.z1, self.dz, dtype=float)
        
        self.Nx = len(self.x_array)
        self.Ny = len(self.y_array)
        self.Nz = len(self.z_array)
    
        self.mcl_axis_translation = xyz_tuple(*self.mcl_axis_translation)
    
        self.HARDWARE_DEBUG = False
    
        #HARDWARE
        self.nanodrive = MCLNanoDrive(debug=self.HARDWARE_DEBUG)
                        
        self.freq_counter = NI_FreqCounter(debug = self.HARDWARE_DEBUG)
        
        #DATA ARRAYS
        self.count_freq_map = np.zeros((self.Nz, self.Ny, self.Nx, ), dtype=np.float64)
        
    def run_3d_scan(self):
        
        
        
        self.set_ijk = (-1,-1,-1)

        self.scanning = True
    
        time0 = time.time()
        
        self.freq_counter.read_freq_buffer() #flush buffer
    
        for iii, ijk in enumerate(ijk_generator((self.Nx, self.Ny, self.Nz), self.axis_scan_order)):

            #previous ijk
            ip, jp, kp = self.set_ijk

            # new ijk
            i,j,k = ijk
            
            
            # move stage
            if i != ip:
                x = self.x_array[i]
                self.nanodrive.set_pos_ax( x , self.mcl_axis_translation.x )
            if j != jp:
                y = self.y_array[j]
                self.nanodrive.set_pos_ax( y , self.mcl_axis_translation.y )
            if k != kp:
                z = self.z_array[k]
                self.nanodrive.set_pos_ax( z , self.mcl_axis_translation.z )
            
            self.set_ijk = ijk
            
            #t1 = time.time()
            self.read_from_hardware()
            #print "read_from_hardware (s)", time.time() - t1
        
            #t1 = time.time()

            time.sleep(self.t_exposure)
            freq = self.freq_counter.read_average_freq_in_buffer()
            #print "counter acquire (s)", time.time() - t1
            
                            
            cts = self.count_freq_map[k,j,i] = freq
            
            REPORT_INTERVAL = 10
            if ((i + j + k) % REPORT_INTERVAL) == 0 :
                print ijk, cts
                t_now = time.time()
                pixel_time = (t_now - time0) / REPORT_INTERVAL
                print "sec per pixel:", pixel_time, "| time remaining (s)",  ( ((self.Nx*self.Ny*self.Nz) - iii)*pixel_time )
                time0 = t_now
            

        #Finish up after scan
        print "saving data..."
        save_params = self.INPUT_PARAM_NAMES + [
                        "count_freq_map","Nx", "Ny", "Nz", 
                        "x_array", "y_array", "z_array"]
        save_dict = dict()
        for key in save_params:
            save_dict[key] = getattr(self, key)
        
        t0 = time.time()
        save_fname = "%i_confocal3d.npz" % t0
        np.savez_compressed(save_fname, **save_dict)
        print "data saved as %s" % save_fname

    def read_from_hardware(self):
        
        pos = self.nanodrive.get_pos()
        
        self.xpos = pos[self.mcl_axis_translation.x-1]
        self.ypos = pos[self.mcl_axis_translation.y-1]
        self.zpos = pos[self.mcl_axis_translation.z-1]

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
    

if __name__ == '__main__':
    params = dict(
        x0 = 35,    x1 = 40, dx = 0.1,
        y0 = 0,     y1 = 40, dy = 0.1,
        z0 = 32,    z1 = 38, dz = 0.1,
        t_exposure = 0.01,
        axis_scan_order = (0,2,1),
        mcl_axis_translation = (2,1,3),
        )
    
    scan = Confocal3DScanNI(**params)
    
    scan.run_3d_scan()
