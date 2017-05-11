import time
import numpy as np
import wx

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

import matplotlib.patches as mpatches


class MPLFigureWithToolbarWX(object):
    
    def __init__(self, panel):
        # needs an empty wxPanel with a vertical wxBoxSizer
        self.panel = panel
        self.fig = Figure()
        self.figcanvas = FigureCanvasWxAgg(panel, -1, self.fig)
        self.figtoolbar = NavigationToolbar2Wx(self.figcanvas)
        self.figtoolbar.Realize()

        self.panel.GetSizer().Add(self.figcanvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.panel.GetSizer().Add(self.figtoolbar, 0, wx.LEFT | wx.EXPAND)
        
        self.panel.Layout()
        
    def redraw(self):
        self.figcanvas.draw()

class UpdateablePlotLine(object):
    
    def __init__(self, ax, X, Y=None, dtype=np.float, current_point=-1, **kwargs):
        self.ax = ax
        self.dtype = dtype
        self.X = X
        self.Y = Y
        if Y == None:
            self.Y = np.ones(len(X), dtype=dtype)
        self.current_point = current_point
        
        self.plotline, = self.ax.plot(self.X, self.Y, **kwargs)
        #self.current_point_annotation = self.ax.annotate("", xy = self.current_coord() )
        self.axvline = self.ax.axvline(self.current_coord()[0], color='k')
        
    def next_datapoint_y(self, value):
        self.current_point += 1
        self.current_point %= len(self.X)
        self.Y[self.current_point] = value
    
    def update_line(self):
        self.plotline.set_xdata(self.X)
        self.plotline.set_ydata(self.Y)
        #self.current_point_annotation.set_position( self.current_coord() )
        self.axvline.set_xdata( [self.current_coord()[0], self.current_coord()[0]] )
        
    def redraw(self):
        self.ax.figure.canvas.draw()
    
    def current_coord(self):
        return (self.X[self.current_point], self.Y[self.current_point])
    
class LoggedQuantity(object):
    
    def __init__(self, name=None, dtype=np.float, input_textctrl=None, input_radiobox=None, 
                        display_textctrl=None, display_gauge=None, display_radiobox = None, 
                        updateable_line=None, input_checkbox=None, display_checkbox=None, initial=0,
                        hardware_set_func = None):
        self.name = name
        self.dtype = dtype
        self.input_textctrl = input_textctrl
        self.input_radiobox = input_radiobox
        self.input_checkbox = input_checkbox
        self.display_textctrl = display_textctrl
        self.display_gauge = display_gauge
        self.display_radiobox = display_radiobox
        self.display_checkbox = display_checkbox
        self.updateable_line = updateable_line
        self.val = dtype(initial)
        self.hardware_set_func = hardware_set_func
        
        #event binding
        if self.input_textctrl:
            # self.wxparent = self.input_textctrl.GetTopLevelParent()
            # self.wxparent.BIND(wx.EVT_TEXT_ENTER, self.on_input_event, self.input_textctrl)
            self.input_textctrl.Bind(wx.EVT_TEXT_ENTER, self.on_input_event)
        if input_radiobox:
            self.input_radiobox.Bind(wx.EVT_RADIOBOX, self.on_input_event)
        if input_checkbox:
            self.input_checkbox.Bind(wx.EVT_CHECKBOX, self.on_input_event)
                
    def on_input_event(self, event):
        # grab value from input_textctrl
        if self.input_textctrl:
            val = self.dtype( self.input_textctrl.GetValue() )
        # or from radiobox
        if self.input_radiobox:
            val = self.dtype( self.input_radiobox.GetSelection() )
        if self.input_checkbox:
            val = self.dtype( self.input_checkbox.GetValue() )
        #self.update_value(val, update_display=True, redraw_figures=False)
        self.val = val
        self.update_display()
        # clear text input
        if self.input_textctrl:
            self.input_textctrl.SetValue("")
        
        # tell hardware to update value
        if self.hardware_set_func:
            self.hardware_set_func(self.val)
        
    def update_display(self, redraw_figures=False):
        if self.display_textctrl:
            self.display_textctrl.SetValue(str(self.val))
        if self.display_gauge:
            self.display_gauge.SetValue(int(self.val))
        if self.display_radiobox:
            self.display_radiobox.SetSelection(int(self.val))
        if self.display_checkbox:
            self.display_checkbox.SetValue(bool(self.val))
            
        if self.updateable_line:
            self.updateable_line.update_line()
            if redraw_figures:
                self.updateable_line.redraw()
    
    def create_updateable_line(self, ax, X, **kwargs):
        self.updateable_line = UpdateablePlotLine(ax, X, dtype=self.dtype, **kwargs)
        return self.updateable_line
    
    def update_value(self, val, update_display=True, redraw_figures=False):
        self.val = val
        if self.updateable_line:
            self.updateable_line.next_datapoint_y(self.val)
        if update_display:
            self.update_display(redraw_figures)
            
def wx_yielded_sleep(t):
    t0 = time.time()
    while time.time() - t0 < t:
        wx.Yield()
        time.sleep(0.01)
