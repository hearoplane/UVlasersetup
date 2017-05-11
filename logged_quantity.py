from PySide import  QtCore, QtGui
import pyqtgraph

class LoggedQuantity(QtCore.QObject):

    updated_value = QtCore.Signal((float,),(int,),(bool,), (), (str,),) # signal sent when value has been updated
    updated_text_value = QtCore.Signal(str)
    updated_choice_index_value = QtCore.Signal(int) # emits the index of the value in self.choices
    
    def __init__(self, name, dtype=float, 
                 hardware_read_func=None, hardware_set_func=None, 
                 initial=0, fmt="%g",
                 ro = False,
                 unit = None,
                 vmin=-1e12, vmax=+1e12, choices=None):
        QtCore.QObject.__init__(self)
        
        self.name = name
        self.dtype = dtype
        self.val = dtype(initial)
        self.hardware_read_func = hardware_read_func
        self.hardware_set_func = hardware_set_func
        self.fmt = fmt # string formatting string. This is ignored if dtype==str
        self.unit = unit
        self.vmin = vmin
        self.vmax = vmax
        self.choices = choices # must be tuple [ ('name', val) ... ]
        self.ro = ro # Read-Only?
        self.oldval = None
        
    def read_from_hardware(self, send_signal=True):
        self.oldval = self.val
        if self.hardware_read_func:
            self.val = self.dtype(self.hardware_read_func())
            if send_signal:
                self.send_display_updates()
        return self.val

    @QtCore.Slot(str)
    @QtCore.Slot(float)
    @QtCore.Slot(int)
    @QtCore.Slot(bool)
    @QtCore.Slot()
    def update_value(self, new_val=None, update_hardware=True, send_signal=True):
        #print "called update_value", self.name, new_val
        if new_val == None:
            new_val = self.sender().text()
        self.val = self.dtype(new_val)
        if update_hardware and self.hardware_set_func:
            self.hardware_set_func(self.val)   
        if send_signal:
            self.send_display_updates()
            
    def send_display_updates(self, force=False):
        if (self.oldval != self.val) or (force):
            #print "send display updates", self.name, self.val, self.oldval
            if self.dtype == str:
                self.updated_value[str].emit(self.val)
                self.updated_text_value.emit(self.val)
            else:
                self.updated_value[str].emit( self.fmt % self.val )
                self.updated_text_value.emit( self.fmt % self.val )
            self.updated_value[float].emit(self.val)
            self.updated_value[int].emit(self.val)
            self.updated_value[bool].emit(self.val)
            self.updated_value[()].emit()
            
            if self.choices is not None:
                choice_vals = [c[1] for c in self.choices]
                if self.val in choice_vals:
                    self.updated_choice_index_value.emit(choice_vals.index(self.val) )
            self.oldval = self.val
            
    def update_choice_index_value(self, new_choice_index, **kwargs):
        self.update_value(self.choices[new_choice_index][1], **kwargs)
        
    def connect_bidir_to_widget(self, widget):
        print type(widget)
        if type(widget) == QtGui.QDoubleSpinBox:
            #self.updated_value[float].connect(widget.setValue )
            #widget.valueChanged[float].connect(self.update_value)
            widget.setKeyboardTracking(False)
            if self.vmin is not None:
                widget.setMinimum(self.vmin)
            if self.vmax is not None:
                widget.setMaximum(self.vmax)
            if self.unit is not None:
                widget.setSuffix(" "+self.unit)
            if self.dtype == int:
                widget.setDecimals(0)
            if self.ro:
                widget.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                widget.setReadOnly(True)
            widget.setValue(self.val)
            #events
            self.updated_value[float].connect(widget.setValue)
            if not self.ro:
                widget.valueChanged[float].connect(self.update_value)
        
        elif type(widget) == QtGui.QSpinBox:
            #self.updated_value[float].connect(widget.setValue )
            #widget.valueChanged[float].connect(self.update_value)
            widget.setKeyboardTracking(False)
            if self.vmin is not None:
                widget.setMinimum(self.vmin)
            if self.vmax is not None:
                widget.setMaximum(self.vmax)
            if self.unit is not None:
                widget.setSuffix(" "+self.unit)
            #if self.dtype == int:
            #    widget.setDecimals(0)
            if self.ro:
                widget.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                widget.setReadOnly(True)
            widget.setValue(self.val)
            #events
            self.updated_value[int].connect(widget.setValue)
            if not self.ro:
                widget.valueChanged[int].connect(self.update_value)        
                
        elif type(widget) == QtGui.QCheckBox:
            print self.name
            #self.updated_value[bool].connect(widget.checkStateSet)
            #widget.stateChanged[int].connect(self.update_value)
            # Ed's version
            print "connecting checkbox widget"
            self.updated_value[bool].connect(widget.setChecked)
            widget.toggled[bool].connect(self.update_value)
            if self.ro:
                #widget.setReadOnly(True)
                widget.setEnabled(False)
        elif type(widget) == QtGui.QLineEdit:
            self.updated_text_value[str].connect(widget.setText)
            widget.setReadOnly(False)  # FIXME
            #widget.editingFinishedEvent[str].connect(self.updated_value)          
        elif type(widget) == QtGui.QComboBox:
            # need to have a choice list to connect to a QComboBox
            assert self.choices is not None 
            widget.clear() # removes all old choices
            for choice_name, choice_value in self.choices:
                widget.addItem(choice_name, choice_value)
            self.updated_choice_index_value[int].connect(widget.setCurrentIndex)
            widget.currentIndexChanged.connect(self.update_choice_index_value)
            
        elif type(widget) == pyqtgraph.widgets.SpinBox.SpinBox:
            #widget.setFocusPolicy(QtCore.Qt.StrongFocus)
            suffix = self.unit
            if self.unit is None:
                suffix = ""
            if self.dtype == int:
                        integer = True
                        minStep=1
                        step=1
            else:
                integer = False
                minStep=.1
                step=.1
            widget.setOpts(
                        suffix=suffix,
                        siPrefix=True,
                        dec=True,
                        step=step,
                        minStep=minStep,
                        bounds=[self.vmin, self.vmax],
                        int=integer)            
            if self.ro:
                widget.setEnabled(False)
                widget.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                widget.setReadOnly(True)
            self.updated_value[float].connect(widget.setValue)
            if not self.ro:
                #widget.valueChanged[float].connect(self.update_value)
                widget.valueChanged.connect(self.update_value)
        else:
            raise ValueError("Unknown widget type")
        
        self.send_display_updates(force=True)
        self.widget = widget
    
    def change_choice_list(self, choices):
        widget = self.widget
        
        self.choices = choices
        
        if type(widget) == QtGui.QComboBox:
            # need to have a choice list to connect to a QComboBox
            assert self.choices is not None 
            widget.clear() # removes all old choices
            for choice_name, choice_value in self.choices:
                widget.addItem(choice_name, choice_value)
        else:
            raise RuntimeError("Invalid widget type.")
    
    def change_min_max(self, vmin=0, vmax=99.99):
        widget = self.widget
        self.vmin = vmin
        self.vmax = vmax
        widget.setRange(vmin, vmax)
        
def print_signals_and_slots(obj):
    for i in xrange(obj.metaObject().methodCount()):
        m = obj.metaObject().method(i)
        if m.methodType() == QtCore.QMetaMethod.MethodType.Signal:
            print "SIGNAL: sig=", m.signature(), "hooked to nslots=",obj.receivers(QtCore.SIGNAL(m.signature()))
        elif m.methodType() == QtCore.QMetaMethod.MethodType.Slot:
            print "SLOT: sig=", m.signature()