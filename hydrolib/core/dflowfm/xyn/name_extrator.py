class NameExtractor:
    """
    Class used to extract the name from a given text.
    Please note that this extractor is specifically made for extracting
    names from .xyn files.
    """

    @staticmethod
    def extract_name(text: str) -> str:
        """
        Extracts a valid name from the given text.

        This function takes a string input, removes comments starting with "#", trims whitespaces,
        and validates the extracted name based on a set of rules. The name can be extracted from
        either a plain string without spaces or a string surrounded by single quotes.

        Rules for a valid name:
        1. Name cannot be empty.
        2. Name cannot contain a "#".
        3. If the name contains spaces, it must be surrounded by single quotes.
        4. If the name starts with a single quote, it must end with a single quote, and vice versa.

        Args:
            text (str): The input text containing the name to be extracted.

        Returns:
            str: The extracted valid name.

        Raises:
            ValueError: If the extracted name does not meet the specified rules.

        Example:
            >>> extract_name("John")
            'John'
            >>> extract_name(" 'John Doe' ")
            'John Doe'
            >>> extract_name(" 'John Doe")
            ValueError: Name cannot be empty, contain a `#` or miss closing `'`.
        """

        def _remove_comment(text: str) -> str:
            if "#" in text:
                text = text.split("#", 1)[0]
            return text

        def _extract_name_between_quotes(text: str) -> str:
            if len(text) <= 2:
                raise ValueError("Name cannot be empty or contain a `#`.")
            name = text.strip("'")
            if len(name.strip()) == 0:
                raise ValueError("Name cannot be empty or contain a `#`.")
            return name

        if not text:
            raise ValueError("Name cannot be empty.")

        text = _remove_comment(text)

        text = text.strip()
        if len(text) == 0:
            raise ValueError("Name cannot be empty or contain a `#`.")

        if text.startswith("'") and text.endswith("'"):
            return _extract_name_between_quotes(text)

        if text.startswith("'") and not text.endswith("'"):
            raise ValueError("Name cannot be empty, contain a `#` or miss closing `'`.")

        if not text.startswith("'") and text.endswith("'"):
            raise ValueError("Name cannot be empty, contain a `#` or miss opening `'`.")

        if " " in text:
            raise ValueError(
                "Name that contains spaces should be surrounded by double `'`."
            )

        return text
