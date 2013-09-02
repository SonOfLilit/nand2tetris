#!/usr/bin/python2

# TODO: function
# TODO: call
# TODO: return
# TODO: initialization
# TODO: compile directory

import os
import re
import sys
from StringIO import StringIO

NEWLINE = '\n'
SYMBOL_RE = re.compile('^[a-zA-Z_.$:][a-zA-Z0-9_.$:]*$')
MAX_LOCALS = 1024


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


class StackOperation(Command):
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
    max_parameter_value = 0x7FFF

    def __init__(self, segment, parameter, program='f'):
        if not 0 <= parameter <= self.max_parameter_value:
            raise SyntaxError('Parameter out of range: %d' % parameter)
        self.segment = segment
        self.parameter = parameter
        self.program = program

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.segment, self.parameter)

    def __str__(self):
        return '%s %s %s' % (self.__class__.__name__.lower(), self.segment.name, self.parameter)


class Push(StackOperation):
    def asm_code(self, i):
        return self.segment.push_asm(self)


class Pop(StackOperation):
    def asm_code(self, i):
        return self.segment.pop_asm(self)


STACK_OPERATIONS = {
    'push': Push,
    'pop': Pop,
}


class Segment(object):
    PUSH_D = '''\
@SP
AM=M+1
A=A-1
M=D'''

    read_to_d = '''\
@%(segment)s
D=M
@%(parameter)d
A=D+A
D=M'''

    SAVE_TARGET_TO_R15 = '''\
@%(segment)s
D=M
@%(parameter)d
D=D+A
@R15
M=D'''

    POP_D = '''\
@SP
AM=M-1
D=M'''

    SAVE_D_TO_TARGET_IN_R15 = '''\
@R15
A=M
M=D'''

    pop_asm_code = NEWLINE.join([SAVE_TARGET_TO_R15, POP_D, SAVE_D_TO_TARGET_IN_R15])

    def __init__(self, name, symbol=None):
        self.name = name
        self.symbol = symbol

    def push_asm(self, push):
        program = push.program
        segment = self.symbol
        parameter = push.parameter
        return (self.read_to_d % locals()) + NEWLINE + self.PUSH_D

    def pop_asm(self, pop):
        program = pop.program
        segment = self.symbol
        parameter = pop.parameter
        return self.pop_asm_code % locals()

    def __repr__(self):
        return self.name.upper()


class ConstantSegment(Segment):
    '''
    >>> Pop(CONSTANT, 1).asm(0)
    Traceback (most recent call last):
    ...
    SyntaxError: Cannot pop constant
    '''
    read_to_d = '''\
@%(parameter)d
D=A'''

    def pop_asm(self, pop):
        raise SyntaxError('Cannot pop constant')


class StaticSegment(Segment):
    read_to_d = '''\
@%(program)s.%(parameter)d
D=M'''

    pop_asm_code = NEWLINE.join([Segment.POP_D,
'''@%(program)s.%(parameter)d
M=D'''])


class FixedSegment(Segment):
    '''
    >>> type(code([Push(POINTER, 1)])) is str
    True
    >>> code([Push(POINTER, 2)])
    Traceback (most recent call last):
    ...
    SyntaxError: Out of "pointer" segment's bounds: 2
    '''

    read_to_d = '''\
@%(address)d
D=M'''

    pop_asm_code = NEWLINE.join([Segment.POP_D,
'''@%(address)d
M=D'''])

    def __init__(self, name, base, size):
        super(FixedSegment, self).__init__(name)
        self.base = base
        self.size = size

    def check_bounds(self, operation):
        if operation.parameter >= self.size:
            raise SyntaxError('Out of "%s" segment\'s bounds: %d' % (self.name, operation.parameter))

    def push_asm(self, push):
        self.check_bounds(push)
        address = self.base + push.parameter
        return (self.read_to_d % locals()) + NEWLINE + self.PUSH_D

    def pop_asm(self, pop):
        self.check_bounds(pop)
        address = self.base + pop.parameter
        return self.pop_asm_code % locals()


