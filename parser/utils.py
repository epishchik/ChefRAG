import random


def sleep_random(around: float, std: float) -> float:
    sleep_duration = random.normalvariate(around, std)
    sleep_duration = max(1.5, sleep_duration)
    return sleep_duration
