#!/usr/bin/python2

from StringIO import StringIO

NEWLINE = '\n'


class SyntaxError(Exception):
    pass


class Command(object):
    def asm(self):
        return '// %s%s%s%s' % (str(self), NEWLINE, self.asm_code(), NEWLINE)


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
            raise SyntaxError('Number out of range: %d' % value)
        self.value = value

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.value)

    def __str__(self):
        return 'push %s %s' % (self.__class__.__name__.lower()[4:], self.value)


class PushConstant(Push):
    def asm_code(self):
        code = \
'''@%d
D=A
@SP
AM=A+1
M=D''' % self.value
        return code


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
    def __str__(self):
        return self.__class__.__name__.lower()

    def __repr__(self):
        return '%s()' % (self.__class__.__name__)


BINARY_OP_HEADER = '''@SP
A=M
D=M
@SP
AM=M-1'''

ADD_CODE = '''%s
M=D+M''' % BINARY_OP_HEADER
SUB_CODE = '''%s
M=M-D''' % BINARY_OP_HEADER

class Add(ArithmeticCommand):
    def asm_code(self):
        return ADD_CODE


class Sub(ArithmeticCommand):
    def asm_code(self):
        return SUB_CODE


EQUALITY_CHECK = BINARY_OP_HEADER + '''
D=D-M
@EQUAL%(unique_identifier)d
D;JEQ
D=%(equal_result)d
@WRITE%(unique_identifier)d
0;JMP
(EQUAL%(unique_identifier)d)
D=%(nonequal_result)d
(WRITE%(unique_identifier)d)
@SP
A=M
M=D'''

class Eq(ArithmeticCommand):
    def asm_code(self):
        equal_result = 1
        nonequal_result = 0
        # TODO
        unique_identifier = 0
        return EQUALITY_CHECK % locals()


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
        if '//' in line:
            line = line[:line.find('//')]
        line = line.strip().split()
        if line == []:
            pass
        elif line[0] == 'push':
            if len(line) != 3:
                raise SyntaxError('Invalid push command: %s' % line)
            _, segment, param = line
            if segment in PUSH_BY_SEGMENT:
                yield PUSH_BY_SEGMENT[segment](parse_number(param))
            else:
                raise SyntaxError('Not a recognized segment: %s' % segment)
        elif line[0] in ARITHMETIC_COMMANDS:
            if len(line) != 1:
                raise SyntaxError('Arithmetic command has no arguments: %s' % line)
            yield ARITHMETIC_COMMANDS[line[0]]()
        else:
            raise SyntaxError('Not a recognized command: %s' % line[0])


def parse_number(s):
    if not s.isdigit():
        raise SyntaxError('Not a number: %s' % s)
    return int(s)


def code(commands):
    '''
    >>> print code([PushConstant(5)])
    // push constant 5
    @5
    D=A
    @SP
    AM=A+1
    M=D
    <BLANKLINE>
    >>> print code([Add()])
    // add
    @SP
    A=M
    D=M
    @SP
    AM=M-1
    M=D+M
    <BLANKLINE>
    >>> print code([Eq()])
    // eq
    @SP
    A=M
    D=M
    @SP
    AM=M-1
    D=D-M
    @EQUAL0
    D;JEQ
    D=1
    @WRITE0
    0;JMP
    (EQUAL0)
    D=0
    (WRITE0)
    @SP
    A=M
    M=D
    <BLANKLINE>
    '''
    output = StringIO()
    for command in commands:
        output.write(command.asm())

    return output.getvalue()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
