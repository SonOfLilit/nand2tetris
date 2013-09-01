#!/usr/bin/python2
"""
An assembler for nand2tetris machine language.

Author: Aur Saraf

    >>> print code(parser('''// Some comments
    ... @sum
    ... M=0
    ... 
    ... @R0
    ... D=M
    ... @counter
    ... M=D
    ... 
    ... (LOOP)
    ... @counter
    ... D=M
    ... @END // More comments
    ... D;JLE
    ... // Sometimes on a line of their own
    ... @sum
    ... D=M
    ... @R1
    ... D=D+M
    ... @sum
    ... M=D
    ... 
    ... @counter
    ... M=M-1
    ... 
    ... @LOOP
    ... 0;JMP
    ... 
    ... (END)
    ... @sum
    ... D=M
    ... @R2
    ... M=D
    ... 
    ... (HALT)
    ... @HALT
    ... 0;JMP'''))
    0000000000010000
    1110101010001000
    0000000000000000
    1111110000010000
    0000000000010001
    1110001100001000
    0000000000010001
    1111110000010000
    0000000000010100
    1110001100000110
    0000000000010000
    1111110000010000
    0000000000000001
    1111000010010000
    0000000000010000
    1110001100001000
    0000000000010001
    1111110010001000
    0000000000000110
    1110101010000111
    0000000000010000
    1111110000010000
    0000000000000010
    1110001100001000
    0000000000011000
    1110101010000111
"""

import os
import re
import sys

NEWLINE = "\n"

COMPS = {
    "0":   "101010",
    "1":   "111111",
    "-1":  "111010",
    "D":   "001100",
    "A":   "110000",
    "!D":  "001101",
    "!A":  "110001",
    "-D":  "001111",
    "-A":  "110011",
    "D+1": "011111",
    "A+1": "110111",
    "D-1": "001110",
    "A-1": "110010",
    "D+A": "000010",
    "D-A": "010011",
    "A-D": "000111",
    "D&A": "000000",
    "D|A": "010101"
}
for key, value in COMPS.items():
    COMPS[key] = "0" + value
    if "A" in key:
        COMPS[key.replace("A", "M")] = "1" + value

DESTS = {
    None: "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}
JUMPS = {
    None:  "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}
comps = "|".join(re.escape(comp) for comp in COMPS)
jumps = "|".join(filter(lambda x: x, JUMPS))
SYMBOL_RE = re.compile("^[a-zA-Z_.$:][a-zA-Z0-9_.$:]*$")
C_INSTRUCTION_RE = re.compile("^(?:(A?M?D?)=|)(%s)(?:|;(%s))$" % (comps, jumps))
del comps
del jumps

BUILTIN_SYMBOLS = {"SCREEN": 0x4000, "KBD": 0x6000}
for i, name in enumerate("SP LCL ARG THIS THAT".split()):
    BUILTIN_SYMBOLS[name] = i
for i in xrange(16):
    BUILTIN_SYMBOLS["R" + str(i)] = i
del i
del name

class SyntaxError(Exception):
    pass

class Command(object):
    def is_instruction(self):
        return True

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)

class Literal(Command):
    pass

class NumericLiteral(Literal):
    def __init__(self, value):
        if not (0 <= value < 2 ** 16):
            raise SyntaxError("Literal out of range: %d" % value)
        self.value = value

    def code(self):
        return "{0:016b}".format(self.value)

class SymbolLiteral(Literal):
    def __init__(self, value):
        if not SYMBOL_RE.match(value):
            raise SyntaxError("Invalid symbol: %s" % value)
        self.value = value

class Label(Command):
    def __init__(self, value):
        if not SYMBOL_RE.match(value):
            raise SyntaxError("Invalid symbol: %s" % value)
        self.value = value

    def is_instruction(self):
        return False

class CInstruction(Command):
    def __init__(self, dest, comp, jump):
        self.dest = dest
        self.comp = comp
        self.jump = jump

    def code(self):
        return "111" + COMPS[self.comp] + DESTS[self.dest] + JUMPS[self.jump]

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.dest, self.comp, self.jump)

    @classmethod
    def parse(cls, line):
        match = C_INSTRUCTION_RE.match(line)
        if not match:
            raise SyntaxError("Invalid line: " + line)
        dest, comp, jmp = match.groups()
        return cls(dest, comp, jmp)


