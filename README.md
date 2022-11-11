Numbering on topside aligns with numbering on schematic.

1-6     VBATT
7       SPI DATA
8       SPICLK
9-14    GND
15-17   DST
18      VCC
19      GND
20-21   VTHERM
22-24   DST
25-30   GND
31      LATCH
32-37   VBATT
38      NC
39      PaperSensor
40      VPS
41      GND
42      PlatenSensor
43      NC
44-45   GND
46      NC
47      MOTORA_L
48      MOTORB_H
49      MOTORA_H
50      MOTORB_L

----

Internal Connections:
Connect  PaperSensor(39) to GND(41)
Connect  PlatenSensor(42) to GND(44)
Connect  VTHERM(20) to GND(19) through a 33K resistor

Analyzer Connections:
0 => SPICLK(8)
1 => SPIDATA(7)
2 => LATCH(31)
3 => DST(15)

4 => MOTORA_L(47)
5 => MOTORB_L(50)

6 => STEPPER_EN

----

Printing Process:
SPI Data

\/ 

Shift Reg

\/ <- LAT low

Latch Reg

\/ <- DST low

Print

----

Look into Analog Discovery 2

---

Poetry setup:
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
poetry config virtualenvs.in-project true

---

!! On 433's the LAT pulse width is ~25ns.
!! This is on the edge of what the analyser can detect and is below the 100ns
!! specified in the mech datasheet.