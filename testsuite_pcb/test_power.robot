*** Settings ***
Documentation       Tests for RS232 baud rate.

Library             martel_printer_test_library.TCUTestLibrary    ${Environment}
Library             martel_printer_test_library.PrinterDebugLibrary    ${Environment}
Resource            utilities.resource

Test Tags           power


*** Test Cases ***
Test MCP1800 Off Current
    [Documentation]    Test the current consumption when the printer is powered off.
    [Tags]    mcp1800_offcurrent
    Printer Power Off
    Sleep    1s
    Open Power Relays
    Battery Voltage Drop 5s Should Be Less Than    400mV

    [Teardown]    Run Keywords
    ...    Close Power Relays    AND
    ...    Wake Printer

Test MCP1800 On Current
    [Documentation]    Test the current consumption while the printer is powered on.
    [Tags]    mcp1800_oncurrent
    Battery Current Should Be Between    50mA    90mA

Test MCP7800 Off Current
    [Documentation]    Test the current consumption when the printer is powered off.
    [Tags]    mcp7800_offcurrent
    Printer Power Off
    Sleep    1s
    Open Power Relays
    Battery Voltage Drop 5s Should Be Less Than    800mV
    Close Power Relays
    Wake Printer
