




interface intf;
	logic enable=0;
endinterface

package my_pkg;

import uvm_pkg::*;
`include "uvm_macros.svh"

class comp1 extends uvm_component;
    `uvm_component_utils(comp1)
    virtual intf vif;
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if(!uvm_config_db#(virtual intf)::get(this, "", "vif", vif)) begin
            `uvm_error("NOVIF", $sformatf("virtual interface not set for component: %s.vif",get_full_name() ))
        end

        `uvm_info("SETVIF",$sformatf("vif.enable is %b before set",vif.enable),UVM_LOW)
        vif.enable = 1;
        `uvm_info("SETVIF",$sformatf("vif.enable is %b after set",vif.enable),UVM_LOW)
    endfunction
endclass

class test1 extends uvm_test;
    `uvm_component_utils(test1)
    comp1 c1;
    function new(string name, uvm_component parent);
        super.new(name, parent);
        `uvm_info("TEST1","In test1 constructor",UVM_LOW)
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        `uvm_info("TEST1","In test1 build_phase",UVM_LOW)
        c1 = comp1::type_id::create("c1", this);
    endfunction
endclass

endpackage



module uvm_cfg_db;

import uvm_pkg::*;
`include "uvm_macros.svh"
import my_pkg::*;

intf intf1();
initial begin
    uvm_config_db_options::turn_on_tracing();
    uvm_config_db#(virtual intf)::set(null, "uvm_test_top.*", "vif", intf1);
    //`uvm_info("DEBUG",$sformatf("%p",uvm_root::get()),UVM_LOW)
    `uvm_info("DEBUG",$sformatf("%s",get_full_name()),UVM_LOW)

    run_test("test1");
end

endmodule