import re


class NameExtractor:
    """
    Class used to extract the name from a given text.
    Please note that this extractor is specifically made for extracting
    names from .xyn files.
    """

    @staticmethod
    def extract_name(text: str) -> str:
        """
        Extract the name from a given text string.

        This function is designed to handle names enclosed with single quotes
        and normal unquoted names. Names between single quotes may contain
        spaces. Names themselves may not contain a single quote.

        Args:
        text (str): The input text string containing the name.

        Returns:
        str: The extracted first name.

        Raises:
        ValueError: If the input text is empty, contains only whitespace,
        or if the name contains a single quote not properly enclosed.
        """

        def _extract_quoted_name(text: str) -> str:
            if not text.endswith("'"):
                raise ValueError(
                    "Name that starts with a `'` should also end with a `'`"
                )

            name = text.strip("'")
            if not name or name.isspace():
                raise ValueError("Name cannot be empty.")

            if "'" in name:
                raise ValueError("Name cannot contain `'`.")

            return name

        def _extract_name(text: str) -> str:
            if "'" in text:
                raise ValueError("Name cannot contain `'`.")

            name = text.split()
            if len(name) == 1:
                return name[0]

            raise ValueError("Name cannot contain spaces.")

        if not text or text.isspace():
            raise ValueError("Name cannot be empty.")

        text = text.strip()

        if text.startswith("'"):
            return _extract_quoted_name(text)

        return _extract_name(text)
