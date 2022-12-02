*** Settings ***
Documentation       Tests for IR data bits and parity.

Library             printer.Printer
Resource            configuration_options.resource
Resource            utils.resource
Resource            samples.resource

Suite Setup         Run Keywords
...                     Open Printer "USB" Interface
...                     Open Printer "IR" Interface
...                     Set Printer Option "${Default Font}" To "Default"
...                     Set Printer Option "&{IR Baud Rate}" To "Default"
...                     Set Test System "IR" Baud Rate To "9600"
Suite Teardown      Run Keywords
...                     Set Printer Option "&{IR FRAME FORMAT}" To "Default"
...                     Set Test System "IR" Frame Format To "8 Bits None"
...                     Close Printer "IR" Interface
...                     Close Printer "USB" Interface

Force Tags          infrared    frame_format


*** Test Cases ***
Test IR With 8 Bits No Parity
    [Documentation]    Verify that the given IR frame format works correctly.

    Set Printer Option "&{IR FRAME FORMAT}" To "8 Bits None"
    Set Test System "IR" Frame Format To "8 Bits None"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR With 8 Bits Even Parity
    [Documentation]    Verify that the given IR frame format works correctly.

    Set Printer Option "&{IR FRAME FORMAT}" To "8 Bits Even"
    Set Test System "IR" Frame Format To "8 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR With 8 Bits Odd Parity
    [Documentation]    Verify that the given IR frame format works correctly.

    Set Printer Option "&{IR FRAME FORMAT}" To "8 Bits Odd"
    Set Test System "IR" Frame Format To "8 Bits Odd"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR With 7 Bits Even Parity
    [Documentation]    Verify that the given IR frame format works correctly.

    Set Printer Option "&{IR FRAME FORMAT}" To "7 Bits Even"
    Set Test System "IR" Frame Format To "7 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR With 7 Bits Odd Parity
    [Documentation]    Verify that the given IR frame format works correctly.

    Set Printer Option "&{IR FRAME FORMAT}" To "7 Bits Odd"
    Set Test System "IR" Frame Format To "7 Bits Odd"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR Parity Error Recovery
    [Documentation]
    ...    Verify that the IR interface can recover after recieving a
    ...    transmission that uses the incorrect parity.

    Set Printer Option "&{IR FRAME FORMAT}" To "8 Bits Odd"
    Set Test System "IR" Frame Format To "8 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Not Match "${ARIAL16 SAMPLE SHORT}"
    Clear Printer Print Buffer

    Set Test System "IR" Frame Format To "8 Bits Odd"
    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly

Test IR Data Bit Error Recovery
    [Documentation]
    ...    Verify that the IR interface can recover after recieving a
    ...    transmission that uses the incorrect number of data bits.

    Set Printer Option "&{IR FRAME FORMAT}" To "7 Bits Even"
    Set Test System "IR" Frame Format To "8 Bits Even"

    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Not Match "${ARIAL16 SAMPLE SHORT}"
    Clear Printer Print Buffer

    Set Test System "IR" Frame Format To "7 Bits Even"
    Print    ${SAMPLE TEXT SHORT}    interface=IR
    Wait Until Print Complete
    Printout Should Match "${ARIAL16 SAMPLE SHORT}" Exactly
