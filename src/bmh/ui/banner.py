from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def render_banner() -> None:
    """Render the standard bmh welcome banner."""
    title_text = Text()
    title_text.append("🧠 ", style="bold cyan")
    title_text.append("Basic Memory Helper (bmh)\n", style="bold cyan")
    title_text.append("Smart discovery & structured card inspector", style="dim")

    panel = Panel(
        title_text,
        border_style="cyan",
        expand=False,
        padding=(0, 2),
    )
    console.print(panel)
