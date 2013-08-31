def parser(text):
    """
    >>> list(parser(""))
    []
    >>> list(parser("@0"))
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
    return []

if __name__ == '__main__':
    import doctest
    doctest.testmod()
