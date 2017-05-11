'''
Created on Mar 18, 2012

@author: esbarnard
'''

import time
import datetime
import numpy as np
import wx

from lab_wx_utils import LoggedQuantity, MPLFigureWithToolbarWX, wx_yielded_sleep
from scanning_spectrum_gui_wx import ScanningSpectrumControlFrame

import pylab as pl

from equipment.mcl_nanodrive import MCLNanoDrive
from equipment.acton_spec import ActonSpectrometer
from equipment.andor_ccd import AndorCCD


XAXIS_ID = 2 # "y"-axis in nanodrive
#FOR LATERAL SCAN
#YAXIS_ID = 1 # "x"-axis in nanodrive

#FOR DEPTH SCAN
YAXIS_ID = 3 # "z"-axis in nanodrive


HARDWARE_DEBUG = False

ANDOR_HFLIP = True
ANDOR_VFLIP = False
ANDOR_AD_CHAN = 1 # 16-bit channel
ANDOR_AD_CHAN = 0 # 14-bit channel


ANDOR_DEFAULT_EXPOSURE = 1.0
ANDOR_DEFAULT_EMGAIN = 100

ROW0 = 250
ROW1 = 325


HISTORY_LEN = 100

SPEC_COMM_PORT = "COM8"

class ScanningTRPLHistMapApp(wx.App):

    def OnInit(self):
       
        print "OnInit"

        self.HARDWARE_DEBUG = HARDWARE_DEBUG
        
        
        self.frame = ScanningSpectrumControlFrame(None)

        # Logged Quantities
        self.x_position = LoggedQuantity(name = 'x_position', dtype=np.float,
                                    display_textctrl = self.frame.m_textCtrl_current_x,
                                    input_textctrl = self.frame.m_textCtrl_set_current_x)
        self.y_position = LoggedQuantity(name = 'y_position', dtype=np.float,
                                    display_textctrl = self.frame.m_textCtrl_current_y,
                                    input_textctrl = self.frame.m_textCtrl_set_current_y)

        # Figure ###############################################################
        self.wxfig = MPLFigureWithToolbarWX(self.frame.m_panel_plot)
        self.fig = self.wxfig.fig
        self.ax = self.fig.add_subplot(111)
        
        # Spectrum Fig
        self.fig2 = pl.figure(2)
        self.ax_speclive  = self.fig2.add_subplot(111)
        #self.c0_hist_line, = self.ax2.plot(np.zeros(HIST_LEN,dtype=float))
        #self.c1_hist_line, = self.ax2.plot(np.zeros(HIST_LEN,dtype=float))
        #self.hist_vline = self.ax2.axvline(0)
        #self.c0_hist = np.zeros(HIST_LEN,dtype=float)
        #self.c1_hist = np.zeros(HIST_LEN,dtype=float)
        self.fig2.show()
        #self.history_i = 0                            
        
        self.spec_plotline, = self.ax_speclive.plot(range(0,512), range(0,512))
        
        ##################### hardware #########################################
        
        self.scanning = False
        
        
        
        ######## MCL NanoDrive Stage ###########################################
        self.nanodrive = MCLNanoDrive(debug=self.HARDWARE_DEBUG)
        try:
            self.frame.m_staticText_maxdim.SetLabel("max: %g x %g um" % (self.nanodrive.cal[XAXIS_ID], self.nanodrive.cal[YAXIS_ID]) )
        except Exception as e:
            print e
            self.frame.m_staticText_maxdim.SetLabel("max: ? x ? um")
        
        self.read_from_hardware()

        self.x_position.hardware_set_func = lambda x: self.nanodrive.set_pos_ax(x, XAXIS_ID)
        self.y_position.hardware_set_func = lambda y: self.nanodrive.set_pos_ax(y, YAXIS_ID)

        
        #Spectrometer ##########################################################
        self.spec     = ActonSpectrometer(port=SPEC_COMM_PORT, debug=self.HARDWARE_DEBUG, dummy=False)
        
        print self.spec.read_grating_info()
        
        self.frame.m_choice_spec_grating.Clear()
        for gnum, gname in self.spec.gratings:
            self.frame.m_choice_spec_grating.Append("%i %s" % (gnum, gname))

        print self.spec.gratings_dict
        
        self.spec.read_grating()
        
        self.frame.m_choice_spec_grating.SetSelection(self.spec.grating - 1)
        
        self.spec.read_wl()
        
        self.frame.m_textCtrl_current_spec_wl.SetValue("%f" % self.spec.wl)

        self.frame.m_textCtrl_set_spec_wl.Bind(wx.EVT_TEXT_ENTER, self.on_change_spec_wl)
        self.frame.m_choice_spec_grating.Bind(wx.EVT_CHOICE, self.on_change_spec_grating)
        #self.frame.m_button_spec_stop.Bind(wx.EVT_BUTTON, self.on_spec_stop_motion)
        ########################################################################

        #Andor CCD##############################################################

        self.ccd = AndorCCD(debug=self.HARDWARE_DEBUG)

        print "Andor CCD"
        print "%g x %g" % (self.ccd.Nx, self.ccd.Ny)
        
        self.spectrum_length = self.ccd.Nx
        
        self.ccd.set_ro_image_mode()
        self.ccd.set_trigger_mode('internal')
        self.ccd.set_image_flip(ANDOR_HFLIP, ANDOR_VFLIP)
        print "flip", self.ccd.get_image_flip()
        self.ccd.set_ad_channel(ANDOR_AD_CHAN)
        self.ccd.set_exposure_time(1.0)
        self.ccd.set_EMCCD_gain(1)
        self.ccd.set_cooler_on()
        self.ccd.get_temperature()
        self.ccd.set_shutter_open()
        
        self.spec_fig = pl.figure(3)
        self.specimg_ax = self.spec_fig.add_subplot(111)
        self.spec_ax = self.spec_fig.add_subplot(611)
        self.spec_ax.set_xlim(0,512)
        self.spec_fig.show()
        
        self.ccd_img = self.specimg_ax.imshow( np.zeros((self.ccd.Nx, self.ccd.Ny),dtype=np.int32) , origin='lower', interpolation='nearest')
        self.specimg_ax.axhline(ROW0, color='w')
        self.specimg_ax.axhline(ROW1, color='w')
        self.specimg_ax.axvline(256, color='w')
        
        self.spec_line, = self.spec_ax.plot( np.zeros(self.ccd.Nx, dtype=np.int32), 'k-')
        self.spec_line2, = self.spec_ax.plot( np.zeros(self.ccd.Nx, dtype=np.int32), 'g-')
        
        self.video_mode = False        
        self.frame.m_button_video_mode_start.Bind(wx.EVT_BUTTON, self.on_start_video_mode)
        self.frame.m_button_video_mode_stop.Bind( wx.EVT_BUTTON, self.on_stop_video_mode)
        
        self.frame.m_textCtrl_andor_exposure.SetValue(str(ANDOR_DEFAULT_EXPOSURE))
        self.frame.m_textCtrl_andor_em.SetValue(str(ANDOR_DEFAULT_EMGAIN))
        
        
        # A/D rate
        
        choice_adc = self.frame.m_choice_andor_adc
        choice_adc.Clear()
        for speed in self.ccd.HSSpeeds[ANDOR_AD_CHAN]:
            choice_adc.Append("%g MHz" % (speed))
        
        choice_adc.SetSelection(0)
        self.ccd.set_hs_speed(0)
        
        choice_adc.Bind(wx.EVT_CHOICE, self.on_change_andor_adc)
        
        
        ########################################################################        



        # update figure
        self.ax.set_xlim(0, self.nanodrive.cal[XAXIS_ID])
        self.ax.set_ylim(0, self.nanodrive.cal[YAXIS_ID])

        # events
        self.frame.Bind(wx.EVT_BUTTON, self.on_start_scan, self.frame.m_button_start)
        self.frame.Bind(wx.EVT_BUTTON, self.on_stop_scan,  self.frame.m_button_stop)

        self.timer = wx.Timer(id=2001)
        self.timer.Bind(wx.EVT_TIMER, self.on_timer)
        
        self.timer.Start(2000)
        
        #self.fast_timer = wx.Timer(id=2002)
        #self.fast_timer.Bind(wx.EVT_TIMER, self.on_fast_timer)
        
        #self.frame.m_checkBox_picoharp_fastreadout.Bind(
        #                            wx.EVT_CHECKBOX, self.on_fast_timer_checkbox)
        
        self.update_display()
        self.frame.Show()
        return True

    def on_timer(self,e):
        self.read_from_hardware()
        self.update_display()
    
