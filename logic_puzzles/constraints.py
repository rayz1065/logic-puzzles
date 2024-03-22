from math import comb
from abc import ABC, abstractmethod


class Constraint(ABC):
    @abstractmethod
    def check(self, *args, **kwargs):
        raise NotImplementedError


class SumConstraint(Constraint):
    def __init__(self, target, total):
        self.target = target
        self.total = total

    def get_missing(self, found):
        return self.target - found

    def get_available(self, found, empty):
        return self.total - found - empty

    def check(self, found, empty):
        missing = self.get_missing(found)
        available = self.get_available(found, empty)
        return 0 <= missing <= available


class CountConstraint(SumConstraint):
    def get_branching_score(self, found, empty):
        missing = self.get_missing(found)
        available = self.get_available(found, empty)
        return -comb(available, missing)
