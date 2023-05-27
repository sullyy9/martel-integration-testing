*** Settings ***
Documentation       Tests for RS232 baud rate.

Library             martel_printer_test_library.TCUTestLibrary

Test Setup          Run Keywords
...                     Set Battery Voltage    5V    AND
...                     Enable Battery Power    AND
...                     Close Power Relays    AND
...                     Sleep    1s
Test Teardown       Run Keywords
...                     Disable Battery Power    AND
...                     Open Power Relays

Test Tags           off_current


*** Test Cases ***
Test MCP1800 Off Current
    [Tags]    mcp1800
    Disable Battery Power
    Battery Voltage Drop 5s Should Be Less Than    600mV

Test MCP7800 Off Current
    [Tags]    mcp7800
    Disable Battery Power
    Battery Voltage Drop 5s Should Be Less Than    600mV
