from random import randint

SIMULATIONS = 1_000_000
counts = [0] * 13
misses = 0

for sim in range(SIMULATIONS):
    while True:
        # first 50/50
        A = randint(1, 2)

        if A == 1:
            B = randint(1, 8)
        else:
            B = randint(9, 16)

        if B < 14: break
        misses += 1

    counts[B-1] += 1

print([round(c/SIMULATIONS, 3) for c in counts])
print("Reroll rate:", round(misses / SIMULATIONS * 100, 2), "%")



