`timescale 1ns/100ps

interface chnl_intf(input clk, input rstn);
    logic [31:0] ch_data;
    logic       ch_valid;
    logic       ch_ready;
    logic [5:0] ch_margin;
    clocking drv_ck @(posedge clk);
        default input #1ns output #1ns;
        output ch_data, ch_valid;
        input  ch_ready, ch_margin;
    endclocking
endinterface

module chnl_initiator(chnl_intf intf);
    string name;
    int idle_cycles = 1;
    function automatic void set_name(string s);
        name = s;
    endfunction

    function automatic void set_idle_cycles(int n);
        idle_cycles = n;
    endfunction

    task automatic chnl_write(input logic [31:0] data);
        @(posedge intf.clk);
        intf.drv_ck.ch_valid <= 1;
        intf.drv_ck.ch_data  <= data;
        @(negedge intf.clk);
        wait(intf.ch_ready === 'b1);
        $display("%t channel initiator [%s] sent data %x", $time, name, data);  
        repeat(idle_cycles) chnl_idle();
    endtask

    task automatic chnl_idle();
        @(posedge intf.clk);
        intf.drv_ck.ch_valid <= 0;
        intf.drv_ck.ch_data  <= 0;
    endtask
endmodule

module chnl_generator;
    int id;
    int num;
    int chnl_arr[$];

    function automatic void initialize(int n);
        id = n;
        num = 0;
    endfunction

    function automatic int get_data();
        int data;
        data = 'h00C0_0000 + (id<<16) + num;
        num++;
        chnl_arr.push_back(data);
        return data;
    endfunction
endmodule





module tb1_my;

chnl_intf chnl0_if(.*);
chnl_intf chnl1_if(.*);
chnl_intf chnl2_if(.*);

chnl_initiator chnl0_init(.intf(chnl0_if));
chnl_initiator chnl1_init(.intf(chnl1_if));
chnl_initiator chnl2_init(.intf(chnl2_if));

chnl_generator gen0();
chnl_generator gen1();
chnl_generator gen2();


logic         clk;
logic         rstn;
logic [31:0]  mcdt_data;
logic         mcdt_val;
logic [ 1:0]  mcdt_id;


mcdt dut(
     .clk_i       (clk)
    ,.rstn_i      (rstn)
    ,.ch0_data_i  (chnl0_if.ch_data     )
    ,.ch0_valid_i (chnl0_if.ch_valid    )
    ,.ch0_ready_o (chnl0_if.ch_ready    )
    ,.ch0_margin_o(chnl0_if.ch_margin   )
    ,.ch1_data_i  (chnl1_if.ch_data     )
    ,.ch1_valid_i (chnl1_if.ch_valid    )
    ,.ch1_ready_o (chnl1_if.ch_ready    )
    ,.ch1_margin_o(chnl1_if.ch_margin   )
    ,.ch2_data_i  (chnl2_if.ch_data     )
    ,.ch2_valid_i (chnl2_if.ch_valid    )
    ,.ch2_ready_o (chnl2_if.ch_ready    )
    ,.ch2_margin_o(chnl2_if.ch_margin   )
    ,.mcdt_data_o (mcdt_data)
    ,.mcdt_val_o  (mcdt_val)
    ,.mcdt_id_o   (mcdt_id)
);

initial begin 
    clk <= 0;
    forever begin
      #5 clk <= !clk;
    end
end

initial begin
    #10 rstn <= 0;
    repeat(10) @(posedge clk);
    rstn <= 1;
end

initial begin
    basic_test();
    burst_test();
    fifo_full_test();
    $display("*****************all of tests have been finished********************");
    $finish();
end



task automatic basic_test();
    // verification component initializationi
    chnl0_init.set_name("chnl0_init");
    chnl1_init.set_name("chnl1_init");
    chnl2_init.set_name("chnl2_init");
    chnl0_init.set_idle_cycles($urandom_range(1,3));
    chnl1_init.set_idle_cycles($urandom_range(1,3));
    chnl2_init.set_idle_cycles($urandom_range(1,3));
    gen0.initialize(0);
    gen1.initialize(1);
    gen2.initialize(2);

    $display("*****************basic_test started********************");
    wait(rstn === 1'b1);
    repeat(5) @(posedge clk);
    fork
        repeat(100) chnl0_init.chnl_write(gen0.get_data());
        repeat(100) chnl1_init.chnl_write(gen1.get_data());
        repeat(100) chnl2_init.chnl_write(gen2.get_data());
    join
    fork
        wait(chnl0_if.ch_margin == 'h20);
        wait(chnl1_if.ch_margin == 'h20);
        wait(chnl2_if.ch_margin == 'h20);
    join
    $display("*****************basic_test finish********************");
endtask

task automatic burst_test();
    // verification component initializationi
    chnl0_init.set_name("chnl0_init");
    chnl1_init.set_name("chnl1_init");
    chnl2_init.set_name("chnl2_init");
    chnl0_init.set_idle_cycles(0);
    chnl1_init.set_idle_cycles(0);
    chnl2_init.set_idle_cycles(0);
    gen0.initialize(0);
    gen1.initialize(1);
    gen2.initialize(2);

    $display("*****************burst_test started********************");
    wait(rstn === 1'b1);
    repeat(5) @(posedge clk);
    fork
        begin
            repeat(500) chnl0_init.chnl_write(gen0.get_data());
            chnl0_init.chnl_idle();
        end
        begin
            repeat(500) chnl1_init.chnl_write(gen1.get_data());
            chnl1_init.chnl_idle();
        end
        begin
            repeat(500) chnl2_init.chnl_write(gen2.get_data());
            chnl2_init.chnl_idle();
        end
    join    
    fork
        wait(chnl0_if.ch_margin == 'h20);
        wait(chnl1_if.ch_margin == 'h20);
        wait(chnl2_if.ch_margin == 'h20);
    join
    $display("*****************burst_test finish********************");
endtask

task automatic fifo_full_test();
    // verification component initializationi
    chnl0_init.set_name("chnl0_init");
    chnl1_init.set_name("chnl1_init");
    chnl2_init.set_name("chnl2_init");
    chnl0_init.set_idle_cycles(0);
    chnl1_init.set_idle_cycles(0);
    chnl2_init.set_idle_cycles(0);
    gen0.initialize(0);
    gen1.initialize(1);
    gen2.initialize(2);
    $display("*****************fifo_full_test started********************");
    wait(rstn === 1'b1);
    repeat(5) @(posedge clk);
    fork : fork_all_run
        forever chnl0_init.chnl_write(gen0.get_data());
        forever chnl1_init.chnl_write(gen1.get_data()); 
        forever chnl2_init.chnl_write(gen2.get_data());
    join_none
    $display("fifo full test: initiator 0/1/2 running.");

    $display("fifo full test: wait for all channel fifos to be full.");
    fork
        wait(chnl0_if.ch_margin == 'h0);
        wait(chnl1_if.ch_margin == 'h0);
        wait(chnl2_if.ch_margin == 'h0);
    join
    $display("fifo full test: all channel fifos have full.");

    disable fork_all_run;
    $display("fifo full test: initiator 0/1/2 stopped.");

    fork
        chnl0_init.chnl_idle();
        chnl1_init.chnl_idle();
        chnl2_init.chnl_idle();
    join

    $display("fifo full test: wait DUT transfer all the data in fifo.");
    fork
        wait(chnl0_if.ch_margin == 'h20);
        wait(chnl1_if.ch_margin == 'h20);
        wait(chnl2_if.ch_margin == 'h20);
    join

    $display("fifo full test: initiator 0/1/2 are idle now.");
    $display("*****************fifo_full_test finish********************");

endtask




endmodule