module systolic_mm #(
    parameter int N = 4,
    parameter int DW = 8,
    parameter int AW = 2*DW + $clog2(N)
) (
    input logic clk,
    input logic rst,
    input logic start,
    input logic [N*N*DW-1:0] a_flat, input logic [N*N*DW-1:0] b_flat,
    // a_flat, b_flat, & c_flat are flattened to be packed into one bus
    output logic [N*N*AW-1:0] c_flat,
    output logic busy, output logic done
);

    localparam int STEPS = 3*N - 2;
    localparam int TW = $clog2(STEPS); // counter width, need enough bits to count from 0 to STEPS-1

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

    // GRID OF CELLS
    logic signed [DW-1:0] a_w [N][N+1]; // a_w[i][j] enters cell (i, j) from the left
    logic signed [DW-1:0] b_w [N+1][N]; // b_w[i][j] enters cell (i, j) from above
    logic signed [AW-1:0] acc [N][N];   // acc[i][j] is the running total of cell (i, j)

    for (genvar i = 0; i < N; i++) begin : g_edge
        assign a_w[i][0] = a_feed[i]; // left edge of row i
        assign b_w[0][i] = b_feed[i]; // top edge of column i
    end

    for (genvar i = 0; i < N; i++) begin : g_row
        for (genvar j = 0; j < N; j++) begin : g_col
            pe #(.DW(DW), .AW(AW)) u_pe (
                .clk(clk), .rst(rst), .clr(go), .en(busy),
                .a_in(a_w[i][j]), .b_in(b_w[i][j]),
                .a_out(a_w[i][j+1]), .b_out(b_w[i+1][j]),
                .acc(acc[i][j])
            );
            assign c_flat[(i*N + j)*AW +: AW] = acc[i][j]; // C[i][j]
        end
    end

endmodule
