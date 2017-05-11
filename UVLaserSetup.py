'''
Scuba Probe Technologies LLC, 2015
@author: dziegler dominik@scubaprobe.com

'''
import sys
from PySide import QtGui, QtCore
import ctypes
from base_gui import BaseGUI
from hardware_components.asi_xy_stage import ASIXYStageComponent
from hardware_components.mcl_xyz_stage import MCLStageComponent
from hardware_components.firefly_cam import PointGreyCamComponent
from hardware_components.ipevo_cam import IpevoCamComponent
from hardware_components.LaserSetupArduino import LSArduinoHardwareComponent
from measurement_components.lever_detection import LeverDetection
from measurement_components.lever_align import LeverAlign 
from measurement_components.auto_focus import AutoFocus
from measurement_components.lever_cutting import LeverCutting

class UVLaserSetup(BaseGUI):
    ui_filename = "UVLaserSetup.ui"
    def setup(self): 
        #Add hardware components
        print "Adding Hardware Components"
        self.stage_hc = self.add_hardware_component(ASIXYStageComponent(self))
        self.MCLstage_hc = self.add_hardware_component(MCLStageComponent(self))
        self.firefly_hc = self.add_hardware_component(PointGreyCamComponent(self))
        self.ipevo_hc = self.add_hardware_component(IpevoCamComponent(self))
        self.lsarduino_hc = self.add_hardware_component(LSArduinoHardwareComponent(self))
        
        #Add measurement components
        print "Create Measurement Components"
        self.lever_detection = self.add_measurement_component(LeverDetection(self))
        self.lever_cutting = self.add_measurement_component(LeverCutting(self))
        self.lever_align = self.add_measurement_component(LeverAlign(self))
        self.auto_focus = self.add_measurement_component(AutoFocus(self))
                        
        # connect previously code-generated elements
        self.stage_hc.asiStage_connectivity.connect_bidir_to_widget(self.stage_hc.connect_hardware_checkBox)
        self.MCLstage_hc.MCLstage_connectivity.connect_bidir_to_widget(self.MCLstage_hc.connect_hardware_checkBox)
        self.firefly_hc.firefly_cam_connectivity.connect_bidir_to_widget(self.firefly_hc.connect_hardware_checkBox)
        self.ipevo_hc.ipevo_cam_connectivity.connect_bidir_to_widget(self.ipevo_hc.connect_hardware_checkBox)
        self.lsarduino_hc.arduino_connectivity.connect_bidir_to_widget(self.lsarduino_hc.connect_hardware_checkBox)
                 
        # display window icon / logo / stream
        self.ui.logo.setPixmap(QtGui.QPixmap("logo_resized.png"));
        
        # Set initial hardware connections (optional)
        self.stage_hc.asiStage_connectivity.update_value(True)
        self.MCLstage_hc.MCLstage_connectivity.update_value(True)
        self.firefly_hc.firefly_cam_connectivity.update_value(True)
        self.ipevo_hc.ipevo_cam_connectivity.update_value(False)
        self.lsarduino_hc.arduino_connectivity.update_value(True) 
        self.lsarduino_hc.topLED_intensity.update_value(30)
        self.lsarduino_hc.bottomLED_intensity.update_value(0)
        
        self.previous_state = 'None'
        self.current_state = 'Start'
        
if __name__ == '__main__':     
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("Laser Setup")
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'ScubaProbe.UVLaserSetup') 
    
    gui = UVLaserSetup()
    gui.show()
    sys.exit(app.exec_())
