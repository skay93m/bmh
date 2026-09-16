from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.spinner import Spinner
from rich.text import Text

from bmh.core.client import BMClient, BMError
from bmh.ui.cards import (
    render_schema_validation_panel,
    render_orphan_list_panel,
    render_doctor_panel,
    render_schema_diff_panel,
    render_lint_all_dashboard,
)

console = Console()

COMMON_NOTE_TYPES = ["task", "insight", "meeting", "decision", "note", "spec", "guide", "report"]


def _handle_error(e: Exception) -> None:
    if isinstance(e, BMError):
        console.print(f"\n[bold red]Basic Memory Error:[/bold red] {e}\n")
    else:
        console.print(f"\n[bold red]Error:[/bold red] {e}\n")


def flow_schema_validate(client: BMClient) -> None:
    """Run schema validation and display results."""
    console.print("\n[bold cyan]── 📐 Schema Validator ──[/bold cyan]")

    console.print("  [dim]Validate specific note type or all notes?[/dim]")
    console.print("  [bold cyan][1][/bold cyan] All notes")
    for i, nt in enumerate(COMMON_NOTE_TYPES, start=2):
        console.print(f"  [bold cyan][{i}][/bold cyan] {nt}")

    choices = ["1"] + [str(i) for i in range(2, len(COMMON_NOTE_TYPES) + 2)]
    choice = Prompt.ask("  Select", choices=choices, default="1").strip()
    target: Optional[str] = None if choice == "1" else COMMON_NOTE_TYPES[int(choice) - 2]

    project = Prompt.ask("  Project filter (optional)", default="").strip()

    with console.status("[cyan]Validating schemas...[/cyan]", spinner="dots"):
        try:
            data = client.schema_validate(target=target, project=project or None)
        except BMError as e:
            data = {"error": str(e)}

    panel = render_schema_validation_panel(data)
    console.print(panel)


def flow_orphan_inspector(client: BMClient) -> None:
    """Run orphan entity detection and display results."""
    console.print("\n[bold cyan]── 🔗 Orphan & Broken Link Inspector ──[/bold cyan]")
    project = Prompt.ask("  Project filter (optional)", default="").strip()

    with console.status("[cyan]Scanning for orphan entities...[/cyan]", spinner="dots"):
        try:
            orphans = client.orphans(project=project or None)
        except BMError as e:
            orphans = [{"error": str(e)}]

    panel = render_orphan_list_panel(orphans)
    console.print(panel)


def flow_doctor(client: BMClient) -> None:
    """Run bm doctor consistency check."""
    console.print("\n[bold cyan]── 🩺 Sync & Index Doctor ──[/bold cyan]")

    with console.status("[cyan]Running consistency checks...[/cyan]", spinner="dots"):
        try:
            data = client.doctor()
        except BMError as e:
            data = {"passed": False, "output": str(e), "steps": [], "status": "failed"}

    panel = render_doctor_panel(data)
    console.print(panel)


def flow_schema_drift(client: BMClient) -> None:
    """Run schema drift analysis for a specific note type."""
    console.print("\n[bold cyan]── 📊 Schema Drift Analyzer ──[/bold cyan]")
    console.print("  Available note types:")
    for i, nt in enumerate(COMMON_NOTE_TYPES, start=1):
        console.print(f"  [bold cyan][{i}][/bold cyan] {nt}")
    console.print(f"  [bold cyan][{len(COMMON_NOTE_TYPES)+1}][/bold cyan] Enter custom type")

    choices = [str(i) for i in range(1, len(COMMON_NOTE_TYPES) + 2)]
    choice = Prompt.ask("  Select note type", choices=choices, default="1").strip()

    if choice == str(len(COMMON_NOTE_TYPES) + 1):
        note_type = Prompt.ask("  Custom note type").strip()
    else:
        note_type = COMMON_NOTE_TYPES[int(choice) - 1]

    project = Prompt.ask("  Project filter (optional)", default="").strip()

    with console.status(f"[cyan]Analyzing schema drift for '{note_type}'...[/cyan]", spinner="dots"):
        try:
            data = client.schema_diff(note_type=note_type, project=project or None)
        except BMError as e:
            data = {"error": str(e), "note_type": note_type, "schema_found": False}

    panel = render_schema_diff_panel(data)
    console.print(panel)


