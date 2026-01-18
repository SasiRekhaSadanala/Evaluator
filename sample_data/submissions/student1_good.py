# Good submission - clean, well-structured, handles all cases

def sum_evens(numbers):
    """
    Calculate the sum of all even numbers in a list.
    
    Args:
        numbers: List of integers
        
    Returns:
        Sum of even numbers, or 0 if no even numbers found
    """
    # Input validation
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")
    
    if not numbers:
        return 0
    
    # Calculate sum of even numbers
    total = 0
    for num in numbers:
        if isinstance(num, int) and num % 2 == 0:
            total += num
    
    return total


# Test cases
if __name__ == "__main__":
    print(sum_evens([1, 2, 3, 4, 5, 6]))  # Expected: 12
    print(sum_evens([]))  # Expected: 0
    print(sum_evens([1, 3, 5]))  # Expected: 0
    print(sum_evens([2, 4, 6, 8]))  # Expected: 20
