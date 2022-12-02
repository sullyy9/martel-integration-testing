*** Settings ***
Documentation       Tests for IR baud rate.

Library             printer.Printer
Resource            configuration_options.resource
Resource            utils.resource
Resource            samples.resource

Suite Setup         Run Keywords
...                     Open Printer "USB" Interface
...                     Open Printer "IR" Interface
...                     Set Printer Option "${Default Font}" To "Default"
...                     Set Printer Option "&{IR FRAME FORMAT}" To "Default"
...                     Set Test System "IR" Frame Format To "8 Bits None"
Suite Teardown      Run Keywords
...                     Set Printer Option "&{IR BAUD RATE}" To "Default"
...                     Set Test System "IR" Baud Rate To "9600"
...                     Close Printer "IR" Interface
...                     Close Printer "USB" Interface

Force Tags          infrared    baud_rate


*** Test Cases ***
Test IR At 600 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "600"
    Set Test System "IR" Baud Rate To "600"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 1200 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "1200"
    Set Test System "IR" Baud Rate To "1200"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 2400 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "2400"
    Set Test System "IR" Baud Rate To "2400"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 4800 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "4800"
    Set Test System "IR" Baud Rate To "4800"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 9600 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "9600"
    Set Test System "IR" Baud Rate To "9600"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 19200 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "19200"
    Set Test System "IR" Baud Rate To "19200"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 38400 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "38400"
    Set Test System "IR" Baud Rate To "38400"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 57600 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "57600"
    Set Test System "IR" Baud Rate To "57600"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR At 115200 Baud
    [Documentation]    Verify that the given IR baud rate works correctly.

    Set Printer Option "&{IR BAUD RATE}" To "115200"
    Set Test System "IR" Baud Rate To "115200"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR Baud Rate Error Recovery
    [Documentation]
    ...    Verify that the IR interface can recover after recieving a
    ...    transmission that uses the incorrect baud rate.

    Set Printer Option "&{IR BAUD RATE}" To "9600"
    Set Test System "IR" Baud Rate To "4800"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Not Match "${ARIAL16 SAMPLE SHORT}"
    Clear Printer Print Buffer

    Set Test System "IR" Baud Rate To "9600"
    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly
