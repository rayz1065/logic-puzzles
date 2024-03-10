from .puzzle import KakuroPuzzle
from logic_puzzles.solver import SimpleBranchingSolver


class KakuroSolver(SimpleBranchingSolver):
    puzzle: KakuroPuzzle

    def _compute_dirty(self, location):
        r, c = location
        dirty = set()
        for i in self.puzzle.constraint_indexes[r, c]:
            cells = self.puzzle.constraints[i][1]
            for other_r, other_c in cells:
                if not self.is_location_set((other_r, other_c)):
                    dirty.add((other_r, other_c))

        return dirty

    def get_branching_score(self, location):
        return 1
