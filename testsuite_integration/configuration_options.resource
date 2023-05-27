*** Settings ***
Documentation       Resource file for config option related stuff.

Library             martel_printer_test_library.PrinterTestLibrary
Library             martel_printer_test_library.PrinterDebugLibrary


*** Variables ***
&{RS232 FRAME FORMAT}       Option=1
...                         Default=1
...                         8 Bits None=1
...                         8 Bits Odd=2
...                         8 Bits Even=3
...                         7 Bits Odd=4
...                         7 Bits Even=5

&{RS232 BAUD RATE}          Option=2
...                         Default=5
...                         115200=1
...                         57600=2
...                         38400=3
...                         19200=4
...                         9600=5
...                         4800=6
...                         2400=7
...                         1200=8
...                         600=9

&{RS232 FLOW CONTROL}       Option=3
...                         Default=1
...                         None=1
...                         Software=2
...                         Hardware=3

&{BLUETOOTH PAIRING}        Option=4
...                         Default=1
...                         Off=1
...                         Standard=2
...                         Silent=3

&{DEFAULT FONT}             Option=5
...                         Default=1
...                         Slot 1=1
...                         Slot 2=2
...                         Slot 3=3
...                         Slot 4=4
...                         Slot 5=5
...                         Slot 6=6
...                         Slot 7=7
...                         Slot 8=8

&{IR FRAME FORMAT}          Option=15
...                         Default=1
...                         8 Bits None=1
...                         8 Bits Odd=2
...                         8 Bits Even=3
...                         7 Bits Odd=4
...                         7 Bits Even=5

&{IR BAUD RATE}             Option=16
...                         Default=5
...                         115200=1
...                         57600=2
...                         38400=3
...                         19200=4
...                         9600=5
...                         4800=6
...                         2400=7
...                         1200=8
...                         600=9

&{IR FLOW CONTROL}          Option=17
...                         Default=1
...                         None=1
...                         Software=2
...                         Hardware=3
