from logic_puzzles.solver import Solver


class BlackArrowsSolver(Solver):
    def _solve(self, r=0, c=0):
        if c == self.puzzle.grid_size:
            c = 0
            r += 1
            if r == self.puzzle.grid_size:
                self.store_solution()
                return 1

        res = 0

        for value in (0, 1):
            if self.puzzle.can_mark(r, c, value):
                self.puzzle.set_mark(r, c, value)
                res += self._solve(r, c + 1)
                self.puzzle.unset_mark(r, c)

        return res
