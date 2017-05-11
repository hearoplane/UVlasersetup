'''
Created on Nov 27, 2012

@author: esbarnard
'''

import time
import datetime
import numpy as np
import wx

from lab_wx_utils import LoggedQuantity, MPLFigureWithToolbarWX, wx_yielded_sleep
#from scanning_spectrum_gui_wx import ScanningSpectrumControlFrame
from spectrum_camera_control_gui_wx import SpectrumCameraControlFrame

import pylab as pl

#from equipment.camera_wrapper import CameraControl
from equipment.acton_spec import ActonSpectrometer
from equipment.andor_ccd import AndorCCD

HARDWARE_DEBUG = True

AD_CHAN = 0

class AndorCameraTestApp(wx.App):

    def OnInit(self):
       
        print "OnInit"

        self.HARDWARE_DEBUG = HARDWARE_DEBUG
                
        self.frame = SpectrumCameraControlFrame(None)

        #self.frame.m_panel_scanarea.Disable()
        
        # Figure
        self.wxfig = MPLFigureWithToolbarWX(self.frame.m_panel_plot)
        self.fig = self.wxfig.fig
        self.ax = self.fig.add_subplot(111)
        self.ax2 = self.fig.add_subplot(611)
        self.ax2.set_xlim(0,512)

        
        #Spectrometer ##########################################################
        self.spec     = ActonSpectrometer(port="COM4", debug=self.HARDWARE_DEBUG)
        
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
        self.frame.m_button_spec_stop.Bind(wx.EVT_BUTTON, self.on_spec_stop_motion)
        ########################################################################

        #Andor CCD##############################################################

        self.ccd = AndorCCD(debug=self.HARDWARE_DEBUG)

        print "Andor CCD"
        print "%g x %g" % (self.ccd.Nx, self.ccd.Ny)
        
        self.ccd.set_ro_image_mode()
        self.ccd.set_trigger_mode('internal')
        self.ccd.set_exposure_time(1.0)
        self.ccd.set_EMCCD_gain(1)
        self.ccd.set_shutter_open()
        
        self.ccd_img = self.ax.imshow( np.zeros((self.ccd.Nx, self.ccd.Ny),dtype=np.int32) , origin='lower', interpolation='nearest')
        self.spec_line, = self.ax2.plot( np.zeros(self.ccd.Nx, dtype=np.int32), 'k-')
        self.spec_line2, = self.ax2.plot( np.zeros(self.ccd.Nx, dtype=np.int32), 'g-')
        self.video_mode = False
        
        self.frame.m_button_video_mode_start.Bind(wx.EVT_BUTTON, self.on_start_video_mode)
        self.frame.m_button_video_mode_stop.Bind( wx.EVT_BUTTON, self.on_stop_video_mode)
        
        
        # A/D rate
        
        choice_adc = self.frame.m_choice_andor_adc
        choice_adc.Clear()
        for speed in self.ccd.HSSpeeds[AD_CHAN]:
            choice_adc.Append("%g MHz" % (speed))
        
        choice_adc.SetSelection(0)
        self.ccd.set_hs_speed(0)
        
        choice_adc.Bind(wx.EVT_CHOICE, self.on_change_andor_adc)
        
        
        ########################################################################



        self.timer = wx.Timer(id=2001)
        self.timer.Bind(wx.EVT_TIMER, self.on_timer)
        
        self.timer.Start(2000)
        
        self.fast_timer = wx.Timer(id=2002)
        self.fast_timer.Bind(wx.EVT_TIMER, self.on_fast_timer)
        
        #self.frame.m_checkBox_picoharp_fastreadout.Bind(
        #                            wx.EVT_CHECKBOX, self.on_fast_timer_checkbox)
        
        #self.update_display()
        self.frame.Show()
        return True

    def on_timer(self,e):
        try:
            temp = self.ccd.get_temperature()
            self.frame.m_textCtrl_andor_temp.SetValue(str(temp))
        except:
            print "failed to get temperature"
            
        #self.read_from_hardware()
        #self.update_display()
    
    def on_fast_timer(self,e):
        self.picoharp.read_count_rates()
        self.frame.m_textCtrl_count0.SetValue(str(self.picoharp.Countrate0))
        self.frame.m_textCtrl_count1.SetValue(str(self.picoharp.Countrate1))
        self.c0_hist[self.hist_i] = self.picoharp.Countrate0
        self.c1_hist[self.hist_i] = self.picoharp.Countrate1
        
        #self.c0_hist_line.set_ydata(self.c0_hist)
        self.c1_hist_line.set_ydata(self.c1_hist)
        self.hist_vline.set_xdata([self.hist_i]*2)
        
        self.hist_i += 1
        self.hist_i %= HIST_LEN
        
        if (self.hist_i % 10) == 0:
            self.ax2.relim()
            self.ax2.autoscale_view(scalex=False, scaley=True)
            #self.ax2.autoscale()
            
        self.fig2.canvas.draw()
    
    def on_fast_timer_checkbox(self,e):
        fast_timer_enable = self.frame.m_checkBox_picoharp_fastreadout.GetValue()
        if fast_timer_enable:
            self.fast_timer.Start(100)
        else:
            self.fast_timer.Stop()

    
    def read_from_hardware(self):
        self.picoharp.read_count_rates()

        self.ypos, self.xpos, z = self.nanodrive.get_pos()
        #self.xpos = self.lockinstage.getx()
        #self.ypos = self.lockinstage.gety()
        return self.xpos, self.ypos
    
    def update_display(self):
        #self.x_position.update_value(self.nanodrive.x_pos)
        #self.y_position.update_value(self.nanodrive.y_pos)
        
        self.x_position.update_value(self.xpos)
        self.y_position.update_value(self.ypos)
        
        
        self.frame.m_textCtrl_count0.SetValue(str(self.picoharp.Countrate0))
        self.frame.m_textCtrl_count1.SetValue(str(self.picoharp.Countrate1))
        
    def on_change_spec_wl(self,evt):
        self.spec_wl = float(self.frame.m_textCtrl_set_spec_wl.GetValue())
        self.frame.m_statusBar.SetStatusText("Setting spectrometer wavelength to %f nm ..." % self.spec_wl)
        self.spec.write_wl_nonblock(self.spec_wl)
        wx.Yield()
        wx.Sleep(1)
        self.spec_done = False
        while not self.spec_done:
            self.spec_done = self.spec.read_done_status()
            self.spec_wl_current = self.spec.read_wl()
            self.frame.m_textCtrl_current_spec_wl.SetValue("%f" % self.spec_wl_current)
            wx.Yield()
            wx.Sleep(1)
        self.frame.m_textCtrl_set_spec_wl.SetValue("")
        self.frame.m_statusBar.SetStatusText("Done setting Spectrometer")
        
    def on_change_spec_grating(self,evt):
        new_grating_index = self.frame.m_choice_spec_grating.GetSelection()
        gnum, gname = self.spec.gratings[new_grating_index]
        if self.HARDWARE_DEBUG: print "Moving spectrometer grating to %i %s (please wait until the move is complete)" % (gnum,gname)
        self.spec.write_grating(gnum)
        
    def on_spec_stop_motion(self,evt):
        pass
        
    
    def on_start_video_mode(self,evt):
        
        
        self.andor_exposure = float(self.frame.m_textCtrl_andor_exposure.GetValue())
        self.andor_em_gain = int(self.frame.m_textCtrl_andor_em.GetValue())

        self.ccd.set_exposure_time(self.andor_exposure)
        self.ccd.set_EMCCD_gain(self.andor_em_gain)
        
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
            self.spectra_data2 = np.average(self.ccd.buffer[200:350], axis=0)
            
            self.spec_line.set_ydata(self.spectra_data)
            self.spec_line2.set_ydata(self.spectra_data2)

            self.ax2.relim()
            self.ax2.autoscale_view(scalex=False, scaley=True)

            self.wxfig.redraw()
            
            
    def on_stop_video_mode(self,evt):
        self.video_mode = False
        self.frame.m_button_video_mode_start.Enable(1)
        self.frame.m_button_video_mode_stop.Disable()
            
    
    
    # Andor CCD Events
    def on_change_andor_adc(self,evt):
        new_hs_speed_i = self.frame.m_choice_andor_adc.GetSelection()
        self.ccd.set_hs_speed(new_hs_speed_i)
        
        

if __name__ == '__main__':
    app = AndorCameraTestApp()
    app.MainLoop()
    