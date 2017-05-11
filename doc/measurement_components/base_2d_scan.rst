Base2DScan Measurement Component
========================================

MadCityLabs Stage 2D scan 

Subclass the Base2DScan measurement component to create 2D map measurements.

You must implement the following methods:
 * scan_specific_setup
 * setup_figure
 * pre_scan_setup
 * collect_pixel
 * scan_specific_savedict
 * update_display
 
 
Examples of subclassed 2D scans:
 * Hyperspectral Imaging: SpectrumScan2DMeasurement
 * APD Confocal imaging: APDConfocalScanMeasurement
 * Time-resolved PL imaging: TRPLScanMeasurement
 
 
 
 Base2DScan
 ----------
 
.. autoclass:: measurement_components.base_2d_scan.Base2DScan
    :members: 
    
