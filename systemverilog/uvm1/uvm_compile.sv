
module uvm_compile;

import uvm_pkg::*;
`include "uvm_macros.svh"

initial begin
	`uvm_info("UVM","Hello, welcome to UVM", UVM_LOW);
	#1us;
	`uvm_info("UVM","Byebye",UVM_LOW);
	$finish;
end


endmodule