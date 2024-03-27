from logic_puzzles.puzzle import Puzzle, PuzzleState


class TemplatePuzzleState(PuzzleState):
    def __init__(self):
        pass


class TemplatePuzzle(Puzzle):
    @classmethod
    def from_string(cls, string):
        pass

    def __init__(self, state=None):
        self.state = state
        if state is None:
            self.initialize_state()

    def __str__(self):
        pass

    def initialize_state(self):
        pass

    def iter_values(self):
        pass

    def iter_locations(self):
        pass

    def get_value(self, location):
        pass

    def can_set(self, location, value):
        pass

    def set_value(self, location, value):
        pass

    def unset_value(self, location):
        pass
