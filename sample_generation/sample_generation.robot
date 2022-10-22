*** Settings ***
Documentation       Generate samples

Library             printer.Printer
Library             printout.ComparisonLibrary

Suite Setup         Connect To Printer Comm Interfaces
Suite Teardown      Disconnect From Printer Comm Interfaces
Test Teardown       Set Printer Option ${Default Font} To 1

Force Tags          example_text


*** Variables ***
${DEFAULT FONT}     5

${SAMPLE TEXT}      Martel Instruments is a leading manufacturer and
...                 global supplier of bespoke and innovative
...                 commercial printing solutions.\n


*** Tasks ***
Generate Arial16 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial16 font.
    [Tags]    arial16

    Set Printer Option ${Default Font} To 1

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/arial16_sample_text.png

Generate Arial12 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial12 font.
    [Tags]    arial12

    Set Printer Option ${Default Font} To 2

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/arial12_sample_text.png

Generate Arial9 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial9 font.
    [Tags]    arial9

    Set Printer Option ${Default Font} To 3

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/arial9_sample_text.png

Generate Arial8 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial8 font.
    [Tags]    arial8

    Set Printer Option ${Default Font} To 4

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/arial8_sample_text.png

Generate Unicode16 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial8 font.
    [Tags]    unicode16

    Set Printer Option ${Default Font} To 5

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/unicode16_sample_text.png

Generate Unicode12 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial8 font.
    [Tags]    unicode12

    Set Printer Option ${Default Font} To 6

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/unicode12_sample_text.png

Generate Unicode8 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial8 font.
    [Tags]    unicode8

    Set Printer Option ${Default Font} To 7

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/unicode8_sample_text.png

Generate Unicode24 Example Text Sample
    [Documentation]    Generate an example text printout sample for the Arial8 font.
    [Tags]    unicode24

    Set Printer Option ${Default Font} To 8

    Print ${Sample Text}
    Wait Until Print Complete

    ${Printout} =    Last Printout
    Save Printout    ${Printout}    ${Sample_Output_Directory}/unicode24_sample_text.png


*** Keywords ***
Set Printer Option ${option:\d+} To ${setting:\d+}
    Enable Printer Debug Mode
    Set Printer Option    ${option}    ${setting}
    Reset Printer
    Sleep    1s
