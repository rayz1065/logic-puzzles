from itertools import product
from logic_puzzles.solver import SimpleBranchingSolver


class SudokuSolver(SimpleBranchingSolver):
    def is_location_set(self, location):
        r, c = location
        return self.state.grid[r][c] is not None

    def iter_locations(self):
        yield from self.puzzle.grid_utils.iter_grid()

    def get_branching_score(self, location):
        return -len(self.puzzle.get_valid_values(location))

    def _get_hints_locations(self, cells):
        hints_locations = {value: [] for value in self.puzzle.sudoku_values}
        for location in cells:
            if self.is_location_set(location):
                r, c = location
                hints_locations.pop(self.state.grid[r][c])
                continue

            valid_values = self.puzzle.get_valid_values(location)
            for value in valid_values:
                hints_locations[value].append(location)

        return hints_locations

    def find_hidden_singles(self):
        to_update = {}

        hidden_singles_locations = []
        for r in range(self.puzzle.grid_utils.rows):
            cells = [(r, c) for c in range(self.puzzle.grid_utils.cols)]
            hidden_singles_locations.append(cells)

        for c in range(self.puzzle.grid_utils.cols):
            cells = [(r, c) for r in range(self.puzzle.grid_utils.rows)]
            hidden_singles_locations.append(cells)

        for square_r in range(self.puzzle.rows_square_count):
            for square_c in range(self.puzzle.cols_square_count):
                cells = list(self.puzzle.iter_square(square_r, square_c))
                hidden_singles_locations.append(cells)

        for cells in hidden_singles_locations:
            hints_locations = self._get_hints_locations(cells)

            for value, locations in hints_locations.items():
                if len(locations) > 1:
                    continue

                if len(locations) == 0:
                    return None

                location = locations[0]
                if to_update.get(location, value) != value:
                    return None

                to_update[location] = value


        return to_update

    def _branching_solve(self):
        to_update = self.find_hidden_singles()

        if to_update is None:
            if self.debug:
                print("Clashes found while looking for hidden singles")
            return 0

        if to_update:
            if self.debug:
                print("Found cells by hidden singles:", len(to_update))
            return self._solve_updates_map(to_update)

        return super()._branching_solve()

    def _compute_dirty(self, location):
        dirty = set()
        r, c = location
        square_r, square_c = self.puzzle.get_square_coords(r, c)
        for new_r in range(self.puzzle.grid_utils.rows):
            if not self.is_location_set((new_r, c)):
                dirty.add((new_r, c))

        for new_c in range(self.puzzle.grid_utils.rows):
            if not self.is_location_set((r, new_c)):
                dirty.add((r, new_c))

        for new_r, new_c in self.puzzle.iter_square(square_r, square_c):
            if not self.is_location_set((new_r, new_c)):
                dirty.add((new_r, new_c))

        return dirty
