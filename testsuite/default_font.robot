*** Settings ***
Documentation       Verify that the default font settings contain the correct
...                 fonts.

Library             printer.Printer
Library             printout.ComparisonLibrary
Resource            configuration_options.resource

Suite Setup         Open Printer USB Interface
Suite Teardown      Close Printer USB Interface
Test Teardown       Run Keywords
...                     Save Comparison If Test Failed
...                     Set Option ${Default Font} To 1

Force Tags          config_options    default_fonts


*** Variables ***
${ARIAL16 SAMPLE}       arial16_sample_text.png
${ARIAL12 SAMPLE}       arial12_sample_text.png
${ARIAL9 SAMPLE}        arial9_sample_text.png
${ARIAL8 SAMPLE}        arial8_sample_text.png
${UNICODE16 SAMPLE}     unicode16_sample_text.png
${UNICODE12 SAMPLE}     unicode12_sample_text.png
${UNICODE8 SAMPLE}      unicode8_sample_text.png

${SAMPLE TEXT}          Martel Instruments is a leading manufacturer and global
...                     supplier of bespoke and innovative commercial printing
...                     solutions.\n


*** Test Cases ***
Default Font 1 Should Be Arial16
    [Documentation]
    ...    Verify that the default font configuration option has the Arial16
    ...    font as its first setting.
    [Tags]    arial16

    Set Option ${DEFAULT FONT} To 1
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL16 SAMPLE}

Default Font 2 Should Be Arial12
    [Documentation]
    ...    Verify that the default font configuration option has the Arial12
    ...    font as its second setting.
    [Tags]    arial12

    Set Option ${DEFAULT FONT} To 2
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL12 SAMPLE}

Default Font 3 Should Be Arial9
    [Documentation]
    ...    Verify that the default font configuration option has the Arial9
    ...    font as its third setting.
    [Tags]    arial9

    Set Option ${DEFAULT FONT} To 3
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL9 SAMPLE}

Default Font 4 Should Be Arial8
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    arial8

    Set Option ${DEFAULT FONT} To 4
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${ARIAL8 SAMPLE}

Default Font 5 Should Be Unicode16
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    unicode16

    Set Option ${DEFAULT FONT} To 5
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${UNICODE16 SAMPLE}

Default Font 6 Should Be Unicode12
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    unicode12

    Set Option ${DEFAULT FONT} To 6
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${UNICODE12 SAMPLE}

Default Font 7 Should Be Unicode8
    [Documentation]
    ...    Verify that the default font configuration option has the Arial8
    ...    font as its fourth setting.
    [Tags]    unicode8

    Set Option ${DEFAULT FONT} To 7
    Print    ${SAMPLE TEXT}
    Wait Until Print Complete
    Printout Should Match ${UNICODE8 SAMPLE}


*** Keywords ***
Printout Should Match ${SAMPLE}
    Load Sample ${SAMPLE}
    ${PRINTOUT} =    Last Printout
    Sample Should Match ${PRINTOUT}

Save Comparison If Test Failed
    [Documentation]
    ...    If the last test failed, generate an image comparing the
    ...    sample and printout and save it.

    ${Printout} =    Last Printout
    Run Keyword If Test Failed
    ...    Save Comparison    ${Printout}    ${TEST NAME}.png
