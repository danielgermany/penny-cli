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
