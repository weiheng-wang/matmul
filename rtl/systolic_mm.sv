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

// CONTROL
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


// EDGE INPUTS
    logic signed [DW-1:0] a_feed [N]; // a_feed[i] enters row i from the left (N wires)
    logic signed [DW-1:0] b_feed [N]; // b_feed[i] enters column i from the top (N wires)

    for (genvar i = 0; i < N; i++) begin : g_feed // creates N copies for the lines below, different i for delay
        logic [TW-1:0] k;  // which entry row i and column i feed on this step
        logic in_window;   // 1 while row i and column i have an entry to feed

        assign k = t - TW'(i); // row i of A and column i of B enter the array i steps late
        
        // busy: not necessary (the cells are frozen when idle), but keeps the feeds at zero when idle
        // k < N: feed zeros before row/column i starts (k wraps to a large value when t-i < 0, k is not signed) and after it runs out of entries
        assign in_window = busy && (k < TW'(N));

        assign a_feed[i] = in_window ? a_r[(i*N + 32'(k))*DW +: DW] : '0; // A[i][k], row is fixed, and column changes with k
        assign b_feed[i] = in_window ? b_r[(32'(k)*N + i)*DW +: DW] : '0; // B[k][i], column is fixed, and row changes with k
    end

endmodule