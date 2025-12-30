"""Recurring charge CLI commands."""

import click
from decimal import Decimal
from rich.console import Console
from rich.table import Table
from ..formatters import print_success, print_error, print_info, print_warning


@click.group()
def recurring():
    """Manage recurring charges."""
    pass


@recurring.command("list")
@click.option("--status", "-s", type=click.Choice(["active", "paused", "cancelled"]), help="Filter by status")
@click.pass_context
def list_recurring(ctx, status):
    """
    List all recurring charges.

    Example: finance recurring list --status active
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        recurring_charges = container.recurring_service().list_recurring_charges(user_id, status=status)

        if not recurring_charges:
            print_info("No recurring charges found.")
            print_info("Use 'finance recurring detect' to find patterns in your transactions.")
            return

        # Display table
        console = Console()
        table = Table(title="Recurring Charges")
        table.add_column("ID", style="dim", justify="right")
        table.add_column("Merchant", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Amount", justify="right", style="yellow")
        table.add_column("Frequency")
        table.add_column("Next Due", justify="center")
        table.add_column("Status", justify="center")

        for charge in recurring_charges:
            # Format status with color
            status_display = charge["status"].capitalize()
            if charge["status"] == "active":
                status_color = "green"
            elif charge["status"] == "paused":
                status_color = "yellow"
            else:
                status_color = "red"

            table.add_row(
                str(charge["id"]),
                charge["merchant"],
                charge["category"],
                f"${float(charge['typical_amount']):.2f}",
                charge["frequency"].capitalize(),
                charge.get("next_expected_date", "-"),
                f"[{status_color}]{status_display}[/{status_color}]",
            )

        console.print(table)
        print_info(f"\nTotal recurring charges: {len(recurring_charges)}")

    except Exception as e:
        print_error(f"Failed to list recurring charges: {str(e)}")
        raise


@recurring.command("detect")
@click.option("--min-occurrences", "-m", default=2, type=int, help="Minimum occurrences to detect pattern")
@click.pass_context
def detect_patterns(ctx, min_occurrences):
    """
    Detect recurring patterns from existing transactions.

    Analyzes your transaction history to identify potential recurring charges
    like subscriptions, bills, and regular payments.

    Example: finance recurring detect --min-occurrences 3
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        print_info("Analyzing transaction patterns...")
        patterns = container.recurring_service().detect_recurring_patterns(user_id, min_occurrences=min_occurrences)

        if not patterns:
            print_info("No recurring patterns detected.")
            print_info(f"Tip: Lower --min-occurrences (current: {min_occurrences}) to find less frequent patterns.")
            return

        # Display detected patterns
        console = Console()
        table = Table(title="Detected Recurring Patterns")
        table.add_column("Merchant", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Avg Amount", justify="right", style="yellow")
        table.add_column("Frequency")
        table.add_column("Count", justify="right")
        table.add_column("Confidence", justify="right")

        for i, pattern in enumerate(patterns, 1):
            table.add_row(
                pattern["merchant"],
                pattern["category"],
                f"${float(pattern['typical_amount']):.2f}",
                pattern["frequency"].capitalize(),
                str(pattern["occurrence_count"]),
                f"{float(pattern['confidence']) * 100:.0f}%",
            )

        console.print(table)
        print_success(f"\nFound {len(patterns)} recurring pattern(s)")
        print_info("To track these charges, use: finance recurring add <merchant> <amount> <frequency>")

    except Exception as e:
        print_error(f"Failed to detect patterns: {str(e)}")
        raise


@recurring.command("upcoming")
@click.option("--days", "-d", default=7, type=int, help="Number of days to look ahead")
@click.pass_context
def upcoming_charges(ctx, days):
    """
    Show recurring charges due soon.

    Example: finance recurring upcoming --days 14
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        upcoming = container.recurring_service().get_upcoming_charges(user_id, days_ahead=days)

        if not upcoming:
            print_info(f"No recurring charges due in the next {days} days.")
            return

        # Display table
        console = Console()
        table = Table(title=f"Recurring Charges Due in Next {days} Days")
        table.add_column("Due Date", justify="center")
        table.add_column("Merchant", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Amount", justify="right", style="yellow")
        table.add_column("Frequency")

        total_amount = Decimal("0")

        for charge in upcoming:
            amount = Decimal(str(charge["typical_amount"]))
            total_amount += amount

            table.add_row(
                charge.get("next_expected_date", "-"),
                charge["merchant"],
                charge["category"],
                f"${float(amount):.2f}",
                charge["frequency"].capitalize(),
            )

        console.print(table)
        print_info(f"\nTotal upcoming: ${float(total_amount):.2f}")

    except Exception as e:
        print_error(f"Failed to get upcoming charges: {str(e)}")
        raise


@recurring.command("add")
@click.argument("merchant")
@click.argument("amount", type=float)
@click.argument("frequency", type=click.Choice(["weekly", "monthly", "annual"]))
@click.option("--category", "-c", help="Transaction category")
@click.option("--notes", "-n", help="Additional notes")
@click.pass_context
def add_recurring(ctx, merchant, amount, frequency, category, notes):
    """
    Manually add a recurring charge.

    Example: finance recurring add "Netflix" 15.99 monthly --category "Entertainment - Streaming"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Default category if not provided
        category = category or "Recurring - Subscription"

        recurring = container.recurring_service().create_recurring_charge(
            user_id=user_id,
            merchant=merchant,
            category=category,
            typical_amount=Decimal(str(amount)),
            frequency=frequency,
            notes=notes,
        )

        print_success(f"Recurring charge added: {merchant}")
        print_info(f"  Amount: ${amount:.2f}")
        print_info(f"  Frequency: {frequency}")
        print_info(f"  Category: {category}")
        if recurring.get("next_expected_date"):
            print_info(f"  Next due: {recurring['next_expected_date']}")

    except Exception as e:
        print_error(f"Failed to add recurring charge: {str(e)}")
        raise


@recurring.command("cancel")
@click.argument("merchant_or_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def cancel_recurring(ctx, merchant_or_id, yes):
    """
    Cancel a recurring charge.

    Can specify by merchant name or ID.

    Example: finance recurring cancel "Netflix"
    Example: finance recurring cancel 5 -y
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Try to parse as ID first
        try:
            recurring_id = int(merchant_or_id)
            recurring = container.recurring_service().get_recurring_charge(recurring_id)
        except (ValueError, Exception):
            # Search by merchant name
            all_recurring = container.recurring_service().list_recurring_charges(user_id, status="active")
            matches = [r for r in all_recurring if r["merchant"].lower() == merchant_or_id.lower()]

            if not matches:
                print_error(f"No active recurring charge found for '{merchant_or_id}'")
                return
            if len(matches) > 1:
                print_error(f"Multiple recurring charges found for '{merchant_or_id}'. Use ID instead.")
                return

            recurring = matches[0]
            recurring_id = recurring["id"]

        # Show details
        print_info(f"Recurring charge: {recurring['merchant']}")
        print_info(f"  Amount: ${float(recurring['typical_amount']):.2f} {recurring['frequency']}")
        print_info(f"  Category: {recurring['category']}")

        # Confirm cancellation
        if not yes and not click.confirm("\nCancel this recurring charge?"):
            print_info("Cancelled")
            return

        # Cancel
        container.recurring_service().cancel_recurring_charge(recurring_id)
        print_success(f"Recurring charge cancelled: {recurring['merchant']}")

    except Exception as e:
        print_error(f"Failed to cancel recurring charge: {str(e)}")
        raise


@recurring.command("pause")
@click.argument("merchant_or_id")
@click.pass_context
def pause_recurring(ctx, merchant_or_id):
    """
    Pause a recurring charge temporarily.

    Example: finance recurring pause "Gym Membership"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Try to parse as ID first
        try:
            recurring_id = int(merchant_or_id)
        except ValueError:
            # Search by merchant name
            all_recurring = container.recurring_service().list_recurring_charges(user_id, status="active")
            matches = [r for r in all_recurring if r["merchant"].lower() == merchant_or_id.lower()]

            if not matches:
                print_error(f"No active recurring charge found for '{merchant_or_id}'")
                return
            if len(matches) > 1:
                print_error(f"Multiple recurring charges found for '{merchant_or_id}'. Use ID instead.")
                return

            recurring_id = matches[0]["id"]

        # Pause
        container.recurring_service().pause_recurring_charge(recurring_id)
        print_success(f"Recurring charge paused")
        print_info("Use 'finance recurring resume' to reactivate")

    except Exception as e:
        print_error(f"Failed to pause recurring charge: {str(e)}")
        raise


@recurring.command("resume")
@click.argument("merchant_or_id")
@click.pass_context
def resume_recurring(ctx, merchant_or_id):
    """
    Resume a paused recurring charge.

    Example: finance recurring resume "Gym Membership"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Try to parse as ID first
        try:
            recurring_id = int(merchant_or_id)
        except ValueError:
            # Search by merchant name
            all_recurring = container.recurring_service().list_recurring_charges(user_id, status="paused")
            matches = [r for r in all_recurring if r["merchant"].lower() == merchant_or_id.lower()]

            if not matches:
                print_error(f"No paused recurring charge found for '{merchant_or_id}'")
                return
            if len(matches) > 1:
                print_error(f"Multiple recurring charges found for '{merchant_or_id}'. Use ID instead.")
                return

            recurring_id = matches[0]["id"]

        # Resume
        container.recurring_service().resume_recurring_charge(recurring_id)
        print_success(f"Recurring charge resumed")

    except Exception as e:
        print_error(f"Failed to resume recurring charge: {str(e)}")
        raise
