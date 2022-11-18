from pathlib import Path

from hydrolibcore.io.rr.topology.models import Link, LinkFile
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


class TestLink:
    def test_create_link(self):
        link = Link(**create_link_values())

        assert link.id == "link_id"
        assert link.name == "link_name"
        assert link.branchid == 1
        assert link.modellinktype == 2
        assert link.branchtype == 3
        assert link.objectid == "link_obid"
        assert link.beginnode == "link_beginnode"
        assert link.endnode == "link_endnode"

    def test_optional_fields_have_correct_defaults(self):
        link = Link(**create_required_link_values())

        assert link.name == None


class TestLinkFile:
    def test_create_linkfile(self):
        linkfile_values = dict(link=[create_link_values()])

        linkfile = LinkFile(**linkfile_values)

        assert len(linkfile.link) == 1
        assert linkfile.link[0].id == "link_id"

    def test_load_from_file(self):

        path = Path(test_input_dir / "rr_network" / "3B_LINK.TP")

        linkfile = LinkFile(filepath=path)

        assert len(linkfile.link) == 61

        link = linkfile.link[7]
        assert link.id == "8"
        assert link.branchid == -1
        assert link.modellinktype == 0
        assert link.branchtype == 17
        assert link.objectid == "3B_LINK"
        assert link.beginnode == "unp_riv_RS373_6"
        assert link.endnode == "lat_936"

    def test_save(self):

        output_file = Path(test_output_dir / "rr" / "serialize_link.tp")
        reference_file = Path(test_reference_dir / "rr" / "serialize_link.tp")

        link = Link(**create_link_values())
        linkfile = LinkFile(link=[link, link, link])
        linkfile.filepath = output_file

        linkfile.save()

        assert_files_equal(output_file, reference_file)

    def test_to_dict(self):
        data = create_link_values()
        link = Link(**data)

        result = link.dict()

        assert result == data


def create_link_values() -> dict:
    linkvalues = dict(nm="link_name")
    linkvalues.update(create_required_link_values())
    return linkvalues


def create_required_link_values() -> dict:
    return dict(
        id="link_id",
        ri=1,
        mt=2,
        bt=3,
        ObID="link_obid",
        bn="link_beginnode",
        en="link_endnode",
    )
