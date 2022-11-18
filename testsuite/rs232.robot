*** Settings ***
Documentation       Tests for RS232 related functionality.

Library             printer.Printer
Library             printout.ComparisonLibrary
Resource            configuration_options.resource
Resource            utils.resource

Suite Setup         Run Keywords
...                     Open Printer USB Interface
...                     Set Option ${DEFAULT FONT} To 1
Suite Teardown      Close Printer USB Interface
Test Teardown       Run Keywords
...                     Save Comparison If Test Failed
...                     Set Printer RS232 Baud Rate To 9600
...                     Set Test System RS232 Baud Rate To 9600

Force Tags          rs232


*** Variables ***
${ARIAL16 SAMPLE SHORT}         arial16_sample_text_short.png
${ARIAL12 SAMPLE SHORT}         arial12_sample_text_short.png
${ARIAL9 SAMPLE SHORT}          arial9_sample_text_short.png
${ARIAL8 SAMPLE SHORT}          arial8_sample_text_short.png
${UNICODE16 SAMPLE SHORT}       unicode16_sample_text_short.png
${UNICODE12 SAMPLE SHORT}       unicode12_sample_text_short.png
${UNICODE8 SAMPLE SHORT}        unicode8_sample_text_short.png

${SAMPLE TEXT SHORT}            Martel Instruments is a leading manufacturer
...                             and global... \n


*** Test Cases ***
Test RS232 At 600 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 600
    Set Test System RS232 Baud Rate To 600

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 1200 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 1200
    Set Test System RS232 Baud Rate To 1200

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 2400 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 2400
    Set Test System RS232 Baud Rate To 2400

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 4800 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 4800
    Set Test System RS232 Baud Rate To 4800

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 9600 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 9600
    Set Test System RS232 Baud Rate To 9600

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 19200 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 19200
    Set Test System RS232 Baud Rate To 19200

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 38400 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 38400
    Set Test System RS232 Baud Rate To 38400

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 57600 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 57600
    Set Test System RS232 Baud Rate To 57600

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}

Test RS232 At 115200 Baud
    [Documentation]    Verify that the given RS232 baud rate works correctly.

    Set Printer RS232 Baud Rate To 115200
    Set Test System RS232 Baud Rate To 115200

    Print    ${SAMPLE TEXT SHORT}    interface=RS232
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE SHORT}
