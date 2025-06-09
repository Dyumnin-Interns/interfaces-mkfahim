module dut_test(
  output reg CLK,
  input RST_N,
  input [2:0] write_address,
  input write_data,
  input write_en,
  output write_rdy,
  input [2:0] read_address,
  input read_en,
  output read_data,
  output read_rdy
);

  dut dut_inst(
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
    CLK = 0;
    forever #5 CLK = ~CLK;
  end

  initial begin
    $dumpfile("ifc.vcd");
    $dumpvars;
  end

endmodule
