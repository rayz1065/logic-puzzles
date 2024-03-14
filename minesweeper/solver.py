from itertools import combinations
import math
from logic_puzzles.solver import SimpleBranchingSolver
from logic_puzzles.grid_utils import ALL_DIRECTIONS


class MinesweeperSolver(SimpleBranchingSolver):
    def get_branching_score(self, location):
        def compute_score(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return -math.comb(available, missing)

        r, c = location
        return max(
            compute_score(
                self.state.found_by_indicator[new_r, new_c, 1],
                self.state.found_by_indicator[new_r, new_c, 0],
                self.puzzle.initial_grid[new_r][new_c],
                len(self.puzzle.adjacent_cells[new_r, new_c]),
            )
            for new_r, new_c in self.puzzle.adjacent_indicators[r, c]
        )

    def _compute_dirty(self, location):
        dirty = set()
        field_r, field_c = location

        # adds all of the cells adjacent to all of the indicators adjacent to the current cell
        for r, c in self.puzzle.adjacent_indicators[field_r, field_c]:
            dirty.update(
                (new_r, new_c)
                for new_r, new_c in self.puzzle.adjacent_cells[r, c]
                if not self.is_location_set((new_r, new_c))
            )

        return dirty

    def _check_mine_placements(self, mines):
        added_by_indicator = {}

        for cell_r, cell_c in mines:
            for new_r, new_c in self.puzzle.adjacent_indicators[cell_r, cell_c]:
                added_by_indicator.setdefault((new_r, new_c), 0)
                added_by_indicator[new_r, new_c] += 1

                if (
                    added_by_indicator[new_r, new_c]
                    + self.state.found_by_indicator[new_r, new_c, 1]
                    > self.puzzle.initial_grid[new_r][new_c]
                ):
                    return False

        return True

    def _find_placements_around_indicators(self):
        """Try every combination of placements of mines around indicators and
        check which ones are valid, this heuristic is helpful whenever a group
        of cells can only contain a certain number of mines and we are therefore
        forced to place mines in the remaining cells.
        """
        to_update = {}

        for r, c in self.puzzle.mine_indicators:
            missing = (
                self.puzzle.initial_grid[r][c] - self.state.found_by_indicator[r, c, 1]
            )
            if missing == 0:
                continue

            empty_cells = [
                (cell_r, cell_c)
                for cell_r, cell_c in self.puzzle.adjacent_cells[r, c]
                if not self.is_location_set((cell_r, cell_c))
            ]
            valid_combinations = {(cell_r, cell_c): 0 for cell_r, cell_c in empty_cells}
            total = 0

            for mines in combinations(empty_cells, missing):
                if not self._check_mine_placements(mines):
                    continue

                total += 1
                for cell_r, cell_c in mines:
                    valid_combinations[cell_r, cell_c] += 1

            for cell_r, cell_c in empty_cells:
                if 0 < valid_combinations[cell_r, cell_c] < total:
                    continue

                # the value of this cells is consistent across all combinations
                new_value = int(valid_combinations[cell_r, cell_c] == total)
                if to_update.get((cell_r, cell_c), new_value) != new_value:
                    # different indicators disagree on the value of this cell
                    return 0

                to_update[cell_r, cell_c] = new_value

        return to_update

    def _branching_solve(self):
        to_update = self._find_placements_around_indicators()

        if to_update:
            return self._solve_updates_map(to_update)

        return super()._branching_solve()
