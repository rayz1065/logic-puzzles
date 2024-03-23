from .puzzle import KakuroPuzzle
from logic_puzzles.solver import SimpleBranchingSolver


class KakuroSolver(SimpleBranchingSolver):
    puzzle: KakuroPuzzle

    def _compute_dirty(self, location):
        location_type, location_data = location
        r, c, *_ = location_data
        dirty = set()
        for i in self.puzzle.cell_constraints[r, c]:
            _, cells = self.puzzle.constraints[i]
            dirty.update((("cell", cell) for cell in cells))
            dirty.update(
                ("hint", (*cell, value))
                for cell in cells
                for value in self.puzzle.iter_values()
            )

        return set(x for x in dirty if not self.is_location_set(x))

    def get_branching_score(self, location):
        location_type, location_data = location
        if location_type == "hint":
            return -1
        return 1
