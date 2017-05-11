# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Feb  9 2012)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class ScanningTRPLControlFrame
###########################################################################

class ScanningTRPLControlFrame ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Scanning TRPL Time Histogram Map", pos = wx.DefaultPosition, size = wx.Size( 1024,640 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer4 = wx.FlexGridSizer( 0, 1, 0, 0 )
		fgSizer4.SetFlexibleDirection( wx.BOTH )
		fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_panel_scanarea = wx.Panel( self.m_panel4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer_scanarea = wx.FlexGridSizer( 0, 4, 0, 0 )
		fgSizer_scanarea.SetFlexibleDirection( wx.BOTH )
		fgSizer_scanarea.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText1 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"Scan Area", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText1, 0, wx.ALL, 5 )
		
		self.m_staticText_maxdim = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"max: 100 x 100 um", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText_maxdim.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText_maxdim, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText2 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"X:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText2, 0, wx.ALL, 5 )
		
		self.m_textCtrl_x0 = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_textCtrl_x0, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_textCtrl_x1 = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"75", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_textCtrl_x1, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText3 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"um", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText3, 0, wx.ALL, 5 )
		
		self.m_staticText4 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"Y:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText4, 0, wx.ALL, 5 )
		
		self.m_textCtrl_y0 = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_textCtrl_y0, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_textCtrl_y1 = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"75", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_textCtrl_y1, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText5 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"um", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText5, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText11 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"Scan Step", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText11, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText111 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"dX:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText111.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText111, 0, wx.ALL, 5 )
		
		self.m_textCtrl_dx = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"1000", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_textCtrl_dx, 0, wx.ALL, 5 )
		
		self.m_staticText12 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"nm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText12, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText13 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"dY:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText13, 0, wx.ALL, 5 )
		
		self.m_textCtrl_dy = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"1000", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_textCtrl_dy, 0, wx.ALL, 5 )
		
		self.m_staticText14 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"nm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText14, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText15 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"Current Position", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText15, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText18 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"x:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText18, 0, wx.ALL, 5 )
		
		self.m_textCtrl_current_x = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		self.m_textCtrl_current_x.SetBackgroundColour( wx.Colour( 255, 128, 0 ) )
		
		fgSizer_scanarea.Add( self.m_textCtrl_current_x, 0, wx.ALL, 5 )
		
		self.m_textCtrl_set_current_x = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		fgSizer_scanarea.Add( self.m_textCtrl_set_current_x, 0, wx.ALL, 5 )
		
		self.m_staticText19 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"um", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText19, 0, wx.ALL, 5 )
		
		self.m_staticText20 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"y:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText20.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText20, 0, wx.ALL, 5 )
		
		self.m_textCtrl_current_y = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		self.m_textCtrl_current_y.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		self.m_textCtrl_current_y.SetBackgroundColour( wx.Colour( 255, 128, 0 ) )
		
		fgSizer_scanarea.Add( self.m_textCtrl_current_y, 0, wx.ALL, 5 )
		
		self.m_textCtrl_set_current_y = wx.TextCtrl( self.m_panel_scanarea, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		fgSizer_scanarea.Add( self.m_textCtrl_set_current_y, 0, wx.ALL, 5 )
		
		self.m_staticText21 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"um", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText21, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText23 = wx.StaticText( self.m_panel_scanarea, wx.ID_ANY, u"Scan Control", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )
		fgSizer_scanarea.Add( self.m_staticText23, 0, wx.ALL, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer_scanarea.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_button_start = wx.Button( self.m_panel_scanarea, wx.ID_ANY, u"Start Scan", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_button_start, 1, wx.ALL|wx.EXPAND, 5 )
		
		self.m_button_stop = wx.Button( self.m_panel_scanarea, wx.ID_ANY, u"Stop Scan", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer_scanarea.Add( self.m_button_stop, 1, wx.ALL|wx.EXPAND, 5 )
		
		
		self.m_panel_scanarea.SetSizer( fgSizer_scanarea )
		self.m_panel_scanarea.Layout()
		fgSizer_scanarea.Fit( self.m_panel_scanarea )
		fgSizer4.Add( self.m_panel_scanarea, 1, wx.EXPAND |wx.ALL, 5 )
		
		self.m_panel_measure = wx.Panel( self.m_panel4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer6 = wx.FlexGridSizer( 0, 6, 0, 0 )
		fgSizer6.SetFlexibleDirection( wx.BOTH )
		fgSizer6.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText16 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"PicoHarp", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )
		fgSizer6.Add( self.m_staticText16, 0, wx.ALL, 5 )
		
		self.m_staticText161 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Measurement", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText161.Wrap( -1 )
		fgSizer6.Add( self.m_staticText161, 0, wx.ALL|wx.EXPAND, 5 )
		
		
		fgSizer6.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer6.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer6.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		
		fgSizer6.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText17 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Time Acq", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText17.Wrap( -1 )
		fgSizer6.Add( self.m_staticText17, 0, wx.ALL, 5 )
		
		self.m_textCtrl_tacq = wx.TextCtrl( self.m_panel_measure, wx.ID_ANY, u"0.01", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer6.Add( self.m_textCtrl_tacq, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText22 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"sec", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )
		fgSizer6.Add( self.m_staticText22, 0, wx.ALL, 5 )
		
		self.m_staticText27 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"SyncDivider", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )
		fgSizer6.Add( self.m_staticText27, 0, wx.ALL, 5 )
		
		m_choice_syncdividerChoices = [ u"1", u"2", u"4", u"8" ]
		self.m_choice_syncdivider = wx.Choice( self.m_panel_measure, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice_syncdividerChoices, 0 )
		self.m_choice_syncdivider.SetSelection( 3 )
		fgSizer6.Add( self.m_choice_syncdivider, 0, wx.ALL|wx.EXPAND, 5 )
		
		
		fgSizer6.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText29 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Range", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText29.Wrap( -1 )
		fgSizer6.Add( self.m_staticText29, 0, wx.ALL, 5 )
		
		self.m_textCtrl_phrange = wx.TextCtrl( self.m_panel_measure, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer6.Add( self.m_textCtrl_phrange, 0, wx.ALL|wx.EXPAND, 5 )
		
		
		fgSizer6.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText291 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Offset", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText291.Wrap( -1 )
		fgSizer6.Add( self.m_staticText291, 0, wx.ALL, 5 )
		
		self.m_textCtrl_phoffset = wx.TextCtrl( self.m_panel_measure, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer6.Add( self.m_textCtrl_phoffset, 0, wx.ALL, 5 )
		
		self.m_staticText34 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"ns", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText34.Wrap( -1 )
		fgSizer6.Add( self.m_staticText34, 0, wx.ALL, 5 )
		
		self.m_staticText35 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"ZeroCross0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText35.Wrap( -1 )
		fgSizer6.Add( self.m_staticText35, 0, wx.ALL, 5 )
		
		self.m_spinCtrl_zerocross0 = wx.SpinCtrl( self.m_panel_measure, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 10 )
		fgSizer6.Add( self.m_spinCtrl_zerocross0, 0, wx.ALL, 5 )
		
		self.m_staticText36 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"mV", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText36.Wrap( -1 )
		fgSizer6.Add( self.m_staticText36, 0, wx.ALL, 5 )
		
		self.m_staticText37 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"ZeroCross1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText37.Wrap( -1 )
		fgSizer6.Add( self.m_staticText37, 0, wx.ALL, 5 )
		
		self.m_spinCtrl_zerocross1 = wx.SpinCtrl( self.m_panel_measure, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 10 )
		fgSizer6.Add( self.m_spinCtrl_zerocross1, 0, wx.ALL, 5 )
		
		self.m_staticText38 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"mV", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText38.Wrap( -1 )
		fgSizer6.Add( self.m_staticText38, 0, wx.ALL, 5 )
		
		self.m_staticText351 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Level0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText351.Wrap( -1 )
		fgSizer6.Add( self.m_staticText351, 0, wx.ALL, 5 )
		
		self.m_textCtrl_level0 = wx.TextCtrl( self.m_panel_measure, wx.ID_ANY, u"10", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer6.Add( self.m_textCtrl_level0, 0, wx.ALL, 5 )
		
		self.m_staticText42 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"mV", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText42.Wrap( -1 )
		fgSizer6.Add( self.m_staticText42, 0, wx.ALL, 5 )
		
		self.m_staticText43 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Level1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText43.Wrap( -1 )
		fgSizer6.Add( self.m_staticText43, 0, wx.ALL, 5 )
		
		self.m_textCtrl_level1 = wx.TextCtrl( self.m_panel_measure, wx.ID_ANY, u"50", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer6.Add( self.m_textCtrl_level1, 0, wx.ALL, 5 )
		
		self.m_staticText44 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"mV", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText44.Wrap( -1 )
		fgSizer6.Add( self.m_staticText44, 0, wx.ALL, 5 )
		
		self.m_staticline3 = wx.StaticLine( self.m_panel_measure, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer6.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline4 = wx.StaticLine( self.m_panel_measure, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer6.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline5 = wx.StaticLine( self.m_panel_measure, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer6.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline6 = wx.StaticLine( self.m_panel_measure, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer6.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline7 = wx.StaticLine( self.m_panel_measure, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer6.Add( self.m_staticline7, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline8 = wx.StaticLine( self.m_panel_measure, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer6.Add( self.m_staticline8, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticText211 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Counts 0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText211.Wrap( -1 )
		fgSizer6.Add( self.m_staticText211, 0, wx.ALL, 5 )
		
		self.m_textCtrl_count0 = wx.TextCtrl( self.m_panel_measure, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		fgSizer6.Add( self.m_textCtrl_count0, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText221 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Hz", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText221.Wrap( -1 )
		fgSizer6.Add( self.m_staticText221, 0, wx.ALL, 5 )
		
		self.m_staticText2111 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Counts 1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2111.Wrap( -1 )
		fgSizer6.Add( self.m_staticText2111, 0, wx.ALL, 5 )
		
		self.m_textCtrl_count1 = wx.TextCtrl( self.m_panel_measure, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		self.m_textCtrl_count1.SetFont( wx.Font( 16, 74, 90, 90, False, "MS Shell Dlg 2" ) )
		
		fgSizer6.Add( self.m_textCtrl_count1, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText2211 = wx.StaticText( self.m_panel_measure, wx.ID_ANY, u"Hz", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2211.Wrap( -1 )
		fgSizer6.Add( self.m_staticText2211, 0, wx.ALL, 5 )
		
		
		fgSizer6.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_checkBox_picoharp_fastreadout = wx.CheckBox( self.m_panel_measure, wx.ID_ANY, u"Fast Readout", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer6.Add( self.m_checkBox_picoharp_fastreadout, 0, wx.ALL, 5 )
		
		
		self.m_panel_measure.SetSizer( fgSizer6 )
		self.m_panel_measure.Layout()
		fgSizer6.Fit( self.m_panel_measure )
		fgSizer4.Add( self.m_panel_measure, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_panel_plot_ctrl = wx.Panel( self.m_panel4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer3 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer3.SetFlexibleDirection( wx.BOTH )
		fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		
		self.m_panel_plot_ctrl.SetSizer( fgSizer3 )
		self.m_panel_plot_ctrl.Layout()
		fgSizer3.Fit( self.m_panel_plot_ctrl )
		fgSizer4.Add( self.m_panel_plot_ctrl, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		self.m_panel4.SetSizer( fgSizer4 )
		self.m_panel4.Layout()
		fgSizer4.Fit( self.m_panel4 )
		bSizer1.Add( self.m_panel4, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.m_panel_plot = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer11 = wx.BoxSizer( wx.VERTICAL )
		
		
		self.m_panel_plot.SetSizer( bSizer11 )
		self.m_panel_plot.Layout()
		bSizer11.Fit( self.m_panel_plot )
		bSizer1.Add( self.m_panel_plot, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
	