CONSTANT = ConstantSegment('constant')
STATIC = StaticSegment('static')
LOCAL = Segment('local', 'LCL')
ARGUMENT = Segment('argument', 'ARG')
THIS = Segment('this', 'THIS')
THAT = Segment('that', 'THAT')
POINTER = FixedSegment('pointer', base=3, size=2)
TEMP = FixedSegment('temp', base=5, size=8)
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
    'not': Not,
}


class BranchingCommand(Command):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "%s %s" % (self.command, self.name)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.name)


class Label(BranchingCommand):
    # there is no need to take care that no two labels of the same
    # name exist, since the assembler does that for us

    command = 'label'

    def asm_code(self, i):
        return '(L%s)' % self.name


class Goto(BranchingCommand):
    command = 'goto'

    def asm_code(self, i):
        return '''\
@L%s
0;JMP''' % self.name


class IfGoto(BranchingCommand):
    command = 'if-goto'

    def asm_code(self, i):
        return Segment.POP_D + '''
@L%s
D;JNE''' % self.name


BRANCHING_COMMANDS = {
    'label': Label,
    'goto': Goto,
    'if-goto': IfGoto,
}


class Function(Command):
    SAVED_VARS = ['LCL', 'ARG', 'THIS', 'THAT']
    SAVE_VAR = '''\
@%s
D=M
'''
    SAVE_VARS = NEWLINE.join([SAVE_VAR % var + Segment.PUSH_D for var in SAVED_VARS])

    # we need to "push constant 0" a variable number of times fast
    # a. load SP into A
    # b. zero at A, increase A  * N
    # (now A holds what should be the new SP)
    # c. write A into SP
    ROOM_FOR_LOCALS_HEADER = '''\
@SP
A=M
'''
    ZERO_LOCAL = '''\
M=0
A=A+1
'''

    ROOM_FOR_LOCALS_FOOTER = '''\
D=A
@SP
M=D'''
    def __init__(self, name, num_locals):
        self.name = name
        self.num_locals = num_locals

    def asm_code(self, i):
        return self.SAVE_VARS + NEWLINE + \
            self.ROOM_FOR_LOCALS_HEADER + \
            self.ZERO_LOCAL * self.num_locals + \
            self.ROOM_FOR_LOCALS_FOOTER

    def __str__(self):
        return 'function %s %d' % (self.name, self.num_locals)

    def __repr__(self):
        return 'Function(%r, %d)' % (self.name, self.num_locals)


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
    SyntaxError: Stack command should have 2 parameters: ['push', 'me']
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
    SyntaxError: Arithmetic command should have 0 parameters: ['add', '5']
    >>> list(parser('label hello'))
    [Label('hello')]
    >>> list(parser('label'))
    Traceback (most recent call last):
    ...
    SyntaxError: Branching command should have 1 parameters: ['label']
    >>> list(parser('label 5'))
    Traceback (most recent call last):
    ...
    SyntaxError: Invalid symbol name: 5
    >>> list(parser('goto hello'))
    [Goto('hello')]
    >>> list(parser('if-goto hello'))
    [IfGoto('hello')]
    >>> list(parser('function mult 1'))
    [Function('mult', 1)]
    >>> list(parser('function mult 1 2'))
    Traceback (most recent call last):
    ...
    SyntaxError: Function command should have 2 parameters: ['function', 'mult', '1', '2']
    >>> list(parser('function 5 2'))
    Traceback (most recent call last):
    ...
    SyntaxError: Invalid symbol name: 5
    >>> list(parser('function prod 1025'))
    Traceback (most recent call last):
    ...
    SyntaxError: Function cannot have 1025 locals
    '''
    for line in text.splitlines():
        if '//' in line:
            line = line[:line.find('//')]
        line = line.strip().split()
        if line == []:
            pass
        elif line[0] in STACK_OPERATIONS:
            check_parameters(line, 2, 'Stack')
            operation, segment, param = line
            if segment in SEGMENTS:
                yield STACK_OPERATIONS[operation](SEGMENTS[segment], parse_number(param))
            else:
                raise SyntaxError('Not a recognized segment: %s' % segment)
        elif line[0] in ARITHMETIC_COMMANDS:
            check_parameters(line, 0, 'Arithmetic')
            yield ARITHMETIC_COMMANDS[line[0]]()
        elif line[0] in BRANCHING_COMMANDS:
            check_parameters(line, 1, 'Branching')
            operation, name = line
            check_symbol_name(name)
            yield BRANCHING_COMMANDS[operation](name)
        elif line[0] == 'function':
            check_parameters(line, 2, 'Function')
            _, name, num_locals = line
            check_symbol_name(name)
            num_locals = parse_number(num_locals)
            if not 0 <= num_locals <= MAX_LOCALS:
                raise SyntaxError('Function cannot have %d locals' % num_locals)
            yield Function(name, num_locals)
        else:
            raise SyntaxError('Not a recognized command: %s' % line[0])

def check_parameters(line, expected_number, name):
    if len(line) != expected_number + 1:
        raise SyntaxError('%s command should have %d parameters: %s' % (name, expected_number, line))

def check_symbol_name(name):
   if not SYMBOL_RE.match(name):
       raise SyntaxError('Invalid symbol name: %s' % name)

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
    >>> print code([Push(CONSTANT, 5), Push(CONSTANT, 4)])
    // push constant 5
    @5
    D=A
    @SP
    AM=M+1
    A=A-1
    M=D
    // push constant 4
    @4
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
    >>> print code([Push(LOCAL, 5)])
    // push local 5
    @LCL
    D=M
    @5
    A=D+A
    D=M
    @SP
    AM=M+1
    A=A-1
    M=D
    <BLANKLINE>
    >>> print code([Pop(LOCAL, 5)])
    // pop local 5
    @LCL
    D=M
    @5
    D=D+A
    @R15
    M=D
    @SP
    AM=M-1
    D=M
    @R15
    A=M
    M=D
    <BLANKLINE>
    >>> print code([Push(TEMP, 5)])
    // push temp 5
    @10
    D=M
    @SP
    AM=M+1
    A=A-1
    M=D
    <BLANKLINE>
    >>> print code([Pop(POINTER, 1)])
    // pop pointer 1
    @SP
    AM=M-1
    D=M
    @4
    M=D
    <BLANKLINE>
    >>> print code([Label('hello')])
    // label hello
    (Lhello)
    <BLANKLINE>
    >>> print code([Goto('hello')])
    // goto hello
    @Lhello
    0;JMP
    <BLANKLINE>
    >>> print code([IfGoto('hello')])
    // if-goto hello
    @SP
    AM=M-1
    D=M
    @Lhello
    D;JNE
    <BLANKLINE>
    >>> print code([Function('mult', 3)])
    // function mult 3
    @LCL
    D=M
    @SP
    AM=M+1
    A=A-1
    M=D
    @ARG
    D=M
    @SP
    AM=M+1
    A=A-1
    M=D
    @THIS
    D=M
    @SP
    AM=M+1
    A=A-1
    M=D
    @THAT
    D=M
    @SP
    AM=M+1
    A=A-1
    M=D
    @SP
    A=M
    M=0
    A=A+1
    M=0
    A=A+1
    M=0
    A=A+1
    D=A
    @SP
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
    if not path.endswith('.vm'):
        print_usage()
        return -1
    if not os.path.exists(path):
        print 'file not found'
        return 1

    with open(path, 'rb') as vmfile:
        hack = code(parser(vmfile.read()))
    with open(path[:-3] + '.asm', 'wb') as asmfile:
        asmfile.write(hack)
    return 0

def print_usage():
        print 'usage: vm.py path/to/file.vm'

if __name__ == '__main__':
    import doctest
    doctest.testmod()

    sys.exit(main(sys.argv[1:]))