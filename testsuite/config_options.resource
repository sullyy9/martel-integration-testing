*** Settings ***
Documentation       Resource file for config option related stuff.

Library             printer.Printer


*** Variables ***
${Default Font}     5


*** Keywords ***
Set Printer Option ${option:\d+} To ${setting:\d+}
    Enable Printer Debug Mode
    Set Printer Option    ${option}    ${setting}
    Reset Printer
    Sleep    1s
