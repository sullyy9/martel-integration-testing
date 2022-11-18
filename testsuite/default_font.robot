*** Settings ***
Documentation       Verify that the default font settings contain the correct
...                 fonts.

Library             printer.Printer
Library             printout.ComparisonLibrary
Resource            configuration_options.resource
Resource            utils.resource
Resource            samples.resource

Suite Setup         Open Printer USB Interface
Suite Teardown      Close Printer USB Interface
Test Teardown       Run Keywords
...                     Save Comparison If Test Failed
...                     Set Printer Option "&{Default Font}" To "Default"

Force Tags          config_options    default_fonts


*** Test Cases ***
Default Font 1 Should Be Arial16
    [Documentation]
    ...    Verify that the default font configuration option has the Arial16
    ...    font as its first setting.
    [Tags]    arial16

    Set Printer Option "&{DEFAULT FONT}" To "Slot 1"
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE}

Default Font 2 Should Be Arial12
    [Documentation]
    ...    Verify that the default font configuration option has the Arial12
    ...    font as its second setting.
    [Tags]    arial12

    Set Printer Option "&{DEFAULT FONT}" To "Slot 2"
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL12 SAMPLE}

Default Font 3 Should Be Arial9
    [Documentation]
    ...    Verify that the default font configuration option has the Arial9
    ...    font as its third setting.
    [Tags]    arial9

    Set Printer Option "&{DEFAULT FONT}" To "Slot 3"
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL9 SAMPLE}

Default Font 4 Should Be Arial8
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    arial8

    Set Printer Option "&{DEFAULT FONT}" To "Slot 4"
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL8 SAMPLE}

Default Font 5 Should Be Unicode16
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    unicode16

    Set Printer Option "&{DEFAULT FONT}" To "Slot 5"
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${UNICODE16 SAMPLE}

Default Font 6 Should Be Unicode12
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    unicode12

    Set Printer Option "&{DEFAULT FONT}" To "Slot 6"
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${UNICODE12 SAMPLE}

Default Font 7 Should Be Unicode8
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    unicode8

    Set Printer Option "&{DEFAULT FONT}" To "Slot 7"
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${UNICODE8 SAMPLE}
