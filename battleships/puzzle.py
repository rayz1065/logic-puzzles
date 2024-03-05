from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import (
    ORTHOGONAL_DIRECTIONS,
    ALL_DIRECTIONS,
    ARROWS,
    GridUtils,
)

# Indicates the available directions to expand a boat
BOAT_SHAPES = {
    "o": [],
    "+": ORTHOGONAL_DIRECTIONS,
}
BOAT_SHAPES.update(((arrow, [(-dr, -dc)]) for arrow, (dr, dc) in ARROWS.items()))


class BattleshipsPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    row_cells_by_value: list[int]
    col_cells_by_value: list[int]
    found_boats: list[int]
    complete_boats: list[int]
    boat_locations: dict[
        tuple[int, int, int, tuple[int, int]], int
    ]  # (boat_size, r, c, direction) -> conflicts
    boat_available_locations_count: list[int]

    def __init__(
        self,
        grid,
        row_cells_by_value,
        col_cells_by_value,
        found_boats,
        complete_boats,
        boat_locations,
        boat_available_locations_count,
    ):
        self.grid = grid
        self.row_cells_by_value = row_cells_by_value
        self.col_cells_by_value = col_cells_by_value
        self.found_boats = found_boats
        self.complete_boats = complete_boats
        self.boat_locations = boat_locations
        self.boat_available_locations_count = boat_available_locations_count


class BattleshipsPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Battaglia+navale"""

    boats: list[int]
    row_counts: list[int]
    col_counts: list[int]
    initial_grid: list[list[str]]
    state: BattleshipsPuzzleState

    @classmethod
    def from_string(self, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        raw_boats = [int(x) for x in lines[0]]
        boats = [0] * (max(raw_boats) + 1)
        for boat in raw_boats:
            boats[boat] += 1
        col_counts = [int(x) for x in lines[1]]
        row_counts = [int(x[0]) for x in lines[2:]]
        initial_grid = [[x.lower() for x in line[1:]] for line in lines[2:]]

        return BattleshipsPuzzle(boats, col_counts, row_counts, initial_grid)

    def __init__(self, boats, col_counts, row_counts, initial_grid, state=None):
        self.boats = boats
        self.col_counts = col_counts
        self.row_counts = row_counts
        self.initial_grid = initial_grid
        self.state = state
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "."
            if not self.state.grid[r][c]:
                return "x" if self.initial_grid[r][c] == "x" else "/"
            if self.initial_grid[r][c] in BOAT_SHAPES:
                return self.initial_grid[r][c]
            return "O"

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(self.grid_utils.cols))
            for r in range(self.grid_utils.rows)
        )

    def initialize_state(self):
        def get_available_spaces(r, c, dr, dc):
            if dr == 0:
                return self.row_counts[r]
            return self.col_counts[c]

        boat_locations = {}
        boat_available_locations_count = [0] * max(
            self.grid_utils.rows, self.grid_utils.cols
        )
        for r, c in self.grid_utils.iter_grid():
            for boat_size in range(1, self.max_boat_size + 1):
                for dr, dc in [(0, 1), (1, 0)]:
                    end_r, end_c = r + (boat_size - 1) * dr, c + (boat_size - 1) * dc
                    is_valid = (
                        self.grid_utils.in_range(end_r, end_c)
                        # TODO: ideally this could be updated as boats are placed and available spaces are reduced
                        and get_available_spaces(r, c, dr, dc) >= boat_size
                    )
                    boat_locations[(boat_size, r, c, (dr, dc))] = 1 - int(is_valid)
                    boat_available_locations_count[boat_size] += int(is_valid)

        self.state = BattleshipsPuzzleState(
            grid=[[None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            row_cells_by_value=([0] * self.grid_utils.rows, [0] * self.grid_utils.rows),
            col_cells_by_value=([0] * self.grid_utils.cols, [0] * self.grid_utils.cols),
            found_boats=[0] * max(self.grid_utils.rows, self.grid_utils.cols),
            complete_boats=[0] * max(self.grid_utils.rows, self.grid_utils.cols),
            boat_locations=boat_locations,
            boat_available_locations_count=boat_available_locations_count,
        )

        for r, c in self.grid_utils.iter_grid():
            cell_type = self.initial_grid[r][c]
            if cell_type == ".":
                continue
            if cell_type == "x":
                if self.state.grid[r][c] is None:
                    self.set_value((r, c), 0)
                continue

            if self.state.grid[r][c] is None:
                self.set_value((r, c), 1)

            if len(BOAT_SHAPES[cell_type]) == 1:
                dr, dc = BOAT_SHAPES[cell_type][0]
                new_r, new_c = r + dr, c + dc

                if self.state.grid[new_r][new_c] is None:
                    self.set_value((new_r, new_c), 1)

            invalid_directions = set(ALL_DIRECTIONS) - set(BOAT_SHAPES[cell_type])
            for new_r, new_c in self.grid_utils.directions_iter(
                r, c, invalid_directions, 1
            ):
                if self.state.grid[new_r][new_c] is None:
                    self.set_value((new_r, new_c), 0)

    @property
    def max_boat_size(self):
        return len(self.boats) - 1

    def get_valid_values(self, location):
        return [value for value in (0, 1) if self.can_set(location, value)]

    def can_set(self, location, value):
        r, c = location
        if value == 1:
            # no cell diagonal from this one can contain a boat
            for new_r, new_c in self.grid_utils.diagonal_iter(r, c, 1):
                if self.state.grid[new_r][new_c] == 1:
                    return False

            # check if the newly created boat is too large
            old_boat_sizes = [len(x) for x in self.get_boats_around(r, c)]
            new_boat_size = sum(old_boat_sizes) + 1
            if new_boat_size > self.max_boat_size:
                return False

            # if we have already placed all the boats,
            # check that we have the right number of boats for each size
            new_found_boats = self.state.found_boats[:]
            new_found_boats[new_boat_size] += 1
            for length in old_boat_sizes:
                new_found_boats[length] -= 1

            current_boat_count = sum(x * i for i, x in enumerate(new_found_boats))
            target_boat_count = sum(x * i for i, x in enumerate(self.boats))

            if current_boat_count == target_boat_count and not all(
                x == y for x, y in zip(new_found_boats, self.boats)
            ):
                return False

            if new_boat_size > self.max_boat_size // 2:
                # sizes of boats cannot shrink,
                # boats of these size cannot be merged into larger boats
                # we can check that for every size there
                # are not too many boats of size [size, size + 1, ...]
                # this is guaranteed by induction for new_boat_size + 1
                target_acc = sum(self.boats[new_boat_size:])
                current_acc = sum(new_found_boats[new_boat_size:])

                if current_acc > target_acc:
                    return False
        else:
            # check that we are not locking a + boat to only one direction
            for dr, dc in ORTHOGONAL_DIRECTIONS:
                new_r, new_c = r + dr, c + dc
                if (
                    not self.grid_utils.in_range(new_r, new_c)
                    or self.initial_grid[new_r][new_c] != "+"
                ):
                    continue

                boat = self.get_boat(new_r, new_c)
                if (r + 2 * dr, c + 2 * dc) in boat:
                    # state: ?+> with ? being the current cell
                    # this cell must also be 1
                    return False

                dr, dc = dc, dr
                for distance in (-1, 1):
                    diag_r, diag_c = new_r + dr * distance, new_c + dc * distance
                    if (
                        not self.grid_utils.in_range(diag_r, diag_c)
                        or self.state.grid[diag_r][diag_c] == 0
                    ):
                        # state: ?+ with ? being the current cell
                        #         X
                        # the diagonal directions cannot host the boat,
                        # therefore this cell must be 1
                        return False

        # this stops AFTER the boat has already been set
        if any(x > y for x, y in zip(self.state.complete_boats, self.boats)):
            return False

        if any(
            x < y for x, y in zip(self.state.boat_available_locations_count, self.boats)
        ):
            return False

        new_row_cells_by_value = [x[r] for x in self.state.row_cells_by_value]
        new_col_cells_by_value = [x[c] for x in self.state.col_cells_by_value]
        new_row_cells_by_value[value] += 1
        new_col_cells_by_value[value] += 1

        bounds = [
            (
                new_col_cells_by_value[1],
                self.grid_utils.rows - new_col_cells_by_value[0],
                self.col_counts[c],
            ),
            (
                new_row_cells_by_value[1],
                self.grid_utils.cols - new_row_cells_by_value[0],
                self.row_counts[r],
            ),
        ]

        for lower, upper, target in bounds:
            if not (lower <= target <= upper):
                return False

        return True

    def get_boats_around(self, r, c):
        boats = []
        for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
            if self.state.grid[new_r][new_c] != 1:
                continue
            boats.append(self.get_boat(new_r, new_c))

        return boats

    def get_boat(self, r, c):
        if self.state.grid[r][c] != 1:
            return []

        for dr, dc in ((-1, 0), (0, -1)):
            while (
                self.grid_utils.in_range(r + dr, c + dc)
                and self.state.grid[r + dr][c + dc] == 1
            ):
                r, c = r + dr, c + dc

        res = [(r, c)]
        for dr, dc in ((1, 0), (0, 1)):
            while (
                self.grid_utils.in_range(r + dr, c + dc)
                and self.state.grid[r + dr][c + dc] == 1
            ):
                r, c = r + dr, c + dc
                res.append((r, c))

        return res

    def is_boat_complete(self, r, c):
        boat = self.get_boat(r, c)

        if len(boat) == 1:
            # a singular boat can be expanded in any direction
            expansion_areas = [(r + dr, c + dc) for dr, dc in ORTHOGONAL_DIRECTIONS]
        else:
            # check if the boat can be expanded at the front or at the back
            min_r, min_c = boat[0]
            max_r, max_c = boat[-1]
            dr = boat[1][0] - min_r
            dc = boat[1][1] - min_c

            expansion_areas = [
                (min_r - dr, min_c - dc),
                (max_r + dr, max_c + dc),
            ]

        return all(
            not self.grid_utils.in_range(new_r, new_c)
            or self.state.grid[new_r][new_c] == 0
            for new_r, new_c in expansion_areas
        )

    def _update_value(self, r, c, value, delta):
        self.state.row_cells_by_value[value][r] += delta
        self.state.col_cells_by_value[value][c] += delta

        if value == 1:
            return

        # check which boat locations are blocked off by this 0
        for dr, dc in [(1, 0), (0, 1)]:
            for distance in range(0, self.max_boat_size):
                new_r, new_c = r - dr * distance, c - dc * distance
                if not self.grid_utils.in_range(new_r, new_c):
                    break

                # any boat of size at least distance + 1 cannot be placed here
                for boat_size in range(distance + 1, self.max_boat_size + 1):
                    end_r, end_c = (
                        new_r + (boat_size - 1) * dr,
                        new_c + (boat_size - 1) * dc,
                    )
                    self.state.boat_locations[
                        (boat_size, new_r, new_c, (dr, dc))
                    ] += delta
                    if self.state.boat_locations[
                        (boat_size, new_r, new_c, (dr, dc))
                    ] in (0, delta):
                        self.state.boat_available_locations_count[boat_size] -= delta

    def _merge_boats(self, r, c, delta):
        lengths = [len(x) for x in self.get_boats_around(r, c)]
        for length in lengths:
            self.state.found_boats[length] -= delta
        self.state.found_boats[sum(lengths) + 1] += delta

    def set_value(self, location, value):
        r, c = location
        if value == 1:
            self._merge_boats(r, c, 1)
        else:
            incomplete_boats = [
                (new_r, new_c)
                for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1)
                if self.state.grid[new_r][new_c] == 1
                and not self.is_boat_complete(new_r, new_c)
            ]

        self.state.grid[r][c] = value
        self._update_value(r, c, value, 1)

        if value == 1:
            if self.is_boat_complete(r, c):
                # completed a boat by placing the last missing segment
                boat = self.get_boat(r, c)
                self.state.complete_boats[len(boat)] += 1
        else:
            for new_r, new_c in incomplete_boats:
                if self.is_boat_complete(new_r, new_c):
                    # completed a boat by placing water on the last side
                    boat = self.get_boat(new_r, new_c)
                    self.state.complete_boats[len(boat)] += 1

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]

        if value == 1:
            if self.is_boat_complete(r, c):
                # removed one of the pieces of a complete boat
                boat = self.get_boat(r, c)
                self.state.complete_boats[len(boat)] -= 1
        else:
            complete_boats = []
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
                if self.state.grid[new_r][new_c] == 1 and self.is_boat_complete(
                    new_r, new_c
                ):
                    complete_boats.append((new_r, new_c))

        self.state.grid[r][c] = None
        self._update_value(r, c, value, -1)

        if value == 0:
            for new_r, new_c in complete_boats:
                if not self.is_boat_complete(new_r, new_c):
                    # removed the water from the side of the boat
                    boat = self.get_boat(new_r, new_c)
                    self.state.complete_boats[len(boat)] -= 1

        if value == 1:
            self._merge_boats(r, c, -1)
