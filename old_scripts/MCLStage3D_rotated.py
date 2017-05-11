'''
Created on July 18, 2012

@author: esbarnard
'''

import time
import numpy as np
import wx

from lab_wx_utils import MPLFigureWithToolbarWX, wx_yielded_sleep


from equipment.mcl_nanodrive import MCLNanoDrive

HARDWARE_DEBUG = False

from MCLStage3D_gui_wx import MCLStage3DFrame


class MCLStage3DApp(wx.App):

    def OnInit(self):
    
        self.HARDWARE_DEBUG = HARDWARE_DEBUG
        
        self.frame = MCLStage3DFrame(None)
        
        self.nanodrive = MCLNanoDrive(debug=self.HARDWARE_DEBUG)
        
        try:
            self.frame.m_staticText_maxdim.SetLabel("[ %g x %g x %g ]" % (self.nanodrive.cal_X, self.nanodrive.cal_Y, self.nanodrive.cal_Z) )
        except Exception as e:
            print e
            self.frame.m_staticText_maxdim.SetLabel("[ ? ? ? ]")
            
        
        
        
        
        y,x,z = self.nanodrive.get_pos()

        self.frame.m_scrollBar_x.SetScrollbar(100*x/self.nanodrive.cal_Y, 1, 100, 1, refresh=True)
        self.frame.m_scrollBar_y.SetScrollbar(100*y/self.nanodrive.cal_X, 1, 100, 1, refresh=True)
        self.frame.m_scrollBar_z.SetScrollbar(100*z/self.nanodrive.cal_Z, 1, 100, 1, refresh=True)

        self.frame.m_textCtrl_x.SetValue("%02.3f" % x)
        self.frame.m_textCtrl_y.SetValue("%02.3f" % y)
        self.frame.m_textCtrl_z.SetValue("%02.3f" % z)

        self.frame.m_scrollBar_x.Bind(wx.EVT_SCROLL, self.on_scroll)
        self.frame.m_scrollBar_y.Bind(wx.EVT_SCROLL, self.on_scroll)
        self.frame.m_scrollBar_z.Bind(wx.EVT_SCROLL, self.on_scroll)
        
        
        self.frame.m_textCtrl_x.Bind(wx.EVT_TEXT_ENTER, self.on_change_text)
        self.frame.m_textCtrl_y.Bind(wx.EVT_TEXT_ENTER, self.on_change_text)
        self.frame.m_textCtrl_z.Bind(wx.EVT_TEXT_ENTER, self.on_change_text)

        
        
        # Figure
        self.wxfig = MPLFigureWithToolbarWX(self.frame.m_panel_plot)
        self.fig = self.wxfig.fig
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, self.nanodrive.cal_Y)
        self.ax.set_ylim(self.nanodrive.cal_X,0)
        
        self.xypos_line, = self.ax.plot([x], [y], 'ro')
        
        self.frame.Show()
        return True

    def on_scroll(self,evt):
        
        self.frame.m_scrollBar_x.Refresh()
        self.frame.m_scrollBar_y.Refresh()
        self.frame.m_scrollBar_z.Refresh()

        new_x = self.frame.m_scrollBar_x.GetThumbPosition()*0.01*self.nanodrive.cal_Y
        new_y = self.frame.m_scrollBar_y.GetThumbPosition()*0.01*self.nanodrive.cal_X
        new_z = self.frame.m_scrollBar_z.GetThumbPosition()*0.01*self.nanodrive.cal_Z

        self.nanodrive.set_pos(new_y, new_x, new_z)
        
        y,x,z = self.nanodrive.get_pos()

        #self.frame.m_scrollBar_x.SetScrollbar(100*x/self.nanodrive.cal_X, 1, 100, 1, refresh=True)
        #self.frame.m_scrollBar_y.SetScrollbar(100*y/self.nanodrive.cal_Y, 1, 100, 1, refresh=True)
        #self.frame.m_scrollBar_z.SetScrollbar(100*z/self.nanodrive.cal_Z, 1, 100, 1, refresh=True)
        
        self.frame.m_textCtrl_x.SetValue("%02.3f" % x)
        self.frame.m_textCtrl_y.SetValue("%02.3f" % y)
        self.frame.m_textCtrl_z.SetValue("%02.3f" % z)

        self.xypos_line.set_xdata([x])
        self.xypos_line.set_ydata([y])
        
        self.wxfig.redraw()
        
        #self.frame.m_scrollBar_x.Refresh()
        #self.frame.m_scrollBar_y.Refresh()
        #self.frame.m_scrollBar_z.Refresh()

    def on_change_text(self,evt):
        new_x = float(self.frame.m_textCtrl_x.GetValue())
        new_y = float(self.frame.m_textCtrl_y.GetValue())
        new_z = float(self.frame.m_textCtrl_z.GetValue())

        self.nanodrive.set_pos(new_y, new_x, new_z)

        y,x,z = self.nanodrive.get_pos()

        self.frame.m_textCtrl_x.SetValue("%02.3f" % x)
        self.frame.m_textCtrl_y.SetValue("%02.3f" % y)
        self.frame.m_textCtrl_z.SetValue("%02.3f" % z)
        
        self.frame.m_scrollBar_x.SetScrollbar(100*x/self.nanodrive.cal_Y, 1, 100, 1, refresh=True)
        self.frame.m_scrollBar_y.SetScrollbar(100*y/self.nanodrive.cal_X, 1, 100, 1, refresh=True)
        self.frame.m_scrollBar_z.SetScrollbar(100*z/self.nanodrive.cal_Z, 1, 100, 1, refresh=True)

        self.wxfig.redraw()

if __name__ == '__main__':
    app = MCLStage3DApp()
            
    app.MainLoop()
    