*** Settings ***
Documentation       Suite for generating digital printout samples.

Library             OperatingSystem
Library             DateTime
Library             martel_printer_test_library.PrinterTestLibrary
Library             martel_printer_test_library.PrinterDebugLibrary
Library             martel_printer_test_library.PrintoutCaptureLibrary

Suite Setup         Run Keywords
...                     Setup Printer Test Library
...                     Setup Printer Debug Library
...                     Setup Printout Capture Library
Test Setup          Printer Clear Print Buffer
