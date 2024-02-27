from logic_puzzles.puzzle import Puzzle, PuzzleState
from .parser import EinsteinParser
from .hint import EinsteinItem, EinsteinHint


class EinsteinState(PuzzleState):
    houses: list[list[EinsteinItem]]
    item_location: dict[EinsteinItem, int]
    conflict_values: list[dict[EinsteinItem, int]]

    def __init__(self, houses, item_location, conflict_values):
        self.houses = houses
        self.item_location = item_location
        self.conflict_values = conflict_values


class EinsteinPuzzle(Puzzle):
    hints: list[EinsteinHint]
    hints_by_item: dict[str, list[EinsteinHint]]
    items_by_type: dict[str, list[EinsteinItem]]
    items: list[EinsteinItem]
    state: EinsteinState

    def __init__(self, hints, items_by_type, state=None):
        self.hints = hints
        self.items_by_type = items_by_type
        self.items = []
        for item_type, items in self.items_by_type.items():
            self.items.extend(items)

        self.hints_by_item = {item: [] for item in self.items}
        for hint in hints:
            for item in [hint.item_1, hint.item_2]:
                self.hints_by_item[item].append(hint)

        if state is None:
            houses = [[] for _ in self.items_by_type["PERSON"]]
            item_locations = {item: None for item in self.items}
            conflict_values = [
                {item: 0 for item in self.items} for _ in self.items_by_type["PERSON"]
            ]
            self.state = EinsteinState(houses, item_locations, conflict_values)

            for i, item in enumerate(self.items_by_type["PERSON"]):
                self.set_house(item, i)
        else:
            self.state = state

    def __str__(self):
        res = ["# Hints"]
        res.extend((f"- {hint}" for hint in self.hints))
        res.append("# State")
        for person in self.state.houses:
            res.append("- " + ", ".join(map(str, person)))

        return "\n".join(res)

    @classmethod
    def from_string(cls, string, parser=None):
        if parser is None:
            parser = EinsteinParser()

        found_item_types = set()

        hints = []
        for line in string.split("\n"):
            if not line:
                continue
            hint = parser.parse_hint(line)
            hints.append(hint)

            for item in [hint.item_1, hint.item_2]:
                found_item_types.add(item.item_type)

        items_count = len(found_item_types) - 1
        items_by_type = {
            item_type: [
                EinsteinItem(item_type, x[0])
                for x in parser.dictionary[item_type][:items_count]
            ]
            for item_type in found_item_types
        }

        return cls(hints, items_by_type)

    def _update_conflict_values(self, item, house, delta):
        dirty = set()

        for hint in self.hints_by_item[item]:
            other_item = hint.item_1 if hint.item_2 == item else hint.item_2

            if hint.negated:
                # other item must not be in the same house
                self.state.conflict_values[house][other_item] += delta
                if (
                    self.state.conflict_values[house][other_item] == delta
                    and self.state.item_location[other_item] is None
                ):
                    dirty.add(other_item)
                continue

            # other item must not be in a different house
            for other_house in range(len(self.state.houses)):
                if other_house != house:
                    self.state.conflict_values[other_house][other_item] += delta
                    if (
                        self.state.conflict_values[other_house][other_item] == delta
                        and self.state.item_location[other_item] is None
                    ):
                        dirty.add(other_item)

        # no two items of the same type in the same home
        for other_item in self.items_by_type[item.item_type]:
            if other_item != item:
                self.state.conflict_values[house][other_item] += delta
                if (
                    self.state.conflict_values[house][other_item] == delta
                    and self.state.item_location[other_item] is None
                ):
                    dirty.add(other_item)

        return dirty

    def set_house(self, item, house):
        assert self.state.item_location[item] is None
        self.state.houses[house].append(item)
        self.state.item_location[item] = house

        return self._update_conflict_values(item, house, 1)

    def unset_house(self, item):
        house = self.state.item_location[item]
        assert house is not None
        self.state.houses[house].remove(item)
        self.state.item_location[item] = None

        self._update_conflict_values(item, house, -1)
