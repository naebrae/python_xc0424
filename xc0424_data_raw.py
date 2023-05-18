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


def main():
    dev = find_device(0x10C4, 0x8468)

    # Possibly initialise
    response = send_command(dev, '01 00 00 02 02')
    if response[0] == 0x55:
        response = send_command(dev, '01 00 00 02 02')

    # Read configuration
    #response = send_command(dev, '01 00 00 05 0a')
    #print(response.hex(' '))

    # Read data map
    map = 0x0058
    dateptr = 0x019c
    dataptr = 0x0d00
    while (map < 0x019c):
        #print ()
        mapread = f'01 00 %04x 1b' % map
        response = bytes(send_command(dev, mapread))
        print(f'{map:04x}  ',end='')
        print(response.hex(' '))
        map += 0x1b
        mapptr = 0
        while (mapptr < 0x1b):
            mapdata = response[mapptr]
            if (mapdata != 0xff):
                #print ()
                mapoff = mapdata + 1;
                dateread = f'01 00 %04x 08' % dateptr
                datadate = send_command(dev, dateread)
                print(f'{dateptr:04x}  ',end='')
                print(datadate.hex(' '))
                dataoff = dataptr
                for x in range(int(mapoff * 3 / 0x27)):
                    dataread = f'01 00 %04x 27' % dataoff
                    datadata = send_command(dev, dataread)
                    print(f'{dataoff:04x}  ',end='')
                    print(datadata.hex(' '))
                    dataoff += 0x27
                if (((mapoff * 3) % 0x27) > 0):
                    dataread = f'01 00 %04x %02x' % (dataoff, ((mapoff * 3) % 0x27))
                    datadata = send_command(dev, dataread)
                    print(f'{dataoff:04x}  ',end='')
                    print(datadata.hex(' '))
            mapptr += 1
            dateptr += 8
            dataptr += (0x40 * 3)

if __name__ == '__main__':
    main()

