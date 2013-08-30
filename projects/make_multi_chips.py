import os
import string

SIZE = 16
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
}
"""
HEADER_LINE = "    %(keyword)s %(items)s;"
BODY_LINE = "    %(gate)s(%(inputs)s, %(outputs)s);"

class Gate(object):
    def __init__(self, gate, size, wide_inputs, single_inputs, outputs):
        self.gate = gate
        self.size = size
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
        return "%(gate)s%(size)d" % self.items("gate", "size")

    @property
    def inputs_code(self):
        return self.header("IN", self.all_inputs(str(self.size), is_header=True))

    @property
    def outputs_code(self):
        return self.header("OUT", self.all_outputs(str(self.size)))

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
                            for i in xrange(self.size))

    def connections(self, items):
        return ", ".join("%s=%s" % (n, i) for n, i in items)


def write_chip(dirname, gate):
    open(os.path.join(dirname, gate.filename), "wb").write(gate.chip)

GATES = {"01": [Gate("And", SIZE, ["a", "b"], [], ["out"]),
                Gate("Or", SIZE, ["a", "b"], [], ["out"]),
                Gate("Mux", SIZE, ["a", "b"], ["sel"], ["out"]),
                Gate("Mux4Way", SIZE, ["a", "b", "c", "d"], ["sel[2]"], ["out"]),
                Gate("Mux8Way", SIZE, list(string.letters[:8]), ["sel[3]"], ["out"])],
         "02": [Gate("Buffer", SIZE, ["in"], [], ["out"])],
         "03/a": [Gate("Bit", SIZE, ["in"], ["load"], ["out"])]}

if __name__ == '__main__':
    for dirname, gates in GATES.iteritems():
        for gate in gates:
            write_chip(dirname, gate)
