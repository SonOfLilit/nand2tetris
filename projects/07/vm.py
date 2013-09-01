#!/usr/bin/python2


class SyntaxError(Exception):
    pass


class Command(object):
    pass


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

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)


class PushConstant(Push):
    pass


class PushStatic(Push):
    pass


class PushLocal(Push):
    pass


class PushArgument(Push):
    pass


class PushThis(Push):
    pass


class PushThat(Push):
    pass


class PushPointer(Push):
    pass


class PushTemp(Push):
    pass


PUSH_BY_SEGMENT = {
    'constant': PushConstant,
    'static': PushStatic,
    'local': PushLocal,
    'argument': PushArgument,
    'this': PushThis,
    'that': PushThat,
    'pointer': PushPointer,
    'temp': PushTemp,
}


class ArithmeticCommand(Command):
    def __repr__(self):
        return "%s()" % (self.__class__.__name__)


class Add(ArithmeticCommand):
    pass


class Sub(ArithmeticCommand):
    pass


class Eq(ArithmeticCommand):
    pass


class Neq(ArithmeticCommand):
    pass


class Gt(ArithmeticCommand):
    pass


class Lt(ArithmeticCommand):
    pass


class And(ArithmeticCommand):
    pass


class Or(ArithmeticCommand):
    pass


class Not(ArithmeticCommand):
    pass


ARITHMETIC_COMMANDS = {
    'add': Add,
    'sub': Sub,
    'eq': Eq,
    'neq': Neq,
    'gt': Gt,
    'lt': Lt,
    'and': And,
    'or': Or,
    'not': Not
}


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
    >>> list(parser('mwaaaah'))
    Traceback (most recent call last):
    ...
    SyntaxError: Not a recognized command: mwaaaah
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
    >>> list(parser('push local 0\\npush argument 0\\npush this 0\\npush that 1\\npush pointer 2\\npush temp 3\\n'))
    [PushLocal(0), PushArgument(0), PushThis(0), PushThat(1), PushPointer(2), PushTemp(3)]
    >>> list(parser('add'))
    [Add()]
    >>> list(parser('sub\\neq\\nneq\\ngt\\nlt\\nand\\nor\\nnot'))
    [Sub(), Eq(), Neq(), Gt(), Lt(), And(), Or(), Not()]
    >>> list(parser('add 5'))
    Traceback (most recent call last):
    ...
    SyntaxError: Arithmetic command has no arguments: ['add', '5']
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
            if segment in PUSH_BY_SEGMENT:
                yield PUSH_BY_SEGMENT[segment](parse_number(param))
            else:
                raise SyntaxError("Not a recognized segment: %s" % segment)
        elif line[0] in ARITHMETIC_COMMANDS:
            if len(line) != 1:
                raise SyntaxError("Arithmetic command has no arguments: %s" % line)
            yield ARITHMETIC_COMMANDS[line[0]]()
        else:
            raise SyntaxError("Not a recognized command: %s" % line[0])


def parse_number(s):
    if not s.isdigit():
        raise SyntaxError("Not a number: %s" % s)
    return int(s)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
