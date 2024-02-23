import sys


class PuzzleState:
    def copy(self):
        raise NotImplementedError


class Puzzle:
    state: PuzzleState

    @classmethod
    def from_string(cls, string):
        raise NotImplementedError

    @classmethod
    def from_file(cls, file=sys.stdin):
        return cls.from_string("\n".join(file))

    def __str__(self):
        raise NotImplementedError

    def set_state(self, state):
        old_state = self.state
        self.state = state
        return old_state

    def copy(self):
        raise NotImplementedError
