import random
from functools import cache


@cache
def _compute_vision_bound(
    buildings, available_heights, compute_upper=True, max_height=-1
):
    if not buildings:
        return 0

    current = buildings[0]
    other_buildings = buildings[1:]

    if current is not None:
        new_max_height = max(max_height, current)
        return int(current > max_height) + _compute_vision_bound(
            other_buildings, available_heights, compute_upper, new_max_height
        )

    res = None
    for height, is_available in enumerate(available_heights):
        if not is_available:
            continue

        new_available = list(available_heights)
        new_available[height] = False
        new_max_height = max(max_height, height)
        new_res = int(height > max_height) + _compute_vision_bound(
            other_buildings, tuple(new_available), compute_upper, new_max_height
        )

        if res is None:
            res = new_res
        else:
            res = max(res, new_res) if compute_upper else min(res, new_res)

    return res


def normalize_buildings(buildings):
    res = []
    max_height = -1
    for i, building in enumerate(buildings):
        max_height = max(max_height, i - 1)
        if building is None:
            res.append(None)
        elif building > max_height:
            max_height = building
            res.append(building)

    return tuple(res)


def compute_vision_upper_bound(buildings):
    grid_size = len(buildings)
    available = tuple((i not in buildings) for i in range(grid_size))
    buildings = normalize_buildings(buildings)
    return _compute_vision_bound(buildings, available, True)


def compute_vision_lower_bound(buildings):
    grid_size = len(buildings)
    available = tuple((i not in buildings) for i in range(grid_size))
    buildings = normalize_buildings(buildings)
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
        tests.append(tuple(test))

    return tests


def main():
    random.seed(1065)
    tests = _generate_tests(count=10000)
    for test in tests:
        print(
            stringy_buildings(test),
            "->",
            compute_vision_upper_bound(test),
            compute_vision_lower_bound(test),
        )


if __name__ == "__main__":
    main()
