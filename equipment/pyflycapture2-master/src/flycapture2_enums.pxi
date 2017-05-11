# -*- coding: utf8 -*-
#
#   pyflycapture2 - python bindings for libflycapture2_c
#   Copyright (C) 2012 Robert Jordens <jordens@phys.ethz.ch>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


# grep "^        FC2_" _FlyCapture2Defs_C.pxd | grep -v "FORCE_32BITS" |
# perl -pe 's/^ *FC2_(.*)$/$1 = FC2_$1/' > flycapture2_enums.pxi

from _FlyCapture2Defs_C cimport *

ERROR_UNDEFINED = FC2_ERROR_UNDEFINED
ERROR_OK = FC2_ERROR_OK
ERROR_FAILED = FC2_ERROR_FAILED
ERROR_NOT_IMPLEMENTED = FC2_ERROR_NOT_IMPLEMENTED
ERROR_FAILED_BUS_MASTER_CONNECTION = FC2_ERROR_FAILED_BUS_MASTER_CONNECTION
ERROR_NOT_CONNECTED = FC2_ERROR_NOT_CONNECTED
ERROR_INIT_FAILED = FC2_ERROR_INIT_FAILED
ERROR_NOT_INTITIALIZED = FC2_ERROR_NOT_INTITIALIZED
ERROR_INVALID_PARAMETER = FC2_ERROR_INVALID_PARAMETER
ERROR_INVALID_SETTINGS = FC2_ERROR_INVALID_SETTINGS
ERROR_INVALID_BUS_MANAGER = FC2_ERROR_INVALID_BUS_MANAGER
ERROR_MEMORY_ALLOCATION_FAILED = FC2_ERROR_MEMORY_ALLOCATION_FAILED
ERROR_LOW_LEVEL_FAILURE = FC2_ERROR_LOW_LEVEL_FAILURE
ERROR_NOT_FOUND = FC2_ERROR_NOT_FOUND
ERROR_FAILED_GUID = FC2_ERROR_FAILED_GUID
ERROR_INVALID_PACKET_SIZE = FC2_ERROR_INVALID_PACKET_SIZE
ERROR_INVALID_MODE = FC2_ERROR_INVALID_MODE
ERROR_NOT_IN_FORMAT7 = FC2_ERROR_NOT_IN_FORMAT7
ERROR_NOT_SUPPORTED = FC2_ERROR_NOT_SUPPORTED
ERROR_TIMEOUT = FC2_ERROR_TIMEOUT
ERROR_BUS_MASTER_FAILED = FC2_ERROR_BUS_MASTER_FAILED
ERROR_INVALID_GENERATION = FC2_ERROR_INVALID_GENERATION
ERROR_LUT_FAILED = FC2_ERROR_LUT_FAILED
ERROR_IIDC_FAILED = FC2_ERROR_IIDC_FAILED
ERROR_STROBE_FAILED = FC2_ERROR_STROBE_FAILED
ERROR_TRIGGER_FAILED = FC2_ERROR_TRIGGER_FAILED
ERROR_PROPERTY_FAILED = FC2_ERROR_PROPERTY_FAILED
ERROR_PROPERTY_NOT_PRESENT = FC2_ERROR_PROPERTY_NOT_PRESENT
ERROR_REGISTER_FAILED = FC2_ERROR_REGISTER_FAILED
ERROR_READ_REGISTER_FAILED = FC2_ERROR_READ_REGISTER_FAILED
ERROR_WRITE_REGISTER_FAILED = FC2_ERROR_WRITE_REGISTER_FAILED
ERROR_ISOCH_FAILED = FC2_ERROR_ISOCH_FAILED
ERROR_ISOCH_ALREADY_STARTED = FC2_ERROR_ISOCH_ALREADY_STARTED
ERROR_ISOCH_NOT_STARTED = FC2_ERROR_ISOCH_NOT_STARTED
ERROR_ISOCH_START_FAILED = FC2_ERROR_ISOCH_START_FAILED
ERROR_ISOCH_RETRIEVE_BUFFER_FAILED = FC2_ERROR_ISOCH_RETRIEVE_BUFFER_FAILED
ERROR_ISOCH_STOP_FAILED = FC2_ERROR_ISOCH_STOP_FAILED
ERROR_ISOCH_SYNC_FAILED = FC2_ERROR_ISOCH_SYNC_FAILED
ERROR_ISOCH_BANDWIDTH_EXCEEDED = FC2_ERROR_ISOCH_BANDWIDTH_EXCEEDED
ERROR_IMAGE_CONVERSION_FAILED = FC2_ERROR_IMAGE_CONVERSION_FAILED
ERROR_IMAGE_LIBRARY_FAILURE = FC2_ERROR_IMAGE_LIBRARY_FAILURE
ERROR_BUFFER_TOO_SMALL = FC2_ERROR_BUFFER_TOO_SMALL
ERROR_IMAGE_CONSISTENCY_ERROR = FC2_ERROR_IMAGE_CONSISTENCY_ERROR
BUS_RESET = FC2_BUS_RESET
ARRIVAL = FC2_ARRIVAL
REMOVAL = FC2_REMOVAL
DROP_FRAMES = FC2_DROP_FRAMES
BUFFER_FRAMES = FC2_BUFFER_FRAMES
UNSPECIFIED_GRAB_MODE = FC2_UNSPECIFIED_GRAB_MODE
TIMEOUT_NONE = FC2_TIMEOUT_NONE
TIMEOUT_INFINITE = FC2_TIMEOUT_INFINITE
TIMEOUT_UNSPECIFIED = FC2_TIMEOUT_UNSPECIFIED
BANDWIDTH_ALLOCATION_OFF = FC2_BANDWIDTH_ALLOCATION_OFF
BANDWIDTH_ALLOCATION_ON = FC2_BANDWIDTH_ALLOCATION_ON
BANDWIDTH_ALLOCATION_UNSUPPORTED = FC2_BANDWIDTH_ALLOCATION_UNSUPPORTED
BANDWIDTH_ALLOCATION_UNSPECIFIED = FC2_BANDWIDTH_ALLOCATION_UNSPECIFIED
INTERFACE_IEEE1394 = FC2_INTERFACE_IEEE1394
INTERFACE_USB_2 = FC2_INTERFACE_USB_2
INTERFACE_USB_3 = FC2_INTERFACE_USB_3
INTERFACE_GIGE = FC2_INTERFACE_GIGE
INTERFACE_UNKNOWN = FC2_INTERFACE_UNKNOWN
DRIVER_1394_CAM = FC2_DRIVER_1394_CAM
DRIVER_1394_PRO = FC2_DRIVER_1394_PRO
DRIVER_1394_JUJU = FC2_DRIVER_1394_JUJU
DRIVER_1394_VIDEO1394 = FC2_DRIVER_1394_VIDEO1394
DRIVER_1394_RAW1394 = FC2_DRIVER_1394_RAW1394
DRIVER_USB_NONE = FC2_DRIVER_USB_NONE
DRIVER_USB_CAM = FC2_DRIVER_USB_CAM
DRIVER_USB3_PRO = FC2_DRIVER_USB3_PRO
DRIVER_GIGE_NONE = FC2_DRIVER_GIGE_NONE
DRIVER_GIGE_FILTER = FC2_DRIVER_GIGE_FILTER
DRIVER_GIGE_PRO = FC2_DRIVER_GIGE_PRO
DRIVER_UNKNOWN = FC2_DRIVER_UNKNOWN
BRIGHTNESS = FC2_BRIGHTNESS
AUTO_EXPOSURE = FC2_AUTO_EXPOSURE
SHARPNESS = FC2_SHARPNESS
WHITE_BALANCE = FC2_WHITE_BALANCE
HUE = FC2_HUE
SATURATION = FC2_SATURATION
GAMMA = FC2_GAMMA
IRIS = FC2_IRIS
FOCUS = FC2_FOCUS
ZOOM = FC2_ZOOM
PAN = FC2_PAN
TILT = FC2_TILT
SHUTTER = FC2_SHUTTER
GAIN = FC2_GAIN
TRIGGER_MODE = FC2_TRIGGER_MODE
TRIGGER_DELAY = FC2_TRIGGER_DELAY
FRAME_RATE = FC2_FRAME_RATE
TEMPERATURE = FC2_TEMPERATURE
UNSPECIFIED_PROPERTY_TYPE = FC2_UNSPECIFIED_PROPERTY_TYPE
FRAMERATE_1_875 = FC2_FRAMERATE_1_875
FRAMERATE_3_75 = FC2_FRAMERATE_3_75
FRAMERATE_7_5 = FC2_FRAMERATE_7_5
FRAMERATE_15 = FC2_FRAMERATE_15
FRAMERATE_30 = FC2_FRAMERATE_30
FRAMERATE_60 = FC2_FRAMERATE_60
FRAMERATE_120 = FC2_FRAMERATE_120
FRAMERATE_240 = FC2_FRAMERATE_240
FRAMERATE_FORMAT7 = FC2_FRAMERATE_FORMAT7
NUM_FRAMERATES = FC2_NUM_FRAMERATES
VIDEOMODE_160x120YUV444 = FC2_VIDEOMODE_160x120YUV444
VIDEOMODE_320x240YUV422 = FC2_VIDEOMODE_320x240YUV422
VIDEOMODE_640x480YUV411 = FC2_VIDEOMODE_640x480YUV411
VIDEOMODE_640x480YUV422 = FC2_VIDEOMODE_640x480YUV422
VIDEOMODE_640x480RGB = FC2_VIDEOMODE_640x480RGB
VIDEOMODE_640x480Y8 = FC2_VIDEOMODE_640x480Y8
VIDEOMODE_640x480Y16 = FC2_VIDEOMODE_640x480Y16
VIDEOMODE_800x600YUV422 = FC2_VIDEOMODE_800x600YUV422
VIDEOMODE_800x600RGB = FC2_VIDEOMODE_800x600RGB
VIDEOMODE_800x600Y8 = FC2_VIDEOMODE_800x600Y8
VIDEOMODE_800x600Y16 = FC2_VIDEOMODE_800x600Y16
VIDEOMODE_1024x768YUV422 = FC2_VIDEOMODE_1024x768YUV422
VIDEOMODE_1024x768RGB = FC2_VIDEOMODE_1024x768RGB
VIDEOMODE_1024x768Y8 = FC2_VIDEOMODE_1024x768Y8
VIDEOMODE_1024x768Y16 = FC2_VIDEOMODE_1024x768Y16
VIDEOMODE_1280x960YUV422 = FC2_VIDEOMODE_1280x960YUV422
VIDEOMODE_1280x960RGB = FC2_VIDEOMODE_1280x960RGB
VIDEOMODE_1280x960Y8 = FC2_VIDEOMODE_1280x960Y8
VIDEOMODE_1280x960Y16 = FC2_VIDEOMODE_1280x960Y16
VIDEOMODE_1600x1200YUV422 = FC2_VIDEOMODE_1600x1200YUV422
VIDEOMODE_1600x1200RGB = FC2_VIDEOMODE_1600x1200RGB
VIDEOMODE_1600x1200Y8 = FC2_VIDEOMODE_1600x1200Y8
VIDEOMODE_1600x1200Y16 = FC2_VIDEOMODE_1600x1200Y16
VIDEOMODE_FORMAT7 = FC2_VIDEOMODE_FORMAT7
NUM_VIDEOMODES = FC2_NUM_VIDEOMODES
MODE_0 = FC2_MODE_0
MODE_1 = FC2_MODE_1
MODE_2 = FC2_MODE_2
MODE_3 = FC2_MODE_3
MODE_4 = FC2_MODE_4
MODE_5 = FC2_MODE_5
MODE_6 = FC2_MODE_6
MODE_7 = FC2_MODE_7
MODE_8 = FC2_MODE_8
MODE_9 = FC2_MODE_9
MODE_10 = FC2_MODE_10
MODE_11 = FC2_MODE_11
MODE_12 = FC2_MODE_12
MODE_13 = FC2_MODE_13
MODE_14 = FC2_MODE_14
MODE_15 = FC2_MODE_15
MODE_16 = FC2_MODE_16
MODE_17 = FC2_MODE_17
MODE_18 = FC2_MODE_18
MODE_19 = FC2_MODE_19
MODE_20 = FC2_MODE_20
MODE_21 = FC2_MODE_21
MODE_22 = FC2_MODE_22
MODE_23 = FC2_MODE_23
MODE_24 = FC2_MODE_24
MODE_25 = FC2_MODE_25
MODE_26 = FC2_MODE_26
MODE_27 = FC2_MODE_27
MODE_28 = FC2_MODE_28
MODE_29 = FC2_MODE_29
MODE_30 = FC2_MODE_30
MODE_31 = FC2_MODE_31
NUM_MODES = FC2_NUM_MODES
PIXEL_FORMAT_MONO8 = FC2_PIXEL_FORMAT_MONO8
PIXEL_FORMAT_411YUV8 = FC2_PIXEL_FORMAT_411YUV8
PIXEL_FORMAT_422YUV8 = FC2_PIXEL_FORMAT_422YUV8
PIXEL_FORMAT_444YUV8 = FC2_PIXEL_FORMAT_444YUV8
PIXEL_FORMAT_RGB8 = FC2_PIXEL_FORMAT_RGB8
PIXEL_FORMAT_MONO16 = FC2_PIXEL_FORMAT_MONO16
PIXEL_FORMAT_RGB16 = FC2_PIXEL_FORMAT_RGB16
PIXEL_FORMAT_S_MONO16 = FC2_PIXEL_FORMAT_S_MONO16
PIXEL_FORMAT_S_RGB16 = FC2_PIXEL_FORMAT_S_RGB16
PIXEL_FORMAT_RAW8 = FC2_PIXEL_FORMAT_RAW8
PIXEL_FORMAT_RAW16 = FC2_PIXEL_FORMAT_RAW16
PIXEL_FORMAT_MONO12 = FC2_PIXEL_FORMAT_MONO12
PIXEL_FORMAT_RAW12 = FC2_PIXEL_FORMAT_RAW12
PIXEL_FORMAT_BGR = FC2_PIXEL_FORMAT_BGR
PIXEL_FORMAT_BGRU = FC2_PIXEL_FORMAT_BGRU
PIXEL_FORMAT_RGB = FC2_PIXEL_FORMAT_RGB
PIXEL_FORMAT_RGBU = FC2_PIXEL_FORMAT_RGBU
PIXEL_FORMAT_BGR16 = FC2_PIXEL_FORMAT_BGR16
PIXEL_FORMAT_422YUV8_JPEG = FC2_PIXEL_FORMAT_422YUV8_JPEG
NUM_PIXEL_FORMATS = FC2_NUM_PIXEL_FORMATS
UNSPECIFIED_PIXEL_FORMAT = FC2_UNSPECIFIED_PIXEL_FORMAT
BUSSPEED_S100 = FC2_BUSSPEED_S100
BUSSPEED_S200 = FC2_BUSSPEED_S200
BUSSPEED_S400 = FC2_BUSSPEED_S400
BUSSPEED_S480 = FC2_BUSSPEED_S480
BUSSPEED_S800 = FC2_BUSSPEED_S800
BUSSPEED_S1600 = FC2_BUSSPEED_S1600
BUSSPEED_S3200 = FC2_BUSSPEED_S3200
BUSSPEED_S5000 = FC2_BUSSPEED_S5000
BUSSPEED_10BASE_T = FC2_BUSSPEED_10BASE_T
BUSSPEED_100BASE_T = FC2_BUSSPEED_100BASE_T
BUSSPEED_1000BASE_T = FC2_BUSSPEED_1000BASE_T
BUSSPEED_10000BASE_T = FC2_BUSSPEED_10000BASE_T
BUSSPEED_S_FASTEST = FC2_BUSSPEED_S_FASTEST
BUSSPEED_ANY = FC2_BUSSPEED_ANY
BUSSPEED_SPEED_UNKNOWN = FC2_BUSSPEED_SPEED_UNKNOWN
PCIE_BUSSPEED_2_5 = FC2_PCIE_BUSSPEED_2_5
PCIE_BUSSPEED_5_0 = FC2_PCIE_BUSSPEED_5_0
PCIE_BUSSPEED_UNKNOWN = FC2_PCIE_BUSSPEED_UNKNOWN
DEFAULT = FC2_DEFAULT
NO_COLOR_PROCESSING = FC2_NO_COLOR_PROCESSING
NEAREST_NEIGHBOR_FAST = FC2_NEAREST_NEIGHBOR_FAST
EDGE_SENSING = FC2_EDGE_SENSING
HQ_LINEAR = FC2_HQ_LINEAR
RIGOROUS = FC2_RIGOROUS
IPP = FC2_IPP
DIRECTIONAL = FC2_DIRECTIONAL
BT_NONE = FC2_BT_NONE
BT_RGGB = FC2_BT_RGGB
BT_GRBG = FC2_BT_GRBG
BT_GBRG = FC2_BT_GBRG
BT_BGGR = FC2_BT_BGGR
FROM_FILE_EXT = FC2_FROM_FILE_EXT
PGM = FC2_PGM
PPM = FC2_PPM
BMP = FC2_BMP
JPEG = FC2_JPEG
JPEG2000 = FC2_JPEG2000
TIFF = FC2_TIFF
PNG = FC2_PNG
RAW = FC2_RAW
HEARTBEAT = FC2_HEARTBEAT
HEARTBEAT_TIMEOUT = FC2_HEARTBEAT_TIMEOUT
STATISTICS_GREY = FC2_STATISTICS_GREY
STATISTICS_RED = FC2_STATISTICS_RED
STATISTICS_GREEN = FC2_STATISTICS_GREEN
STATISTICS_BLUE = FC2_STATISTICS_BLUE
STATISTICS_HUE = FC2_STATISTICS_HUE
STATISTICS_SATURATION = FC2_STATISTICS_SATURATION
STATISTICS_LIGHTNESS = FC2_STATISTICS_LIGHTNESS
WINDOWS_X86 = FC2_WINDOWS_X86
WINDOWS_X64 = FC2_WINDOWS_X64
LINUX_X86 = FC2_LINUX_X86
LINUX_X64 = FC2_LINUX_X64
MAC = FC2_MAC
UNKNOWN_OS = FC2_UNKNOWN_OS
BYTE_ORDER_LITTLE_ENDIAN = FC2_BYTE_ORDER_LITTLE_ENDIAN
BYTE_ORDER_BIG_ENDIAN = FC2_BYTE_ORDER_BIG_ENDIAN
TIFF_NONE = FC2_TIFF_NONE
TIFF_PACKBITS = FC2_TIFF_PACKBITS
TIFF_DEFLATE = FC2_TIFF_DEFLATE
TIFF_ADOBE_DEFLATE = FC2_TIFF_ADOBE_DEFLATE
TIFF_CCITTFAX3 = FC2_TIFF_CCITTFAX3
TIFF_CCITTFAX4 = FC2_TIFF_CCITTFAX4
TIFF_LZW = FC2_TIFF_LZW
TIFF_JPEG = FC2_TIFF_JPEG
