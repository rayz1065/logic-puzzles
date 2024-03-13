from collections import namedtuple
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils, ARROWS

DIRECTION_ARROW = {value: key for key, value in ARROWS.items()}


class StitchesPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    links: list[int | None]  # link_id -> present
    found_by_row: dict[tuple[int, int], int]  # r, value -> frequency
    found_by_col: dict[tuple[int, int], int]  # c, value -> frequency
    found_by_region: dict[tuple[int, int], int]  # region, value -> frequency
    found_by_region_pairs: dict[
        tuple[tuple[int, int], int], int
    ]  # a, b, value -> frequency
    used_holes: dict[tuple[int, int], int]  # r, c -> link_id

    def __init__(
        self,
        grid,
        links,
        found_by_row,
        found_by_col,
        found_by_region,
        found_by_region_pairs,
        used_holes,
    ):
        self.grid = grid
        self.links = links
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.found_by_region = found_by_region
        self.found_by_region_pairs = found_by_region_pairs
        self.used_holes = used_holes


class StitchesLink(namedtuple("StitchesLink", ["cells", "regions"])):
    pass


class StitchesPuzzle(Puzzle):
    initial_grid: list[list[str]]
    target_by_row: list[int]
    target_by_col: list[int]
    target_by_region: dict[str, int]
    state: StitchesPuzzleState
    grid_utils: GridUtils
    links_by_cell: dict[tuple[int, int], list[int]]  # cell -> link ids
    regions: dict[str, list[tuple[int, int]]]  # region -> cells
    links: list[StitchesLink]
    neighbors_by_region: dict[
        str, dict[str, list[int]]
    ]  # region -> neighboring region -> link ids
    stitches_by_regions_pair: int

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.strip().split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]

        target_by_col = [int(x) for x in lines.pop(0)]
        target_by_row = [int(x[0]) for x in lines]
        initial_grid = [row[1:] for row in lines]

        return cls(initial_grid, target_by_row, target_by_col)

    def __init__(self, initial_grid, target_by_row, target_by_col, state=None):
        self.initial_grid = initial_grid
        self.target_by_row = target_by_row
        self.target_by_col = target_by_col
        self.state = state

        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))

        self.links_by_cell = {(r, c): [] for r, c in self.grid_utils.iter_grid()}
        self.regions = {}
        for r, c in self.grid_utils.iter_grid():
            region = self.initial_grid[r][c]
            self.regions.setdefault(region, []).append((r, c))

        link_locations = [
            ((r, c), (r, c + 1))
            for r in range(self.grid_utils.rows)
            for c in range(self.grid_utils.cols - 1)
        ] + [
            ((r, c), (r + 1, c))
            for r in range(self.grid_utils.rows - 1)
            for c in range(self.grid_utils.cols)
        ]

        self.links = []
        self.neighbors_by_region = {}

        for cells in link_locations:
            regions = tuple(sorted(self.initial_grid[r][c] for r, c in cells))
            if len(set(regions)) == 2:
                link = StitchesLink(cells=cells, regions=regions)
                link_id = len(self.links)
                self.links.append(link)

                self.neighbors_by_region.setdefault(regions[0], dict()).setdefault(
                    regions[1], []
                ).append(link_id)
                self.neighbors_by_region.setdefault(regions[1], dict()).setdefault(
                    regions[0], []
                ).append(link_id)

                self.links_by_cell[cells[0]].append(link_id)
                self.links_by_cell[cells[1]].append(link_id)

        total_links = sum(self.target_by_row) // 2
        total_neighbors = sum(len(x) for x in self.neighbors_by_region.values()) // 2
        if total_links % total_neighbors != 0:
            raise ValueError("total_links is not a multiple of total_neighbors")

        self.stitches_by_regions_pair = total_links // total_neighbors

        self.target_by_region = {
            region: len(self.neighbors_by_region[region])
            * self.stitches_by_regions_pair
            for region in self.neighbors_by_region.keys()
        }

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "_"
            if self.state.grid[r][c] == 0:
                return "."
            if self.state.used_holes[r, c] is None:
                return "o"

            link = self.links[self.state.used_holes[r, c]]
            other_r, other_c = (
                link.cells[0] if (r, c) != link.cells[0] else link.cells[1]
            )
            direction = (other_r - r, other_c - c)
            return DIRECTION_ARROW[direction]

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(self.grid_utils.cols))
            for r in range(self.grid_utils.rows)
        )

    def initialize_state(self):
        region_pairs = set(link.regions for link in self.links)

        self.state = StitchesPuzzleState(
            grid=[[None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            links={link_id: None for link_id, _ in enumerate(self.links)},
            found_by_row={
                (r, value): 0 for r in range(self.grid_utils.rows) for value in range(2)
            },
            found_by_col={
                (c, value): 0 for c in range(self.grid_utils.cols) for value in range(2)
            },
            found_by_region={
                (region, value): 0
                for region in self.regions.keys()
                for value in range(2)
            },
            found_by_region_pairs={
                ((region_a, region_b), value): 0
                for region_a, region_b in region_pairs
                for value in range(2)
            },
            used_holes={
                (r, c): None
                for r in range(self.grid_utils.rows)
                for c in range(self.grid_utils.cols)
            },
        )

    def iter_values(self):
        yield from (0, 1)

    def iter_locations(self):
        for coords in self.grid_utils.iter_grid():
            yield ("cell", coords)

        for link_id, _ in enumerate(self.links):
            yield ("link", link_id)

    def can_set_link(self, link_id, value):
        link = self.links[link_id]
        cells = link.cells
        regions = link.regions

        if value == 1:
            # check that these regions are not already linked enough times
            if (
                self.state.found_by_region_pairs[regions, 1] + 1
                > self.stitches_by_regions_pair
            ):
                return False

            # check that the holes aren't marked as absent
            if any(self.state.grid[r][c] == 0 for r, c in cells):
                return False

            # check that none of the holes is used
            if any(self.state.used_holes[r, c] is not None for r, c in cells):
                return False

        if value == 0:
            region_a, region_b = regions
            # check that we are not throwing out the last available link
            if (
                self.state.found_by_region_pairs[regions, 0] + 1
                > len(self.neighbors_by_region[region_a][region_b])
                - self.stitches_by_regions_pair
            ):
                return False

            # check that this link is not required by one of the two cells
            if any(
                self.state.grid[r][c] == 1
                and self.get_available_links(r, c) == [link_id]
                for r, c in cells
            ):
                return False

        return True

    def get_available_links(self, r, c):
        if self.state.used_holes[r, c] is not None:
            return [self.state.used_holes[r, c]]

        res = []
        for link_id in self.links_by_cell[r, c]:
            link = self.links[link_id]
            other_r, other_c = (
                link.cells[0] if (r, c) != link.cells[0] else link.cells[1]
            )
            if (
                self.state.grid[other_r][other_c] != 0
                and self.state.links[link_id] is None
            ):
                res.append(link_id)

        return res

    def can_set_grid(self, r, c, value):
        # check that this hole is not required
        if value == 0 and self.state.used_holes[r, c] is not None:
            return False

        if value == 1 and self.state.used_holes[r, c] is None:
            # check that a link is available for this cell
            available_neighbors = self.get_available_links(r, c)
            if len(available_neighbors) == 0:
                return False

        # check that the bounds are still satisfied
        self.set_value(("cell", (r, c)), value)

        region = self.initial_grid[r][c]
        BOUNDS = [
            (
                self.state.found_by_row[r, 1],
                self.state.found_by_row[r, 0],
                self.target_by_row[r],
                self.grid_utils.cols,
            ),
            (
                self.state.found_by_col[c, 1],
                self.state.found_by_col[c, 0],
                self.target_by_col[c],
                self.grid_utils.rows,
            ),
            (
                self.state.found_by_region[region, 1],
                self.state.found_by_region[region, 0],
                self.target_by_region[region],
                len(self.regions[region]),
            ),
        ]

        def _check_bounds(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return 0 <= missing <= available

        res = all(
            _check_bounds(found, empty, target, total)
            for found, empty, target, total in BOUNDS
        )

        self.unset_value(("cell", (r, c)))

        return res

    def can_set(self, location, value):
        location_type, location_data = location
        if location_type == "link":
            return self.can_set_link(location_data, value)

        r, c = location_data
        return self.can_set_grid(r, c, value)

    def get_value(self, location):
        location_type, location_data = location
        if location_type == "link":
            link_id = location_data
            return self.state.links[link_id]

        r, c = location_data
        return self.state.grid[r][c]

    def _update_link(self, link_id, value, delta):
        link = self.links[link_id]
        self.state.found_by_region_pairs[link.regions, value] += delta

    def set_link(self, link_id, value):
        assert self.state.links[link_id] is None
        self.state.links[link_id] = value
        if value == 1:
            link = self.links[link_id]
            for r, c in link.cells:
                self.state.used_holes[r, c] = link_id

        self._update_link(link_id, value, 1)

    def unset_link(self, link_id):
        value = self.state.links[link_id]
        assert value is not None
        self.state.links[link_id] = None
        if value == 1:
            link = self.links[link_id]
            for r, c in link.cells:
                self.state.used_holes[r, c] = None

        self._update_link(link_id, value, -1)

    def _update_cell(self, r, c, value, delta):
        region = self.initial_grid[r][c]
        self.state.found_by_row[r, value] += delta
        self.state.found_by_col[c, value] += delta
        self.state.found_by_region[region, value] += delta

    def set_cell(self, r, c, value):
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_cell(r, c, value, 1)

    def unset_cell(self, r, c):
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_cell(r, c, value, -1)

    def set_value(self, location, value):
        location_type, location_data = location
        if location_type == "link":
            self.set_link(location_data, value)
        else:
            r, c = location_data
            self.set_cell(r, c, value)

    def unset_value(self, location):
        location_type, location_data = location
        if location_type == "link":
            self.unset_link(location_data)
        else:
            r, c = location_data
            self.unset_cell(r, c)
