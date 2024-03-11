import random
from functools import cache


@cache
def _compute_vision_bound(
    buildings, all_available_heights, compute_upper=True, max_height=-1
):
    """all_available_heights is a tuple where each element corresponds
    to a cell. Each such value is a tuple of booleans where each element is
    True if the corresponding height is available for the cell.
    """
    if not buildings:
        return 0

    current = buildings[0]
    other_buildings = buildings[1:]

    if current is not None:
        new_max_height = max(max_height, current)
        new_available_heights = all_available_heights[1:]
        res = _compute_vision_bound(
            other_buildings,
            new_available_heights,
            compute_upper,
            new_max_height,
        )
        if res is None:
            return None

        return res + int(current > max_height)

    res = None
    for height, is_available in enumerate(all_available_heights[0]):
        if not is_available:
            continue

        new_available_heights = list(all_available_heights)
        for i, available_heights in enumerate(new_available_heights):
            new_available_heights[i] = list(available_heights)
            new_available_heights[i][height] = False
            new_available_heights[i] = tuple(new_available_heights[i])
        new_available_heights = tuple(new_available_heights[1:])

        new_max_height = max(max_height, height)

        new_res = _compute_vision_bound(
            other_buildings,
            new_available_heights,
            compute_upper,
            new_max_height,
        )

        if new_res is None:
            continue

        new_res += int(height > max_height)

        if res is None:
            res = new_res
        else:
            res = max(res, new_res) if compute_upper else min(res, new_res)

    return res


def normalize_buildings(buildings, available_heights):
    res = []
    available_heights_res = []
    max_height = -1
    for i, building in enumerate(buildings):
        max_height = max(max_height, i - 1)
        if building is None:
            res.append(None)
            available_heights_res.append(available_heights[i])
        elif building > max_height:
            max_height = building
            res.append(building)
            available_heights_res.append(available_heights[i])

    return tuple(res), tuple(available_heights_res)


def compute_vision_upper_bound(buildings, available):
    buildings, available = normalize_buildings(buildings, available)
    return _compute_vision_bound(buildings, available, True)


def compute_vision_lower_bound(buildings, available):
    buildings, available = normalize_buildings(buildings, available)
    return _compute_vision_bound(buildings, available, False)


def stringy_buildings(buildings):
    return " ".join(str(i) if i is not None else "." for i in buildings)


def _generate_tests(grid_size=6, count=100):
    tests = []
    for _ in range(count):
        test = []
        # don't pick the same number twice
        numbers = list(range(0, grid_size))
        random.shuffle(numbers)
        for _ in range(grid_size):
            if random.choice([True, False]):
                test.append(numbers.pop())
            else:
                test.append(None)

        available = tuple(
            tuple(i not in test for i in range(grid_size)) for _ in range(grid_size)
        )

        tests.append((tuple(test), available))

    return tests


def main():
    random.seed(1065)
    tests = _generate_tests(count=10000)
    for test, available in tests:
        print(
            stringy_buildings(test),
            "->",
            compute_vision_upper_bound(test, available),
            compute_vision_lower_bound(test, available),
        )


if __name__ == "__main__":
    main()
