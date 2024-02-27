from logic_puzzles.solver import Solver
from .puzzle import CommunicatingVesselsPuzzle


class CommunicatingVesselsSolver(Solver):
    def _solve(self, shape_idx=0, height_idx=0):
        if shape_idx == len(self.puzzle.shapes):
            self.store_solution()
            return 1

        if height_idx == len(self.puzzle.shapes[shape_idx].heights):
            return self._solve(shape_idx + 1, 0)

        shape = self.puzzle.shapes[shape_idx]
        r = shape.heights[height_idx]

        res = 0

        # try setting this row to 0, update all rows above
        updated_values = []
        for other_r in shape.heights[height_idx:]:
            if not self.puzzle.can_set_value(shape_idx, other_r, 0):
                break

            updated_values.append(other_r)
            self.puzzle.set_value(shape_idx, other_r, 0)
        else:
            # all rows updated successfully
            res += self._solve(shape_idx + 1, 0)

        for other_r in updated_values:
            self.puzzle.unset_value(shape_idx, other_r)

        # try setting this row to 1
        # this assumes all rows below have already been set to 1
        if self.puzzle.can_set_value(shape_idx, r, 1):
            self.puzzle.set_value(shape_idx, r, 1)
            res += self._solve(shape_idx, height_idx + 1)
            self.puzzle.unset_value(shape_idx, r)

        return res
