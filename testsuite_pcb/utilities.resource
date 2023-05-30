*** Settings ***
Documentation       Tests for RS232.

Library             Dialogs
Library             martel_printer_test_library.TCUTestLibrary    ${Environment}
Library             martel_printer_test_library.PrinterDebugLibrary    ${Environment}
Library             martel_printer_test_library.PrinterTestLibrary    ${Environment}


*** Keywords ***
Wake Printer
    [Documentation]    Wake up the printer using RS232 if available otherwise ask the user to do it.
    IF    ${Environment.has_rs232_wakeup}
        ${wake command}=    Convert To Bytes    0 0 0    int
        RS232 Send    ${wake command}
    ELSE
        Pause Execution    Turn printer on
    END
    Sleep    0.5s
