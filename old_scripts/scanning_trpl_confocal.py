'''
Created on Mar 18, 2012

@author: esbarnard
'''

import time
import numpy as np
import wx

from lab_wx_utils import LoggedQuantity, MPLFigureWithToolbarWX, wx_yielded_sleep
from scanning_trpl_confocal_gui_wx import ScanningTRPLControlFrame

from equipment import MCLNanoDrive, SRSlockin, LockinStage, PicoHarp300

HARDWARE_DEBUG = True

class ScanningTRPLConfocalApp(wx.App):

    def OnInit(self):
       
        print "OnInit"

        self.HARDWARE_DEBUG = HARDWARE_DEBUG
        
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

        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self.on_timer)
        
        self.timer.Start(2000)
        
        self.update_display()
        self.frame.Show()
        return True

    def on_timer(self,e):
        self.read_from_hardware()
        self.update_display()

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
        
        self.waittime = float(self.frame.m_textCtrl_waittime.GetValue())
        self.average_n = int(self.frame.m_textCtrl_average_n.GetValue())

        # create data arrays
        self.integrated_count_map_c0 = np.zeros((self.Nx, self.Ny), dtype=int)
        self.integrated_count_map_c1 = np.zeros((self.Nx, self.Ny), dtype=int)
        #self.time_trace_map = np.zeros( (self.Nx, self.Ny, self.picoharp.HISTCHAN),dtype=int)

        #update figure
        self.aximg = self.ax.imshow(self.integrated_count_map_c1, 
                                    origin='lower',
                                    vmin=5e4, vmax=2e5, interpolation='nearest', 
                                    extent=[self.x0, self.x1, self.y0, self.y1])
        self.wxfig.redraw()
        
        
    
        for j in range(self.Ny):
            #self.nanodrive.SetY(self.y_array[j])
            if not self.scanning:
                    continue
            y = self.y_array[j]
            self.lockinstage.sety(y)
            self.read_from_hardware()
            y = self.ypos
            for i in range(self.Nx):
                if not self.scanning:
                    continue
                x = self.xpos  = self.x_array[i]
                wx.Yield()
                #self.nanodrive.SetX(self.x_array[i])
                #self.nanodrive.set_pos(x, y)
                #print "nanodrive set_pos: ", x, y
                self.lockinstage.setx(x)
                #if self.HARDWARE_DEBUG: print "lockin stage moved to ", x, y
                
                
                #ph.setup_experiment()#Range, Offset, Tacq, SyncDivider, CFDZeroCross0, CFDLevel0, CFDZeroCross1, CFDLevel1)
                #ph.start_histogram(Tacq=2300)
                c0avg = 0
                c1avg = 0
                for n in range(self.average_n):
                    if self.waittime > 0.1:
                        wx_yielded_sleep(self.waittime)
                    else:
                        time.sleep(self.waittime)
                    c0, c1 = self.picoharp.read_count_rates()
                    c0avg += c0
                    c1avg += c1
                c0avg /= self.average_n
                c1avg /= self.average_n
                
                #print c0avg, c1avg
                
                self.integrated_count_map_c0[j,i] = c0avg
                self.integrated_count_map_c1[j,i] = c1avg
                
                #x1, y1 = self.nanodrive.get_pos()
                #print "get pos: ", x1,y1
                
                # update display
                self.update_display()
                
                if not (i % 10):
                    #self.update_figure()
                    print "updating figure"
                    self.read_from_hardware()
                    self.aximg.set_data(self.integrated_count_map_c1)
                    self.wxfig.redraw()

        # clean up after scan
        self.aximg.set_data(self.integrated_count_map_c1)
        self.wxfig.redraw()
        self.update_display()
        self.scanning = False
        print "scanning done"
        
        print "saving data"
        t0 = time.time()
        np.savetxt("%i_confocal_scan.csv" % t0, self.integrated_count_map_c1, delimiter=',')
        
    
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
    app = ScanningTRPLConfocalApp()
    app.MainLoop()
    