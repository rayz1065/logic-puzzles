import sys
import copy


class PuzzleState:
    def copy(self):
        return copy.deepcopy(self)


class Puzzle:
    state: PuzzleState

    @classmethod
    def from_string(cls, string, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_file(cls, file=sys.stdin, *args, **kwargs):
        return cls.from_string("\n".join(file), *args, **kwargs)

    def __str__(self):
        raise NotImplementedError

    def set_state(self, state):
        old_state = self.state
        self.state = state
        return old_state
