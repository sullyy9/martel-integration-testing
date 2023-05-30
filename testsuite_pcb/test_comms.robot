*** Settings ***
Documentation       Tests for RS232.

Library             martel_printer_test_library.TCUTestLibrary    ${Environment}
Library             martel_printer_test_library.PrinterDebugLibrary    ${Environment}
Library             martel_printer_test_library.PrinterTestLibrary    ${Environment}
Resource            utilities.resource

Test Setup          Printer Reset

Test Tags           comms


*** Variables ***
${TEST STRING}      Martel Instruments is a leading manufacturer and global...


*** Test Cases ***
Test RS232 Comms
    [Documentation]    Check that data can be sent and received over RS232.
    [Tags]    rs232

    IF    ${Environment.has_rs232_through_tcu}
        RS232 Send Dummy Command And Expect Response
    ELSE
        Printer Redirect Enable
        Rs232 Send And Expect Echo    ${TEST STRING}
    END

Test USB Comms
    [Documentation]    Check that data can be sent and received over RS232.
    [Tags]    usb
    Printer Redirect Enable
    USB Send And Expect Echo    ${TEST STRING}
