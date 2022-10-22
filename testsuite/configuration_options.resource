*** Settings ***
Documentation       Resource file for config option related stuff.

Library             printer.Printer


*** Variables ***
${DEFAULT FONT}     5


*** Keywords ***
Set Option ${option:\d+} To ${setting:\d+}
    Enable Printer Debug Mode
    Set Printer Option    ${option}    ${setting}
    Reset Printer
    Sleep    1s
