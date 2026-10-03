module pe #( // processing unit
    parameter int DW = 8,
    // data width, 8 bits per matrix entry for A and B
    parameter int AW = 18
    /* accumulator width, bits in the running total for each pe,
       one product of 8-bit numbers needs 16 bits,
       and adding four (A,B,C are 4x4 matrices) of them needs 2 more so 18 */
) (
    input logic clk,
    input logic rst, input logic clr, input logic en,
    input logic signed [DW-1:0] a_in, input logic signed [DW-1:0] b_in,
    output logic signed [DW-1:0] a_out, output logic signed [DW-1:0] b_out,
    output logic signed [AW-1:0] acc
);

    logic signed [2*DW-1:0] product;
    assign product = a_in * b_in;

    always_ff @(posedge clk) begin
        if (rst || clr) begin
            a_out <= '0;
            b_out <= '0;
            acc <= '0;
        end
        else if (en) begin
            a_out <= a_in;
            b_out <= b_in;
            acc <= acc + AW'(product);
        end
    end

endmodule
