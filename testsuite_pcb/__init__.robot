*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             martel_printer_test_library.TCUTestLibrary    ${Environment}
Library             martel_printer_test_library.PrinterDebugLibrary    ${Environment}
Library             martel_printer_test_library.PrinterTestLibrary    ${Environment}

Suite Setup         Setup TCU Test Library
