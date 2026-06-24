class Solution:
    def threeSum(self, nums, target=0):
        res = []
        nums = sorted(nums)
        n = len(nums)
        for i in range(0,n-2):
            if i > 0 and nums[i] == nums[i-1]:
                continue
            left = i + 1
            right = n - 1
            required_sum = -nums[i]
            while left < right:
                s = nums[left] + nums[right]
                if s == required_sum:
                    res.append([nums[i], nums[left], nums[right]])
                    left += 1
                    right -= 1
                    while left < n and nums[left] == nums[left-1]:
                        left += 1
                    while right > i and nums[right] == nums[right+1]:
                        right -= 1
                elif s < required_sum:
                    left += 1
                else:
                    right -= 1
        return res
