#!/bin/env python
import array
import sys
import usb.core
import usb.util
from datetime import datetime

def find_device(VID, PID):
    device = usb.core.find(idVendor = VID, idProduct = PID)

    if device is None:
        sys.exit("Could not find device.")

    try:
        if device.is_kernel_driver_active(0):
            device.detach_kernel_driver(0)
    except usb.core.USBError as e:
        sys.exit("Could not detach kernel driver: %s" % str(e))
    except NotImplementedError:
        # This is not a thing on Windows so ignore the error
        pass

    try:
        device.reset()
        device.set_configuration()
    except usb.core.USBError as e:
        sys.exit("Could not set configuration: %s" % str(e))
    return device


def send_command(device, command):
    # access the first configuration
    # cfg = device[0]
    # access the first interface
    # intf = cfg[(0,0)]
    # second endpoint
    # ep = intf[1]
    ep_in = device[0][(0,0)][0]
    ep_out = device[0][(0,0)][1]

    pkt = bytearray.fromhex(command)
    pkt.append(sum(pkt) & 0xFF)
    pkt = bytearray([ 0x02, len(pkt) & 0xff ]) + pkt
    #print (bytes(pkt).hex(' '), ' =>  ', end='', flush=True)
    pkt = pkt + array.array('B',(0,)*(ep_out.wMaxPacketSize-len(pkt)))

    try:
        device.write(ep_out.bEndpointAddress, pkt, timeout=5000)
    except usb.core.USBError as e:
        sys.exit(str(e))

    try:
        data = bytes(device.read(ep_in.bEndpointAddress, ep_in.wMaxPacketSize, timeout=5000))
        datasize = data[1]
        #print(data[:datasize+2].hex(' '))
        return data[2:datasize+1]
    except usb.core.USBError as e:
        sys.exit(str(e))


