package test_pkg;
import uvm_pkg::*;
`include "uvm_macros.svh"

class top extends uvm_test;

	`uvm_component_utils(top)
	
	function new(string name="top", uvm_component parent=null);
		super.new(name,parent);
		`uvm_info("UVM_TOP","Function new is called",UVM_LOW)
	endfunction

	task run_phase(uvm_phase phase);
		phase.raise_objection(this);
		
		`uvm_info("UVM_TOP","test is running",UVM_LOW)		

		phase.drop_objection(this);
	endtask

endclass



endpackage


module uvm_test_inst;
	import uvm_pkg::*;
	`include "uvm_macros.svh"
	
	import test_pkg::*;

initial begin
	`uvm_info("UVM_TOP","test start",UVM_LOW)
	run_test("top");
	`uvm_info("UVM_TOP","test finish",UVM_LOW)
end
	


endmodule