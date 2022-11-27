*** Settings ***
Documentation       Integration testing suite for Martel MCP1800 B series
...                 printers.

Library             printer.Printer

Suite Setup         Run Keywords
...                     Create Printer Library Output Directories
...                     Select Printer Mechanism
...                     Select Printer USB Port
...                     Select Printer RS232 Port
Suite Teardown      Shutdown Printer
Test Setup          Clear Printer Print Buffer
