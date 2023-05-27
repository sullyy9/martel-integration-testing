*** Settings ***
Documentation       Tests for RS232 baud rate.

Library             martel_printer_test_library.PrinterTestLibrary
Library             martel_printer_test_library.PrinterDebugLibrary
Resource            ../configuration_options.resource

Suite Setup         Run Keywords
...                     RS232 Configure    baud_rate=9600    data_bits=8    parity=None    AND
...                     Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[Default]    AND
...                     Printer Reset
Suite Teardown      Run Keywords
...                     RS232 Configure    baud_rate=9600    data_bits=8    parity=None    AND
...                     Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[Default]    AND
...                     Printer Reset

Force Tags          baud_rate


*** Variables ***
${SAMPLE TEXT}      Martel Instruments is a leading manufacturer and global
...                 supplier of bespoke and innovative commercial printing
...                 solutions.


*** Test Cases ***
Test RS232 At 600 Baud
    [Documentation]    Test the RS232 interface at 600 baud.

    RS232 Configure    baud_rate=600
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[600]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 1200 Baud
    [Documentation]    Test the RS232 interface at 1200 baud.

    RS232 Configure    baud_rate=1200
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[1200]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 2400 Baud
    [Documentation]    Test the RS232 interface at 2400 baud.

    RS232 Configure    baud_rate=2400
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[2400]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 4800 Baud
    [Documentation]    Test the RS232 interface at 4800 baud.

    RS232 Configure    baud_rate=4800
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[4800]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 9600 Baud
    [Documentation]    Test the RS232 interface at 9600 baud.

    RS232 Configure    baud_rate=9600
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[9600]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 19200 Baud
    [Documentation]    Test the RS232 interface at 19200 baud.

    RS232 Configure    baud_rate=19200
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[19200]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 38400 Baud
    [Documentation]    Test the RS232 interface at 38400 baud.

    RS232 Configure    baud_rate=38400
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[38400]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 57600 Baud
    [Documentation]    Test the RS232 interface at 57600 baud.

    RS232 Configure    baud_rate=57600
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[57600]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 At 115200 Baud
    [Documentation]    Test the RS232 interface at 115200 baud.

    RS232 Configure    baud_rate=115200
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[115200]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 Baud Rate Error Recovery
    [Documentation]
    ...    Verify that the RS232 interface can recover after recieving a
    ...    transmission that uses the incorrect baud rate.

    RS232 Configure    baud_rate=38400
    Printer Set Option    ${RS232 BAUD RATE}[Option]    ${RS232 BAUD RATE}[9600]
    Printer Reset

    Printer Redirect Enable
    RS232 Send    ${SAMPLE TEXT}
    Sleep    1s

    RS232 Configure    baud_rate=9600
    RS232 Send And Expect Echo    ${SAMPLE TEXT}
