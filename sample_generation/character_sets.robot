*** Settings ***
Documentation       Generate samples

Library             OperatingSystem
Library             martel_printer_test_library.PrinterTestLibrary
Library             martel_printer_test_library.PrinterDebugLibrary
Library             martel_printer_test_library.PrintoutCaptureLibrary

Suite Setup         Run Keywords
...                     Printer Set Option    ${Default Font}    1    AND
...                     Printer Reset    AND
...                     Create Directory    ${SAMPLE DIRECTORY}


*** Variables ***
${SAMPLE TEXT}          Martel Instruments is a leading manufacturer and
...                     global supplier of bespoke and innovative
...                     commercial printing solutions.\n

${SAMPLE TEXT SHORT}    Martel Instruments is a leading manufacturer and
...                     global... \n

${DEFAULT FONT}         5
${FONT SLOT 1}          50

&{FONT ID}              Arial8=1
...                     Arial8_ISO8859_7=2
...                     Arial9=3
...                     Arial12=4
...                     Arial12_ISO8859_7=5
...                     Arial16=6
...                     Arial16_ISO8859_1=7
...                     Arial16_ISO8859_2=8
...                     Arial16_ISO8859_7=9
...                     Arial16_ISO8859_9=10
...                     Arial16_ISO8859_13=11
...                     NewEcma94_16=12
...                     NewRoman8_16=13
...                     Unicode8=251
...                     Unicode12=252
...                     Unicode16=253
...                     Unicode24=254

${SAMPLE DIRECTORY}     ${OUTPUT DIR}/character_set_samples


*** Tasks ***
Generate Standard Samples
    [Documentation]
    ...    Generate digital character set sample printouts using no font styling.
    [Tags]    character_set_sample    styling_none

    Set Local Variable    ${output directory}    ${SAMPLE DIRECTORY}/standard
    Create Directory    ${output directory}

    FOR    ${FONT NAME}    ${FONT ID}    IN    &{FONT ID}
        Set Local Variable    ${sample file}    ${output directory}/${FONT NAME}.png
        ${sample exists} =    Run Keyword And Return Status    File Should Exist    ${sample file}
        IF    not ${sample exists}
            Generate Sample    ${FONT ID}    ${output directory}/${FONT NAME}.png
        END
    END

Generate Bold Samples
    [Documentation]
    ...    Generate digital character set sample printouts using only bold font styling.
    [Tags]    character_set_sample    styling_bold

    Set Local Variable    ${output directory}    ${SAMPLE DIRECTORY}/bold
    Create Directory    ${output directory}

    FOR    ${FONT NAME}    ${FONT ID}    IN    &{FONT ID}
        Set Local Variable    ${sample file}    ${output directory}/${FONT NAME}.png
        ${sample exists} =    Run Keyword And Return Status    File Should Exist    ${sample file}
        IF    not ${sample exists}
            Generate Bold Sample    ${FONT ID}    ${output directory}/${FONT NAME}.png
        END
    END

Generate Italic Samples
    [Documentation]
    ...    Generate digital character set sample printouts using only italic font styling.
    [Tags]    character_set_sample    styling_italic

    Set Local Variable    ${output directory}    ${SAMPLE DIRECTORY}/italic
    Create Directory    ${output directory}

    FOR    ${FONT NAME}    ${FONT ID}    IN    &{FONT ID}
        Set Local Variable    ${sample file}    ${output directory}/${FONT NAME}.png
        ${sample exists} =    Run Keyword And Return Status    File Should Exist    ${sample file}
        IF    not ${sample exists}
            Generate Italic Sample    ${FONT ID}    ${output directory}/${FONT NAME}.png
        END
    END

Generate Bold Italic Samples
    [Documentation]
    ...    Generate digital character set sample printouts using bold & italic font styling.
    [Tags]    character_set_sample    styling_italic    styling_bold

    Set Local Variable    ${output directory}    ${SAMPLE DIRECTORY}/bold_italic
    Create Directory    ${output directory}

    FOR    ${FONT NAME}    ${FONT ID}    IN    &{FONT ID}
        Set Local Variable    ${sample file}    ${output directory}/${FONT NAME}.png
        ${sample exists} =    Run Keyword And Return Status    File Should Exist    ${sample file}
        IF    not ${sample exists}
            Generate Bold Italic Sample    ${FONT ID}    ${output directory}/${FONT NAME}.png
        END
    END


*** Keywords ***
Generate Sample
    [Documentation]
    ...    Generate a sample with the given text using the given
    ...    default font.
    [Arguments]    ${FONT}    ${FILEPATH}

    Printer Set Option    ${FONT SLOT 1}    ${FONT}
    Printer Reset

    Run Keywords And Capture Printout
    ...    USB Print Sequence    Full Character Set
    Save Printout    ${FILEPATH}
    Clear Printout

Generate Bold Sample
    [Documentation]
    ...    Generate a sample with the given text using the given
    ...    default font.
    [Arguments]    ${FONT}    ${FILEPATH}

    Printer Set Option    ${FONT SLOT 1}    ${FONT}
    Printer Reset

    USB Send Command    Enable Bold Command
    Run Keywords And Capture Printout
    ...    USB Print Sequence    Full Character Set
    Save Printout    ${FILEPATH}
    Clear Printout

Generate Italic Sample
    [Documentation]
    ...    Generate a sample with the given text using the given
    ...    default font.
    [Arguments]    ${FONT}    ${FILEPATH}

    Printer Set Option    ${FONT SLOT 1}    ${FONT}
    Printer Reset

    USB Send Command    Enable Italic Command
    Run Keywords And Capture Printout
    ...    USB Print Sequence    Full Character Set
    Save Printout    ${FILEPATH}
    Clear Printout

Generate Bold Italic Sample
    [Documentation]
    ...    Generate a sample with the given text using the given
    ...    default font.
    [Arguments]    ${FONT}    ${FILEPATH}

    Printer Set Option    ${FONT SLOT 1}    ${FONT}
    Printer Reset

    USB Send Command    Enable Bold Command
    USB Send Command    Enable Italic Command
    Run Keywords And Capture Printout
    ...    USB Print Sequence    Full Character Set
    Save Printout    ${FILEPATH}
    Clear Printout
