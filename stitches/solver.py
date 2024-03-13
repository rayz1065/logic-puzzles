import math
from logic_puzzles.solver import SimpleBranchingSolver


class StitchesSolver(SimpleBranchingSolver):
    def _compute_dirty(self, location):
        if location[0] == "link":
            link = self.puzzle.links[location[1]]
            cells = link.cells
        else:
            cells = [location[1]]

        dirty = set()

        for r, c in cells:
            # the column of the cell
            dirty.update(
                ("grid", (r, new_c)) for new_c in range(self.puzzle.grid_utils.cols)
            )

            # the row of the cell
            dirty.update(
                ("grid", (new_r, c)) for new_r in range(self.puzzle.grid_utils.rows)
            )

            # the region of the cell
            region = self.puzzle.initial_grid[r][c]
            dirty.update(
                ("grid", (new_r, new_c))
                for new_r, new_c in self.puzzle.regions[region]
            )

            # the stitches in the region
            dirty.update(
                ("link", link_id)
                for region_links in self.puzzle.neighbors_by_region[region].values()
                for link_id in region_links
            )

        return set(x for x in dirty if not self.is_location_set(x))

    def get_branching_score(self, location):
        if location[0] == "link":
            return -math.inf

        def compute_score(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return -math.comb(available, missing)

        r, c = location[1]
        region = self.puzzle.initial_grid[r][c]
        return max(
            compute_score(
                self.state.found_by_row[r, 1],
                self.state.found_by_row[r, 0],
                self.puzzle.target_by_row[r],
                self.puzzle.grid_utils.cols,
            ),
            compute_score(
                self.state.found_by_col[c, 1],
                self.state.found_by_col[c, 0],
                self.puzzle.target_by_col[c],
                self.puzzle.grid_utils.rows,
            ),
            compute_score(
                self.state.found_by_region[region, 1],
                self.state.found_by_region[region, 0],
                self.puzzle.target_by_region[region],
                len(self.puzzle.regions[region]),
            ),
        )
