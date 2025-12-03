

module uvm_class_inst;

import uvm_pkg::*;
`include "uvm_macros.svh"


class top extends uvm_component;
	`uvm_component_utils(top)

	function new(string name="top", uvm_component parent=null);
		super.new(name,parent);
		`uvm_info("UVM_TOP", "UVM_TOP creating", UVM_LOW)
	endfunction
endclass



initial begin
	top t;
	`uvm_info("UVM_TOP","test start",UVM_LOW)
	t = new("top t",null);
	`uvm_info("UVM_TOP","test finish",UVM_LOW)

end


endmodule