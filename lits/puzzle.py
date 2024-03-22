from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils

SHAPES = {
    "I": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "L": ((0, 0), (0, 1), (0, 2), (1, 2)),
    "T": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "S": ((0, 0), (0, 1), (1, 1), (1, 2)),
}


def normalize_shape_position(cells):
    min_x = min(x for x, y in cells)
    min_y = min(y for x, y in cells)
    return tuple(sorted((x - min_x, y - min_y) for x, y in cells))


def rotate_shape(cells):
    return normalize_shape_position([(-y, x) for x, y in cells])


def mirror_shape(cells):
    return normalize_shape_position([(-x, y) for x, y in cells])


def get_all_shapes_orientations():
    found = set()
    for shape_type, cells in SHAPES.items():
        for _ in range(4):
            found.add((shape_type, cells))
            cells = rotate_shape(cells)
        cells = mirror_shape(cells)
        for _ in range(4):
            found.add((shape_type, cells))
            cells = rotate_shape(cells)

    return found


class LitsPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_region: dict[tuple[int, int], int]

    def __init__(self, grid, found_by_region):
        self.grid = grid
        self.found_by_region = found_by_region


class LitsPuzzle(Puzzle):
    regions_grid: list[list[str]]
    state: LitsPuzzleState
    grid_utils: GridUtils
    regions: dict[str, list[tuple[int, int]]]
    shapes_locations: list[tuple[str, tuple[tuple[int, int]]]]
    shapes_by_region: dict[str, list[tuple[str, tuple[tuple[int, int]]]]]
    shapes_by_cell: dict[tuple[int, int], list[tuple[str, tuple[tuple[int, int]]]]]
    state: LitsPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]

        return cls(lines)

    def __init__(self, regions_grid, state=None):
        self.regions_grid = regions_grid
        self.state = state
        self.grid_utils = GridUtils(len(regions_grid), len(regions_grid[0]))

        self.regions = {}
        for r, c in self.grid_utils.iter_grid():
            region = self.regions_grid[r][c]
            self.regions.setdefault(region, []).append((r, c))

        # precompute all of the possible shapes
        self.shapes_locations = []
        self.shapes_by_region = {region: [] for region in self.regions}
        for shape_type, cells in get_all_shapes_orientations():
            for r, c in self.grid_utils.iter_grid():
                translated_cells = tuple((r + dr, c + dc) for dr, dc in cells)
                base_r, base_c = translated_cells[0]
                if not self.grid_utils.in_range(base_r, base_c):
                    continue

                region = self.regions_grid[base_r][base_c]
                if any(
                    not self.grid_utils.in_range(new_r, new_c)
                    or self.regions_grid[new_r][new_c] != region
                    for new_r, new_c in translated_cells
                ):
                    continue

                self.shapes_locations.append((shape_type, translated_cells))
                self.shapes_by_region[region].append((shape_type, translated_cells))

        self.shapes_by_cell = {(r, c): [] for r, c in self.grid_utils.iter_grid()}
        for shape_type, cells in self.shapes_locations:
            for cell in cells:
                self.shapes_by_cell[cell].append((shape_type, cells))

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "_"
            if not self.state.grid[r][c]:
                return "."
            shape = self.get_shape_at(r, c)
            return "O" if shape is None else shape[0]

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(self.grid_utils.cols))
            for r in range(self.grid_utils.rows)
        )

    def initialize_state(self):
        self.state = LitsPuzzleState(
            grid=[
                [None for _ in range(self.grid_utils.cols)]
                for _ in range(self.grid_utils.rows)
            ],
            found_by_region={
                (region, value): 0
                for region in self.regions
                for value in self.iter_values()
            },
        )

    def iter_values(self):
        yield from (0, 1)

    def iter_locations(self):
        yield from self.grid_utils.iter_grid()

    def count_pieces_by_cells(self, cells):
        empty_cells = 0
        full_cells = 0
        for r, c in cells:
            if self.state.grid[r][c] == 0:
                empty_cells += 1
            elif self.state.grid[r][c] == 1:
                full_cells += self.state.grid[r][c]

        return empty_cells, full_cells

    def get_value(self, location):
        r, c = location
        return self.state.grid[r][c]

    def count_cells_in_square(self, top_left_r, top_left_c):
        if not self.grid_utils.in_range(
            top_left_r, top_left_c
        ) or not self.grid_utils.in_range(top_left_r + 1, top_left_c + 1):
            return 0

        return sum(
            int(self.state.grid[r][c] == 1)
            for r in range(top_left_r, top_left_r + 2)
            for c in range(top_left_c, top_left_c + 2)
        )

    def get_shape_at(self, r, c):
        if self.state.grid[r][c] != 1:
            return None

        return next(
            iter(
                shape
                for shape in self.shapes_by_cell[r, c]
                if self.count_pieces_by_cells(shape[1]) == (0, 4)
            ),
            None,
        )

    def get_adjacent_cells(self, shape):
        _, cells = shape
        base_r, base_c = cells[0]
        region = self.regions_grid[base_r][base_c]
        return set(
            (new_r, new_c)
            for r, c in cells
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1)
            if self.regions_grid[new_r][new_c] != region
        )

    def check_shape_clashes(self, shape):
        shape_type, _ = shape
        adjacent_cells = self.get_adjacent_cells(shape)

        # check that the shape is not adjacent to another shape of the same type
        for r, c in adjacent_cells:
            other_shape = self.get_shape_at(r, c)
            if other_shape is not None and other_shape[0] == shape_type:
                return False

        # check that the shape is not isolated
        if all(self.state.grid[r][c] == 0 for r, c in adjacent_cells):
            return False

        return True

    def get_connected_component(self, r, c):
        visited = set([(r, c)])
        stack = [(r, c)]
        while stack:
            r, c = stack.pop()
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
                if (new_r, new_c) in visited or self.state.grid[new_r][new_c] == 0:
                    continue
                visited.add((new_r, new_c))
                stack.append((new_r, new_c))

        return visited

    def can_set(self, location, value):
        r, c = location
        region = self.regions_grid[r][c]
        if value == 1:
            # check that no square is caused by this cell
            if any(
                self.count_cells_in_square(new_r, new_c) >= 3
                for new_r in range(r - 1, r + 1)
                for new_c in range(c - 1, c + 1)
            ):
                return False

            # check that we are not placing too many cells in this region
            if self.state.found_by_region[region, 1] >= 4:
                return False

            # check that this contributes to a potential shape
            expected_full_cells = self.state.found_by_region[region, 1]
            candidate_shape = None
            candidates_count = 0
            for shape in self.shapes_by_cell[r, c]:
                empty_cells, full_cells = self.count_pieces_by_cells(shape[1])
                if empty_cells == 0 and full_cells == expected_full_cells:
                    candidate_shape = shape
                    candidates_count += 1
                    if candidates_count > 1:
                        break

            if candidates_count == 0:
                return False

            if candidates_count == 1 and not self.check_shape_clashes(candidate_shape):
                return False

            return True

        # check that we are not removing too many cells
        potential_cells = (
            len(self.regions[region]) - self.state.found_by_region[region, 0] - 1
        )
        if potential_cells < 4:
            return False

        for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
            shape = self.get_shape_at(new_r, new_c)
            if shape is None:
                continue

            # check that we are not isolating the shape
            adjacent = self.get_adjacent_cells(shape)
            if all(
                self.state.grid[r_][c_] == 0 or (r_, c_) == (r, c)
                for r_, c_ in adjacent
            ):
                return False

        return True

    def _update_value(self, location, value, delta):
        r, c = location
        region = self.regions_grid[r][c]
        self.state.found_by_region[region, value] += delta

    def set_value(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_value(location, value, 1)

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_value(location, value, -1)
