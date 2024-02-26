from logic_puzzles.Puzzle import Puzzle, PuzzleState


class CommunicatingVesselsPuzzleState(PuzzleState):
    water: list[list[int]]

    def __init__(
        self, rows_missing, cols_missing, rows_available, cols_available, water
    ):
        self.rows_missing = rows_missing
        self.cols_missing = cols_missing
        self.rows_available = rows_available
        self.cols_available = cols_available
        self.water = water

    def copy(self):
        return CommunicatingVesselsPuzzleState(
            self.rows_missing.copy(),
            self.cols_missing.copy(),
            self.rows_available.copy(),
            self.cols_available.copy(),
            [row.copy() for row in self.water],
        )


class CommunicatingVesselShape:
    cells: list[tuple[int, int]]
    cells_by_height: dict[int, list[int]]

    def __init__(self, cells):
        # this assumes that there are no 'upside-down U' shapes
        # i.e. filling a higher cell always fills up all the lower ones
        self.cells = cells
        self.cells_by_height = {}
        for r, c in cells:
            self.cells_by_height.setdefault(r, []).append(c)

        self.heights = sorted(self.cells_by_height.keys(), key=lambda x: -x)


class CommunicatingVesselsPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Vasi+comunicanti"""

    state: CommunicatingVesselsPuzzleState
    rows: list[int]
    cols: list[int]
    grid: list[list[int]]
    shapes: list[CommunicatingVesselShape]

    def __init__(self, grid, rows, cols, state=None):
        self.grid = grid
        self.rows = rows
        self.cols = cols
        shape_cells = {}
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                shape_cells.setdefault(cell, []).append((r, c))

        self.shapes = []
        for cells in shape_cells.values():
            self.shapes.append(CommunicatingVesselShape(cells))

        if state is None:
            water = [[None for _ in row] for row in grid]
            rows_missing = rows.copy()
            cols_missing = cols.copy()
            rows_available = [len(cols)] * len(rows)
            cols_available = [len(rows)] * len(cols)
            state = CommunicatingVesselsPuzzleState(
                rows_missing, cols_missing, rows_available, cols_available, water
            )

        self.state = state

    @classmethod
    def from_string(cls, string):
        def parse_entry(entry):
            return None if entry == "." else int(entry)

        lines = [x.strip().split() for x in string.split("\n") if x]
        cols = list(map(parse_entry, lines[0]))
        rows = [parse_entry(lines[i][0]) for i in range(1, len(lines))]
        grid = [[parse_entry(x) for x in line[1:]] for line in lines[1:]]

        return cls(grid, rows, cols)

    def __str__(self):
        def stringify_entry(entry):
            return "." if entry is None else str(entry)

        res = []
        res.append("  " + " ".join(stringify_entry(x) for x in self.cols))
        for i, row in enumerate(self.grid):
            res.append(
                stringify_entry(self.rows[i])
                + " "
                + " ".join("." if x is None else str(x) for x in row)
            )

        res.append("  " + " ".join(stringify_entry(x) for x in self.state.cols_missing))
        for i, row in enumerate(self.state.water):
            res.append(
                stringify_entry(self.state.rows_missing[i])
                + " "
                + " ".join("O" if x else "." for x in self.state.water[i])
            )

        return "\n".join(res)

    def copy(self):
        return CommunicatingVesselsPuzzle(
            self.grid, self.rows, self.cols, self.state.copy()
        )

    def _can_set_value(self, missing, available, count, value):
        if missing is None:
            return True

        available -= count
        missing -= count * value

        return available >= missing >= 0

    def can_set_value(self, shape_idx, r, value):
        """NOTE: does not check rows above or below"""
        shape = self.shapes[shape_idx]

        if not self._can_set_value(
            self.state.rows_missing[r],
            self.state.rows_available[r],
            len(shape.cells_by_height[r]),
            value,
        ):
            return False

        for c in shape.cells_by_height[r]:
            if not self._can_set_value(
                self.state.cols_missing[c],
                self.state.cols_available[c],
                1,
                value,
            ):
                return False

        return True

    def _update_value(self, shape_idx, r, value, delta):
        shape = self.shapes[shape_idx]

        for c in shape.cells_by_height[r]:
            if self.state.rows_missing[r] is not None:
                self.state.rows_missing[r] -= delta * value
                self.state.rows_available[r] -= delta

            if self.state.cols_missing[c] is not None:
                self.state.cols_missing[c] -= delta * value
                self.state.cols_available[c] -= delta

    def set_value(self, shape_idx, r, value):
        shape = self.shapes[shape_idx]
        for c in shape.cells_by_height[r]:
            self.state.water[r][c] = value

        self._update_value(shape_idx, r, value, 1)

    def unset_value(self, shape_idx, r):
        shape = self.shapes[shape_idx]
        for c in shape.cells_by_height[r]:
            value = self.state.water[r][c]
            self.state.water[r][c] = None

        self._update_value(shape_idx, r, value, -1)
