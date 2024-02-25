from collections import namedtuple
from enum import Enum


class EinsteinItem(namedtuple("EinsteinItem", ["item_type", "item_value"])):
    def __str__(self):
        return f"({self.item_type}: '{self.item_value}')"


class EinsteinHint(namedtuple("EinsteinHint", ["item_1", "item_2", "negated"])):
    def __str__(self):
        return f"{'not ' if self.negated else ''}({self.item_1} <-> {self.item_2})"
