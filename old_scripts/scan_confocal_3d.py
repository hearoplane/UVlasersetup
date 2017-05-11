from collections import namedtuple
import numpy as np
from equipment.mcl_nanodrive import MCLNanoDrive
from equipment.pypicoharp import PicoHarp300
import time

"""
Parameters

x0, x1, dx
y0, y1, dy
z0, z1, dz

tacq
phrange
phoffset
syncdiv
zerocross0
zerocross1
level0
level1

axis_order = (0,1,2)
zig_zag_scan = True

axis_translation = xyz_tuple( 2,1,3 )
"""

xyz_tuple = namedtuple('xyz', 'x y z')


class ConfocalTRPL3DScan(object):


    INPUT_PARAM_NAMES = """x0 x1 dx y0 y1 dy z0 z1 dz
                    tacq phrange phoffset syncdiv zerocross0 zerocross1 level0 level1
                    axis_scan_order mcl_axis_translation
                    stored_histogram_chan""".split()

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
        #try:
        #    self.frame.m_staticText_maxdim.SetLabel("max: %g x %g um" % (self.nanodrive.cal_Y, self.nanodrive.cal_X) )

        self.picoharp = PicoHarp300(devnum=0, debug=self.HARDWARE_DEBUG)

        #DATA ARRAYS
        self.integrated_count_map = np.zeros((self.Nz, self.Ny, self.Nx, ), dtype=int)
        
        print "size of time_trace_map %e" %  (self.Nx* self.Ny * self.Nz * self.stored_histogram_chan)
        
        self.time_trace_map = np.zeros( (self.Nz, self.Ny, self.Nx, self.stored_histogram_chan),dtype=np.uint16)
                    
    
    def run_3d_scan(self):
        
        self.picoharp.setup_experiment(
                   Binning=self.phrange, SyncOffset=self.phoffset, 
                   Tacq=self.tacq, SyncDivider=self.syncdiv, 
                   CFDZeroCross0=self.zerocross0, CFDLevel0=self.level0, 
                   CFDZeroCross1=self.zerocross1, CFDLevel1=self.level1 )

        self.set_ijk = (-1,-1,-1)


        self.scanning = True
    
        time0 = time.time()
    
        for iii, ijk in enumerate(ijk_generator((self.Nx, self.Ny, self.Nz), self.axis_scan_order)):

            if iii == 0:
                i,j,k = ijk
                print "moving to start position"
                self.nanodrive.set_pos_ax_slow( self.x_array[i] , self.mcl_axis_translation.x )
                self.nanodrive.set_pos_ax_slow( self.y_array[j] , self.mcl_axis_translation.y )
                self.nanodrive.set_pos_ax_slow( self.z_array[k] , self.mcl_axis_translation.z )

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
            
            self.read_from_hardware()
        
            ph = self.picoharp
            
            ph.start_histogram(Tacq=self.tacq)
            while not ph.check_done_scanning():
                time.sleep(0.01)
        
            ph.stop_histogram()
            hist_data = ph.read_histogram_data()


            
            self.time_trace_map[k,j,i,:] = hist_data[0:self.stored_histogram_chan]
                
            cts = self.integrated_count_map[k,j,i] = sum(hist_data)

            if ((i + j + k) % 10) == 0 :
                print ijk, cts
                t_now = time.time()
                pixel_time = (t_now - time0)*0.1
                print "sec per pixel:", pixel_time, "| time remaining (s)",  ( ((self.Nx*self.Ny*self.Nz) - iii)*pixel_time )
                time0 = t_now
                
                        
        #Finish up after scan
        print "saving data..."
        save_params = self.INPUT_PARAM_NAMES + [
                        "time_trace_map","Nx", "Ny", "Nz", 
                        "x_array", "y_array", "z_array",
                        "countrate0",
                        "integrated_count_map"]
        save_dict = dict()
        for key in save_params:
            save_dict[key] = getattr(self, key)
        
        t0 = time.time()
        save_fname = "%i_time_trace_map3d.npz" % t0
        np.savez_compressed(save_fname, **save_dict)
        print "data saved as %s" % save_fname

        
        
    def read_from_hardware(self):
        print self.picoharp.read_count_rates()
        self.countrate0 = self.picoharp.Countrate0
        
        pos = self.nanodrive.get_pos()
        
        self.xpos = pos[self.mcl_axis_translation.x-1]
        self.ypos = pos[self.mcl_axis_translation.y-1]
        self.zpos = pos[self.mcl_axis_translation.z-1]
                
        #self.xpos = self.lockinstage.getx()
        #self.ypos = self.lockinstage.gety()
        #return self.xpos, self.ypos



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
        x0 = 20,    x1 = 55,  dx = 1.0,
        y0 = 20,    y1 = 55,  dy = 1.0,
        z0 =  0.0,    z1 = 50.0,  dz = 1.0,
        tacq = 500,
        phrange = 4,
        phoffset = 0,
        syncdiv = 8,
        zerocross0 = 8, level0 = 10,
        zerocross1 = 10, level1 = 100,
        axis_scan_order = (2,1,0),
        mcl_axis_translation = (2,1,3),
        stored_histogram_chan = 250
        )
    
    scan = ConfocalTRPL3DScan(**params)
    
    scan.run_3d_scan()
