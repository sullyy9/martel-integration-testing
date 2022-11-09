*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             printer.Printer
Library             printout.ComparisonLibrary

Suite Setup         Run Keywords
...                     Create Comparison Library Output Directories
...                     Create Printer Library Output Directories
...                     Select Printer Mechanism
...                     Select Printer USB Port
Suite Teardown      Shutdown Printer
