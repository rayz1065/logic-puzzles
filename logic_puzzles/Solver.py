from .Puzzle import Puzzle, PuzzleState
import time


class SolverException(Exception):
    pass

class SolverTimeoutException(SolverException):
    pass

class SolverTargetReachedException(SolverException):
    pass

class Solver:
    debug: bool
    puzzle: Puzzle
    target_solutions: int
    timeout_seconds: float
    solutions: list[PuzzleState]
    start_time: float

    def __init__(
        self, puzzle, debug=False, target_solutions=None, timeout_seconds=None
    ):
        self.puzzle = puzzle
        self.debug = debug
        self.target_solutions = target_solutions
        self.timeout_seconds = timeout_seconds
        self.solutions = None
        self.start_time = None

    @property
    def state(self):
        return self.puzzle.state

    def store_solution(self):
        self.solutions.append(self.puzzle.state.copy())
        if self.debug:
            print(self.puzzle)

        if self.target_solutions is not None:
            if len(self.solutions) >= self.target_solutions:
                raise SolverTargetReachedException

    def _solve(self):
        raise NotImplementedError

    def solve(self):
        if self.debug:
            print("Solving puzzle")
            print(self.puzzle)

        try:
            self.solutions = []
            self.start_time = time.time()
            self._solve()
        except SolverTargetReachedException:
            pass

        return self.solutions

    def check_timeout(self):
        if self.timeout_seconds is not None:
            if time.time() - self.start_time > self.timeout_seconds:
                raise SolverTimeoutException
