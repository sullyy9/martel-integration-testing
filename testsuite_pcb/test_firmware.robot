*** Settings ***
Documentation       Test properties of the printer firmware, font library and bluetooth firmware.

Library             martel_printer_test_library.TCUTestLibrary    ${Environment}
Library             martel_printer_test_library.PrinterDebugLibrary    ${Environment}
Library             martel_printer_test_library.PrinterTestLibrary    ${Environment}

Test Setup          Run Keywords
...                     Printer Reset

Test Tags           firmware


*** Test Cases ***
Test Checksum
    [Documentation]    Check that the checksum returned by the printer matches that of the firmware.
    [Tags]    checksum
    Printer Firmware Checksum Should Be    63388
