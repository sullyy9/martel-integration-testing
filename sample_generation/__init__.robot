*** Settings ***
Documentation       Sample generation suite

Library             printer.Printer
Library             printout
Library             OperatingSystem
Library             DateTime

Suite Setup         Create Sample Output Directory
Suite Teardown      Shutdown Printer

Force Tags          example


*** Keywords ***
Create Sample Output Directory
    ${Date Time}    Get Current Date    result_format=%Y-%m-%d@%H-%M
    ${Outdir}    Get Variable Value
    ...    $Sample_Output_Directory
    ...    ${CURDIR}/output/${Date Time}

    Set Global Variable    $Sample_Output_Directory    ${Outdir}
    Create Directory    ${Sample_Output_Directory}
