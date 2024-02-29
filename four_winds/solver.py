from logic_puzzles.solver import Solver
from itertools import product


class FourWindsSolver(Solver):
    def _solve(self):
        unmet_demand = self.puzzle.get_unmet_demand()
        if unmet_demand == 0:
            self.store_solution()
            return 1

        potential_parents_by_count = [[] for _ in range(5)]

        for r, c in product(range(self.puzzle.rows), range(self.puzzle.cols)):
            if self.state.regions_grid[r][c] is not None:
                continue

            potential_regions = self.puzzle.get_potential_regions(r, c)
            if len(potential_regions) == 0:
                return 0

            potential_parents_by_count[len(potential_regions)].append(
                (r, c, potential_regions)
            )

        for parents_count in range(1, 5):
            if len(potential_parents_by_count[parents_count]) > 0:
                break
        else:
            raise ValueError("unmet_demand > 0 but no cells to fill")

        r, c, potential_regions = potential_parents_by_count[parents_count][0]
        res = 0
        for region in potential_regions:
            updated_cells = self.puzzle.set_region_ray(r, c, region)
            res += self._solve()
            for new_r, new_c in updated_cells:
                self.puzzle.unset_region(new_r, new_c)

        return res
