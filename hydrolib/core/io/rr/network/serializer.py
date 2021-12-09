import os
from pathlib import Path


class NodeFileSerializer:
    @staticmethod
    def serialize(path: Path, data: dict):
        """
        Serializes the RR node topology data to the file at the specified path.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as f:
            for node in data["node"]:
                line = f"NODE {NodeFileSerializer._to_line(node)} node{os.linesep}"
                f.write(line.encode("utf8"))

    @staticmethod
    def _to_line(node: dict) -> str:
        identifier = node["id"]
        nm = node["nm"]
        ri = node["ri"]
        mt = node["mt"]
        nt = node["nt"]
        obid = node["ObID"]
        px = node["px"]
        py = node["py"]

        return f"id '{identifier}' nm '{nm}' ri '{ri}' mt 1 '{mt}' nt {nt} ObID '{obid}' px {px} py {py}"
