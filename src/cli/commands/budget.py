"""Budget CLI commands."""

import click
from decimal import Decimal
from ..formatters import print_success, print_error, print_budget_status, print_info


@click.group()
def budget():
    """Manage budgets."""
    pass


@budget.command("add")
@click.argument("category")
@click.argument("limit", type=float)
@click.pass_context
def add_budget(ctx, category, limit):
    """
    Add a budget for a category.

    Example: finance budget add "Food & Dining - Restaurants" 300
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        budget = container.budget_service().create_budget(
            user_id=user_id, category=category, monthly_limit=Decimal(str(limit))
        )

        print_success(f"Budget created for {category}")
        print_info(f"Monthly limit: ${budget['monthly_limit']:.2f}")

    except Exception as e:
        print_error(f"Failed to create budget: {str(e)}")
        raise


@budget.command("list")
@click.pass_context
def list_budgets(ctx):
    """List all budgets."""
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        budgets = container.budget_service().list_budgets(user_id)

        if not budgets:
            print_info("No budgets found. Create one with: finance budget add")
            return

        for b in budgets:
            print_info(f"{b['category']}: ${b['monthly_limit']:.2f}/month")

    except Exception as e:
        print_error(f"Failed to list budgets: {str(e)}")
        raise


@budget.command("status")
@click.option("--month", "-m", help="Month to check (MM or YYYY-MM)")
@click.pass_context
def budget_status(ctx, month):
    """Show budget status for current month."""
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Parse month if provided
        year = None
        month_num = None
        if month:
            from datetime import datetime

            if "-" in month:
                year, month_num = map(int, month.split("-"))
            else:
                year = datetime.now().year
                month_num = int(month)

        budget_statuses = container.budget_service().get_all_budget_status(user_id, year, month_num)
        print_budget_status(budget_statuses)

    except Exception as e:
        print_error(f"Failed to get budget status: {str(e)}")
        raise


@budget.command("edit")
@click.argument("category")
@click.option("--limit", "-l", type=float, help="New monthly limit")
@click.option("--threshold", "-t", type=float, help="Alert threshold (0.0-1.0)")
@click.pass_context
def edit_budget(ctx, category, limit, threshold):
    """
    Edit an existing budget.

    Example: finance budget edit "Food & Dining - Restaurants" --limit 400
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Check if any fields are being updated
        if not any([limit, threshold]):
            print_error("No fields to update. Use --help to see available options.")
            return

        # Validate threshold range
        if threshold is not None and (threshold < 0 or threshold > 1):
            print_error("Alert threshold must be between 0.0 and 1.0")
            return

        # Get current budget
        budget = container.budget_service().budget_repo.get_by_category(user_id, category)
        if not budget:
            print_error(f"No budget found for category '{category}'")
            return

        # Show current values
        print_info(f"Current budget for {category}:")
        print_info(f"  Limit: ${budget['monthly_limit']:.2f}")
        print_info(f"  Alert Threshold: {float(budget['alert_threshold']) * 100:.0f}%")

        # Build updates
        updates = {}
        if limit is not None:
            updates["monthly_limit"] = float(limit)
        if threshold is not None:
            updates["alert_threshold"] = float(threshold)

        # Update budget
        container.budget_service().update_budget(budget["id"], **updates)

        # Show updated values
        updated = container.budget_service().get_budget(budget["id"])
        print_success(f"Budget updated for {category}")
        print_info(f"  New Limit: ${updated['monthly_limit']:.2f}")
        print_info(f"  New Alert Threshold: {float(updated['alert_threshold']) * 100:.0f}%")

    except Exception as e:
        print_error(f"Failed to edit budget: {str(e)}")
        raise


@budget.command("delete")
@click.argument("category")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_budget(ctx, category, yes):
    """
    Delete a budget.

    Example: finance budget delete "Food & Dining - Restaurants"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get budget
        budget = container.budget_service().budget_repo.get_by_category(user_id, category)
        if not budget:
            print_error(f"No budget found for category '{category}'")
            return

        # Show budget details
        print_info(f"Budget for {category}:")
        print_info(f"  Monthly Limit: ${budget['monthly_limit']:.2f}")
        print_info(f"  Alert Threshold: {float(budget['alert_threshold']) * 100:.0f}%")

        # Confirm deletion
        if not yes and not click.confirm(f"\nDelete this budget?"):
            print_info("Cancelled")
            return

        # Delete budget
        container.budget_service().delete_budget(budget["id"])
        print_success(f"Budget deleted for {category}")

    except Exception as e:
        print_error(f"Failed to delete budget: {str(e)}")
        raise


@budget.command("alerts")
@click.option("--month", "-m", help="Month to check (MM or YYYY-MM)")
@click.pass_context
def budget_alerts(ctx, month):
    """
    Show budget alerts (approaching or over limit).

    Example: finance budget alerts
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Parse month if provided
        year = None
        month_num = None
        if month:
            from datetime import datetime

            if "-" in month:
                year, month_num = map(int, month.split("-"))
            else:
                year = datetime.now().year
                month_num = int(month)

        # Get all budget statuses
        budget_statuses = container.budget_service().get_all_budget_status(user_id, year, month_num)

        # Filter to only alerts
        alerts = [s for s in budget_statuses if s and (s["should_alert"] or s["is_over"])]

        if not alerts:
            print_success("No budget alerts! All budgets are healthy.")
            return

        # Show alerts
        print_warning(f"Found {len(alerts)} budget alert(s):")
        print_budget_status(alerts, show_alerts_only=True)

    except Exception as e:
        print_error(f"Failed to check budget alerts: {str(e)}")
        raise
