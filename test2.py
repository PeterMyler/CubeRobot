arr = [[1, 2, 3], [0, 8, 2], [3, 2, 1], [10, 0, 0]]

print(tuple(map(max, zip(*arr))))
print(tuple(map(min, zip(*arr))))