*** Settings ***
Documentation       Verify that the default font settings contain the correct
...                 fonts.

Library             printer.Printer
Library             printout_matching


*** Keywords ***
Printout Should Match "${sample_path}" Exactly
    [Documentation]
    ...    Verify that the last printed printout matches a given sample.

    ${sample} =    Load Printout    ${sample_path}
    ${printout} =    Last Printout
    Printouts Should Match Exactly    ${sample}    ${printout}

Printout Should Not Match "${sample_path}"
    [Documentation]
    ...    Verify that the last printed printout doesn't match a given sample.

    ${sample} =    Load Printout    ${sample_path}
    ${printout} =    Last Printout
    Printouts Should Not Match    ${sample}    ${printout}
