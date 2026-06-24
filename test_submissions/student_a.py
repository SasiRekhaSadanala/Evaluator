# Student A - Factorial implementation
def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Test cases
for i in range(6):
    print(f"factorial({i}) = {factorial(i)}")
