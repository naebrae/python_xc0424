#!/bin/env python
import array
import sys
import usb.core
import usb.util
import datetime
import sqlite3

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

def insert_humtemp(cur, humtemp, st, interval):
    y = 0
    while y < len(humtemp):
        datadate = f'\'{st:%Y-%m-%d %H:%M:%S}\''
        # Need to take 20 because 0 in data allows for -20 offset
        humid = int(humtemp[y]) - 20
        y += 1
        # Need to take 500 from temp because 0 in data is -40.0C plus -10.0C offset
        temp = ((int(humtemp[y]) * 0x100) + (int(humtemp[y+1]) - 500)) / 10
        y += 2

        cur.execute('SELECT * FROM data WHERE (datatime=? AND humidity=? AND temperature_C=?)', (datadate, humid, temp))
        entry = cur.fetchone()
        if entry is None:
            cur.execute('INSERT INTO data (datatime, humidity, temperature_C) VALUES (?,?,?)', (datadate, humid, temp))
            print('Inserting ',datadate, humid, temp)

        time_change = datetime.timedelta(seconds=interval)
        st += time_change
    return st

def date_hex(datedec):
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
    serial = f'{response[0]:02X}' + f'{response[1]:02X}' + f'{response[2]:02X}' + f'{response[3]:02X}'

    #db_name = 'xc0424_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.db'
    db_name = 'xc0424_' + serial + '.db'
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    res = cursor.execute("CREATE TABLE IF NOT EXISTS data (datatime DATETIME, humidity INTEGER, temperature_C FLOAT)")
    db.commit()

    print("Scanning for new data")
    # Read data map
    map = 0x0058
    dateptr = 0x019c
    dataptr = 0x0d00
    while (map < 0x019c):
        #print ()
        mapread = f'01 00 %04x 1b' % map
        response = bytes(send_command(dev, mapread))
        #print(response.hex(' '))
        map += 0x1b
        mapptr = 0
        while (mapptr < 0x1b):
            mapdata = response[mapptr]
            if (mapdata != 0xff):
                mapoff = mapdata + 1;
                dateread = f'01 00 %04x 08' % dateptr
                datadate = send_command(dev, dateread)

                st_year = date_hex(datadate[0]) + 2000
                st_month = date_hex(datadate[1])
                st_day = date_hex(datadate[2])
                st_hour = date_hex(datadate[3])
                st_minute = date_hex(datadate[4])
                st_second = date_hex(datadate[5])

                starttime = datetime.datetime( st_year, st_month, st_day, st_hour, st_minute, st_second )
                interval = (int(datadate[6]) * 0x100) + int(datadate[7])

                dataoff = dataptr
                for x in range(int(mapoff * 3 / 0x27)):
                    dataread = f'01 00 %04x 27' % dataoff
                    datadata = send_command(dev, dataread)
                    starttime = insert_humtemp(cursor, datadata, starttime, interval)
                    db.commit()
                    dataoff += 0x27
                if (((mapoff * 3) % 0x27) > 0):
                    dataread = f'01 00 %04x %02x' % (dataoff, ((mapoff * 3) % 0x27))
                    datadata = send_command(dev, dataread)
                    starttime = insert_humtemp(cursor, datadata, starttime, interval)
                    db.commit()
            mapptr += 1
            dateptr += 8
            dataptr += (0x40 * 3)

if __name__ == '__main__':
    main()
