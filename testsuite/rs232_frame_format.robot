*** Settings ***
Documentation       Tests for RS232 data bits and parity.

Library             printer.Printer
Resource            configuration_options.resource
Resource            utils.resource
Resource            samples.resource

Suite Setup         Run Keywords
...                     Open Printer "USB" Interface
...                     Open Printer "RS232" Interface
...                     Set Printer Option "${Default Font}" To "Default"
...                     Set Printer Option "&{RS232 Baud Rate}" To "Default"
...                     Set Test System "RS232" Baud Rate To "9600"
Suite Teardown      Run Keywords
...                     Close Printer "USB" Interface
...                     Close Printer "RS232" Interface
...                     Set Printer Option "&{RS232 FRAME FORMAT}" To "Default"
...                     Set Test System "RS232" Frame Format To "8 Bits None"

Force Tags          rs232    frame_format


*** Test Cases ***
Test RS232 With 8 Bits No Parity
    [Documentation]    Verify that the given RS232 frame format works correctly.

    Set Printer Option "&{RS232 FRAME FORMAT}" To "8 Bits None"
    Set Test System "RS232" Frame Format To "8 Bits None"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 With 8 Bits Even Parity
    [Documentation]    Verify that the given RS232 frame format works correctly.

    Set Printer Option "&{RS232 FRAME FORMAT}" To "8 Bits Even"
    Set Test System "RS232" Frame Format To "8 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 With 8 Bits Odd Parity
    [Documentation]    Verify that the given RS232 frame format works correctly.

    Set Printer Option "&{RS232 FRAME FORMAT}" To "8 Bits Odd"
    Set Test System "RS232" Frame Format To "8 Bits Odd"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 With 7 Bits Even Parity
    [Documentation]    Verify that the given RS232 frame format works correctly.

    Set Printer Option "&{RS232 FRAME FORMAT}" To "7 Bits Even"
    Set Test System "RS232" Frame Format To "7 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 With 7 Bits Odd Parity
    [Documentation]    Verify that the given RS232 frame format works correctly.

    Set Printer Option "&{RS232 FRAME FORMAT}" To "7 Bits Odd"
    Set Test System "RS232" Frame Format To "7 Bits Odd"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 Parity Error Recovery
    [Documentation]
    ...    Verify that the RS232 interface can recover after recieving a
    ...    transmission that uses the incorrect parity.

    Set Printer Option "&{RS232 FRAME FORMAT}" To "8 Bits Odd"
    Set Test System "RS232" Frame Format To "8 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Not Match "${ARIAL16 SAMPLE SHORT}"
    Clear Printer Print Buffer

    Set Test System "RS232" Frame Format To "8 Bits Odd"
    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 Data Bit Error Recovery
    [Documentation]
    ...    Verify that the RS232 interface can recover after recieving a
    ...    transmission that uses the incorrect number of data bits.

    Set Printer Option "&{RS232 FRAME FORMAT}" To "7 Bits Even"
    Set Test System "RS232" Frame Format To "8 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Not Match "${ARIAL16 SAMPLE SHORT}"
    Clear Printer Print Buffer

    Set Test System "RS232" Frame Format To "7 Bits Even"
    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly
