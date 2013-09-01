#!/usr/bin/python2

class SyntaxError(Exception):
    pass


class Command(object):
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)


class Push(Command):
    pass


class PushConstant(Push):
    '''
    >>> PushConstant(0)
    PushConstant(0)
    >>> PushConstant(0x7FFF).value == 0x7FFF
    True
    >>> PushConstant(0x8000)
    Traceback (most recent call last):
    ...
    SyntaxError: Constant out of range: 32768
    '''
    def __init__(self, value):
        if not 0 <= value < 2 ** 15:
            raise SyntaxError("Constant out of range: %d" % value)
        self.value = value


def parser(text):
    '''
    >>> list(parser(''))
    []
    >>> list(parser('push constant 0'))
    [PushConstant(0)]
    >>> list(parser('push constant 2\\npush constant 1'))
    [PushConstant(2), PushConstant(1)]
    >>> list(parser('// haha\\n  // haha'))
    []
    >>> list(parser('push constant 0 // haha'))
    [PushConstant(0)]
    '''
    for line in text.splitlines():
        if "//" in line:
            line = line[:line.find("//")]
        line = line.strip().split()
        if line == []:
            pass
        elif len(line) == 3 and line[:2] == ["push", "constant"]:
            yield PushConstant(int(line[2]))
    return


if __name__ == '__main__':
    import doctest
    doctest.testmod()
