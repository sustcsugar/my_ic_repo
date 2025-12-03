`timescale 1ns / 100ps

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

package chnl_pkg;
    // transaction message
    class chnl_trans;
        int data;
        int id;
        int num;
    endclass: chnl_trans

    // channel initiator
    class chnl_initiator;
        string name;
        int idle_cycles;
        virtual chnl_intf intf;

        function new(string name = "chnl_initiator");
            this.name = name;
            this.idle_cycles = 1;
        endfunction

        function void set_name(string s);
            this.name = s;
        endfunction

        function void set_idle_cycles(int n);
            this.idle_cycles = n;
        endfunction

        function void set_interface(virtual chnl_intf intf);
            if(intf == null)
                $error("interface handle is NULL, please check if target interface has been intantiated");
            else
                this.intf = intf;
        endfunction

        task chnl_write(input chnl_trans t);
            @(posedge intf.clk);
            intf.drv_ck.ch_valid <= 1;
            intf.drv_ck.ch_data  <= t.data;
            @(negedge intf.clk);
            wait(intf.ch_ready === 'b1);
            $display("%t channel initiator [%s] sent data %x", $time, name, t.data);
            repeat(idle_cycles) chnl_idle();
        endtask

        task chnl_idle();
            @(posedge intf.clk);
            intf.drv_ck.ch_valid <= 0;
            intf.drv_ck.ch_data  <= 0;
        endtask

    endclass: chnl_initiator

    // data generator
    class chnl_generator;
        chnl_trans t;
        chnl_trans trans_arr[$];
        int id;
        int num;

        function new(int id);
            this.id = id;
            this.num = 0;
        endfunction

        function chnl_trans get_trans();
            t = new ();
            t.data = 'h00C0_0000 + (id << 16) + num;
            t.id   = this.id;
            t.num  = this.num;
            this.num++;
            trans_arr.push_back(t);
            return t;
        endfunction

    endclass: chnl_generator

    class chnl_agent;
        chnl_initiator init;
        chnl_generator gen;
        virtual chnl_intf vif;
        int ntrans;

        function new(string name = "chnl_agent", int id = 0, int ntrans = 1);
            this.init = new(name);
            this.gen  = new(id);
            this.ntrans = ntrans;
        endfunction

        function void set_ntrans(int n);
            this.ntrans = n;
        endfunction

        function void set_interface(virtual chnl_intf intf);
            if(intf == null)
                $error("interface handle is NULL, please check if target interface has been intantiated");
            else
                this.vif = intf;
                this.init.set_interface(intf);
        endfunction

        task run();
            repeat(this.ntrans) this.init.chnl_write(this.gen.get_trans());
            this.init.chnl_idle();
        endtask
    endclass: chnl_agent

    class chnl_root_test;
        chnl_agent agent[3];
        string name;

        function new(int ntrans = 100, string name = "chnl_root_test");
            this.name = name;
            foreach(agent[i]) begin
                this.agent[i] = new($sfotmatf("chnl_agent%0d",i),i,ntrans);
            end
            $display("%s instantiate objects",this.name);
        endfunction

        function void set_interface(virtual chnl_intf ch0_vif,
                                    virtual chnl_intf ch1_vif,
                                    virtual chnl_intf ch2_vif);
            agent[0].set_interface(ch0_vif);
            agent[1].set_interface(ch1_vif);
            agent[2].set_interface(ch2_vif);
        endfunction

        task run();
            $display("%s started testing DUT", this.name);
            fork
                agent[0].run();
                agent[1].run();
                agent[2].run();
            join
            fork
                wait(agent[0].vif.ch_margin == 'h20);
                wait(agent[1].vif.ch_margin == 'h20);
                wait(agent[2].vif.ch_margin == 'h20);
            join
            $display("%s 3 channel all data have been transferred", this.name);
            $display("%s finished testing DUT", this.name);
        endtask
    endclass: chnl_root_test

    class chnl_basic_test extends chnl_root_test;
        function new(int ntrans = 200, string name = "chnl_basic_test");
            super.new(ntrans, name);
            foreach(agent[i])begin
                agent[i].init.set_idle_cycles($urandom_range(1,3));
            end
            $display("%s configured objects", this.name);
        endfunction
    endclass: chnl_basic_test

    class chnl_burst_test extends chnl_root_test;
        function new(int ntrans = 500, string name = "chnl_burst_test");
            super.new(ntrans, "chnl_burst_test");
            foreach(agent[i])begin
                agent[i].init.set_idle_cycles(0);
            end
            $display("%s configured objects", this.name);
        endfunction
    endclass: chnl_burst_test

    class chnl_fifo_full_test extends chnl_root_test;
        function new(int ntrans = 1000000,string name = "chnl_fifo_full_test");
            super.new(ntrans,name);
            foreach(agent[i])begin
                agent[i].init.set_idle_cycles(0);
            end
            $display("%s configured objects", this.name);
        endfunction

        task run();
            $display("%s started testing DUT", this.name);
            fork:fork_all_run
                agent[0].run();
                agent[1].run();
                agent[2].run();
            join_none
            $display("%s 3 agent is running and sending data", this.name);

            fork
                wait(agent[0].vif.ch_margin == 'h0);
                wait(agent[1].vif.ch_margin == 'h0);
                wait(agent[2].vif.ch_margin == 'h0);
            join
            $display("%s 3 agent 3 channel fifo are FULL", this.name);

            $display("%s stop 3 agent run", this.name);
            disable fork_all_run;

            fork
                agent[0].init.chnl_idle();
                agent[1].init.chnl_idle();
                agent[2].init.chnl_idle();
            join

            fork
                wait(agent[0].vif.ch_margin == 'h20);
                wait(agent[1].vif.ch_margin == 'h20);
                wait(agent[2].vif.ch_margin == 'h20);
            join
            $display("%s 3 channel fifo has transferred all data.", this.name);
            $display("%s Finished testing DUT", this.name);
        endtask
    endclass: chnl_fifo_full_test



endpackage: chnl_pkg

module my_tb4;
    import chnl_pkg::*;

    // common signals
    logic clk;
    logic rstn;

    // mcdt signals
    logic [31:0] mcdt_data_o;
    logic        mcdt_val_o ;
    logic [1:0]  mcdt_id_o  ;

    // DUT instantiation
    mcdt dut(
        .clk_i       (clk                ),
        .rstn_i      (rstn               ),
        .ch0_data_i  (chnl0_if.ch_data   ),
        .ch0_valid_i (chnl0_if.ch_valid  ),
        .ch0_ready_o (chnl0_if.ch_ready  ),
        .ch0_margin_o(chnl0_if.ch_margin ),
        .ch1_data_i  (chnl1_if.ch_data   ),
        .ch1_valid_i (chnl1_if.ch_valid  ),
        .ch1_ready_o (chnl1_if.ch_ready  ),
        .ch1_margin_o(chnl1_if.ch_margin ),
        .ch2_data_i  (chnl2_if.ch_data   ),
        .ch2_valid_i (chnl2_if.ch_valid  ),
        .ch2_ready_o (chnl2_if.ch_ready  ),
        .ch2_margin_o(chnl2_if.ch_margin ),
        .mcdt_data_o (mcdt_data_o        ),
        .mcdt_val_o  (mcdt_val_o         ),
        .mcdt_id_o   (mcdt_id_o          )
    );

    chnl_intf chnl0_if(clk, rstn);
    chnl_intf chnl1_if(clk, rstn);
    chnl_intf chnl2_if(clk, rstn);

    chnl_basic_test basic_test;
    chnl_burst_test burst_test;
    chnl_fifo_full_test fifo_full_test;


    // clock generation
    initial begin 
        clk <= 0;
        forever begin
            #5 clk <= !clk;
        end
    end
    // reset trigger
    initial begin
        #10 rstn <= 0;
        repeat(10) @(posedge clk);
        rstn <= 1;
    end


    initial begin
        basic_test = new(200,"sg_chnl_bastic_test");
        burst_test = new(500,"sg_chnl_burst_test");
        fifo_full_test = new(1000000,"sg_chnl_fifo_full_test");

        basic_test.set_interface(chnl0_if, chnl1_if, chnl2_if);
        burst_test.set_interface(chnl0_if, chnl1_if, chnl2_if);
        fifo_full_test.set_interface(chnl0_if, chnl1_if, chnl2_if);

        basic_test.run();
        burst_test.run();
        fifo_full_test.run();

        $finish();
    end


endmodule