// push constant 1

// find top of stack and make room
@SP
AM=A+1
// write constant 1
M=1


// alternative that works with all constants

// load constant into D
@1
D=A
// find top of stack and make room
@SP
AM=A+1
// write constant
M=D


// pop static 1

// find top of stack
@SP
A=M
// read value
D=M
// write value to static 1
@f.1
M=D
// free room
@SP
M=M-1


// push constant 5

// load 5 in D
@5
D=A
// like before
@SP
AM=A+1
M=D


// add

// read top of stack into D
@SP
A=M
D=M
// free top of stack, keeping top of stack in A
@SP
AM=M-1
// add D to top of stack
M=D+M
// all in all we removed one value from the stack and overwrote
// another with their sum, which is exactly what we wanted


// pop local 2

// pop into D
@SP
A=M
D=M
@SP
M=M-1

// find local 0
@LOCAL
// local 2
A=A+1
A=A+1
// write D into local 2
M=D


// alternative that works for local k with k >> 2

// find local 2
@LOCAL
D=A
@2
D=D+A
// save it to R13
@R13
M=D

// pop into D
@SP
A=M
D=M
@SP
M=M-1

// save D into local 2 (which is in R13)
@R13
A=M
M=D


// eq - remove two top values from stack and write to top of stack
// 1 if they are equal, else 0

// read top of stack into D
@SP
A=M
D=M
// free top of stack, keeping top of stack in A
@SP
AM=M-1
// substract top of stack from D
D=D-M
// are they equal?
@EQUAL
D;JEQ
D=0
@WRITE
0;JMP
(EQUAL)
D=1
(WRITE)
// write D to top of stack
@SP
A=M
M=D
