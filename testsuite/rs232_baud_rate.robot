*** Settings ***
Documentation       Tests for RS232 baud rate.

Library             printer.Printer
Resource            configuration_options.resource
Resource            utils.resource
Resource            samples.resource

Suite Setup         Run Keywords
...                     Open Printer "USB" Interface
...                     Open Printer "RS232" Interface
...                     Set Printer Option "${Default Font}" To "Default"
...                     Set Printer Option "&{RS232 FRAME FORMAT}" To "Default"
...                     Set Test System "RS232" Frame Format To "8 Bits None"
Suite Teardown      Run Keywords
...                     Close Printer "USB" Interface
...                     Close Printer "RS232" Interface
...                     Set Printer Option "&{RS232 BAUD RATE}" To "Default"
...                     Set Test System "RS232" Baud Rate To "9600"

Force Tags          rs232    baud_rate


*** Test Cases ***
Test RS232 At 600 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "600"
    Set Test System "RS232" Baud Rate To "600"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 1200 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "1200"
    Set Test System "RS232" Baud Rate To "1200"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 2400 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "2400"
    Set Test System "RS232" Baud Rate To "2400"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 4800 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "4800"
    Set Test System "RS232" Baud Rate To "4800"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 9600 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "9600"
    Set Test System "RS232" Baud Rate To "9600"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 19200 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "19200"
    Set Test System "RS232" Baud Rate To "19200"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 38400 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "38400"
    Set Test System "RS232" Baud Rate To "38400"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 57600 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "57600"
    Set Test System "RS232" Baud Rate To "57600"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 At 115200 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer Option "&{RS232 BAUD RATE}" To "115200"
    Set Test System "RS232" Baud Rate To "115200"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test RS232 Baud Rate Error Recovery
    [Documentation]
    ...    Verify that the RS232 interface can recover after recieving a
    ...    transmission that uses the incorrect baud rate.

    Set Printer Option "&{RS232 BAUD RATE}" To "9600"
    Set Test System "RS232" Baud Rate To "4800"

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Not Match "${ARIAL16 SAMPLE SHORT}"
    Clear Printer Print Buffer

    Set Test System "RS232" Baud Rate To "9600"
    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly
