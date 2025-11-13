def define_env(env):
    """
    Set up specific environment for documentation site,
    with some convenience macro's.

    Available custom mkdocs-macros that produce Markdown content:
    { sobek_um(anchor, linktext) }: (deep)link to SOBEK User Manual PDF.
    { dflowfm_um(anchor, linktext) }: (deep)link to D-Flow FM User Manual PDF.
    { gh_issue(number, linktext) }: link to GitHub issue page.
    { gh_pr(number, linktext) }: link to GitHub pull request page.
    { gh_repo(path, linktext) }: link to a file's page in the GitHub repo.

    """

    dflowfm_um_url = (
        "https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf"
    )
    sobek_um_url = "https://content.oss.deltares.nl/sobek2/SOBEK_User_Manual.pdf"
    hydrolib_core_url = "https://github.com/Deltares/HYDROLIB-core"

    def _get_url(url: str, anchor: str = None):
        return url + ("#" + anchor if anchor else "")

    @env.macro
    def dflowfm_um(anchor: str = "", linktext: str = "D-Flow FM UM"):
        """Create Markdown link for D-Flow FM User Manual, with optional anchor/bookmark."""

        return "[" + linktext + "](" + _get_url(dflowfm_um_url, anchor) + ")"

    @env.macro
    def sobek_um(anchor: str = "", linktext: str = "SOBEK UM"):
        """Create Markdown link for SOBEK User Manual, with optional anchor/bookmark."""

        return "[" + linktext + "](" + _get_url(sobek_um_url, anchor) + ")"

    @env.macro
    def gh_issue(number: int, linktext: str = None):
        """Create Markdown link to GitHub issue page."""

        return (
            "["
            + (linktext or "#" + str(number))
            + "]("
            + hydrolib_core_url
            + "/issues/"
            + str(number)
            + ")"
        )

    @env.macro
    def gh_pr(number: int, linktext: str = None):
        """Create Markdown link to GitHub pull request page."""

        return (
            "["
            + (linktext or "#" + str(number))
            + "]("
            + hydrolib_core_url
            + "/pull/"
            + str(number)
            + ")"
        )

    @env.macro
    def gh_repo(path: str, linktext: str = None):
        """Create Markdown link to a file's page in the GitHub repo."""

        return (
            "["
            + (linktext or "#" + path)
            + "]("
            + hydrolib_core_url
            + "/blob/main/"
            + path
            + ")"
        )
