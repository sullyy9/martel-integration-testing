*** Settings ***
Documentation       Generate samples

Library             printer.Printer
Library             printout.ComparisonLibrary

Suite Setup         Open Printer USB Interface
Suite Teardown      Close Printer USB Interface
Test Teardown       Set Printer Option ${Default Font} To 1


*** Variables ***
${SAMPLE TEXT}          Martel Instruments is a leading manufacturer and
...                     global supplier of bespoke and innovative
...                     commercial printing solutions.\n

${SAMPLE TEXT SHORT}    Martel Instruments is a leading manufacturer and
...                     global... \n

${DEFAULT FONT}         5

${ARIAL16}              1
${ARIAL12}              2
${ARIAL9}               3
${ARIAL8}               4
${UNICODE16}            5
${UNICODE12}            6
${UNICODE8}             7


*** Tasks ***
Generate Text Samples
    [Documentation]
    ...    Generate digital printout's for the text sample in a variety of
    ...    fonts.
    [Tags]    sample_text
    [Template]    Generate Sample With
    ${SAMPLE TEXT}    ${ARIAL16}    arial16_sample_text
    ${SAMPLE TEXT}    ${ARIAL12}    arial12_sample_text
    ${SAMPLE TEXT}    ${ARIAL9}    arial9_sample_text
    ${SAMPLE TEXT}    ${ARIAL8}    arial8_sample_text
    ${SAMPLE TEXT}    ${UNICODE16}    unicode16_sample_text
    ${SAMPLE TEXT}    ${UNICODE12}    unicode12_sample_text
    ${SAMPLE TEXT}    ${UNICODE8}    unicode8_sample_text

Generate Short Text Samples
    [Documentation]
    ...    Generate digital printout's for the short text sample in a variety
    ...    of fonts.
    [Tags]    short_sample_text
    [Template]    Generate Sample With
    ${SAMPLE TEXT SHORT}    ${ARIAL16}    arial16_sample_text_short
    ${SAMPLE TEXT SHORT}    ${ARIAL12}    arial12_sample_text_short
    ${SAMPLE TEXT SHORT}    ${ARIAL9}    arial9_sample_text_short
    ${SAMPLE TEXT SHORT}    ${ARIAL8}    arial8_sample_text_short
    ${SAMPLE TEXT SHORT}    ${UNICODE16}    unicode16_sample_text_short
    ${SAMPLE TEXT SHORT}    ${UNICODE12}    unicode12_sample_text_short
    ${SAMPLE TEXT SHORT}    ${UNICODE8}    unicode8_sample_text_short


*** Keywords ***
Set Printer Option ${option:\d+} To ${setting:\d+}
    Enable Printer Debug Mode
    Set Printer Option    ${option}    ${setting}
    Reset Printer
    Sleep    1s

Generate Sample With
    [Documentation]
    ...    Generate a sample with the given text using the given
    ...    default font.
    [Arguments]    ${TEXT}    ${SETTING}    ${NAME}

    Set Printer Option ${Default Font} To ${SETTING}

    Print    ${TEXT}    name=${NAME}
    Wait Until Print Complete
