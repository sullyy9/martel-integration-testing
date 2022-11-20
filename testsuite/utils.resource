*** Settings ***
Documentation       Verify that the default font settings contain the correct
...                 fonts.

Library             printer.Printer
Library             printout.ComparisonLibrary


*** Keywords ***
Printout Should Match ${SAMPLE}
    [Documentation]
    ...    Verify that the last printed printout matches a given sample.

    Load Sample "${SAMPLE}"
    ${PRINTOUT} =    Last Printout
    Sample Should Match "${PRINTOUT}"

Save Comparison If Test Failed
    [Documentation]
    ...    If the last test failed, generate an image comparing the
    ...    sample and printout and save it.

    ${Printout} =    Last Printout
    Run Keyword If Test Failed
    ...    Save Comparison    ${Printout}    ${TEST NAME}.png
