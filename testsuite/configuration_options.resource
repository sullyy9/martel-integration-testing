*** Settings ***
Documentation       Resource file for config option related stuff.

Library             printer.Printer


*** Variables ***
${DEFAULT FONT}     5


*** Keywords ***
Set Option ${option} To ${setting}
    Enable Printer Debug Mode
    Set Printer Option    ${option}    ${setting}
    Reset Printer
    Close Printer USB Interface
    Sleep    1s
    Open Printer USB Interface
    Send Printer Command    Feed Line\n
