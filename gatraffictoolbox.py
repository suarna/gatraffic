import random
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plot


def adapt(individual, cycle: int, lower_limit: int, upper_limit: int):
    """Adapt the cycle to a fixed parameters, the time is fairly distributed
    :param individual: The plan chromosome
    :param cycle: cycle length
    :param lower_limit: lower allowed time value
    :param upper_limit: upper allowed time value
    :return: A list with new phase length
    """

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


# function that returns the moving average
def ma(data, w: int):
    """Function to compute the moving average

    :param data: a list with the values to be computed
    :param w: the window used to compute the convolution, for example, 50 for MA-50
    :return:An ndarray with the result of the ma

    """
    return np.convolve(data, np.ones(w), 'valid') / w







