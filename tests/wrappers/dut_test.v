module dut_test(

  output reg  CLK,
  input  RST_N,

  // Write interface
  // -------------------------------
  input  [2 : 0] write_address,
  input  write_data,
  input  write_en,
  output write_rdy,

  // Read interface
  // -------------------------------
  input  [2 : 0] read_address,
  input  read_en,
  output read_data,
  output read_rdy

  );


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


// Clock generation
  initial begin
    CLK = 0;
    forever #5 CLK = ~CLK;
  end

// Waveform dumping
  initial begin
    $dumpfile("ifc.vcd");
    $dumpvars(0, dut_test);
  end  

endmodule

