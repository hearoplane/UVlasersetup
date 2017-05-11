from PySide import QtCore, QtGui
from logged_quantity import LoggedQuantity
from collections import OrderedDict
import pyqtgraph as pg

class HardwareComponent(QtCore.QObject):

    def __init__(self, gui, debug=False):
        """type gui: BaseGUI
        """        
        QtCore.QObject.__init__(self)
        self.gui = gui
        self.debug = debug
        self.logged_quantities = OrderedDict()
        self.operations = OrderedDict()
        
        self.setup()
        
        self._add_control_widgets_to_hardware_tab()
        
        self.has_been_connected_once = False
        self.is_connected = False

    def add_logged_quantity(self, name, **kwargs):
        lq = LoggedQuantity(name=name, **kwargs)
        self.logged_quantities[name] = lq
        return lq

    def add_operation(self, name, op_func):
        """type name: str
           type op_func: QtCore.Slot
        """
        self.operations[name] = op_func   

    def _add_control_widgets_to_hardware_tab(self):
        cwidget = self.gui.ui.hardware_tab_scrollArea_content_widget
        
        self.controls_groupBox = QtGui.QGroupBox(self.name)
        self.controls_formLayout = QtGui.QFormLayout()
        self.controls_groupBox.setLayout(self.controls_formLayout)
        
        cwidget.layout().addWidget(self.controls_groupBox)
        
        self.connect_hardware_checkBox = QtGui.QCheckBox("Connect to Hardware")
        self.controls_formLayout.addRow("Connect", self.connect_hardware_checkBox)
        self.connect_hardware_checkBox.stateChanged.connect(self.enable_connection)
        
        self.control_widgets = OrderedDict()
        for lqname, lq in self.logged_quantities.items():
            #: :type lq: LoggedQuantity
            if lq.choices is not None:
                widget = QtGui.QComboBox()
            elif lq.dtype in [int, float]:
                widget = pg.SpinBox()
            elif lq.dtype in [bool]:
                widget = QtGui.QCheckBox()  
            elif lq.dtype in [str]:
                widget = QtGui.QLineEdit()
            lq.connect_bidir_to_widget(widget)

            # Add to formlayout
            self.controls_formLayout.addRow(lqname, widget)
            self.control_widgets[lqname] = widget
        
        self.op_buttons = OrderedDict()
        for op_name, op_func in self.operations.items(): 
            op_button = QtGui.QPushButton(op_name)
            op_button.clicked.connect(op_func)
            self.controls_formLayout.addRow(op_name, op_button)
        
        self.read_from_hardware_button = QtGui.QPushButton("Read From Hardware")
        self.read_from_hardware_button.clicked.connect(self.read_from_hardware)
        self.controls_formLayout.addRow("Logged Quantities:", self.read_from_hardware_button)
    
    @QtCore.Slot(bool)
    def enable_connection(self, enable=True):
        if enable:
            self.connect()
        else:
            self.disconnect()    
        
    @QtCore.Slot()    
    def read_from_hardware(self):
        for name, lq in self.logged_quantities.items():
            print "read_from_hardware", name
            lq.read_from_hardware()
     
    def setup(self):
        """
        Runs during DOWENEED__init__, before the hardware connection is established
        Should generate desired LoggedQuantities
        """
        raise NotImplementedError()     
        
    def connect(self):
        """
        Opens a connection to hardware
        and connects hardware to associated LoggedQuantities
        """
        raise NotImplementedError()
        
    def disconnect(self):
        """
        Disconnects the hardware and severs hardware--LoggedQuantities link
        """
        raise NotImplementedError()
    