def parser(text):
    """
    >>> list(parser(""))
    []
    >>> list(parser("@0"))
    [NumericLiteral(0)]
    >>> list(parser("@65535"))
    [NumericLiteral(65535)]
    >>> list(parser("@65536"))
    Traceback (most recent call last):
    ...
    SyntaxError: Literal out of range: 65536
    >>> list(parser(" @0 "))
    [NumericLiteral(0)]
    >>> list(parser("@a"))
    [SymbolLiteral('a')]
    >>> list(parser("@-"))
    Traceback (most recent call last):
    ...
    SyntaxError: Invalid symbol: -
    >>> list(parser("@a\\n@a"))
    [SymbolLiteral('a'), SymbolLiteral('a')]
    >>> list(parser("@a\\n@b //@c"))
    [SymbolLiteral('a'), SymbolLiteral('b')]
    >>> list(parser("(NAM.E)"))
    [Label('NAM.E')]
    >>> list(parser("0;JMP"))
    [CInstruction(None, '0', 'JMP')]
    >>> list(parser("A=A+1"))
    [CInstruction('A', 'A+1', None)]
    >>> list(parser("D=D+M"))
    [CInstruction('D', 'D+M', None)]
    >>> list(parser("0;JNE"))
    [CInstruction(None, '0', 'JNE')]
    >>> list(parser("0;jmp"))
    Traceback (most recent call last):
    ...
    SyntaxError: Invalid line: 0;jmp
    >>> len(list(parser('''@sum
    ... M=0
    ... 
    ... @R0
    ... D=M
    ... @counter
    ... M=D
    ... 
    ... (LOOP)
    ... @counter
    ... D=M
    ... @END
    ... D;JLE
    ... 
    ... @sum
    ... D=M
    ... @R1
    ... D=D+M
    ... @sum
    ... M=D
    ... 
    ... @counter
    ... M=M-1
    ... 
    ... @LOOP
    ... 0;JMP
    ... 
    ... (END)
    ... @sum
    ... D=M
    ... @R2
    ... M=D
    ... 
    ... (HALT)
    ... @HALT
    ... 0;JMP''')))
    29
    """
    for line in text.splitlines():
        if "//" in line:
            line = line[:line.find("//")]
        line = line.strip()
        if line == "":
            pass
        elif line.startswith("@"):
            literal = line[1:]
            if literal[0].isdigit():
                yield NumericLiteral(int(literal))
            else:
                yield SymbolLiteral(literal)
        elif line.startswith("(") and line.endswith(")"):
            yield Label(line[1:-1])
        else:
            yield CInstruction.parse(line)


def code(commands):
    """
    >>> code([])
    ''
    >>> code([NumericLiteral(0x3333)])
    '0011001100110011'
    >>> code([NumericLiteral(0x3333), NumericLiteral(0x5555)])
    '0011001100110011\\n0101010101010101'
    >>> code([CInstruction(None, '0', 'JMP')])
    '1110101010000111'
    >>> code([CInstruction("AM", "M+1", None)])
    '1111110111101000'
    >>> code([Label('HI')])
    ''
    >>> code([SymbolLiteral("i")])
    '0000000000010000'
    >>> code([SymbolLiteral("i"), SymbolLiteral("J"), SymbolLiteral("i")])
    '0000000000010000\\n0000000000010001\\n0000000000010000'
    >>> code([SymbolLiteral("R0")])
    '0000000000000000'
    >>> code([SymbolLiteral("R10")])
    '0000000000001010'
    >>> code([SymbolLiteral("R15")])
    '0000000000001111'
    >>> code([Label("i"), SymbolLiteral("i")])
    '0000000000000000'
    >>> code([Label("i"), Label("i")])
    Traceback (most recent call last):
    ...
    SyntaxError: Label redefined: i
    >>> code([SymbolLiteral("i"), Label("i")])
    '0000000000000001'
    """
    commands = list(commands)

    symbols = dict(BUILTIN_SYMBOLS)
    counter = 0
    for i, command in enumerate(commands):
        if command.is_instruction():
            counter += 1
        if isinstance(command, Label):
            if command.value in symbols:
                raise SyntaxError("Label redefined: %s" % command.value)
            symbols[command.value] = counter

    first_free_variable = 16
    for i, command in enumerate(commands):
        if isinstance(command, SymbolLiteral):
            if command.value not in symbols:
                symbols[command.value] = first_free_variable
                first_free_variable += 1
            commands[i] = NumericLiteral(symbols[command.value])

    return NEWLINE.join(command.code() for command in commands if command.is_instruction())


def main(args):
    if len(args) != 1:
        print_usage()
        return -1
    path, = args
    if not path.endswith(".asm"):
        print_usage()
        return -1
    if not os.path.exists(path):
        print "file not found"
        return 1

    with open(path, "rb") as asmfile:
        hack = code(parser(asmfile.read()))
    with open(path[:-4] + ".hack", "wb") as hackfile:
        hackfile.write(hack)
    return 0

def print_usage():
        print "usage: assembler.py path/to/file.asm"

if __name__ == '__main__':
    import doctest
    doctest.testmod()

    sys.exit(main(sys.argv[1:]))