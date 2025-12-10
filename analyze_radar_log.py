import json
import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

def get_latest_log_file():
    # Look for fHist_*.json files in the output directory
    output_dir = "output"
    if not os.path.exists(output_dir):
        print(f"Directory '{output_dir}' does not exist.")
        return None
        
    log_files = glob.glob(os.path.join(output_dir, "fHist_*.json"))
    if not log_files:
        return None
    
    # Sort by modification time, newest first
    latest_file = max(log_files, key=os.path.getmtime)
    return latest_file

def analyze_radar_log(file_path):
    if file_path is None:
        print("No file provided and no logs found in output directory.")
        return

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"Loading {file_path}...")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    if not data:
        print("Log file is empty.")
        return

    # Extract data
    timestamps = []
    abs_frame_nums = []
    
    print(f"Processing {len(data)} frames...")
    
    for i, entry in enumerate(data):
        # timestamp
        ts = entry.get('timestamp')
        
        # frame number from header
        header = entry.get('header', {})
        abs_fn = header.get('frameNumber')
        
        # We only care about frames that have both a timestamp and a valid frame number
        if ts is not None and abs_fn is not None:
             timestamps.append(ts)
             abs_frame_nums.append(abs_fn)

    timestamps = np.array(timestamps)
    abs_frame_nums = np.array(abs_frame_nums)

    if len(timestamps) < 2:
        print("Not enough data to analyze intervals.")
        return

    # --- Filtering: Start only once the radar starts sending frames ---
    # We look for the first valid frame number from the hardware. 
    # Usually this is 1, or it resets. We will trim leading data if needed.
    # However, since we filtered for None above, we just need to ensure we have a sequence.
    # The user might be referring to the first interval often being garbage (startup latency).
    # Let's drop the very first interval to be safe, as it represents the time between 
    # the first and second logged frame, which might include initialization overhead.
    
    # Actually, let's keep it but just warn.
    pass

    # 1. Missed Frames Analysis (using Frame Numbers)
    missed_total = 0
    gaps = []
    
    diffs = np.diff(abs_frame_nums)
    
    # Expect diff of 1. Anything > 1 is a skip.
    gap_locs = np.where(diffs > 1)[0]
    
    for idx in gap_locs:
        skip_size = diffs[idx] - 1
        missed_total += skip_size
        
        prev_frame = abs_frame_nums[idx]
        next_frame = abs_frame_nums[idx+1]
        
        time_gap = timestamps[idx+1] - timestamps[idx]
        
        # idx is the index in the filtered arrays
        gaps.append((idx + 1, prev_frame, next_frame, int(skip_size), time_gap))
            
    print("\n--- Analysis Report ---")
    print(f"Total Valid Frames Logged: {len(timestamps)}")
    print(f"Duration: {timestamps[-1] - timestamps[0]:.2f} seconds")
    
    if len(abs_frame_nums) > 0:
        print(f"Frame Number Range: {abs_frame_nums[0]} to {abs_frame_nums[-1]}")
        print(f"Total Missed Frames (Hardware Counter): {int(missed_total)}")
        if gaps:
            print("\nMissed Frame Events:")
            print(f"{ 'Log Index':<10} {'Prev Frame':<15} {'Next Frame':<15} {'Skipped':<10} {'Time Gap (s)':<15}")
            for g in gaps:
                print(f"{g[0]:<10} {g[1]:<15} {g[2]:<15} {g[3]:<10} {g[4]:.4f}")
    
    # 2. Time Interval Analysis
    intervals = np.diff(timestamps)
    intervals_ms = intervals * 1000
    
    # Filter out extremely large first interval if it exists (e.g. > 1 sec for a 40ms radar)
    # This addresses "plot starts only once the radar starts sending frames" if there's a startup lag.
    valid_intervals_ms = intervals_ms
    start_index = 0
    
    if len(intervals_ms) > 0 and intervals_ms[0] > 1000:
        print(f"\n[Info] Excluding initial interval of {intervals_ms[0]:.2f} ms from stats/plots.")
        valid_intervals_ms = intervals_ms[1:]
        start_index = 1

    if len(valid_intervals_ms) == 0:
        print("No valid intervals to plot.")
        return

    mean_dt_ms = np.mean(valid_intervals_ms)
    std_dt_ms = np.std(valid_intervals_ms)
    max_dt_ms = np.max(valid_intervals_ms)
    min_dt_ms = np.min(valid_intervals_ms)
    median_dt_ms = np.median(valid_intervals_ms)
    
    # Define bins (2ms width)
    max_val_ms = max(200, max_dt_ms + 50) 
    bins = np.arange(0, max_val_ms, 2) 

    # Calculate mode for binned data
    counts, bin_edges = np.histogram(valid_intervals_ms, bins=bins)
    mode_idx = np.argmax(counts)
    mode_dt_ms = (bin_edges[mode_idx] + bin_edges[mode_idx+1]) / 2

    print("\n--- Timing Statistics ---")
    print(f"Mean Interval: {mean_dt_ms:.2f} ms")
    print(f"Median Interval: {median_dt_ms:.2f} ms")
    print(f"Mode Interval: {mode_dt_ms:.2f} ms")
    print(f"Std Dev:       {std_dt_ms:.2f} ms")
    print(f"Min Interval:  {min_dt_ms:.2f} ms")
    print(f"Max Interval:  {max_dt_ms:.2f} ms")

    # Plotting
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Histogram of Intervals (ms)
    ax1 = axes[0]
    
    counts, _, _ = ax1.hist(valid_intervals_ms, bins=bins, color='skyblue', edgecolor='black')
    ax1.set_title('Distribution of Time Intervals between Frames')
    ax1.set_xlabel('Interval (ms)')
    ax1.set_ylabel('Count')
    ax1.grid(True, alpha=0.5)
    ax1.axvline(mean_dt_ms, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_dt_ms:.2f}ms')
    ax1.axvline(median_dt_ms, color='green', linestyle='dashed', linewidth=1, label=f'Median: {median_dt_ms:.2f}ms')
    ax1.axvline(mode_dt_ms, color='purple', linestyle='dashed', linewidth=1, label=f'Mode: {mode_dt_ms:.2f}ms')
    ax1.legend()

    # Plot 2: Interval vs Frame Index
    ax2 = axes[1]
    
    # x-axis needs to match the valid_intervals_ms
    # If we skipped the first interval (start_index=1), our data starts at log index 2.
    # Original timestamps indices: 0, 1, 2, ...
    # Intervals: (1-0), (2-1), ...
    # If start_index = 1, we take (2-1), which corresponds to arrival of frame 2.
    
    x_axis = np.arange(start_index + 1, len(timestamps))
    
    ax2.plot(x_axis, valid_intervals_ms, marker='o', markersize=2, linestyle='-', linewidth=0.5, label='Frame Interval')
    
    # Highlight gaps
    if gaps:
        for g in gaps:
            # g[0] is the index of the frame *after* the gap in the original lists
            # We want to plot the interval ending at this frame.
            # The interval index in 'intervals' is g[0]-1.
            # If we shifted 'valid_intervals_ms' by start_index, we need to adjust.
            
            raw_interval_idx = g[0] - 1
            if raw_interval_idx >= start_index:
                # Index in the plotted array
                plot_idx = raw_interval_idx - start_index
                if plot_idx < len(valid_intervals_ms):
                    val = valid_intervals_ms[plot_idx]
                    ax2.scatter(g[0], val, color='red', s=50, zorder=5) # Plot at original log index x

    ax2.set_title('Inter-Frame Arrival Time vs. Log Index')
    ax2.set_xlabel('Log Index')
    ax2.set_ylabel('Time Interval (ms)')
    ax2.grid(True, alpha=0.5)
    # Add legend manually for gaps if not present in plot call
    if gaps:
         ax2.scatter([], [], color='red', s=50, label='Gap Detected')
    ax2.legend()

    plt.tight_layout()
    print("\nDisplaying plots...")
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Inspect radar log for missed frames and timing.")
    parser.add_argument("file_path", nargs='?', help="Path to fHist_*.json. If omitted, finds latest in output/ directory.")
    args = parser.parse_args()
    
    target_file = args.file_path
    if not target_file:
        target_file = get_latest_log_file()
        if target_file:
            print(f"Auto-detected latest log: {target_file}")
    
    analyze_radar_log(target_file)