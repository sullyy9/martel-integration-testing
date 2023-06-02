*** Settings ***
Documentation       Test properties of the printer firmware, font library and bluetooth firmware.

Library             Dialogs
Library             martel_printer_test_library.TCUTestLibrary    ${Environment}
Library             martel_printer_test_library.PrinterDebugLibrary    ${Environment}
Library             martel_printer_test_library.PrinterTestLibrary    ${Environment}

Test Setup          Run Keywords
...                     Printer Reset

Test Tags           self_test


*** Test Cases ***
Test Checksum
    [Documentation]    Check that the checksum returned by the printer matches that of the firmware.
    [Tags]    checksum

    ${checksum}=    Printer Measure    Printer Firmware Checksum
    Should Be Equal As Integers    ${checksum}    15139

Test Battery ADC
    [Documentation]    Check that ADC gives a resonable battery reading.
    [Tags]    adc    battery

    ${voltage}=    Printer Measure    Battery Voltage
    Should Be True    ${voltage} >= 4.8
    Should Be True    ${voltage} <= 5.2

Test Vcc ADC
    [Documentation]    Check that ADC gives a resonable Vcc reading.
    [Tags]    adc    vcc

    ${voltage}=    Printer Measure    Vcc Voltage
    Should Be True    ${voltage} >= 3.1
    Should Be True    ${voltage} <= 3.5

Test Paper Sensor
    [Documentation]    Check that ADC gives a resonable paper sensor reading.
    [Tags]    adc    paper

    ${value}=    Printer Measure    Paper Sensor
    Should Be True    ${value} <= 600

    Pause Execution    Remove paper and press ok
    ${value}=    Printer Measure    Paper Sensor
    Should Be True    ${value} >= 700

    [Teardown]    Pause Execution    Insert paper and press ok

Test RTC Present
    [Documentation]    Check that the RTC is present.
    [Tags]    rtc

    ${rtc_present}=    Printer Measure    RTC Present
    Should Be Equal As Integers    ${rtc_present}    1
