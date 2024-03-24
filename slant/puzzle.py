from itertools import product
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils, STRAIGHT_LINES
from logic_puzzles.constraints import CountConstraint


class SlantPuzzleState(PuzzleState):
    grid: list[list[str | None]]
    found_by_intersection: dict[tuple[int, int, int], int]

    def __init__(self, grid, found_by_intersection):
        self.grid = grid
        self.found_by_intersection = found_by_intersection


class SlantPuzzle(Puzzle):
    intersections: list[list[int | None]]
    state: SlantPuzzleState
    grid_utils: GridUtils
    numbered_intersections: list[tuple[int, int]]
    intersections_by_cell: dict[tuple[int, int], list[tuple[int, int, str]]]
    intersections_constraints: dict[tuple[int, int], CountConstraint]

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        intersections = [
            [int(cell) if cell.isdigit() else None for cell in line] for line in lines
        ]
        return cls(intersections)

    def __init__(self, intersections, state=None):
        self.intersections = intersections
        self.state = state
        self.grid_utils = GridUtils(
            len(self.intersections) - 1, len(self.intersections[0]) - 1
        )
        self.numbered_intersections = [
            (r, c)
            for r in range(self.grid_utils.rows + 1)
            for c in range(self.grid_utils.cols + 1)
            if self.intersections[r][c] is not None
        ]
        self.intersections_by_cell = {
            (r, c): [] for r, c in self.grid_utils.iter_grid()
        }
        self.intersections_constraints = {}
        for r, c in self.numbered_intersections:
            neighbors = 0

            for dr, dc in product(range(-1, 1), repeat=2):
                new_r, new_c = r + dr, c + dc
                if not self.grid_utils.in_range(new_r, new_c):
                    continue

                slant = "\\" if dr == dc else "/"
                self.intersections_by_cell[new_r, new_c].append((r, c, slant))
                neighbors += 1

            self.intersections_constraints[r, c] = CountConstraint(
                self.intersections[r][c], neighbors
            )

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_intersection(cell):
            return str(cell) if cell is not None else "."

        def stringify_cell(cell):
            return cell if cell is not None else "_"

        lines = []
        for r in range(self.grid_utils.rows + 1):
            lines.append(" ".join(map(stringify_intersection, self.intersections[r])))
            if r < self.grid_utils.rows:
                lines.append(" " + " ".join(map(stringify_cell, self.state.grid[r])))
        return "\n".join(lines)

    def initialize_state(self):
        self.state = SlantPuzzleState(
            grid=[[None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            found_by_intersection={
                (r, c, value): 0
                for r, c in self.numbered_intersections
                for value in (0, 1)
            },
        )

    def iter_locations(self):
        yield from self.grid_utils.iter_grid()

    def iter_values(self):
        yield from ("/", "\\")

    def can_set(self, location, value):
        r, c = location

        res = True
        self.set_value(location, value)

        for new_r, new_c, _ in self.intersections_by_cell[r, c]:
            if not self.intersections_constraints[new_r, new_c].check(
                self.state.found_by_intersection[new_r, new_c, 1],
                self.state.found_by_intersection[new_r, new_c, 0],
            ):
                res = False
                break

        if res and self.find_cycle(r, c, max_distance=5)[0]:
            res = False

        self.unset_value(location)

        return res

    def get_value(self, location):
        r, c = location
        return self.state.grid[r][c]

    def _update_value(self, r, c, value, delta):
        for new_r, new_c, slant in self.intersections_by_cell[r, c]:
            new_value = 1 if slant == value else 0
            self.state.found_by_intersection[new_r, new_c, new_value] += delta

    def set_value(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_value(r, c, value, 1)

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_value(r, c, value, -1)

    def adjacent_intersections(self, r, c):
        """(r, c) are the coordinates of an intersection"""
        for dr, dc in product(range(-1, 1), repeat=2):
            cell_r, cell_c = r + dr, c + dc
            if not self.grid_utils.in_range(cell_r, cell_c):
                continue

            slant = "\\" if dr == dc else "/"
            new_r, new_c = cell_r + dr + 1, cell_c + dc + 1
            yield cell_r, cell_c, new_r, new_c, slant

    def find_cycle(self, r, c, max_distance=None):
        """(r, c) are the coordinates of an intersection"""
        stack = [(r, c)]
        parents = {(r, c): None}
        distances = {(r, c): 0}

        while stack:
            r, c = stack.pop()
            parent = parents[r, c]
            distance = distances[r, c]

            for cell_r, cell_c, new_r, new_c, slant in self.adjacent_intersections(
                r, c
            ):
                if self.state.grid[cell_r][cell_c] != slant:
                    continue

                if (new_r, new_c) == parent:
                    continue

                if (new_r, new_c) in parents:
                    return True, parents

                parents[new_r, new_c] = (r, c)
                distances[new_r, new_c] = distances[r, c] + 1
                if max_distance is not None and distances[new_r, new_c] > max_distance:
                    continue

                stack.append((new_r, new_c))

        return False, parents

    def check_no_cycles(self):
        visited = set()

        for r, row in enumerate(self.intersections):
            for c, _ in enumerate(row):
                if (r, c) in visited:
                    continue

                found, new_visited = self.find_cycle(r, c)
                if found:
                    return False

                visited.update(new_visited)

        return True
