from .puzzle import Puzzle, PuzzleState
import time
import random
from abc import ABC, abstractmethod


class SolverException(Exception):
    pass


class SolverTimeoutException(SolverException):
    pass


class SolverTargetReachedException(SolverException):
    pass


class Solver(ABC):
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

    @abstractmethod
    def _solve(self):
        raise NotImplementedError

    def store_solution(self):
        self.solutions.append(self.puzzle.state.copy())
        if self.debug:
            print(self.puzzle)

        if self.target_solutions is not None:
            if len(self.solutions) >= self.target_solutions:
                raise SolverTargetReachedException

    def _debug_init(self):
        print("Solving puzzle")
        print(self.puzzle)

    def _debug_complete(self):
        print(f"Found {len(self.solutions)} solutions")

    def solve(self):
        if self.debug:
            self._debug_init()

        try:
            self.solutions = []
            self.start_time = time.time()
            self._solve()
        except SolverTargetReachedException:
            pass

        if self.debug:
            self._debug_complete()

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


class SimpleBranchingSolver(Solver, ABC):
    @abstractmethod
    def get_branching_score(self, location):
        raise NotImplementedError

    @abstractmethod
    def _compute_dirty(self, location):
        raise NotImplementedError

    def is_location_set(self, location):
        return self.puzzle.get_value(location) is not None

    def _update_all_dirty(self, dirty):
        updated = set()

        while len(dirty) > 0:
            location = dirty.pop()
            if self.is_location_set(location):
                continue

            valid_values = self.puzzle.get_valid_values(location)
            if len(valid_values) == 0:
                # unset all the updated values and report the failure
                for location in updated:
                    self.puzzle.unset_value(location)
                return None

            if len(valid_values) > 1:
                continue

            value = valid_values[0]
            self.puzzle.set_value(location, value)
            dirty.update(self._compute_dirty(location))
            updated.add(location)

        return updated

    def _solve_dirty(self, dirty):
        self.check_timeout()

        updated = self._update_all_dirty(dirty)

        if updated is None:
            return 0

        res = self._branching_solve()
        for location in updated:
            self.puzzle.unset_value(location)

        return res

    def _solve_updates_map(self, to_update):
        updated = []
        dirty = set()

        res = 0
        for location, value in to_update.items():
            if not self.puzzle.can_set(location, value):
                break

            updated.append(location)
            self.puzzle.set_value(location, value)
            dirty.update(self._compute_dirty(location))
        else:
            res += self._solve_dirty(dirty)

        for location in updated:
            self.puzzle.unset_value(location)

        return res

    def _debug_branching(self, location):
        print(f"Branching at {location}")

    def _branching_solve(self):
        self.check_timeout()

        best_score, location = None, None
        for new_location in self.puzzle.iter_locations():
            if self.is_location_set(new_location):
                continue

            score = self.get_branching_score(new_location)
            if best_score is None or score > best_score:
                best_score, location = score, new_location

        if best_score is None:
            self.store_solution()
            return 1

        if self.debug:
            self._debug_branching(location)

        res = 0
        for value in self.branching_order(self.puzzle.get_valid_values(location)):
            self.puzzle.set_value(location, value)
            dirty = self._compute_dirty(location)
            res += self._solve_dirty(dirty)
            self.puzzle.unset_value(location)

        return res

    def _solve(self):
        dirty = set(self.puzzle.iter_locations())
        return self._solve_dirty(dirty)
