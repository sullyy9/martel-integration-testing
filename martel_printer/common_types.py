from enum import IntEnum, unique

@unique
class ControlCode(IntEnum):
    NULL = 0x00
    HT = 0x09
    LF = 0x0A
    FF = 0x0C
    CR = 0x0D
    SO = 0x0E # Double width on.
    SI = 0x0F # Double width off.
    CAN = 0x18 # Clear print buffer. 
    ESC = 0x1B