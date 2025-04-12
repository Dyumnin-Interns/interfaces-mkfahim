module dut_test(
    CLK,
	   RST_N,

	   write_address,
	   write_data,
	   write_en,
	   write_rdy,

	   read_address,
	   read_en,
	   read_data,
	   read_rdy);
  output reg  CLK;
  input  RST_N;

  // action method write
  input  [2 : 0] write_address;
  input  write_data;
  input  write_en;
  output write_rdy;

  // actionvalue method read
  input  [2 : 0] read_address;
  input  read_en;
  output read_data;
  output read_rdy;

  dut dut( 
    // The first 'dut' is the module name 
    // The second 'dut' is the instance name (we're calling this specific instance 'dut')
    .CLK(CLK),
    .RST_N(RST_N),

    .write_address(write_address),
    .write_data(write_data),
    .write_en(write_en),
    .write_rdy(write_rdy),
    
    .read_address(read_address),
    .read_en(read_en),
    .read_data(read_data),
    .read_rdy(read_rdy)
);

initial begin
    $dumpfile("ifc.vcd");
    $dumpvars;
    CLK = 0;
    forever begin
        CLK =~ CLK;
    end
  end

  endmodule

