#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// Function to calculate factorial
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

// Function to find maximum in array
int findMax(vector<int>& arr) {
    int maxVal = arr[0];
    for (int i = 1; i < arr.size(); i++) {
        if (arr[i] > maxVal) {
            maxVal = arr[i];
        }
    }
    return maxVal;
}

int main() {
    // Test factorial
    cout << "Factorial of 5: " << factorial(5) << endl;
    
    // Test findMax
    vector<int> numbers = {3, 7, 2, 9, 1};
    cout << "Maximum value: " << findMax(numbers) << endl;
    
    return 0;
}
