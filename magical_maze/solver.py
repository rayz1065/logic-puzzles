from puzzle import MagicalMazePuzzle, MAX_VALUE
from logic_puzzles.Solver import Solver
import sys


class MagicalMazeSolver(Solver):
    puzzle: MagicalMazePuzzle

    def _solve_dirty(
        self,
        dist,
        last_value,
        dirty: set[tuple[int, int]],
    ):
        """Before trying the normal branching strategy, try to fill the dirty cells"""
        self.check_timeout()

        while len(dirty) > 0:
            r, c = dirty.pop()

            # if the cell is not filled we can try to fill it
            if self.state.values[r][c] is None:
                break

        if len(dirty) == 0:
            return self._solve(dist, last_value)

        available_values = self.puzzle.get_available_values(r, c)

        # no available values, we must have made a mistake
        if len(available_values) == 0:
            return 0

        # check if a branch is necessary on this cell
        if len(available_values) > 1:
            return self._solve_dirty(dist, last_value, dirty)

        # no branch is necessary
        value = available_values[0]
        dirty.update(self.puzzle.set_value(r, c, value))
        res = self._solve_dirty(dist, last_value, dirty)
        self.puzzle.unset_value(r, c)

        return res

    def _solve(self, dist=0, last_value=0):
        self.check_timeout()

        if dist == self.puzzle.grid_size**2:
            self.store_solution()
            return 1

        r, c = self.puzzle.locations[dist]
        value = (last_value % MAX_VALUE) + 1

        # check if the value present at the cell has already been filled in
        if self.state.values[r][c] is not None:
            if self.state.values[r][c] == 0:
                return self._solve(dist + 1, last_value)
            elif self.state.values[r][c] == value:
                return self._solve(dist + 1, value)
            return 0

        res = 0

        # try leaving the cell empty
        if not self.puzzle.must_fill_cell(r, c):
            dirty = self.puzzle.set_value(r, c, 0)
            res += self._solve_dirty(dist + 1, last_value, dirty)
            self.puzzle.unset_value(r, c)

        if self.state.conflict_values[r][c][value]:
            return res

        # fill the cell with the current value
        dirty = self.puzzle.set_value(r, c, value)
        res += self._solve_dirty(dist + 1, value, dirty)
        self.puzzle.unset_value(r, c)

        return res


def main():
    puzzle = MagicalMazePuzzle.from_file()
    solver = MagicalMazeSolver(puzzle, debug=False)
    solutions = solver.solve()

    print(f"Found {len(solutions)} solutions")
    for state in solutions:
        puzzle.set_state(state)
        print("-----------------")
        print(puzzle)


if __name__ == "__main__":
    main()
