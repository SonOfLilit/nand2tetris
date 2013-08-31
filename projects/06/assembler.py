import re

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
    "A+1": "011011",
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


class SyntaxError(Exception):
    pass

class Command(object):
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)

class Literal(Command):
    pass

class NumericLiteral(Literal):
    def __init__(self, value):
        if not (0 <= value < 2 ** 16):
            raise SyntaxError("Literal out of range: %d" % value)
        self.value = value

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

class CInstruction(Command):
    def __init__(self, dest, comp, jmp):
        self.dest = dest
        self.comp = comp
        self.jmp = jmp

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.dest, self.comp, self.jmp)

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
    30
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
    """


if __name__ == '__main__':
    import doctest
    doctest.testmod()
