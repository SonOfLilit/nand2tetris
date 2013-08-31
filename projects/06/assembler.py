import re

SYMBOL_RE = re.compile("[a-zA-Z_.$:][a-zA-Z0-9_.$:]*")


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
    >>> list(parser("0;jmp"))
    Traceback:
    ...
    SyntaxError
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
            raise SyntaxError("Invalid line: " + line)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
