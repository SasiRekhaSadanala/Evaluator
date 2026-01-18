# Average submission - works but missing some polish

def sum_evens(numbers):
    # Sum of even numbers
    result = 0
    for n in numbers:
        if n % 2 == 0:
            result = result + n
    return result


# Test
print(sum_evens([1, 2, 3, 4, 5, 6]))
print(sum_evens([]))
print(sum_evens([1, 3, 5]))
