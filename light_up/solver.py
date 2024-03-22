from logic_puzzles.solver import SimpleBranchingSolver
from logic_puzzles.grid_utils import ORTHOGONAL_DIRECTIONS


class LightUpSolver(SimpleBranchingSolver):
    def _compute_dirty(self, location):
        r, c = location
        dirty = set()
        for dr, dc in ORTHOGONAL_DIRECTIONS:
            new_r, new_c = r + dr, c + dc
            for new_r, new_c in self.puzzle.grid_utils.ray_iter(r + dr, c + dc, dr, dc):
                if self.puzzle.initial_grid[new_r][new_c] != ".":
                    break

                if not self.is_location_set((new_r, new_c)):
                    dirty.add((new_r, new_c))

            box_r, box_c = new_r, new_c
            if (new_r, new_c) in self.puzzle.box_constraints:
                for new_r, new_c in self.puzzle.grid_utils.orthogonal_iter(
                    box_r, box_c
                ):
                    if self.puzzle.initial_grid[new_r][new_c] != ".":
                        continue

                    if not self.is_location_set((new_r, new_c)):
                        dirty.add((new_r, new_c))

        return dirty

    def get_branching_score(self, location):
        r, c = location
        return -self.state.available_lights[r][c]
