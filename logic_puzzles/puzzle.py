import sys
import copy
from abc import ABC, abstractclassmethod, abstractmethod


class PuzzleState:
    def copy(self):
        return copy.deepcopy(self)


class Puzzle(ABC):
    state: PuzzleState

    @abstractclassmethod
    def from_string(cls, string, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_file(cls, file=sys.stdin, *args, **kwargs):
        return cls.from_string("\n".join(file), *args, **kwargs)

    @abstractmethod
    def __str__(self):
        raise NotImplementedError

    @abstractmethod
    def initialize_state(self):
        raise NotImplementedError

    def set_state(self, state):
        old_state = self.state
        self.state = state
        if state is None:
            self.initialize_state()

        return old_state

    def reset_state(self):
        return self.set_state(None)

    def get_valid_values(self, location):
        return [value for value in self.iter_values() if self.can_set(location, value)]

    @abstractmethod
    def iter_values(self):
        raise NotImplementedError

    @abstractmethod
    def iter_locations(self):
        raise NotImplementedError

    @abstractmethod
    def get_value(self, location):
        raise NotImplementedError

    @abstractmethod
    def can_set(self, location, value):
        raise NotImplementedError

    @abstractmethod
    def set_value(self, location, value):
        raise NotImplementedError

    @abstractmethod
    def unset_value(self, location):
        raise NotImplementedError
