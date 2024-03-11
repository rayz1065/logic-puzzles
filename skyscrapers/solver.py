from logic_puzzles.solver import SimpleBranchingSolver


class SkyscrapersSolver(SimpleBranchingSolver):
    def get_branching_score(self, location):
        location_type, location_data = location
        if location_type == "hint":
            # never branch on hints
            return -self.puzzle.grid_utils.rows * 2

        r, c = location_data
        return -sum(
            self.puzzle.get_value(("hint", (r, c, value))) is None
            for value in self.puzzle.iter_values()
        )

    def _compute_dirty(self, location):
        location_type, location_data = location

        r, c, *_ = location_data

        dirty = set(
            ("grid", (new_r, c)) for new_r in range(self.puzzle.grid_utils.rows)
        )
        dirty.update(
            ("hint", (new_r, c, value))
            for new_r in range(self.puzzle.grid_utils.rows)
            for value in self.puzzle.iter_values()
        )
        dirty.update(
            ("grid", (r, new_c)) for new_c in range(self.puzzle.grid_utils.rows)
        )
        dirty.update(
            ("hint", (r, new_c, value))
            for new_c in range(self.puzzle.grid_utils.rows)
            for value in self.puzzle.iter_values()
        )

        return set(x for x in dirty if not self.is_location_set(x))
