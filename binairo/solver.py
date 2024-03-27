from logic_puzzles.solver import SimpleBranchingSolver


class BinairoSolver(SimpleBranchingSolver):
    def _try_combination(self, r, c, dr, dc, updates):
        res = True
        updated = []

        for i, (new_r, new_c) in enumerate(
            self.puzzle.grid_utils.ray_iter(r, c, dr, dc)
        ):
            if self.is_location_set((new_r, new_c)):
                continue

            value = updates[new_r, new_c]
            if not self.puzzle.can_set((new_r, new_c), value):
                res = False
                break

            self.puzzle.set_value((new_r, new_c), value)
            updated.append((new_r, new_c))

        for new_r, new_c in updated:
            self.puzzle.unset_value((new_r, new_c))

        return res

    def try_all_single_missing(self):
        to_update = {}

        CONSTRAINTS = [
            (
                (r, 0, 0, 1),
                self.puzzle.row_constraint,
                (self.state.found_by_row[r, 0], self.state.found_by_row[r, 1]),
            )
            for r in range(self.puzzle.grid_utils.rows)
        ] + [
            (
                (0, c, 1, 0),
                self.puzzle.col_constraint,
                (self.state.found_by_col[c, 0], self.state.found_by_col[c, 1]),
            )
            for c in range(self.puzzle.grid_utils.cols)
        ]

        for ray_bounds, constraint, found in CONSTRAINTS:
            cells = [(r, c) for r, c in self.puzzle.grid_utils.ray_iter(*ray_bounds)]
            if found[0] + found[1] == len(cells):
                continue
            if found[0] != constraint.target - 1 and found[1] != constraint.target - 1:
                continue

            value = 0 if found[0] == constraint.target - 1 else 1
            empty_cells = [cell for cell in cells if not self.is_location_set(cell)]

            valid_combinations = 0
            frequencies = {location: 0 for location in empty_cells}

            # pick the location that will be different from the others
            for odd_location in empty_cells:
                updates = {new_location: 1 - value for new_location in empty_cells}
                updates[odd_location] = value
                if not self._try_combination(*ray_bounds, updates):
                    continue

                valid_combinations += 1
                for new_location in empty_cells:
                    frequencies[new_location] += updates[new_location]

            for new_location, freq in frequencies.items():
                # check if the value of the cells is consistent across every valid combination
                if 0 < freq < valid_combinations:
                    continue

                new_value = 0 if freq == 0 else 1
                if to_update.get(new_location, new_value) != new_value:
                    return None

                to_update[new_location] = new_value

        return to_update

    def get_branching_score(self, location):
        r, c = location
        return max(
            self.puzzle.row_constraint.get_branching_score(
                self.state.found_by_row[r, 1], self.state.found_by_row[r, 0]
            ),
            self.puzzle.col_constraint.get_branching_score(
                self.state.found_by_col[c, 1], self.state.found_by_col[c, 0]
            ),
        )

    def _compute_dirty(self, location):
        r, c = location
        dirty = set()

        dirty.update((new_r, c) for new_r in range(self.puzzle.grid_utils.rows))
        dirty.update((r, new_c) for new_c in range(self.puzzle.grid_utils.cols))

        return set(x for x in dirty if not self.is_location_set(x))

    def _branching_solve(self):
        to_update = self.try_all_single_missing()

        if to_update is None:
            return 0

        if self.debug:
            print(f"Found by trying singe missing: {len(to_update)}")

        if to_update:
            return self._solve_updates_map(to_update)

        return super()._branching_solve()
