"""
This module provides a class for filtering and ranking a list of strings based
on a pattern string.  It is intended to be used in a command palette or similar
interface where the user types a query string to filter a list of items.
"""
import re

class MenuFilter:
    """
    A class for filtering and ranking a list of strings based on a pattern
    string. The pattern string is used to build a regular expression that
    matches the pattern. The strings in the list are then scored based on how
    well they match the pattern, and the list is filtered and ranked based on
    these scores.

    Example usage:
        mf = MenuFilter()
        items = ["apple", "banana", "cherry", "date"]
        filtered = mf.filter_list("ae", items)
        print(filtered)
    """

    def __init__(self):
        pass

    def _build_regex(self, query:str) -> str:
        """
        Builds the regular expression for scoring matches.
        """
        return '.*?'.join(map(re.escape, list(query)))

    def _score(self, string:str, regex:str, ignorecase:bool=True) -> float:
        """
        Scores a string based on how well it matches the pattern string. Returns
        a score between 0 and 100.  The higher the score, the better the match.
        Factors that affect the score include the position and length of the
        match: matches that occur earlier in the string and are longer score
        higher.
        """
        if ignorecase:
            match = re.search(regex, string, re.IGNORECASE)
        else:
            match = re.search(regex, string)
        if match is None:
            return 0
        # Derive a score based on the position and length of the match
        pos_match = match.start() + 1  # +1 to avoid division by zero
        len_match = (match.end() - match.start()) + 1
        return 100.0 / (pos_match * len_match)

    def rank_list(self, query:str, items: list[str]) -> list[tuple[str, float]]:
        """
        Ranks a list of items based on how well they match the pattern string.
        Returns a list of tuples with the item and its corresponding score.
        """
        regex = self._build_regex(query)
        ranked = [(item, self._score(item, regex)) for item in items]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def filter_list(self, query:str, items:list[str]) -> list[str]:
        """
        Filters and ranks a list of items based on how well they match the query
        string. Returns a list of items that have a non-zero score, sorted by
        score.
        """
        ranked = self.rank_list(query, items)
        return [item for item, score in ranked if score > 0]
