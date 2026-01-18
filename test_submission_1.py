"""
Student submission 1 - Calculate factorial
"""

def factorial(n):
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


def fibonacci(n):
    """Generate fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    
    fib_list = [0, 1]
    while len(fib_list) < n:
        fib_list.append(fib_list[-1] + fib_list[-2])
    return fib_list


if __name__ == "__main__":
    print(f"5! = {factorial(5)}")
    print(f"First 10 fibonacci numbers: {fibonacci(10)}")
