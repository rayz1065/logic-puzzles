from logic_puzzles.solver import SimpleBranchingSolver


class GalaxiesSolver(SimpleBranchingSolver):
    def iter_locations(self):
        yield from self.puzzle.grid_utils.iter_grid()

    def is_location_set(self, location):
        r, c = location
        return self.state.grid[r][c] is not None

    def _debug_init(self):
        # print the cell_galaxies for testing purposes
        PRETTY_GALAXY = ["+", "Q", "x", "X", "o", "O", "0", "s", "8", "S"]

        def stringify_cell(r, c, galaxy_id):
            new_r, new_c = self.puzzle.rotational_symmetry(r, c, galaxy)
            hash_ = hash(tuple(sorted(((r, c), (new_r, new_c)))))
            cell_str = (
                PRETTY_GALAXY[(hash_ % len(PRETTY_GALAXY))]
                if galaxy_id in self.puzzle.cell_galaxies[r][c]
                else "."
            )
            return cell_str

        for galaxy_id, galaxy in enumerate(self.puzzle.galaxies):
            print(f"Galaxy {galaxy_id}:")
            for r in range(self.puzzle.grid_utils.rows):
                print(
                    " ".join(
                        stringify_cell(r, c, galaxy_id)
                        for c in range(self.puzzle.grid_utils.cols)
                    )
                )

    def _compute_dirty(self, location):
        r, c = location
        dirty = set()
        for galaxy_id in self.puzzle.cell_galaxies[r][c]:
            for new_location in self.puzzle.galaxy_cells[galaxy_id]:
                if not self.is_location_set(new_location):
                    dirty.add(new_location)

        return dirty

    def get_branching_score(self, location):
        r, c = location
        return -len(self.puzzle.cell_galaxies[r][c])
