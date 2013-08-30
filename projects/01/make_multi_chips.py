SIZE = 16
GATES = ["And", "Or"]

FILENAME_TEMPLATE = "%(gate)s%(size)d.hdl"

LINE_TEMPLATE = "    %(gate)s(a=a[%(i)d], b=b[%(i)d], out=out[%(i)d]);"
TEMPLATE = """// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/01/%(gate)s%(size)s.hdl

/**
 * %(size)d-bit-wise %(gate)s gate: for i = 0..SIZE: out[i] = a[i] %(gate)s b[i]
 */
CHIP %(gate)s%(size)d {
    IN a[%(size)d], b[%(size)d];
    OUT out[%(size)d];

    PARTS:
%(code)s
}
"""

def write_chip(gate):
    size = SIZE
    open(FILENAME_TEMPLATE % locals(), "wb").write(generate_chip(gate, size))

def generate_chip(gate, size):
    code = "\n".join(LINE_TEMPLATE % dict(gate=gate, i=i) for i in xrange(size))
    return TEMPLATE % locals()

if __name__ == '__main__':
    for gate in GATES:
        write_chip(gate)
