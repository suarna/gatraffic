import random

import numpy as np


def adapt(individual, cycle, lower_limit, upper_limit):
    length = len(individual)-1
    div = []
    arr = individual[0:length]
    for n in range(0, length):
        div.append(np.floor(np.abs(cycle-np.sum(arr)) / length))
    remainder = np.abs(cycle-np.sum(arr)) % length
    if cycle-np.sum(arr) > 0:
        for n in range(0, length):
            while arr[n]+div[n] > upper_limit:
                div[n] -= 1
                remainder += 1
            arr[n] += div[n]
        minimum = np.min(arr)
        indices = [i for i, x in enumerate(arr) if x == minimum]
        idx = random.randint(0, len(indices)-1)
        arr[indices[idx]] += remainder
    elif cycle - np.sum(arr) < 0:
        for n in range(0, length):
            while arr[n]-div[n] < lower_limit:
                div[n] -= 1
                remainder += 1
            arr[n] -= div[n]
        maximum = np.max(arr)
        indices = [i for i, x in enumerate(arr) if x == maximum]
        idx = random.randint(0, len(indices) - 1)
        arr[indices[idx]] -= remainder
    arr.append(individual[length])
    return arr









