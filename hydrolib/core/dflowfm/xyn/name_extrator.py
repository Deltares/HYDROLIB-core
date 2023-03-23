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
        Extract the first name from a given text string.

        This function is designed to handle names enclosed with single quotes
        and normal unquoted names. For names enclosed with single quotes,
        it will extract the name within the quotes. For normal names, it
        will extract the first word in the text string.

        Args:
        text (str): The input text string containing the name.

        Returns:
        str: The extracted first name.

        Raises:
        ValueError: If the input text is empty, contains only whitespace,
        or if the name contains a single quote not properly enclosed.
        """
        if not text or text.isspace():
            raise ValueError("Name cannot be empty.")

        text = text.strip()

        if text.startswith("'"):
            match = re.search(r"'(.*?)'", text)
            if not match:
                raise ValueError(
                    "Name that starts with a `'` should also end with a `'`"
                )

            name = match.group(1).strip("'")
            if len(name) == 0 or name.isspace():
                raise ValueError("Name cannot be empty.")
            else:
                return name

        if "'" in text:
            raise ValueError("Name cannot contain `'`.")

        return text.split()[0]
