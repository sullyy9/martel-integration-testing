*** Settings ***
Documentation       Tests for the infrared communications interface.

Library             printer.Printer

Suite Setup         Run Keywords
...                     Open Printer "USB" Interface
...                     Open Printer "IR" Interface
Suite Teardown      Run Keywords
...                     Close Printer "IR" Interface
...                     Close Printer "USB" Interface

Force Tags          infrared
