from collections import namedtuple
import numpy as np
from equipment import MCLNanoDrive
from equipment.acton_spec import ActonSpectrometer
from equipment.andor_ccd import AndorCCD
import time

#import pylab as pl
#pl.ion()

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


ANDOR_HFLIP = True
ANDOR_VFLIP = False


SPEC_COMM_PORT = "COM4"


SHOW_GRAPH = False

class ConfocalSpectrum3DScan(object):


    INPUT_PARAM_NAMES = """x0 x1 dx y0 y1 dy z0 z1 dz
                    t_exposure emgain ad_chan ad_hs_speed_index bin_row0 bin_row1
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
                
        self.mono     = ActonSpectrometer(port=SPEC_COMM_PORT, debug=self.HARDWARE_DEBUG, dummy=False)
        self.mono_grating = self.mono.read_grating()
        self.mono_wl  = self.mono.read_wl()
        
        self.ccd = AndorCCD(debug=self.HARDWARE_DEBUG)
        print "Andor CCD"
        print "%g x %g" % (self.ccd.Nx, self.ccd.Ny)
        self.spectrum_length = self.ccd.Nx
        self.ccd.set_cooler_on()
        self.ccd.get_temperature()
        
        if SHOW_GRAPH:
            self.fig = pl.figure(1)
            self.ax  = self.fig.add_subplot(111)
            self.spec_plotline, = self.ax.plot(np.ones(self.spectrum_length))
            self.fig.show()
        
        #DATA ARRAYS
        self.integrated_count_map = np.zeros((self.Nz, self.Ny, self.Nx, ), dtype=int)
        self.spec_map = np.zeros( (self.Nz, self.Ny, self.Nx, self.spectrum_length),dtype=np.int32)            
    
    def run_3d_scan(self):
        
        self.ccd.set_ro_image_mode()
        self.ccd.set_trigger_mode('internal')
        self.ccd.set_image_flip(ANDOR_HFLIP, ANDOR_VFLIP)
        print "flip", self.ccd.get_image_flip()
        self.ccd.set_ad_channel(self.ad_chan)
        self.ccd.set_exposure_time(self.t_exposure)
        self.ccd.set_EMCCD_gain(self.emgain)
        self.ccd.set_cooler_on()
        self.ccd.get_temperature()
        self.ccd.set_shutter_open()        
        self.ccd.set_hs_speed(self.ad_hs_speed_index)

        self.set_ijk = (-1,-1,-1)

        self.scanning = True
    
        time0 = time.time()
    
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
            self.ccd.start_acquisition()
            stat = "ACQUIRING"
            while stat!= "IDLE":
                time.sleep(self.ccd.exposure_time * 0.1)
                stati, stat = self.ccd.get_status()
            self.ccd.get_acquired_data()
            #print "ccd acquire (s)", time.time() - t1
            
            spectrum = np.sum(self.ccd.buffer[self.bin_row0:self.bin_row1], axis=0)

            self.spec_map[k,j,i,:] = spectrum
                
            cts = self.integrated_count_map[k,j,i] = sum(spectrum)

           
            
            if ((i + j + k) % 10) == 0 :
                print ijk, cts
                t_now = time.time()
                pixel_time = (t_now - time0)*0.1
                print "sec per pixel:", pixel_time, "| time remaining (s)",  ( ((self.Nx*self.Ny*self.Nz) - iii)*pixel_time )
                time0 = t_now
            
            #if ((i + j + k) % 2) == 0 :
            if True:
                if SHOW_GRAPH:
                    self.spec_plotline.set_ydata(spectrum)
                    self.ax.relim()
                    self.ax.autoscale_view(tight=None, scalex=False, scaley=True)
                    self.fig.canvas.draw()                
        
        #Finish up after scan
        print "saving data..."
        save_params = self.INPUT_PARAM_NAMES + [
                        "spec_map","Nx", "Ny", "Nz", 
                        "spectrum_length",
                        "mono_grating", "mono_wl",
                        "x_array", "y_array", "z_array",
                        "integrated_count_map"]
        save_dict = dict()
        for key in save_params:
            save_dict[key] = getattr(self, key)
        
        t0 = time.time()
        save_fname = "%i_spec_map3d.npz" % t0
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
        x0 = 39,    x1 = 47, dx = 0.15,
        y0 = 30.5,    y1 = 37.5, dy = 0.15,
        z0 = 17,    z1 = 26.5, dz = 0.15,
        t_exposure = 0.1,
        emgain = 100,
        ad_chan = 0,
        ad_hs_speed_index = 0,
        bin_row0 = 250,
        bin_row1 = 325,
        axis_scan_order = (1,2,0),
        mcl_axis_translation = (2,1,3),
        )
    
    scan = ConfocalSpectrum3DScan(**params)
    
    scan.run_3d_scan()
