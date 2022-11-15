*** Settings ***
Documentation       Suite for generating digital printout samples.

Library             OperatingSystem
Library             DateTime
Library             printer.Printer

Suite Setup         Run Keywords
...                     Create Printer Library Output Directories
...                     Select Printer Mechanism
...                     Select Printer USB Port
Suite Teardown      Shutdown Printer
