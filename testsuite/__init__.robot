*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             printer.Printer

Suite Setup         Run Keywords
...                     Create Printer Library Output Directories
...                     Select Printer Mechanism Analyzer
...                     Select Printer USB Interface
...                     Select Printer RS232 Interface
...                     Select Printer Ir Interface
Suite Teardown      Shutdown Printer
Test Setup          Clear Printer Print Buffer
