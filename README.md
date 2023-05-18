# XC-0424

## Description

Python scripts to configure and read data from Digitech XC-0424 Temperature and Humidity Data Logger on Linux



![XC-0424](XC0424.jpg)

Specification :

- 20736 readings capacity
- Logging interval from 8 seconds to 4 hours
- Temperature range: -40 to 60C°
- Humidity range: 1%RH - 99%RH
- Power: 1 x 3V CR2032
- Battery life: 12 months
- Dimensions: 87(L) x 60(W) x 19(H)mm


## Requirements

- pyusb

## Usage

> Need to run as root for pyusb to access the usb device.


1. Write the configuration

Edit the xc0424_config_write.py in the section after # Replace the existing configuration settings

The following will configure 'cyclic' mode (old data is over written when full, 'acyclic' will stop recording when full) with a sample taken every minute (60 seconds).

```
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
interval = (60 * 1)         # in seconds

#first_times_start  = datetime.fromisoformat('2023-05-15T00:00')
#first_times_end    = datetime.fromisoformat('2023-05-15T01:00')
#second_times_start = datetime.fromisoformat('2023-05-15T02:00')
#second_times_end   = datetime.fromisoformat('2023-05-15T03:00')
#third_times_start  = datetime.fromisoformat('2023-05-15T04:00')
#third_times_end    = datetime.fromisoformat('2023-05-15T05:00')
#fourth_times_start = datetime.fromisoformat('2023-05-15T06:00')
#fourth_times_end   = datetime.fromisoformat('2023-05-15T07:00')
```


Segmented mode (only samples during supplied times). In the example, only the first and fourth times are used.

```
# Replace the existing configuration settings

# Mask out the existing value (&) then add the new (|)
#config = config & LCDAutoOffMask | LCDautoOffEnable
config = config & modeMask | segmented
#config = config & h12Mask | h24
#config = config & dmMask | DM
#config = config & fMask | C

#humoff = 0            # -20 to 20
#tempoff = 0.0         # -10.0C to 10.0C

# 8,16,24,32,40,48,56 seconds or 1 to 240 minutes
#interval = (60 * 1)         # in seconds

first_times_start  = datetime.fromisoformat('2023-05-18T00:00')
first_times_end    = datetime.fromisoformat('2023-05-18T01:00')
#second_times_start = datetime.fromisoformat('2023-05-18T02:00')
#second_times_end   = datetime.fromisoformat('2023-05-18T03:00')
#third_times_start  = datetime.fromisoformat('2023-05-18T04:00')
#third_times_end    = datetime.fromisoformat('2023-05-18T05:00')
fourth_times_start = datetime.fromisoformat('2023-05-18T06:00')
fourth_times_end   = datetime.fromisoformat('2023-05-18T07:00')
```


Then write the configuration

```
sudo ./xc0424_config_write.py
```

2. Read the configuration

```
sudo ./xc0420_config_read.py
```

Output:

> msb is the most significate bit of the interval bytes. Don't know what it is but it is sometimes set (will be 128 in the output).

Cyclic or Acyclic

```
LCD auto off: Enabled
Mode: Cycle
Time Display: 24h
Date: DM
Temperature Unit: C
msb:  0
Interval: 8 secs
Temperature Offset:  0.0
Humidity Offset:  0

Current: 22.8C  73.0F  50%
Minimum: 18.6C  65.5F  45%
Maximum: 24.4C  75.9F  56%
```

Segmented mode

```
LCD auto off: Enabled
Mode: Segmented
Time Display: 24h
Date: DM
Temperature Unit: C
msb:  0
Interval: 8 secs
Temperature Offset:  0.0
Humidity Offset:  0

Segmented Times:
First Time:  2023-05-18 00:00 2023-05-18 01:00
Second Time:
Third Time:
Fourth Time: 2023-05-18 06:00 2023-05-18 07:00

Current: 23.5C  74.3F  49%
Minimum: 18.6C  65.5F  45%
Maximum: 24.4C  75.9F  56%
```


3. Read the data to CSV

```
sudo ./xc0424_data_csv.py > results.csv
```

Output:

```
YYYY-MM-DDTHH:MM:SS,HUM_%,TEMP_C,TEMP_F
2023-05-17T13:45:08,50,22.1,71.8
2023-05-17T13:45:16,50,22.1,71.8
2023-05-17T13:45:24,50,22.1,71.8
2023-05-17T13:45:32,50,22.1,71.8
2023-05-17T13:45:40,50,22.1,71.8
```


4. Read the data to sqlite3 database

```
sudo ./xc0424_data_sql.py
```

> Creates a sqlite3 database in the current directory called xc0424_XXXXXXXX.db where XXXXXXXX is the value that I believe is the device ID of the unit. Re-running the script will add to the same database.

Output:

```
Scanning for new data
Inserting  '2023-05-17 19:39:39' 50 23.2
Inserting  '2023-05-17 19:39:47' 50 23.2
Inserting  '2023-05-17 19:39:55' 50 23.2
Inserting  '2023-05-17 19:40:03' 50 23.2
Inserting  '2023-05-17 19:40:11' 50 23.2
Inserting  '2023-05-17 19:40:19' 50 23.2
Inserting  '2023-05-17 19:40:27' 50 23.2
Inserting  '2023-05-17 19:40:35' 50 23.3
Inserting  '2023-05-17 19:40:43' 50 23.3
```


5. Read and print raw data

> This is included to show how the data is stored.

```
sudo ./xc0424_data_raw.py
```

Output:

> The output makes more sense if sorted. The first value is the memory location.
>
> 0058 is the first bitmap of data stored.
> - 3f means that a data block is complete,
> - ff means that there is no data in that block.
> - less than 3f is the number of samples in the block (ie, maximum is 3f)
>
> 019c is the first of the data block start date and time plus the interval
>
> 0d00-0d9c is the first of the data blocks with 3f (63) bytes representing 21 samples ( 3 bytes per sample )
>
> 01a4 is the second data block start date and time plus the interval
>
> 0dc0-0de7 is the second of the data blocks (with only 0e samples)
>
> 0073 is the second bitmap

```
0058  3f 0e ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
019c  23 05 17 20 34 03 00 08
0d00  45 02 df 45 02 df 45 02 df 45 02 df 45 02 de 45 02 de 45 02 de 45 02 de 45 02 df 45 02 de 45 02 df 45 02 df 45 02 df
0d27  45 02 df 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0
0d4e  45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0 45 02 e0
0d75  45 02 e0 45 02 e0 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1
0d9c  45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1
01a4  23 05 17 20 42 35 00 08
0dc0  45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1 45 02 e1
0de7  45 02 e1 45 02 e1
0073  ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
```
