import os
import sys
import re
import json
from .hint import EinsteinHint, EinsteinItem


def remove_variation_selector(text):
    variation_selector_pattern = re.compile(r"\uFE0F")
    return variation_selector_pattern.sub("", text)


def clean_dictionary(dictionary):
    # apply remove_variation_selector on every item
    # make the values always lists, for consistency
    for item_type, items in dictionary.items():
        dictionary[item_type] = [
            (
                [remove_variation_selector(item)]
                if not isinstance(item, list)
                else list(map(remove_variation_selector, item))
            )
            for item in items
        ]

    return dictionary


def compile_item_relations(item_relations):
    for relation in item_relations:
        relation["pattern"] = re.compile(relation["pattern"])
    return item_relations


relations_sample_path = os.path.join(os.path.dirname(__file__), "relations-sample.json")
with open(relations_sample_path, "r") as fin:
    RELATIONS_DATA = json.load(fin)
    SAMPLE_DICTIONARY = clean_dictionary(RELATIONS_DATA["DICTIONARY"])
    SAMPLE_ITEM_RELATIONS = compile_item_relations(RELATIONS_DATA["PARSING_RULES"])


class EinsteinParser:
    dictionary: dict[str, list[str]]
    item_relations: list[dict[str, str]]

    def __init__(
        self, dictionary=SAMPLE_DICTIONARY, item_relations=SAMPLE_ITEM_RELATIONS
    ):
        self.dictionary = dictionary
        self.item_relations = item_relations

    def get_item_name(self, item_type, text):
        text = remove_variation_selector(text)
        for item in self.dictionary[item_type]:
            if text in item:
                return item[0]

        return None

    def parse_hint(self, text):
        res = []
        for relation in self.item_relations:
            match = relation["pattern"].match(text)
            if not match:
                continue

            item_1 = self.get_item_name(relation["item_1"], match.group("item_1"))
            item_2 = self.get_item_name(relation["item_2"], match.group("item_2"))
            negation = match.group("negation") != ""

            if item_1 is None or item_2 is None:
                continue

            hint = EinsteinHint(
                EinsteinItem(relation["item_1"], item_1),
                EinsteinItem(relation["item_2"], item_2),
                negation,
            )
            res.append(hint)

        if len(res) == 0:
            raise ValueError(f"No pattern matched for {text}")

        if len(res) > 1 and not all(x == res[0] for x in res):
            raise ValueError(f"Multiple patterns matched for {text}")

        return res[0]
