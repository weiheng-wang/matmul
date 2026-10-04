module systolic_mm #(
    parameter int N = 2,
    parameter int DW = 8,
    parameter int AW = 2*DW + $clog2(N)
) (
    input logic clk,
    input logic rst,
    input logic start,
    input logic [N*N*DW-1:0] a_flat, input logic [N*N*DW-1:0] b_flat,
    // a_flat, b_flat, & c_flat are flattended to be packed into one bus
    output logic [N*N*AW-1:0] c_flat,
    output logic busy, output logic done
);

    localparam int STEPS = 3*N - 2;
    localparam int TW = $clog2(STEPS); // counter width, 2 bits for 4 steps

    logic [TW-1:0] t;

    logic go;
    assign go = start && !busy;

    logic [N*N*DW-1:0] a_r;
    logic [N*N*DW-1:0] b_r;

    always_ff @(posedge clk) begin
        if (rst) begin
            busy <= 0;
            done <= 0;
            t <= '0;
        end
        else if (go) begin
            busy <= 1;
            t <= '0;
            done <= 0;

            a_r <= a_flat;
            b_r <= b_flat;
        end
        else if (busy) begin
            t <= t + 1;
            if (t == TW'(STEPS - 1)) begin
                busy <= 0;
                done <= 1;
            end
        end
        else begin
            done <= 0;
        end
    end

endmodule