def main():
    dev = find_device(0x10C4, 0x8468)

    # Not sure what this read does, possibly initialise
    response = send_command(dev, '01 00 00 02 02')
    if response[0] == 0x55:
        response = send_command(dev, '01 00 00 02 02')

    # Read configuration
    response = send_command(dev, '01 00 00 05 0a')
    config = response[4]
    # The most significate bit of the interval can be set so remove it before multipling
    interval = (((response[5]&0x7f)*0x100) + response[6])
    tempoff = (((response[7]*0x100) + response[8]) / 10) - 10.0
    humoff = response[9] - 20

    # Define constants
    LCDAutoOffMask = 0xdf       #  1101 1111
    modeMask = 0xe7             #  1110 0111
    h12Mask = 0xfb              #  1111 1011
    dmMask = 0xfd               #  1111 1101
    fMask = 0xfe                #  1111 1110

    LCDautoOffDisable = 0x00
    LCDautoOffEnable = 0x20     #  0010 0000
    acyclic = 0x00
    cyclic = 0x08               #  0000 1000
    segmented = 0x10            #  0001 0000
    h12 = 0x00
    h24 = 0x04                  #  0000 0100
    DM = 0x00
    MD = 0x02                   #  0000 0010
    F = 0x00
    C = 0x01                    #  0000 0001



    # Replace the existing configuration settings

    # Mask out the existing value (&) then add the new (|)
    #config = config & LCDAutoOffMask | LCDautoOffEnable
    config = config & modeMask | cyclic
    #config = config & h12Mask | h24
    #config = config & dmMask | DM
    #config = config & fMask | C

    #humoff = 0            # -20 to 20
    #tempoff = 0.0         # -10.0C to 10.0C

    # 8,16,24,32,40,48,56 seconds or 1 to 240 minutes
    #interval = (60 * 1)         # in seconds

    first_times_start  = datetime.fromisoformat('2023-05-18T00:00')
    first_times_end    = datetime.fromisoformat('2023-05-18T01:00')
    #second_times_start = datetime.fromisoformat('2023-05-15T02:00')
    #second_times_end   = datetime.fromisoformat('2023-05-15T03:00')
    #third_times_start  = datetime.fromisoformat('2023-05-15T04:00')
    #third_times_end    = datetime.fromisoformat('2023-05-15T05:00')
    #fourth_times_start = datetime.fromisoformat('2023-05-15T06:00')
    #fourth_times_end   = datetime.fromisoformat('2023-05-15T07:00')



    # Build new configuration from above and write to device
    times = 0
    try:
        fourth_times_start
    except NameError:
        fourth_times = datetime.now().strftime("%y ") + '%02x' % (datetime.now().month) + datetime.now().strftime(" %d %H %M")
    else:
        times += 0x80
        fourth_times = fourth_times_start.strftime("%y ") + '%02x' % (fourth_times_start.month) + fourth_times_start.strftime(" %d %H %M")
    try:
        fourth_times_end
    except NameError:
        fourth_times += ' ' + datetime.now().strftime("%y ") + '%02x' % (datetime.now().month) + datetime.now().strftime(" %d %H %M")
    else:
        fourth_times += ' ' + fourth_times_end.strftime("%y ") + '%02x' % (fourth_times_end.month) + fourth_times_end.strftime(" %d %H %M")

    try:
        third_times_start
    except NameError:
        third_times = datetime.now().strftime("%y ") + '%02x' % (datetime.now().month) + datetime.now().strftime(" %d %H %M")
    else:
        times += 0x40
        third_times = third_times_start.strftime("%y ") + '%02x' % (third_times_start.month) + third_times_start.strftime(" %d %H %M")
    try:
        third_times_end
    except NameError:
        third_times += ' ' + datetime.now().strftime("%y ") + '%02x' % (datetime.now().month) + datetime.now().strftime(" %d %H %M")
    else:
        third_times += ' ' + third_times_end.strftime("%y ") + '%02x' % (third_times_end.month) + third_times_end.strftime(" %d %H %M")

    try:
        second_times_start
    except NameError:
        second_times = datetime.now().strftime("%y ") + '%02x' % (datetime.now().month) + datetime.now().strftime(" %d %H %M")
    else:
        times += 0x20
        second_times = second_times_start.strftime("%y ") + '%02x' % (second_times_start.month) + second_times_start.strftime(" %d %H %M")
    try:
        second_times_end
    except NameError:
        second_times += ' ' + datetime.now().strftime("%y ") + '%02x' % (datetime.now().month) + datetime.now().strftime(" %d %H %M")
    else:
        second_times += ' ' + second_times_end.strftime("%y ") + '%02x' % (second_times_end.month) + second_times_end.strftime(" %d %H %M")

    try:
        first_times_start
    except NameError:
        first_times = datetime.now().strftime("%y ") + '%02x' % (datetime.now().month + times) + datetime.now().strftime(" %d %H %M")
    else:
        times += 0x10
        first_times = first_times_start.strftime("%y ") + '%02x' % (first_times_start.month + times) + first_times_start.strftime(" %d %H %M")
    try:
        first_times_end
    except NameError:
        first_times += ' ' + datetime.now().strftime("%y ") + '%02x' % (datetime.now().month) + datetime.now().strftime(" %d %H %M")
    else:
        first_times += ' ' + first_times_end.strftime("%y ") + '%02x' % (first_times_end.month) + first_times_end.strftime(" %d %H %M")

    # 8,16,24,32,40,48,56 seconds or 1 to 240 minutes
    if interval < 60:
        if not interval in [8,16,24,32,40,48,56]:
            print("Interval of", interval, "is not 8, 16, 24, 32, 40, 48, or 56 seconds, defaulting to 32 seconds")
            interval = 32
    elif interval > (60*240):
        print("Interval of", interval, "is too large, defaulting to 240 minutes")
        interval = (60*240)
    elif interval % 60 != 0:
        print("Interval of", interval, "seconds is not in minutes, rounding to", round(interval/60)*60, "seconds")
        interval = round(interval/60)

    # Stored offset is not float so multiple by 10 to remove decimal. 0 stored is offset of -10.0 (100) so add 100 to supplied offset
    # (ie 0 = offset of -10.0, 100 = offset of 0.0)
    if tempoff >= -10.0 and tempoff <= 10:
        tempoff = int(tempoff*10)+100
    else:
        print("Invalid offset of", tempoff, "supplied so default to 0.0")
        tempoff = 100

    # 0 stored is offset of -20 so add 20 to supplied offset. (ie 0 = offset of -20, 20 = offset of 0)
    if humoff >= -20 and humoff <= 20:
        humoff = humoff+20
    else:
        print("Invalid offset of", humoff, "supplied so default to 0")
        humoff = 20

    cfg_str = "00 22 " + '%02x' % config + ' %02x' % int((interval & 0xff00)/0x100) + ' %02x' % int(interval & 0x00ff)
    cfg_str = cfg_str + ' %02x' % int((tempoff & 0xff00)/0x100) + ' %02x' % int(tempoff & 0x00ff)
    cfg_str = cfg_str + ' %02x' % humoff
    #print(cfg_str)

    # Write current date and time
    response = send_command(dev, datetime.now().strftime("00 11 %y %m %d %H %M %S"))

    # Write configuration
    response = send_command(dev, cfg_str)
    #print(response.hex(' '))

    if response[0]==0xaa and config & segmented == segmented:     # If segmented mode
        seg_times = first_times + " " + second_times + " " + third_times + " " + fourth_times
        # Write segmented times
        response = send_command(dev, '00 04 '+seg_times)
        # Clear data
        response = send_command(dev, '00 08')

if __name__ == '__main__':
    main()

