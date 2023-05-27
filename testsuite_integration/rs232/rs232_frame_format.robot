*** Settings ***
Documentation       Tests for RS232 data bits and parity.

Library             martel_printer_test_library.PrinterTestLibrary
Library             martel_printer_test_library.PrinterDebugLibrary
Resource            ../configuration_options.resource

Suite Setup         Run Keywords
...                     RS232 Configure    baud_rate=9600    data_bits=8    parity=None    AND
...                     Printer Set Option ${RS232 Baud Rate}[Option]    ${RS232 Baud Rate}[Default]    AND
...                     Printer Reset
Suite Teardown      Run Keywords
...                     RS232 Configure    baud_rate=9600    data_bits=8    parity=None    AND
...                     Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[Default]    AND
...                     Printer Reset

Force Tags          frame_format


*** Variables ***
${SAMPLE TEXT}      Martel Instruments is a leading manufacturer and global
...                 supplier of bespoke and innovative commercial printing
...                 solutions.


*** Test Cases ***
Test RS232 With 8 Bits No Parity
    [Documentation]    Test the RS232 interface with 8 bits no parity.

    RS232 Configure    data_bits=8    parity=None
    Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[8 Bits None]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 With 8 Bits Even Parity
    [Documentation]    Test the RS232 interface with 8 bits even parity.

    RS232 Configure    data_bits=8    parity=Even
    Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[8 Bits Even]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 With 8 Bits Odd Parity
    [Documentation]    Test the RS232 interface with 8 bits odd parity.

    RS232 Configure    data_bits=8    parity=Odd
    Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[8 Bits Odd]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 With 7 Bits Even Parity
    [Documentation]    Test the RS232 interface with 7 bits even parity.

    RS232 Configure    data_bits=7    parity=Even
    Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[7 Bits Even]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 With 7 Bits Odd Parity
    [Documentation]    Test the RS232 interface with 7 bits odd parity.

    RS232 Configure    data_bits=7    parity=Odd
    Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[7 Bits Odd]
    Printer Reset

    Printer Redirect Enable
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 Parity Error Recovery
    [Documentation]
    ...    Verify that the RS232 interface can recover after recieving a
    ...    transmission that uses the incorrect parity.

    RS232 Configure    data_bits=8    parity=Even
    Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[8 Bits Odd]
    Printer Reset

    Printer Redirect Enable
    RS232 Send    ${SAMPLE TEXT}
    Sleep    1s

    RS232 Configure    data_bits=8    parity=Odd
    RS232 Send And Expect Echo    ${SAMPLE TEXT}

Test RS232 Data Bit Error Recovery
    [Documentation]
    ...    Verify that the RS232 interface can recover after recieving a
    ...    transmission that uses the incorrect number of data bits.

    RS232 Configure    data_bits=7    parity=Even
    Printer Set Option    ${RS232 FRAME FORMAT}[Option]    ${RS232 FRAME FORMAT}[8 Bits Even]
    Printer Reset

    Printer Redirect Enable
    RS232 Send    ${SAMPLE TEXT}
    Sleep    1s

    RS232 Configure    data_bits=8    parity=Even
    RS232 Send And Expect Echo    ${SAMPLE TEXT}
