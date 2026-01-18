"""
Student submission 2 - Simple counter
"""

class Counter:
    def __init__(self, start=0):
        self.value = start
    
    def increment(self):
        self.value += 1
    
    def decrement(self):
        self.value -= 1
    
    def reset(self):
        self.value = 0
    
    def get_value(self):
        return self.value


if __name__ == "__main__":
    counter = Counter()
    counter.increment()
    counter.increment()
    print(f"Counter value: {counter.get_value()}")
