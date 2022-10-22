*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             printer.Printer
Library             printout.ComparisonLibrary

Suite Setup         Create Comparison Library Output Directories
Suite Teardown      Shutdown Printer
