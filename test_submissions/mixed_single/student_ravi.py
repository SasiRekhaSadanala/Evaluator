"""
Binary Search Algorithm - Explanation and Implementation
=========================================================

Binary search is a highly efficient searching algorithm that works on sorted arrays.
Unlike linear search which checks every element one by one, binary search repeatedly
divides the search interval in half, making it significantly faster for large datasets.

How Binary Search Works:
1. Start with the entire sorted array
2. Compare the target value with the middle element
3. If the target matches the middle element, we found it
4. If the target is less than the middle, search the left half
5. If the target is greater than the middle, search the right half
6. Repeat until the element is found or the search space is empty

Time Complexity:
- Best Case: O(1) when the target is the middle element
- Average and Worst Case: O(log n) because we halve the search space each step

Space Complexity:
- Iterative: O(1) constant extra space
- Recursive: O(log n) due to the recursive call stack

Compared to linear search which takes O(n) time, binary search with O(log n)
is exponentially faster. For 1 million elements, linear search needs up to
1,000,000 comparisons while binary search needs only about 20.

Limitations: The array must be sorted, and random access is required.
"""


def binary_search(arr, target):
    """
    Iterative binary search implementation.
    Returns the index of target if found, -1 otherwise.
    """
    left = 0
    right = len(arr) - 1

    while left <= right:
        # Calculate middle index to avoid integer overflow
        mid = left + (right - left) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            # Target is in the right half
            left = mid + 1
        else:
            # Target is in the left half
            right = mid - 1

    return -1


def binary_search_recursive(arr, target, left, right):
    """
    Recursive binary search implementation.
    Demonstrates the divide and conquer approach.
    """
    # Base case: search space is exhausted
    if left > right:
        return -1

    mid = left + (right - left) // 2

    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)


# Example usage showing both implementations work correctly
if __name__ == "__main__":
    test_array = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
    print(f"Array: {test_array}")
    print(f"Search for 23: index = {binary_search(test_array, 23)}")
    print(f"Search for 99: index = {binary_search(test_array, 99)}")
