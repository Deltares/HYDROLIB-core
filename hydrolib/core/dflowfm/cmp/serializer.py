from pathlib import Path
from typing import Any, Dict, List

from hydrolib.core.basemodel import ModelSaveSettings


class CmpSerializer:
    @staticmethod
    def serialize(
        path: Path,
        data: Dict[str, List[Any]],
        save_settings: ModelSaveSettings,
    ) -> None:
        """
        Serialize components data to a file in .cmp format.

        Args:
            path (Path): The path to the destination .cmp file.
            data (Dict[str, List[Any]]): A dictionary with keys "comments" and "components".
            - "comments" represents comments found at the start of the file.
            - "components" is a list of dictionaries with the values as "period", "amplitude" and "phase".
                - "period" is a float as a string.
                - "amplitude" is a float as a string.
                - "phase" is a float as a string.

            save_settings (ModelSaveSettings): The save settings to be used.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        comment_lines = CmpSerializer._serialize_comment_lines(data)
        components_lines = CmpSerializer._serialize_components_lines(data)

        file_content = CmpSerializer._serialize_file_content(
            components_lines, comment_lines
        )
        with path.open("w", encoding="utf8") as file:
            file.write(file_content)

    @staticmethod
    def _serialize_comment_lines(data: Dict[str, List[Any]]) -> List[str]:
        comment_lines = []
        for comment in data["comments"]:
            comment_lines.append(f"{'#' if comment != '' else ''}{comment}")
        return comment_lines

    @staticmethod
    def _serialize_components_lines(data: Dict[str, List[Any]]) -> List[str]:
        components_lines = []
        for component in data["components"]:
            components_lines.append(
                f"{component['period']} {component['amplitude']} {component['phase']}"
            )
        return components_lines

    @staticmethod
    def _serialize_file_content(
        components_lines: List[str], comment_lines: List[str]
    ) -> str:
        return "\n".join(comment_lines + components_lines)
