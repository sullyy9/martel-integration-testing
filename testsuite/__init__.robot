*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             martel_printer_test_library.PrinterTestLibrary
Library             martel_printer_test_library.PrinterDebugLibrary

Suite Setup         Run Keywords
...                     Setup Printer Test Library
...                     Setup Printer Debug Library
Test Setup          Printer Clear Print Buffer
