#!/usr/bin/python2

import os
import sys
from StringIO import StringIO

NEWLINE = '\n'


class SyntaxError(Exception):
    pass


class Command(object):
    def asm(self, i):
        '''
        Returns hack assembly code for this command.

        i is a unique number, useful to distinguish labels for
        different commands.
        '''
        return '// %s%s%s%s' % (str(self), NEWLINE, self.asm_code(i), NEWLINE)


class Push(Command):
    '''
    >>> Push(CONSTANT, 0)
    Push(CONSTANT, 0)
    >>> Push(CONSTANT, 0x7FFF).parameter == 0x7FFF
    True
    >>> Push(CONSTANT, 0x8000)
    Traceback (most recent call last):
    ...
    SyntaxError: Parameter out of range: 32768
    '''
    MAX_PARAMETER_VALUE = 0x7FFF

    def __init__(self, segment, parameter):
        if not 0 <= parameter <= self.MAX_PARAMETER_VALUE:
            raise SyntaxError('Parameter out of range: %d' % parameter)
        self.segment = segment
        self.parameter = parameter

    def asm_code(self, i):
        return self.segment.push_code(self)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.segment, self.parameter)

    def __str__(self):
        return 'push %s %s' % (self.segment.name, self.parameter)


class Segment(object):
    def __init__(self, name):
        self.name = name

    def push_code(self, push):
        return PUSH_CONSTANT % push.parameter

    def __repr__(self):
        return self.name.upper()


PUSH_CONSTANT = '''@%d
D=A
@SP
AM=M+1
A=A-1
M=D'''

PUSH_LOCAL = '''@LOCAL
A=M
D=M
@SP
AM=M+1
A=A-1
M=D'''


CONSTANT = Segment('constant')
STATIC = Segment('static')
LOCAL = Segment('local')
ARGUMENT = Segment('argument')
THIS = Segment('this')
THAT = Segment('that')
POINTER = Segment('pointer')
TEMP = Segment('temp')
SEGMENTS = {
    'constant': CONSTANT,
    'static': STATIC,
    'local': LOCAL,
    'argument': ARGUMENT,
    'this': THIS,
    'that': THAT,
    'pointer': POINTER,
    'temp': TEMP,
}


class ArithmeticCommand(Command):
    def __str__(self):
        return self.__class__.__name__.lower()

    def __repr__(self):
        return '%s()' % (self.__class__.__name__)


BINARY_OP_HEADER = '''@SP
AM=M-1
D=M
A=A-1'''

ADD_CODE = '''%s
M=D+M''' % BINARY_OP_HEADER
SUB_CODE = '''%s
M=M-D''' % BINARY_OP_HEADER
NEG_CODE = '''@SP
A=M-1
M=-M
'''
class Add(ArithmeticCommand):
    def asm_code(self, i):
        return ADD_CODE


class Sub(ArithmeticCommand):
    def asm_code(self, i):
        return SUB_CODE


class Neg(ArithmeticCommand):
    def asm_code(self, i):
        return NEG_CODE


EQUALITY_CHECK = BINARY_OP_HEADER + '''
D=D-M
@EQUAL%(unique_identifier)d
D;%(jump)s
D=0
@WRITE%(unique_identifier)d
0;JMP
(EQUAL%(unique_identifier)d)
D=-1
(WRITE%(unique_identifier)d)
@SP
A=M-1
M=D'''

class Equality(ArithmeticCommand):
    def asm_code(self, i):
        jump = self.JUMP
        unique_identifier = i
        return EQUALITY_CHECK % locals()

class Eq(Equality):
    JUMP = 'JEQ'

class Gt(Equality):
    # x < y <==> y > x
    JUMP = 'JLT'

class Lt(Equality):
    # x < y <==> y > x
    JUMP = 'JGT'


# 1111 & 1111 = 1111
# 1111 & 0000 = 0000
# 0000 & 1111 = 0000
# 0000 & 0000 = 0000
AND_CODE = '''%s
M=M&D''' % BINARY_OP_HEADER
# 1111 | 1111 = 1111
# 1111 | 0000 = 1111
# 0000 | 1111 = 1111
# 0000 | 0000 = 0000
OR_CODE = '''%s
M=M|D''' % BINARY_OP_HEADER
NOT_CODE = '''@SP
A=M-1
M=!M
'''

class And(ArithmeticCommand):
    def asm_code(self, i):
        return AND_CODE


class Or(ArithmeticCommand):
    def asm_code(self, i):
        return OR_CODE


class Not(ArithmeticCommand):
    def asm_code(self, i):
        return NOT_CODE


ARITHMETIC_COMMANDS = {
    'add': Add,
    'sub': Sub,
    'neg': Neg,
    'eq': Eq,
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
    [Push(CONSTANT, 0)]
    >>> list(parser('push constant 2\\npush constant 1'))
    [Push(CONSTANT, 2), Push(CONSTANT, 1)]
    >>> list(parser('// haha\\n  // haha'))
    []
    >>> list(parser('push constant 0 // haha'))
    [Push(CONSTANT, 0)]
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
    [Push(STATIC, 5)]
    >>> list(parser('push static dynamic'))
    Traceback (most recent call last):
    ...
    SyntaxError: Not a number: dynamic
    >>> list(parser('push local 0\\npush argument 0\\npush this 0\\npush that 1\\npush pointer 2\\npush temp 3\\n'))
    [Push(LOCAL, 0), Push(ARGUMENT, 0), Push(THIS, 0), Push(THAT, 1), Push(POINTER, 2), Push(TEMP, 3)]
    >>> list(parser('add'))
    [Add()]
    >>> list(parser('sub\\nneg\\neq\\ngt\\nlt\\nand\\nor\\nnot'))
    [Sub(), Neg(), Eq(), Gt(), Lt(), And(), Or(), Not()]
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
            if segment in SEGMENTS:
                yield Push(SEGMENTS[segment], parse_number(param))
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
    >>> print code([Push(CONSTANT, 5)])
    // push constant 5
    @5
    D=A
    @SP
    AM=M+1
    A=A-1
    M=D
    <BLANKLINE>
    >>> print code([Add()])
    // add
    @SP
    AM=M-1
    D=M
    A=A-1
    M=D+M
    <BLANKLINE>
    >>> print code([Eq()])
    // eq
    @SP
    AM=M-1
    D=M
    A=A-1
    D=D-M
    @EQUAL0
    D;JEQ
    D=0
    @WRITE0
    0;JMP
    (EQUAL0)
    D=-1
    (WRITE0)
    @SP
    A=M-1
    M=D
    <BLANKLINE>
    '''
    output = StringIO()
    for i, command in enumerate(commands):
        output.write(command.asm(i))

    return output.getvalue()


def main(args):
    if len(args) != 1:
        print_usage()
        return -1
    path, = args
    if not path.endswith(".vm"):
        print usage
        return -1
    if not os.path.exists(path):
        print "file not found"
        return 1

    with open(path, "rb") as vmfile:
        hack = code(parser(vmfile.read()))
    with open(path[:-3] + ".asm", "wb") as asmfile:
        asmfile.write(hack)
    return 0

def print_usage():
        print "usage: vm.py path/to/file.vm"

if __name__ == '__main__':
    import doctest
    doctest.testmod()

    sys.exit(main(sys.argv[1:]))