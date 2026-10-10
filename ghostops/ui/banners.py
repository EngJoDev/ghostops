"""
GhostOps - ASCII Branding and Visual Headers.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from ghostops import __version__

ASCII_LOGO = r"""
   ________  ______  _____ ______ ____  ____  _____
  / ____/ / / / __ \/ ___//_  __// __ \/ __ \/ ___/
 / / __/ /_/ / / / /\__ \  / /  / / / / /_/ /\__ \ 
/ /_/ / __  / /_/ /___/ / / /  / /_/ / ____/___/ / 
\____/_/ /_/\____//____/ /_/   \____/_/    /____/  
"""

def get_welcome_banner() -> Panel:
    """Generates the main visual header panel for GhostOps."""
    text = Text()
    text.append(ASCII_LOGO, style="bold cyan")
    text.append("\n  ⚡ Autonomous Linux & DevOps SRE Terminal Copilot\n", style="bold yellow")
    text.append(f"  v{__version__} | MIT Open Source | Native Linux Engine\n", style="dim white")

    return Panel(
        Align.center(text),
        border_style="bright_blue",
        padding=(0, 2),
        subtitle="[bold green]System: Ready[/bold green] • [bold magenta]Engine: Active[/bold magenta]",
        subtitle_align="right"
    )

def print_banner(console: Console) -> None:
    """Print the welcome banner to the given console."""
    console.print(get_welcome_banner())
