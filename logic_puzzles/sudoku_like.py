from abc import ABC, abstractmethod


def find_hidden_singles(hint_groups):
    to_update = {}

    for hints_locations in hint_groups:
        for value, locations in hints_locations.items():
            if len(locations) > 1:
                continue

            if len(locations) == 0:
                # There is no place this value can go in
                return None

            location = locations[0]
            if to_update.get(location, value) != value:
                # This location is the only one for multiple values
                return None

            to_update[location] = value

    return to_update


class SudokuLike(ABC):
    @abstractmethod
    def get_constrained_locations(self):
        """Get all the location groups which are constrained to contain
        all of the available values (i.e. rows, columns, squares)"""
        raise NotImplementedError

    def get_locations_by_value(self, cells):
        """Returns a map from each unset value to the list of locations it fits in"""
        res = {value: [] for value in self.puzzle.iter_values()}
        for location in cells:
            value = self.puzzle.get_value(location)
            if value is not None:
                res.pop(value)
                continue

            valid_values = self.puzzle.get_valid_values(location)
            for value in valid_values:
                res[value].append(location)

        return res

    def find_hidden_singles(self):
        constrained_locations = self.get_constrained_locations()
        hint_groups = list(map(self.get_locations_by_value, constrained_locations))
        to_update = find_hidden_singles(hint_groups)

        return to_update

    def _solve_hidden_singles(self):
        to_update = self.find_hidden_singles()

        if to_update is None:
            return 0

        if self.debug:
            print("Found cells by hidden singles:", len(to_update))

        if to_update:
            return self._solve_updates_map(to_update)

        return None
