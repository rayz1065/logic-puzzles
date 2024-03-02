from itertools import product

ORTHOGONAL_DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
DIAGONAL_DIRECTIONS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ALL_DIRECTIONS = ORTHOGONAL_DIRECTIONS + DIAGONAL_DIRECTIONS
BENDS = {
    "|": [(1, 0), (-1, 0)],
    "-": [(0, 1), (0, -1)],
    "J": [(-1, 0), (0, -1)],
    "L": [(-1, 0), (0, 1)],
    "l": [(-1, 0), (0, 1)],
    "j": [(-1, 0), (0, -1)],
    "7": [(1, 0), (0, -1)],
    "F": [(1, 0), (0, 1)],
    "f": [(1, 0), (0, 1)],
}
WIND_ROSE = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
    "NE": (-1, 1),
    "NW": (-1, -1),
    "SE": (1, 1),
    "SW": (1, -1),
}
ARROWS = {
    "^": (-1, 0),
    ">": (0, 1),
    "v": (1, 0),
    "V": (1, 0),
    "<": (0, -1),
}


class GridUtils:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def in_range(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def ray_iter(self, r, c, dr, dc, max_distance=None):
        max_distance = max_distance or self.rows + self.cols
        for distance in range(max_distance + 1):
            new_r, new_c = r + dr * distance, c + dc * distance
            if not self.in_range(new_r, new_c):
                break
            yield new_r, new_c

    def directions_iter(self, r, c, directions, max_distance=None):
        for dr, dc in directions:
            yield from self.ray_iter(r, c, dr, dc, max_distance)

    def orthogonal_iter(self, r, c, max_distance=None):
        yield from self.directions_iter(r, c, ORTHOGONAL_DIRECTIONS, max_distance)

    def diagonal_iter(self, r, c, max_distance=None):
        yield from self.directions_iter(r, c, DIAGONAL_DIRECTIONS, max_distance)

    def all_directions_iter(self, r, c, max_distance=None):
        yield from self.directions_iter(r, c, ALL_DIRECTIONS, max_distance)

    def iter_grid(self):
        yield from product(range(self.rows), range(self.cols))