#    def on_fast_timer(self,e):
#        self.picoharp.read_count_rates()
#        self.frame.m_textCtrl_count0.SetValue(str(self.picoharp.Countrate0))
#        self.frame.m_textCtrl_count1.SetValue(str(self.picoharp.Countrate1))
#        self.c0_hist[self.hist_i] = self.picoharp.Countrate0
#        self.c1_hist[self.hist_i] = self.picoharp.Countrate1
#        
#        #self.c0_hist_line.set_ydata(self.c0_hist)
#        self.c1_hist_line.set_ydata(self.c1_hist)
#        self.hist_vline.set_xdata([self.hist_i]*2)
#        
#        self.history_i += 1
#        self.history_i %= HISTORY_LEN
#        
#        if (self.hist_i % 10) == 0:
#            self.ax2.relim()
#            self.ax2.autoscale_view(scalex=False, scaley=True)
#            #self.ax2.autoscale()
#            
#        self.fig2.canvas.draw()
    
    def on_fast_timer_checkbox(self,e):
        fast_timer_enable = self.frame.m_checkBox_picoharp_fastreadout.GetValue()
        if fast_timer_enable:
            self.fast_timer.Start(100)
        else:
            self.fast_timer.Stop()

    def on_start_scan(self,e):
        print "start scan"
        
        self.scanning = True
        
        # get scan parameters:
        self.x0 = float(self.frame.m_textCtrl_x0.GetValue())
        self.x1 = float(self.frame.m_textCtrl_x1.GetValue())
        self.y0 = float(self.frame.m_textCtrl_y0.GetValue())
        self.y1 = float(self.frame.m_textCtrl_y1.GetValue())
    
        self.dx = float(self.frame.m_textCtrl_dx.GetValue())/1000.
        self.dy = float(self.frame.m_textCtrl_dy.GetValue())/1000.
    
        self.x_array = np.arange(self.x0, self.x1, self.dx, dtype=float)
        self.y_array = np.arange(self.y0, self.y1, self.dy, dtype=float)
        
        self.Nx = len(self.x_array)
        self.Ny = len(self.y_array)
        
        print "Nx, Ny", self.Nx, self.Ny
        
        self.andor_exposure = float(self.frame.m_textCtrl_andor_exposure.GetValue())
        self.andor_em_gain = int(self.frame.m_textCtrl_andor_em.GetValue())


        ### create data arrays
        self.integrated_count_map = np.zeros((self.Ny, self.Nx), dtype=int)
        self.spectrum_map = np.zeros( (self.Ny, self.Nx, self.spectrum_length),dtype=int)
        
        print "shape:", self.integrated_count_map.shape, self.spectrum_map.shape 

        ### update figure
        self.aximg = self.ax.imshow(self.integrated_count_map, 
                                    origin='lower',
                                    vmin=1e4, vmax=1e5, interpolation='nearest', 
                                    extent=[self.x0, self.x1, self.y0, self.y1])
        self.wxfig.redraw()
        
        
        # set up experiment
        self.ccd.set_exposure_time(self.andor_exposure)
        self.ccd.set_EMCCD_gain(self.andor_em_gain)


        # Scan!            
        line_time0 = time.time()
        for jj in range(self.Ny):
            if not self.scanning:
                    break
            y = self.y_array[jj]
            self.nanodrive.set_pos_ax(y, YAXIS_ID)
            self.read_from_hardware()
            y = self.ypos
            print "line time:", time.time() - line_time0
            print "pixel time:", float(time.time() - line_time0)/len(self.x_array)
            line_time0 = time.time()
            
            if jj % 2: #odd lines
                x_line_indicies = range(self.Nx)
            else:       #even lines -- traverse in opposite direction
                x_line_indicies = range(self.Nx)[::-1]                  
                    
            for ii in x_line_indicies:
                if not self.scanning:
                    break
                x = self.xpos  = self.x_array[ii]
                wx.Yield()
                self.nanodrive.set_pos_ax(x, XAXIS_ID)
                
                
                self.ccd.start_acquisition()
                stat = "ACQUIRING"
                while stat!= "IDLE":
                    wx_yielded_sleep(self.ccd.exposure_time * 0.25)
                    stati, stat = self.ccd.get_status()
                self.ccd.get_acquired_data()
                
                spectrum = np.sum(self.ccd.buffer[ROW0:ROW1], axis=0)
                
                self.spectrum_map[jj,ii,:] = spectrum
                
                self.integrated_count_map[jj,ii] = sum(spectrum)
                
                # update display
                try:
                    self.update_display()
                except Exception, err:
                    print "Failed to update_display", err
                
                try:
                    self.spec_plotline.set_ydata(spectrum)
                    self.ax_speclive.relim()
                    self.ax_speclive.autoscale_view(tight=None, scalex=False, scaley=True)
                    self.fig2.canvas.draw()
                except Exception as err:
                    print "Failed to update spectrum plot", err
                
                if not (ii % 5):
                    #self.update_figure()
                    try:
                        #print "updating figure"
                        #self.read_from_hardware()
                        self.aximg.set_data(self.integrated_count_map)
                        try:
                            count_min =  np.min(self.integrated_count_map[np.nonzero(self.integrated_count_map)])
                        except Exception as err:
                            count_min = 0
                        count_max = np.max(self.integrated_count_map)
                        self.aximg.set_clim(count_min, count_max + 1)
                        self.wxfig.redraw()
                    except Exception, err:
                        print "Failed to update figure:", err
                

        # clean up after scan
        self.aximg.set_data(self.integrated_count_map)
        self.wxfig.redraw()
        self.update_display()
        self.scanning = False
        print "scanning done"
        
        print "saving data..."
        t0 = time.time()
        #np.savetxt("%i_confocal_scan.csv" % t0, 
        #           self.integrated_count_map, delimiter=',')
        
        save_params = ["spectrum_map", "x0", "x1", "y0", "y1",
                       "Nx", "Ny", 
                       "x_array", "y_array",
                       "dx", "dy", "integrated_count_map"]
        save_dict = dict()
        for key in save_params:
            save_dict[key] = getattr(self, key)
        

        for key in ["XAXIS_ID", "YAXIS_ID","HARDWARE_DEBUG","ANDOR_HFLIP","ANDOR_VFLIP","ANDOR_AD_CHAN","ROW0","ROW1"]:
            save_dict[key] = globals()[key]
        
        for key in ["wl", "gratings", "grating"]:
            save_dict["spec_"+key] = getattr(self.spec, key)
        
        for key in ["exposure_time", "em_gain", "temperature", "ad_chan", "ro_mode", "Nx", "Ny"]:
            save_dict["andor_"+key] = getattr(self.ccd, key)
            
        
        save_dict["time_saved"] = t0
        
        np.savez_compressed("%i_spec_map.npz" % t0, **save_dict)
        print "data saved"
    
    def read_from_hardware(self):
        pos = self.nanodrive.get_pos()
        self.xpos = pos[XAXIS_ID-1]
        self.ypos = pos[YAXIS_ID-1]
        
        try:
            self.ccd.get_temperature()
        except:
            pass
    
    def on_stop_scan(self,e):
        self.scanning = False
        self.update_display()

    def update_display(self):
        self.x_position.update_value(self.xpos)
        self.y_position.update_value(self.ypos)
        self.frame.m_textCtrl_andor_temp.SetValue(str(self.ccd.temperature))

    # Acton Spectrometer Events ################################################
    def on_change_spec_wl(self,evt):
        self.spec_wl = float(self.frame.m_textCtrl_set_spec_wl.GetValue())
        self.frame.m_statusBar.SetStatusText("Setting spectrometer wavelength to %f nm ..." % self.spec_wl)
        #self.spec.write_wl_nonblock(self.spec_wl)
        #wx.Yield()
        #wx.Sleep(1)
        #self.spec_done = False
        #while not self.spec_done:
        #    self.spec_done = self.spec.read_done_status()
        #    self.spec_wl_current = self.spec.read_wl()
        #    self.frame.m_textCtrl_current_spec_wl.SetValue("%f" % self.spec_wl_current)
        #    wx.Yield()
        #    wx.Sleep(1)
        self.spec.write_wl(self.spec_wl)
        wx.Yield()
        wx.Sleep(0.2)
        self.spec_wl_current = self.spec.read_wl()                
        self.frame.m_textCtrl_current_spec_wl.SetValue("%f" % self.spec_wl_current)
        
        self.frame.m_textCtrl_set_spec_wl.SetValue("")
        self.frame.m_statusBar.SetStatusText("Done setting Spectrometer")
        
    def on_change_spec_grating(self,evt):
        new_grating_index = self.frame.m_choice_spec_grating.GetSelection()
        gnum, gname = self.spec.gratings[new_grating_index]
        if self.HARDWARE_DEBUG: print "Moving spectrometer grating to %i %s (please wait until the move is complete)" % (gnum,gname)
        self.spec.write_grating(gnum)

    # Andor CCD Events #########################################################
    def on_change_andor_adc(self,evt):
        new_hs_speed_i = self.frame.m_choice_andor_adc.GetSelection()
        self.ccd.set_hs_speed(new_hs_speed_i)

    def on_start_video_mode(self,evt):
        
        self.andor_exposure = float(self.frame.m_textCtrl_andor_exposure.GetValue())
        self.andor_em_gain = int(self.frame.m_textCtrl_andor_em.GetValue())

        self.ccd.set_exposure_time( self.andor_exposure)
        self.ccd.set_EMCCD_gain(    self.andor_em_gain)
        
        self.frame.m_button_video_mode_start.Disable()
        self.frame.m_button_video_mode_stop.Enable(1)
        
        self.video_mode = True
        
        while self.video_mode:
            self.ccd.start_acquisition()
            stat = "ACQUIRING"
            while stat!= "IDLE":
                wx_yielded_sleep(0.1)
                stati, stat = self.ccd.get_status()
            self.ccd.get_acquired_data()
            self.ccd_img.set_data(self.ccd.buffer)
            count_min = np.min(self.ccd.buffer)
            count_max = np.max(self.ccd.buffer)
            self.ccd_img.set_clim(count_min, count_max)
            
            
            self.spectra_data = np.average(self.ccd.buffer, axis=0)
            self.spectra_data2 = np.average(self.ccd.buffer[ROW0:ROW1], axis=0)
            
            self.spec_line.set_ydata(self.spectra_data)
            self.spec_line2.set_ydata(self.spectra_data2)

            self.spec_ax.relim()
            self.spec_ax.autoscale_view(scalex=False, scaley=True)
            
            self.spec_fig.canvas.draw()
            
    def on_stop_video_mode(self,evt):
        self.video_mode = False
        self.frame.m_button_video_mode_start.Enable(1)
        self.frame.m_button_video_mode_stop.Disable()
            


if __name__ == '__main__':
    app = ScanningTRPLHistMapApp()
    app.MainLoop()
    
