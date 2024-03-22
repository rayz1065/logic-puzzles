from logic_puzzles.solver import SimpleBranchingSolver


class LitsSolver(SimpleBranchingSolver):
    def get_branching_score(self, location):
        # prioritize regions with fewer combinations of shapes
        r, c = location
        region = self.puzzle.regions_grid[r][c]
        return -len(self.puzzle.shapes_by_region[region])

    def _try_placing(self, shape):
        updated = set()

        res = True
        for r, c in shape[1]:
            if self.is_location_set((r, c)):
                continue

            if not self.puzzle.can_set((r, c), 1):
                res = False
                break

            self.puzzle.set_value((r, c), 1)
            updated.add((r, c))

        for r, c in updated:
            self.puzzle.unset_value((r, c))

        return res

    def try_every_shape(self):
        """
        For every region, try to place every possible shape,
        set any cell that is either always 0 or always 1 in all shapes
        """
        to_update = {}

        for region in self.puzzle.regions:
            expected_full_cells = self.puzzle.state.found_by_region[region, 1]
            if expected_full_cells == 4:
                continue

            total_valid_shapes = 0
            valid_locations = {}
            for shape in self.puzzle.shapes_by_region[region]:
                empty_cells, full_cells = self.puzzle.count_pieces_by_cells(shape[1])
                if empty_cells > 0 or full_cells != expected_full_cells:
                    continue

                if not self._try_placing(shape):
                    continue

                total_valid_shapes += 1
                for r, c in shape[1]:
                    valid_locations.setdefault((r, c), 0)
                    valid_locations[r, c] += 1

            if total_valid_shapes == 0:
                # we did a mistake, this region cannot be filled with any shape
                return None

            for (r, c), freq in valid_locations.items():
                if self.is_location_set((r, c)) or 0 < freq < total_valid_shapes:
                    continue

                # NOTE: to_update[r, c] is only updated once, no need to check if there's a conflict
                new_value = 1 if valid_locations[(r, c)] == total_valid_shapes else 0
                to_update[r, c] = new_value

        return to_update

    def check_all_connected(self):
        visited = None
        for r, c in self.puzzle.iter_locations():
            if self.puzzle.get_value((r, c)) != 1:
                continue

            if visited is None:
                visited = self.puzzle.get_connected_component(r, c)
            elif (r, c) not in visited:
                return False

        return True

    def _branching_solve(self):
        to_update = self.try_every_shape()
        if to_update is None:
            return 0

        if self.debug:
            print("found by trying every shape", len(to_update))

        if to_update:
            return self._solve_updates_map(to_update)

        if not self.check_all_connected():
            if self.debug:
                print("Found parts that were not connected")
            return 0

        return super()._branching_solve()

    def _compute_dirty(self, location):
        return set(self.puzzle.iter_locations())
