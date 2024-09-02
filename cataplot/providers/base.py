"""
Base class for providers that provide data to be plotted.
"""

from datetime import datetime

class BaseProvider:
    """
    Base class for providers that provide data to be plotted.
    """
    def __init__(self):
        pass

    def listdir(self, path:str='/') -> list[tuple[str, str, str]]:
        """
        Returns a list of (name, type, description) items in the specified path.

            - name: The name of the item
            - type: The type of the item (e.g. "item" or "dir")
            - description: A description of the item
        
        For items that are "dir" type, listdir() can be called with the item's
        name to list the items in that directory.  In this case, the name should
        be the name of the directory and the description should be the number of
        items in the directory.
        """
        raise NotImplementedError

    def get_data(self, path: str, start: datetime, end: datetime) -> list:
        """
        Returns a list of values between the start and end times from the
        specified plottable item.  Path must be type "item".
        """
        # allow item to be a list of items so provider subclass can efficiently
        # batch the request (e.g. in some databases, data items come from the
        # same row, so we can avoid getting the row more than once.  May not
        # matter if sql client isn't getting the entire row because they're
        # using substr though.)
        pass
