import sys
from logic_puzzles.solver import SimpleBranchingSolver
from .puzzle import EinsteinPuzzle, EinsteinState


class EinsteinSolver(SimpleBranchingSolver):
    puzzle: EinsteinPuzzle

    def _compute_dirty(self, item):
        dirty = set()
        for hint in self.puzzle.hints_by_item[item]:
            other_item = hint.item_1 if hint.item_2 == item else hint.item_2

            if not self.is_location_set(other_item):
                dirty.add(other_item)

        for other_item in self.puzzle.items_by_type[item.item_type]:
            if not self.is_location_set(other_item):
                dirty.add(other_item)

        return dirty

    def get_branching_score(self, location):
        return -sum(self.puzzle.get_valid_values(location))

    def is_location_set(self, location):
        return self.state.item_location.get(location) is not None

    def iter_locations(self):
        yield from self.puzzle.items
