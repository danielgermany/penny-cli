"""Terminal output formatting with Rich."""

from decimal import Decimal
from datetime import date, datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

console = Console()


def print_success(message: str):
    """Print success message."""
    console.print(f"[green][OK][/green] {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"[red][ERROR][/red] {message}", style="bold red")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[yellow][WARNING][/yellow] {message}", style="yellow")


def print_info(message: str):
    """Print info message."""
    console.print(f"[blue][INFO][/blue] {message}")


def format_currency(amount: Decimal | float, currency: str = "USD") -> str:
    """Format amount as currency."""
    if isinstance(amount, Decimal):
        amount = float(amount)
    return f"${amount:,.2f}"


def format_date(dt: date | datetime) -> str:
    """Format date."""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime("%Y-%m-%d") if isinstance(dt, (date, datetime)) else str(dt)


def print_transaction_table(transactions: list[dict]):
    """Print transactions as table."""
    if not transactions:
        print_info("No transactions found.")
        return

    table = Table(title="Recent Transactions")
    table.add_column("ID", style="dim")
    table.add_column("Date")
    table.add_column("Merchant")
    table.add_column("Category")
    table.add_column("Amount", justify="right")
    table.add_column("Type")

    for tx in transactions:
        amount = Decimal(str(tx["amount"]))
        type_color = "red" if tx["type"] == "expense" else "green"

        table.add_row(
            str(tx["id"]),
            format_date(tx["date"]),
            tx.get("merchant", "Unknown"),
            tx.get("category", "Uncategorized"),
            f"[{type_color}]{format_currency(amount)}[/{type_color}]",
            tx["type"].capitalize(),
        )

    console.print(table)


def print_account_table(accounts: list[dict]):
    """Print accounts as table."""
    if not accounts:
        print_info("No accounts found.")
        return

    table = Table(title="Accounts")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Institution")
    table.add_column("Balance", justify="right")

    for acc in accounts:
        balance = Decimal(str(acc["current_balance"]))
        balance_color = "green" if balance >= 0 else "red"

        table.add_row(
            str(acc["id"]),
            acc["name"],
            acc["type"].replace("_", " ").title(),
            acc.get("institution", "-"),
            f"[{balance_color}]{format_currency(balance)}[/{balance_color}]",
        )

    console.print(table)


def print_budget_status(budget_statuses: list[dict]):
    """Print budget status."""
    if not budget_statuses:
        print_info("No budgets found.")
        return

    table = Table(title="Budget Status")
    table.add_column("Category")
    table.add_column("Spent", justify="right")
    table.add_column("Limit", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Progress")

    for status in budget_statuses:
        if not status:
            continue

        spent = status["spent"]
        limit = status["limit"]
        remaining = status["remaining"]
        percentage = status["percentage"]

        # Color based on status
        if status["is_over"]:
            color = "red"
        elif status["should_alert"]:
            color = "yellow"
        else:
            color = "green"

        # Simple progress bar with ASCII characters
        filled = int(min(percentage, 100) // 5)
        empty = 20 - filled
        progress_bar = f"[{color}]{'#' * filled}{'-' * empty}[/{color}]"

        table.add_row(
            status["budget"]["category"],
            f"[{color}]{format_currency(spent)}[/{color}]",
            format_currency(limit),
            f"[{color}]{format_currency(remaining)}[/{color}]",
            f"{progress_bar} {percentage:.1f}%",
        )

    console.print(table)
