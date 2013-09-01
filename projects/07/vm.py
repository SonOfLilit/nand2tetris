#!/usr/bin/python2

class SyntaxError(Exception):
    pass


class Command(object):
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)


class Push(Command):
    '''
    >>> Push(0)
    Push(0)
    >>> Push(0x7FFF).value == 0x7FFF
    True
    >>> Push(0x8000)
    Traceback (most recent call last):
    ...
    SyntaxError: Number out of range: 32768
    '''
    def __init__(self, value):
        if not 0 <= value < 2 ** 15:
            raise SyntaxError("Number out of range: %d" % value)
        self.value = value


class PushConstant(Push):
    pass


class PushStatic(Push):
    pass


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
    >>> list(parser('push constant struggle'))
    Traceback (most recent call last):
    ...
    SyntaxError: Not a number: struggle
    >>> list(parser('push me away'))
    Traceback (most recent call last):
    ...
    SyntaxError: Not a recognized segment: me
    >>> list(parser('push me'))
    Traceback (most recent call last):
    ...
    SyntaxError: Invalid push command: ['push', 'me']
    >>> list(parser('push static 5'))
    [PushStatic(5)]
    >>> list(parser('push static dynamic'))
    Traceback (most recent call last):
    ...
    SyntaxError: Not a number: dynamic
    '''
    for line in text.splitlines():
        if "//" in line:
            line = line[:line.find("//")]
        line = line.strip().split()
        if line == []:
            pass
        elif line[0] == "push":
            if len(line) != 3:
                raise SyntaxError("Invalid push command: %s" % line)
            _, segment, param = line
            if segment == "constant":
                yield PushConstant(parse_number(param))
            elif segment == "static":
                yield PushStatic(parse_number(param))
            else:
                raise SyntaxError("Not a recognized segment: %s" % segment)


def parse_number(s):
    if not s.isdigit():
        raise SyntaxError("Not a number: %s" % s)
    return int(s)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
