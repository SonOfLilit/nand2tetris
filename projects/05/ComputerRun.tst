load Computer.hdl,
ROM32K load Fill.hack;

repeat 6 {
    tick, tock;
}

set reset 1, tick, tock;
set reset 0, tick, tock;


repeat {
    tick, tock;
}
