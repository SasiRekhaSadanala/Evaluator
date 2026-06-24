def sum_evens(numbers):
    """
    Returns the sum of all even numbers in the list.
    """
    if not isinstance(numbers, list):
        # Handle invalid input gracefully
        return 0
        
    total = 0
    for num in numbers:
        # Check if number is even
        if num % 2 == 0:
            total += num
    return total
