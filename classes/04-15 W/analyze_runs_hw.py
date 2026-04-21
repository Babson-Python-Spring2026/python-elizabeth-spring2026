def analyze_runs(nums):
    current_run = [nums[0]]
    current_direction = "none"
    longest_increasing = []
    longest_decreasing = []
    num_increasing_runs = 0
    num_decreasing_runs = 0

    for i in range(1, len(nums)):
        current = nums[i]
        previous = nums[i - 1]

        if current > previous:
            if current_direction != "increasing":
                current_direction = "increasing"
                num_increasing_runs += 1
                current_run = [previous, current]
            else:
                current_run = current_run + [current]
            if len(current_run) > len(longest_increasing):
                longest_increasing = current_run

        elif current < previous:
            if current_direction != "decreasing":
                current_direction = "decreasing"
                num_decreasing_runs += 1
                current_run = [previous, current]
            else:
                current_run = current_run + [current]
            if len(current_run) > len(longest_decreasing):
                longest_decreasing = current_run

        else:
            current_run = [current]
            current_direction = "none"

    if len(longest_increasing) >= len(longest_decreasing):
        longest_run_values = longest_increasing
    else:
        longest_run_values = longest_decreasing

    return {
        "longest_increasing_run": len(longest_increasing),
        "longest_decreasing_run": len(longest_decreasing),
        "num_increasing_runs": num_increasing_runs,
        "num_decreasing_runs": num_decreasing_runs,
        "longest_run_values": longest_run_values
    }

print(analyze_runs([2, 4, 8, 3, 1, 5]))