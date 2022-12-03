*** Settings ***
Documentation       Tests for the RS232 communications interface.

Library             printer.Printer

Suite Setup         Run Keywords
...                     Open Printer "USB" Interface
...                     Open Printer "RS232" Interface
Suite Teardown      Run Keywords
...                     Close Printer "RS232" Interface
...                     Close Printer "USB" Interface

Force Tags          rs232
