#!/bin/env python
import array
import sys
import usb.core
import usb.util
import datetime

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
        device.write(ep_out.bEndpointAddress, pkt)
    except usb.core.USBError as e:
        sys.exit(str(e))

    try:
        data = bytes(device.read(ep_in.bEndpointAddress, ep_in.wMaxPacketSize))
        datasize = data[1]
        #print(data[:datasize+2].hex(' '))
        return data[2:datasize+1]
    except usb.core.USBError as e:
        sys.exit(str(e))

def date_hex(datedec):
    # The dates are stored as hex but are decimal (ie 2023/05/15 is stored as 0x23 0x05 0x15)
    datehex = int((((datedec & 0xf0)/16)*10) + (datedec & 0x0f))
    return datehex

def main():
    dev = find_device(0x10C4, 0x8468)

    # Possibly initialise
    response = send_command(dev, '01 00 00 02 02')
    if response[0] == 0x55:
        response = send_command(dev, '01 00 00 02 02')

    # Read configuration
    response = send_command(dev, '01 00 00 05 0a')
    #print(response.hex(' '))

    # Not sure what the first 4 bytes of the returned configuration are. They are always the same but vary between monitors. Assuming serial number.
    print("SerialNo? : ",f'{response[0]:02X}',f'{response[1]:02X}',f'{response[2]:02X}',f'{response[3]:02X}', sep='')

    temp_off = int(response[7] * 0x100 + response[8])
    hum_off = int(response[9])
    msb = response[5] & 0x80     # most significant bit of the interval. Sometimes set, not sure why?
    interval = (int(response[5] & 0x7f) * 0x100) + int(response[6])
    LCDautoOff = response[4] & 0x20
    mode = response[4] & 0x18
    H12or24 = response[4] & 0x04
    DMorMD = response[4] & 0x02
    ForC = response[4] & 0x01

    print("LCD auto off: ", sep='', end='')
    if LCDautoOff == 0x20:
        print("Enabled")
    else:
        print("Disabled")

    print("Mode: ", sep='', end='')
    match mode:
        case 0x0:
            print("Acyclic")
        case 0x8:
            print("Cycle")
        case 0x10:
            print("Segmented")

    print("Time Display: ", sep='', end='')
    if H12or24 == 0x04:
        print("24h")
    else:
        print("12h")

    print("Date: ", sep='', end='')
    if DMorMD == 0x02:
        print("MD")
    else:
        print("DM")

    print("Temperature Unit: ", sep='', end='')
    if ForC == 0x01:
        print("C")
    else:
        print("F")

    print("msb: ", msb)

    print("Interval: ", sep='', end='')
    if interval < 60:
        print(interval, "secs")
    else:
        print(int(interval/60), "mins")

    print("Temperature Offset: ", (temp_off - 100) / 10)
    print("Humidity Offset: ", (hum_off - 20))
    print()

    if mode == 0x10:
        # Read segmented data times
        response = send_command(dev, '01 00 00 18 28')

        print('Segmented Times:')
        print('First Time:  ', end='')
        if (response[1] & 0x10 == 0x10):
            print('20',f'{date_hex(response[0]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[1] & 0x0f):02d}', '-', sep='', end='')
            print(f'{date_hex(response[2]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[3]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[4]):02d}', ' ', sep='', end='')
            print('20',f'{date_hex(response[5]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[6]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[7]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[8]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[9]):02d}', ' ', sep='', end='')
        print()

        print('Second Time: ', end='')
        if (response[1] & 0x20 == 0x20):
            print('20',f'{date_hex(response[10]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[11]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[12]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[13]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[14]):02d}', ' ', sep='', end='')
            print('20',f'{date_hex(response[15]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[16]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[17]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[18]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[19]):02d}', ' ', sep='', end='')
        print()

        print('Third Time:  ', end='')
        if (response[1] & 0x40 == 0x40):
            print('20',f'{date_hex(response[20]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[21]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[22]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[23]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[24]):02d}', ' ', sep='', end='')
            print('20',f'{date_hex(response[25]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[26]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[27]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[28]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[29]):02d}', ' ', sep='', end='')
        print()

        print('Fourth Time: ', end='')
        if (response[1] & 0x80 == 0x80):
            print('20',f'{date_hex(response[30]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[31]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[32]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[33]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[34]):02d}', ' ', sep='', end='')
            print('20',f'{date_hex(response[35]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[36]):02d}', '-', sep='', end='')
            print(f'{date_hex(response[37]):02d}', ' ', sep='', end='')
            print(f'{date_hex(response[38]):02d}', ':', sep='', end='')
            print(f'{date_hex(response[39]):02d}', ' ', sep='', end='')
        print()

        print()

    # Get current temp & hum
    response = send_command(dev, '01 01 02')
    curtemp = (((response[1] * 0x100) + response[2]) - 500) / 10
    curtempF = curtemp * 9 / 5 + 32
    curhum = response[0] - 20
    print('Current: ', curtemp, 'C  ', f'{curtempF:0.1f}', 'F  ', curhum, '%', sep='')

    # Get max and mins
    response = send_command(dev, '01 00 00 50 06')
    maxtemp = (((response[0] * 0x100) + response[1]) - 500) / 10
    maxtempF = maxtemp * 9 / 5 + 32
    maxhum = response[2] - 20
    mintemp = (((response[3] * 0x100) + response[4]) - 500) / 10
    mintempF = mintemp * 9 / 5 + 32
    minhum = response[5] - 20
    print('Minimum: ', mintemp, 'C  ', f'{mintempF:0.1f}', 'F  ', minhum, '%', sep='')
    print('Maximum: ', maxtemp, 'C  ', f'{maxtempF:0.1f}', 'F  ', maxhum, '%', sep='')
    print()


if __name__ == '__main__':
    main()

