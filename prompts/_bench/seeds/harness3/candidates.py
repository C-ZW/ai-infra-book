"""Two candidate implementations of the same contract: sum_to(n) = 0+1+...+n.

`fast_sum_to` is correct and quick. `slow_sum_to` is correct for small n but
loops in pure Python and additionally hangs (infinite loop) for n < 0 — a
benchmark harness must time it out and/or capture the failure without crashing.
"""


def fast_sum_to(n):
    return n * (n + 1) // 2


def slow_sum_to(n):
    total = 0
    i = 0
    while i != n:          # infinite loop when n < 0
        i += 1
        total += i
    return total


CANDIDATES = [fast_sum_to, slow_sum_to]
TEST_INPUTS = [0, 1, 10, 100, -1]
