import os
import string

WIDTH = 16
FILENAME = "%(name)s.hdl"
NEWLINE = "\n"
FILE = """// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/01/%(name)s.hdl

CHIP %(name)s {
%(inputs_code)s
%(outputs_code)s

    PARTS:
%(body_code)s
}"""
HEADER_LINE = "    %(keyword)s %(items)s;"
BODY_LINE = "    %(gate)s(%(inputs)s, %(outputs)s);"

class Gate(object):
    def __init__(self, gate, width, wide_inputs, single_inputs, outputs):
        self.gate = gate
        self.width = width
        self.wide_inputs = wide_inputs
        self.single_inputs = single_inputs
        self.outputs = outputs

    def items(self, *names):
        """
        Utility function to generate sub-expressions and return a dict.
        """
        return dict((name, getattr(self, name)) for name in names)

    @property
    def chip(self):
        return FILE % self.items("name", "inputs_code", "outputs_code", "body_code")

    @property
    def filename(self):
        return FILENAME % self.items("name")

    @property
    def name(self):
        return "%(gate)s%(width)d" % self.items("gate", "width")

    @property
    def inputs_code(self):
        return self.header("IN", self.all_inputs(str(self.width), is_header=True))

    @property
    def outputs_code(self):
        return self.header("OUT", self.all_outputs(str(self.width)))

    def all_inputs(self, index_string, is_header=False):
        return self.indexed(self.wide_inputs, index_string) + self.indexed(self.single_inputs, None, is_header)

    def all_outputs(self, index_string):
        return self.indexed(self.outputs, index_string)

    def indexed(self, items, index_string=None, is_header=False):
        # to allow vectors that are left untouched
        if not is_header and items and "[" in items[0]:
            items = [item[:item.find("[")] for item in items]

        if index_string is None:
            index_string = ""
        else:
            index_string = "[" + index_string + "]"
        return [(name, "%s%s" % (name, index_string)) for name in items]

    def header(self, keyword, items):
        return HEADER_LINE % dict(keyword=keyword, items=", ".join(item[1] for item in items))

    @property
    def body_code(self):
        gate = self.gate
        inputs = self.connections(self.all_inputs("%(i)d"))
        outputs = self.connections(self.all_outputs("%(i)d"))
        return NEWLINE.join(BODY_LINE % dict(gate=gate,
                                             inputs=inputs % dict(i=i),
                                             outputs=outputs % dict(i=i))
                            for i in xrange(self.width))

    def connections(self, items):
        return ", ".join("%s=%s" % (n, i) for n, i in items)


class Ram(Gate):
    def __init__(self, width, bits, block_bits):
        super(Ram, self).__init__("RAM", width, ["in"], ["load", "address[%d]" % bits], ["out"])
        self.size = 2 ** bits
        self.bits = bits
        self.block_bits = block_bits
        self.block_size = 2 ** block_bits
        address_size = 2 ** (bits - block_bits)
        self.address_size = address_size
        self.letters_numbers = zip(string.letters[:address_size], range(address_size))

    def humanize_size(self, size):
        if size > 1024:
            return str(size / 1024) + "K"
        return str(size)

    @property
    def name(self):
        return "%s%s" % (self.gate, self.humanize_size(self.size))

    @property
    def block_name(self):
        return "%s%s" % (self.gate, self.humanize_size(self.block_size))

    @property
    def body_code(self):
        return NEWLINE.join([self.dmux, self.blocks, self.mux])

    @property
    def dmux(self):
        address = self.subaddress(self.block_bits, self.bits - self.block_bits)
        loads = ", ".join(["%s=load%d" % (letter, number) for letter, number in self.letters_numbers])
        address_size = self.address_size
        return "    DMux%(address_size)dWay(in=load, sel=%(address)s, %(loads)s);" % locals()

    @property
    def mux(self):
        outs = ", ".join(["%s=out%d" % (letter, number) for letter, number in self.letters_numbers])
        address = self.subaddress(self.block_bits, self.bits - self.block_bits)
        address_size = self.address_size
        return "    Mux%(address_size)sWay16(%(outs)s, sel=%(address)s, out=out);" % locals()

    @property
    def blocks(self):
        return NEWLINE.join(
            "    %(block_name)s(in=in, load=load%(i)s, address=%(address)s, out=out%(i)s);" % dict(block_name=self.block_name, i=i, address=self.subaddress(0, self.block_bits)) for i in range(self.address_size))

    def subaddress(self, first, count):
        return "address[%d..%d]" % (first, first + count - 1)

def write_chip(dirname, gate):
    open(os.path.join(dirname, gate.filename), "wb").write(gate.chip.replace(NEWLINE, "\r\n"))

GATES = {"01": [Gate("And", WIDTH, ["a", "b"], [], ["out"]),
                Gate("Or", WIDTH, ["a", "b"], [], ["out"]),
                Gate("Mux", WIDTH, ["a", "b"], ["sel"], ["out"]),
                Gate("Mux4Way", WIDTH, ["a", "b", "c", "d"], ["sel[2]"], ["out"]),
                Gate("Mux8Way", WIDTH, list(string.letters[:8]), ["sel[3]"], ["out"])],
         "02": [Gate("Buffer", WIDTH, ["in"], [], ["out"])],
         "03/a": [Gate("Bit", WIDTH, ["in"], ["load"], ["out"]),
                  Ram(WIDTH, 6, 3)],
         "03/b": [Ram(WIDTH, 9, 6), Ram(WIDTH, 12, 9), Ram(WIDTH, 14, 12)]}

if __name__ == '__main__':
    for dirname, gates in GATES.iteritems():
        for gate in gates:
            write_chip(dirname, gate)
