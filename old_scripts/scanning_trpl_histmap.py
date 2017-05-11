'''
Created on Mar 18, 2012

@author: esbarnard
'''

import time
import datetime
import numpy as np
import wx

from lab_wx_utils import LoggedQuantity, MPLFigureWithToolbarWX, wx_yielded_sleep
from scanning_trpl_histmap_gui_wx import ScanningTRPLControlFrame

from equipment import MCLNanoDrive, SRSlockin, LockinStage, PicoHarp300

HARDWARE_DEBUG = True

class ScanningTRPLHistMapApp(wx.App):

    def OnInit(self):
       
        print "OnInit"

        self.HARDWARE_DEBUG = HARDWARE_DEBUG
        
        self.STORED_HISTCHAN = 5000
        
        self.frame = ScanningTRPLControlFrame(None)

        # Logged Quantities
        self.x_position = LoggedQuantity(name = 'x_position', dtype=np.float,
                                    display_textctrl = self.frame.m_textCtrl_current_x,
                                    input_textctrl = self.frame.m_textCtrl_set_current_x)
        self.y_position = LoggedQuantity(name = 'x_position', dtype=np.float,
                                    display_textctrl = self.frame.m_textCtrl_current_y,
                                    input_textctrl = self.frame.m_textCtrl_set_current_y)

        # Figure
        self.wxfig = MPLFigureWithToolbarWX(self.frame.m_panel_plot)
        self.fig = self.wxfig.fig
        self.ax = self.fig.add_subplot(111)
        

        # hardware
        self.scanning = False
        
        """
        #self.nanodrive = MCLNanoDrive(debug=self.HARDWARE_DEBUG)
        try:
            self.frame.m_staticText_maxdim.SetLabel("max: %g x %g um" % (self.nanodrive.cal_X, self.nanodrive.cal_Y) )
        except Exception as e:
            print e
            self.frame.m_staticText_maxdim.SetLabel("max: ? x ? um")
        """    
        
        self.frame.m_staticText_maxdim.SetLabel("max: 75 x 75 um")
         
        self.srslockin = SRSlockin(port="COM5", gpibaddr=8)
        self.lockinstage = LockinStage(srs=self.srslockin, 
                                       POSMIN=0, POSMAX=75, channels={'x':1, 'y':2, 'z':3})
        
        self.picoharp = PicoHarp300(devnum=0, debug=self.HARDWARE_DEBUG)

        self.read_from_hardware()

        self.x_position.hardware_set_func = lambda x: self.lockinstage.setx(x)
        self.y_position.hardware_set_func = lambda y: self.lockinstage.sety(y)

        #self.x_position.hardware_set_func = lambda x: self.nanodrive.set_pos_ax(x, 1)
        #self.y_position.hardware_set_func = lambda y: self.nanodrive.set_pos_ax(y, 2)

        # update figure
        #self.ax.set_xlim(0, self.nanodrive.cal_X)
        #self.ax.set_ylim(0, self.nanodrive.cal_Y)
        self.ax.set_xlim(0, 75)
        self.ax.set_ylim(0, 75)

        # events
        self.frame.Bind(wx.EVT_BUTTON, self.on_start_scan, self.frame.m_button_start)
        self.frame.Bind(wx.EVT_BUTTON, self.on_stop_scan,  self.frame.m_button_stop)

        self.timer = wx.Timer(id=2001)
        self.timer.Bind(wx.EVT_TIMER, self.on_timer)
        
        self.timer.Start(2000)
        
        self.fast_timer = wx.Timer(id=2002)
        self.fast_timer.Bind(wx.EVT_TIMER, self.on_fast_timer)
        
        self.frame.m_checkBox_picoharp_fastreadout.Bind(
                                    wx.EVT_CHECKBOX, self.on_fast_timer_checkbox)
        
        self.update_display()
        self.frame.Show()
        return True

    def on_timer(self,e):
        self.read_from_hardware()
        self.update_display()
    
    def on_fast_timer(self,e):
        self.picoharp.read_count_rates()
        self.frame.m_textCtrl_count0.SetValue(str(self.picoharp.Countrate0))
        self.frame.m_textCtrl_count1.SetValue(str(self.picoharp.Countrate1))
    
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
        
        self.tacq = int(float(self.frame.m_textCtrl_tacq.GetValue())*1000)
        self.phrange = int(self.frame.m_textCtrl_phrange.GetValue())
        self.phoffset = int(self.frame.m_textCtrl_phoffset.GetValue())
        self.syncdiv = int(self.frame.m_choice_syncdivider.GetString(self.frame.m_choice_syncdivider.GetSelection()))

        self.zerocross0 = int(self.frame.m_spinCtrl_zerocross0.GetValue())
        self.zerocross1 = int(self.frame.m_spinCtrl_zerocross0.GetValue())

        self.level0 = int(self.frame.m_textCtrl_level0.GetValue())
        self.level1 = int(self.frame.m_textCtrl_level1.GetValue())

        # create data arrays
        #self.integrated_count_map_c0 = np.zeros((self.Nx, self.Ny), dtype=int)
        self.integrated_count_map_c1 = np.zeros((self.Ny, self.Nx), dtype=int)
        self.time_trace_map = np.zeros( (self.Ny, self.Nx, self.STORED_HISTCHAN),dtype=int)
        
        print "shape:", self.integrated_count_map_c1.shape, self.time_trace_map.shape 

        #update figure
        self.aximg = self.ax.imshow(self.integrated_count_map_c1, 
                                    origin='lower',
                                    vmin=1e4, vmax=1e5, interpolation='nearest', 
                                    extent=[self.x0, self.x1, self.y0, self.y1])
        self.wxfig.redraw()
        
        
        # set up experiment
        self.picoharp.setup_experiment(
                   Range=self.phrange, Offset=self.phoffset, 
                   Tacq=self.tacq, SyncDivider=self.syncdiv, 
                   CFDZeroCross0=self.zerocross0, CFDLevel0=self.level0, 
                   CFDZeroCross1=self.zerocross1, CFDLevel1=self.level1 )
    
        for jj in range(self.Ny):
            #self.nanodrive.SetY(self.y_array[j])
            if not self.scanning:
                    break
            y = self.y_array[jj]
            self.lockinstage.sety(y)
            self.read_from_hardware()
            y = self.ypos
            for ii in range(self.Nx):
                if not self.scanning:
                    break
                x = self.xpos  = self.x_array[ii]
                wx.Yield()
                #self.nanodrive.SetX(self.x_array[i])
                #self.nanodrive.set_pos(x, y)
                #print "nanodrive set_pos: ", x, y
                self.lockinstage.setx(x)
                #if self.HARDWARE_DEBUG: print "lockin stage moved to ", x, y
                
                ph = self.picoharp
                
                ph.start_histogram(Tacq=self.tacq)
                while not ph.check_done_scanning():
                    wx.Yield()
                
                ph.stop_histogram()
                hist_data = ph.read_histogram_data()
                
                self.time_trace_map[jj,ii,:] = hist_data[0:self.STORED_HISTCHAN]
                
                self.integrated_count_map_c1[jj,ii] = sum(hist_data)
                
                #x1, y1 = self.nanodrive.get_pos()
                #print "get pos: ", x1,y1
                
                # update display
                try:
                    self.update_display()
                except Exception, err:
                    print "Failed to update_display", err
                
                if not (ii % 5):
                    #self.update_figure()
                    try:
                        print "updating figure"
                        self.read_from_hardware()
                        self.aximg.set_data(self.integrated_count_map_c1)
                        count_min =  np.min(self.integrated_count_map_c1[np.nonzero(self.integrated_count_map_c1)])
                        count_max = np.max(self.integrated_count_map_c1)
                        self.aximg.set_clim(count_min, count_max + 1)
                        self.wxfig.redraw()
                    except Exception, err:
                        print "Failed to update figure:", err

        # clean up after scan
        self.aximg.set_data(self.integrated_count_map_c1)
        self.wxfig.redraw()
        self.update_display()
        self.scanning = False
        print "scanning done"
        
        print "saving data"
        t0 = time.time()
        np.savetxt("%i_confocal_scan.csv" % t0, 
                   self.integrated_count_map_c1, delimiter=',')
        
        save_params = ["time_trace_map", "x0", "x1", "y0", "y1", "tacq", "phrange", 
                       "phoffset", "syncdiv", "Nx", "Ny", "zerocross0", "zerocross1",
                       "x_array", "y_array",
                       "level0", "level1", "dx", "dy", "integrated_count_map_c1"]
        save_dict = dict()
        for key in save_params:
            save_dict[key] = getattr(self, key)
        
        np.savez_compressed("%i_time_trace_map.npz" % t0, **save_dict)
        print "data saved"
    
    def read_from_hardware(self):
        self.picoharp.read_count_rates()

        self.xpos = self.lockinstage.getx()
        self.ypos = self.lockinstage.gety()
        return self.xpos, self.ypos
    
    def on_stop_scan(self,e):
        self.scanning = False
        #self.nanodrive.get_pos()
        self.update_display()

    def update_display(self):
        #self.x_position.update_value(self.nanodrive.x_pos)
        #self.y_position.update_value(self.nanodrive.y_pos)
        
        self.x_position.update_value(self.xpos)
        self.y_position.update_value(self.ypos)
        
        
        self.frame.m_textCtrl_count0.SetValue(str(self.picoharp.Countrate0))
        self.frame.m_textCtrl_count1.SetValue(str(self.picoharp.Countrate1))

if __name__ == '__main__':
    app = ScanningTRPLHistMapApp()
    app.MainLoop()
    