from collections import defaultdict

numbers = [1.2, 1.5, 2.1, 3.4, 0.9, 5.11, 8.7]
d = defaultdict(float)
for i in range(7):
	d[i] += numbers[i]
print(dict(d))