def flow_lint_all(client: BMClient) -> None:
    """Run complete 'Lint All' diagnostic health check and display unified dashboard."""
    console.print("\n[bold cyan]── 🏆 Lint All Health Dashboard ──[/bold cyan]")
    project = Prompt.ask("  Project filter (optional)", default="").strip()
    drift_type = Prompt.ask("  Note type for drift analysis (optional, e.g. 'task')", default="task").strip()

    results: Dict[str, Any] = {}

    # Step 1: Doctor
    with console.status("[cyan][1/4] Running bm doctor...[/cyan]", spinner="dots"):
        try:
            doctor_data = client.doctor()
        except BMError as e:
            doctor_data = {"passed": False, "output": str(e), "steps": [], "status": "failed"}
    results["doctor"] = doctor_data
    results["doctor_passed"] = doctor_data.get("passed", False)
    console.print(f"  Doctor: {'[green]PASSED[/green]' if doctor_data.get('passed') else '[red]FAILED[/red]'}")

    # Step 2: Schema validation
    with console.status("[cyan][2/4] Validating schemas...[/cyan]", spinner="dots"):
        try:
            schema_data = client.schema_validate(project=project or None)
        except BMError as e:
            schema_data = {"error": str(e)}
    results["schema"] = schema_data
    valid = schema_data.get("valid_count", 0)
    total = schema_data.get("total_notes", 0)
    errors = schema_data.get("error_count", 0)
    warnings = schema_data.get("warning_count", 0)
    console.print(f"  Schema: [green]{valid}/{total}[/green] valid, [yellow]{warnings}[/yellow] warnings, [red]{errors}[/red] errors")

    # Step 3: Orphans
    with console.status("[cyan][3/4] Scanning for orphans...[/cyan]", spinner="dots"):
        try:
            orphan_list = client.orphans(project=project or None)
        except BMError as e:
            orphan_list = [{"error": str(e)}]
    results["orphans"] = orphan_list
    orphan_count = len([o for o in orphan_list if "error" not in o])
    console.print(f"  Orphans: {'[green]None[/green]' if orphan_count == 0 else f'[yellow]{orphan_count}[/yellow] found'}")

    # Step 4: Schema drift
    if drift_type:
        with console.status(f"[cyan][4/4] Analyzing schema drift for '{drift_type}'...[/cyan]", spinner="dots"):
            try:
                drift_data = client.schema_diff(note_type=drift_type, project=project or None)
            except BMError as e:
                drift_data = {"error": str(e), "note_type": drift_type, "schema_found": False}
        results["drift"] = drift_data
        new_f = len(drift_data.get("new_fields", []))
        drop_f = len(drift_data.get("dropped_fields", []))
        drift_count = new_f + drop_f
        results["drift_count"] = drift_count
        console.print(f"  Drift: {'[green]Aligned[/green]' if drift_count == 0 else f'[yellow]{drift_count}[/yellow] drifting fields'}")

    console.print()
    panel = render_lint_all_dashboard(results)
    console.print(panel)


def run_lint_hub(client: Optional[BMClient] = None) -> None:
    """Top-level Lint Hub interactive menu."""
    bm_client = client or BMClient()

    while True:
        console.print("\n[bold cyan]── 🩺 Lint Hub ──[/bold cyan]")
        console.print("  [bold cyan][1][/bold cyan] 📐 Schema Validator  [dim](validate note frontmatter & schemas)[/dim]")
        console.print("  [bold cyan][2][/bold cyan] 🔗 Orphan Inspector  [dim](detect unlinked knowledge graph nodes)[/dim]")
        console.print("  [bold cyan][3][/bold cyan] 🩺 Sync Doctor  [dim](verify database/file consistency)[/dim]")
        console.print("  [bold cyan][4][/bold cyan] 📊 Schema Drift Analyzer  [dim](detect schema vs. actual note drift)[/dim]")
        console.print("  [bold cyan][5][/bold cyan] 🏆 Lint All  [dim](full health checkup + dashboard)[/dim]")
        console.print("  [bold cyan][0][/bold cyan] ↩  Back to Main Menu")
        console.print("[dim]──────────────────────────────────────────────[/dim]")

        try:
            choice = Prompt.ask(
                "Select action",
                choices=["1", "2", "3", "4", "5", "0"],
                default="5",
                show_choices=False,
            ).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            flow_schema_validate(bm_client)
        elif choice == "2":
            flow_orphan_inspector(bm_client)
        elif choice == "3":
            flow_doctor(bm_client)
        elif choice == "4":
            flow_schema_drift(bm_client)
        elif choice == "5":
            flow_lint_all(bm_client)
        elif choice == "0":
            break

        if choice not in ("0",):
            try:
                cont = Prompt.ask("\n  Continue in Lint Hub? (Enter or 'q' to go back)", default="")
                if cont.strip().lower() in ("q", "quit", "exit", "n", "no"):
                    break
            except (KeyboardInterrupt, EOFError):
                break
