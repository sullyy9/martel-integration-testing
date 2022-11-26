*** Settings ***
Documentation       Variables containing printout samples and the text used to
...                 generate them


*** Variables ***
${SAMPLE TEXT}                  Martel Instruments is a leading manufacturer and global
...                             supplier of bespoke and innovative commercial printing
...                             solutions.\n

${SAMPLE TEXT SHORT}            Martel Instruments is a leading manufacturer
...                             and global... \n

${ARIAL16 SAMPLE}               ${SAMPLE DIR}/arial16_sample_text.png
${ARIAL12 SAMPLE}               ${SAMPLE DIR}/arial12_sample_text.png
${ARIAL9 SAMPLE}                ${SAMPLE DIR}/arial9_sample_text.png
${ARIAL8 SAMPLE}                ${SAMPLE DIR}/arial8_sample_text.png
${UNICODE16 SAMPLE}             ${SAMPLE DIR}/unicode16_sample_text.png
${UNICODE12 SAMPLE}             ${SAMPLE DIR}/unicode12_sample_text.png
${UNICODE8 SAMPLE}              ${SAMPLE DIR}/unicode8_sample_text.png

${ARIAL16 SAMPLE SHORT}         ${SAMPLE DIR}/arial16_sample_text_short.png
${ARIAL12 SAMPLE SHORT}         ${SAMPLE DIR}/arial12_sample_text_short.png
${ARIAL9 SAMPLE SHORT}          ${SAMPLE DIR}/arial9_sample_text_short.png
${ARIAL8 SAMPLE SHORT}          ${SAMPLE DIR}/arial8_sample_text_short.png
${UNICODE16 SAMPLE SHORT}       ${SAMPLE DIR}/unicode16_sample_text_short.png
${UNICODE12 SAMPLE SHORT}       ${SAMPLE DIR}/unicode12_sample_text_short.png
${UNICODE8 SAMPLE SHORT}        ${SAMPLE DIR}/unicode8_sample_text_short.png
