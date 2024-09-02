"""
Base class for providers that provide data to be plotted.
"""
from abc import ABC, abstractmethod
from datetime import datetime

class BaseProvider(ABC):
    """
    Base class for providers that provide data to be plotted.
    """
    def __init__(self, name:str, description:str='', config:dict|None=None):
        self.name = name
        self.description = description
        if config is None:
            self._config = self._generate_default_config()
        else:
            self.set_config(config)

    def _generate_default_config(self):
        """
        Generates a default configuration for this provider based on the
        configuration schema.  Returns a dictionary with the default values for
        each parameter.
        """
        schema = self.get_config_schema()
        config = {}
        for key, params in schema.items():
            if "default" in params:
                config[key] = params["default"]
            else:
                config[key] = None
        return config

    def get_config(self):
        """
        Returns the configuration for this provider.
        """
        return self._config

    def set_config(self, config:dict):
        """
        Sets the configuration for this provider.  The config parameter is a
        dictionary containing the configuration parameters to set.
        """
        schema = self.get_config_schema()

        # Check that all supplied parameters are valid and have the correct type
        for key, value in config.items():
            if key not in schema:
                raise ValueError(f"Unknown configuration parameter: {key}")
            expected_type = schema[key]['dtype']
            if not isinstance(value, expected_type):
                raise TypeError(f"Incorrect type for {key}: expected {expected_type}")

        # Check that all required parameters are present
        self.validate_config()

        # It is safe to set the configuration now
        self._config = config

    def validate_config(self):
        """
        Checks that the configuration is valid by ensuring that all required
        parameters are present.  Raises a ValueError if any required parameters
        are missing.
        """
        schema = self.get_config_schema()

        for key, params in schema.items():
            if params.get("required") and self._config.get(key) is None:
                raise ValueError(f"Missing required configuration parameter: {key}")

    @abstractmethod
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

    @abstractmethod
    def get_data(self, path: str, start: datetime, end: datetime) -> list:
        """
        Returns a list of values between the start and end times from the
        specified plottable item.  Path must be type "item".
        """
        # FIXME: Consider allowing path to be a list of paths so provider
        # subclass can efficiently batch the request (e.g. in some databases,
        # data items come from the same row, so we can avoid getting the row
        # more than once.

    @abstractmethod
    def get_config_schema(self) -> dict:
        """
        Returns a dictionary that describes the configuration parameters for
        this provider.  The keys are the parameter names and the values are
        dictionaries with the following keys:

            - dtype: The python data type of the parameter (e.g. int, str,
              float, bool)
            - required: True if the parameter is required, False otherwise
            - opts: A list of options that specify how the parameter should be
              formatted in the user interface.  E.g. "password" to
              hide the value in the UI, "hex" to display the value as a hex
              string, etc. (optional)
            - default: The default value for the parameter (optional)
            - description: A description of the parameter (optional)

        Example: {
            "host": {
                "dtype": "string",
                "required": True,
                "description": "The hostname of the server"
            },
            "port": {
                "dtype": "int",
                "required": False,
                "default": 8080,
                "description": "The port number of the server"
            },
            "username": {
                "dtype": "string",
                "required": False,
                "description": "The username to use for authentication"
            },
            "password": {
                "dtype": "password",
                "required": False,
                "description": "The password to use for authentication",
                "opts": ["password"]
            }
        }
        """
