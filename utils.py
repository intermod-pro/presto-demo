import sys
from typing import Optional, Tuple


def address_port_from_cli() -> Tuple[str, Optional[int]]:
    """Get IP address and port number as parameters to the script.

    Port number is optional. Print usage information if failing to get IP address.
    """
    if len(sys.argv) == 2:
        address = sys.argv[1]
        port = None
    elif len(sys.argv) == 3:
        address = sys.argv[1]
        port = int(sys.argv[2])
    else:
        raise RuntimeError("IP address missing! Usage: `python scriptname.py ADDRESS [PORT]`")

    return address, port


def show(plt, fig):
    """Show matplotlib figure.

    Calls one of:
    - ``plt.show()`` if running in a non-interactive environment
    - ``fig.show()`` if running in an interactive environment
    """
    if hasattr(sys, "ps1"):
        fig.show()
    else:
        plt.show()
