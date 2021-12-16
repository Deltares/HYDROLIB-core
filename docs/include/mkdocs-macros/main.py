def define_env(env):
    "Hook function"

    dflowfm_um_url = "https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf"
    sobek_um_url = "https://content.oss.deltares.nl/delft3d/manuals/SOBEK_User_Manual.pdf"
    hydrolib_core_url = "https://github.com/Deltares/HYDROLIB-core"

    @env.macro
    def mymacro():
      return "Hello World"

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
    def sobek_um(anchor: str = "", linktext: str = "SOBEK UM"):
        """Create Markdown link for SOBEK User Manual, with optional anchor/bookmark."""
    
        return "[" + linktext + "](" + _get_url(sobek_um_url, anchor) + ")"

    @env.macro
    def gh_issue(number: int, linktext: str = None):
        """Create Markdown link to GitHub issue page."""

        return "[" + (linktext or "#"+str(number)) + "](" + hydrolib_core_url + "/issues/" + str(number) + ")"

    @env.macro
    def gh_PR(number: int, linktext: str = None):
        """Create Markdown link to GitHub pull request page."""

        return "[" + (linktext or "#"+str(number)) + "](" + hydrolib_core_url + "/pull/" + str(number) + ")"

