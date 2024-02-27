import sys
from logic_puzzles.solver import Solver
from .puzzle import EinsteinPuzzle, EinsteinState


class EinsteinSolver(Solver):
    puzzle: EinsteinPuzzle

    def _solve_dirty(self, item_idx, dirty):
        self.check_timeout()

        if len(dirty) == 0:
            return self._solve(item_idx)

        item = dirty.pop()
        if self.state.item_location.get(item) is not None:
            return self._solve_dirty(item_idx, dirty)

        valid_houses = [
            i
            for i, house in enumerate(self.state.houses)
            if self.state.conflict_values[i][item] == 0
        ]
        if len(valid_houses) == 0:
            return 0

        if len(valid_houses) != 1:
            return self._solve_dirty(item_idx, dirty)

        house = valid_houses[0]
        dirty.update(self.puzzle.set_house(item, house))
        res = self._solve_dirty(item_idx, dirty)
        self.puzzle.unset_house(item)

        return res

    def _solve(self, item_idx=0):
        self.check_timeout()

        if item_idx == len(self.puzzle.items):
            self.store_solution()
            return 1

        item = self.puzzle.items[item_idx]
        if self.state.item_location.get(item) is not None:
            return self._solve(item_idx + 1)

        res = 0
        for i, house in enumerate(self.state.houses):
            if self.state.conflict_values[i][item] > 0:
                continue

            dirty = self.puzzle.set_house(item, i)
            res += self._solve_dirty(item_idx + 1, dirty)
            self.puzzle.unset_house(item)

        return res
