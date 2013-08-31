class Literal(object):
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)

class NumericLiteral(Literal):
    def __init__(self, value):
        self.value = value

def parser(text):
    """
    >>> list(parser(""))
    []
    >>> list(parser("@0"))
    [NumericLiteral(0)]
    >>> list(parser(" @0"))
    [NumericLiteral(0)]
    >>> list(parser("@a"))
    [SymbolLiteral("a")]
    >>> list(parser("@a\\n@a"))
    [SymbolLiteral("a"), SymbolLiteral("a")]
    >>> list(parser("@a @b //@c"))
    [SymbolLiteral("a"), SymbolLiteral("b")]
    >>> list(parser("0;JMP"))
    [CInstruction(None, "0", "JMP")]
    >>> list(parser("0;jmp"))
    Traceback:
    ...
    SyntaxError
    """
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("@"):
            yield NumericLiteral(int(line[1:]))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
