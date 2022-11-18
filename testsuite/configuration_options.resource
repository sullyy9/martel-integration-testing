*** Settings ***
Documentation       Resource file for config option related stuff.

Library             printer.Printer


*** Variables ***
&{RS232 DATA BITS AND PARITY}       option=1
...                                 8 bits none=1
...                                 8 bits odd=2
...                                 8 bits even=3
...                                 7 bits odd=4
...                                 7 bits even=5

&{RS232 BAUD RATE}                  option=2
...                                 115200=1
...                                 57600=2
...                                 38400=3
...                                 19200=4
...                                 9600=5
...                                 4800=6
...                                 2400=7
...                                 1200=8
...                                 600=9

&{RS232 FLOW CONTROL}               option=3
...                                 none=1
...                                 software=2
...                                 hardware=3

&{BLUETOOTH PAIRING}                option=4
...                                 none=1
...                                 standard=2
...                                 silent=3

${DEFAULT FONT}                     5


*** Keywords ***
Set Option ${option} To ${setting}
    Enable Printer Debug Mode
    Set Printer Option    ${option}    ${setting}
    Reset Printer
    Close Printer USB Interface
    Sleep    1s
    Open Printer USB Interface
    Send Printer Command    Feed Line\n

Set Printer RS232 Baud Rate To ${setting}
    Set Option ${RS232 BAUD RATE}[option] To ${RS232 BAUD RATE}[${setting}]
