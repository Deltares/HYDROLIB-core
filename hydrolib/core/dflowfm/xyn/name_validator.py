class NameValidator:
    """
    Class used to validate the name from a given text.
    Please note that this validator is specifically made for validating
    names in .xyn files.
    """

    @staticmethod
    def validate(name: str) -> str:
        """
        Validate the given name.

        This function is designed to handle names enclosed with single quotes
        and normal unquoted names. Names between single quotes may contain
        spaces. Names themselves may not contain a single quote. Any leading
        or trailing whitespace will be trimmed from the name.

        Args:
            name (str): The name to validate.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If the name is empty, contains only whitespace,
                or if the name contains a single quote not properly enclosed.
        """

        def _validate_quoted_name(name: str) -> str:
            if not name.endswith("'"):
                raise ValueError(
                    "Name that starts with a `'` should also end with a `'`"
                )

            name = name.strip("'")
            if not name or name.isspace():
                raise ValueError("Name cannot be empty.")

            if "'" in name:
                raise ValueError("Name cannot contain `'`.")

            return name

        def _validate_name(name: str) -> str:
            if "'" in name:
                raise ValueError("Name cannot contain `'`.")

            split_name = name.split()
            if len(split_name) == 1:
                return split_name[0]

            raise ValueError("Name cannot contain spaces.")

        if not name or name.isspace():
            raise ValueError("Name cannot be empty.")

        name = name.strip()

        if name.startswith("'"):
            return _validate_quoted_name(name)

        return _validate_name(name)
