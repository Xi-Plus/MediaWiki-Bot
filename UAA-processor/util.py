from enum import Flag, auto


class Action(Flag):
    NOTHING = 0
    REPORT = auto()
    BLOCK = auto()
    BLOCK_NOTALK = auto()
    BLOCK_NOMAIL = auto()
    BLOCK_REVDEL = auto()
