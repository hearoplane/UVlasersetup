from ctypes import *
ps5000a_handle = c_short(0)
status = c_long()
#serial = c_char_p()
print(windll.ps5000a)
print('doing OpenUnit')

def TryGettingInfo() :
    print('doing TryGettingInfo')
    requiredSize = c_int16(0) #: SmallInt
    RInfo = c_int() #: PICO_INFO

    MyReturnStr = create_string_buffer(15)
    for RInfo in range(0,10): # requested info
        #print('doing GetUnitInfo')
        status = windll.ps5000a.ps5000aGetUnitInfo( ps5000a_handle, byref(MyReturnStr), c_int16(len(MyReturnStr)), byref(requiredSize), RInfo)
        if status == 0:
            #print('GetUnitInfo ok, requiredSize=', requiredSize)
            print('GetUnitInfo ok, MyReturnStr=', MyReturnStr.value)
        else:
            print('GetUnitInfo failed, status=', status)

if __name__ == '__main__':
    try:
        status = windll.ps5000a.ps5000aOpenUnit( byref( ps5000a_handle), None, 4)
        print(status)
        if status == 0 :
            print('OpenUnit ok, handle=', ps5000a_handle)
            TryGettingInfo()
        elif status == 282 :
            print('OpenUnit failed, status=', status, ' handle=', ps5000a_handle)
            print('doing ChangePowerSource');
            status = windll.ps5000a.ps5000aChangePowerSource( ps5000a_handle, 282)
            if status == 0 :
                print('ChangePowerSource ok')
                TryGettingInfo()
            else:
                print('ChangePowerSource failed, status=', status, ' handle=', ps5000a_handle)
        else:
            print('OpenUnit failed, status=', status, ' handle=', ps5000a_handle)
    finally:
        if ps5000a_handle != 0 :
            print('doing CloseUnit')
            status = windll.ps5000a.ps5000aCloseUnit( ps5000a_handle)
            if status == 0 :
                print('CloseUnit ok')
            else:
                print('CloseUnit failed, status=', status, ' handle=', ps5000a_handle)
            print

