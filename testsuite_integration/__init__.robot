*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             martel_printer_test_library.PrinterTestLibrary
Library             martel_printer_test_library.PrinterDebugLibrary
Library             martel_printer_test_library.PrintoutCaptureLibrary

Suite Setup         Run Keywords
...                     Setup Printer Test Library
...                     Setup Printer Debug Library
...                     Setup Printout Capture Library
Test Setup          Printer Clear Print Buffer
Test Teardown       Printer Reset
