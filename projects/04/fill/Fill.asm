// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, the
// program clears the screen, i.e. writes "white" in every pixel.

@BLANK_WAIT
0;JMP

(BLANK)
@8192
D=A
@counter
M=D
(BLANK_LOOP)
@SCREEN
D=A
@counter
D=D+M
A=D
D=0
M=D
@counter
MD=M-1
@BLANK_LOOP
D;JGE

(BLANK_WAIT)
@KBD
D=M
@FILL
D;JNE
@BLANK_WAIT
0;JMP

(FILL)
@8192
D=A
@counter
M=D
(FILL_LOOP)
@SCREEN
D=A
@counter
D=D+M
A=D
D=-1
M=D
@counter
MD=M-1
@FILL_LOOP
D;JGE

(FILL_WAIT)
@KBD
D=M
@BLANK
D;JEQ
@FILL_WAIT
0;JMP
