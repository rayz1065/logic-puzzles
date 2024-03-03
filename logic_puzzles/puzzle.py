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
        raise NotImplementedError

    def can_set(self, location, value):
        raise NotImplementedError

    def set_value(self, location, value):
        raise NotImplementedError

    def unset_value(self, location):
        raise NotImplementedError
