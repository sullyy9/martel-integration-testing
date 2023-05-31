*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             Dialogs
Library             martel_printer_test_library.TCUTestLibrary    ${Environment}
Library             martel_printer_test_library.PrinterDebugLibrary    ${Environment}
Library             martel_printer_test_library.PrinterTestLibrary    ${Environment}
Resource            utilities.resource

Suite Setup         Run Keywords
...                     Setup TCU Test Library    AND
...                     Setup Printer Debug Library    AND
...                     Setup Printer Test Library    AND
...                     Set Battery Voltage    5V    AND
...                     Enable Battery Power    AND
...                     Close Power Relays    AND
...                     Pause Execution    Program printer and press ok  AND
...                     Wake Printer
Suite Teardown      Open Power Relays
