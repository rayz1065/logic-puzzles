from .puzzle import Puzzle, PuzzleState
import time
import random


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
    randomize_branching: bool

    def __init__(
        self,
        puzzle,
        debug=False,
        target_solutions=None,
        timeout_seconds=None,
        randomize_branching=False,
    ):
        self.puzzle = puzzle
        self.debug = debug
        self.target_solutions = target_solutions
        self.timeout_seconds = timeout_seconds
        self.randomize_branching = randomize_branching
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

        if self.debug:
            print(f"Found {len(self.solutions)} solutions")

        return self.solutions

    def check_timeout(self):
        if self.timeout_seconds is not None:
            if time.time() - self.start_time > self.timeout_seconds:
                raise SolverTimeoutException

    def branching_order(self, iterable):
        if self.randomize_branching:
            iterable = list(iterable)
            random.shuffle(iterable)

        return iterable

    def clear_solutions(self):
        self.solutions = None
        self.start_time = None

    def set_puzzle(self, puzzle):
        self.puzzle = puzzle
        self.clear_solutions()
