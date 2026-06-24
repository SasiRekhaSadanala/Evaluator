class Solution:
    def threeSumClosest(self, nums, target):
        res_sum = 0
        nums.sort()
        n = len(nums)
        max_diff = float('inf')
        for i in range(0,n-2):
            left = i+1
            right = n-1
            req_sum = target - nums[i]
            while left < right:
                s = (nums[left] + nums[right])
                diff = abs(s - req_sum)
                if diff < max_diff:
                    max_diff = diff
                    res_sum = nums[i] + s
                if req_sum == s:
                    return target
                elif s < req_sum:
                    left += 1
                else:
                    right -= 1
        return res_sum
