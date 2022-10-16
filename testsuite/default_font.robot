*** Settings ***
Documentation       Verify that the default font settings contain the correct fonts.

Library             printer.Printer
Library             printout.ComparisonLibrary
Resource            config_options.resource

Suite Setup         Connect To Printer Comm Interfaces
Suite Teardown      Disconnect From Printer Comm Interfaces
Test Teardown       Run Keywords
...                     Save Comparison If Test Failed    AND
...                     Set Printer Option ${Default Font} To 1


*** Variables ***
${Arial16 Sample}       arial16_sample_text.png
${Arial12 Sample}       arial12_sample_text.png
${Arial9 Sample}        arial9_sample_text.png
${Arial8 Sample}        arial8_sample_text.png

${Sample Text}          Martel Instruments is a leading manufacturer and global supplier of bespoke and innovative commercial printing solutions.\n


*** Test Cases ***
Default Font 1 Should Be Arial16
    [Tags]    config_options    default_fonts

    Given Default Font Is Set To 1
    When Printing ${Sample Text}
    Then Printout Should Match ${Arial16 Sample}

Default Font 2 Should Be Arial12
    [Tags]    config_options    default_fonts

    Given Default Font Is Set To 2
    When Printing ${Sample Text}
    Then Printout Should Match ${Arial12 Sample}

Default Font 3 Should Be Arial9
    [Tags]    config_options    default_fonts

    Given Default Font Is Set To 3
    When Printing ${Sample Text}
    Then Printout Should Match ${Arial9 Sample}

Default Font 4 Should Be Arial8
    [Tags]    config_options    default_fonts

    Given Default Font Is Set To 4
    When Printing ${Sample Text}
    Then Printout Should Match ${Arial8 Sample}


*** Keywords ***
Default Font Is Set To ${Setting:\d+}
    Enable Printer Debug Mode
    Set Printer Option    ${Default Font}    ${Setting}
    Reset Printer
    Sleep    1s

Printing ${Text}
    Print ${Text}
    Wait Until Print Complete

Printout Should Match ${Sample}
    Load Sample ${Sample}
    ${Printout} =    Last Printout
    Sample Should Match ${Printout}

Save Comparison If Test Failed
    ${Printout} =    Last Printout
    Run Keyword If Test Failed    Save Comparison    ${Printout}    ${TEST NAME}.png
