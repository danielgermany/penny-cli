"""Reporting and analytics CLI commands."""

import click
from datetime import date
from decimal import Decimal
from rich.console import Console
from rich.table import Table
from ..formatters import print_success, print_error, print_info, format_currency


@click.group()
def report():
    """Generate financial reports and analytics."""
    pass


@report.command("monthly")
@click.option("--month", "-m", help="Month (MM or YYYY-MM), defaults to current")
@click.option("--compare", "-c", is_flag=True, help="Compare to previous month")
@click.pass_context
def monthly_summary(ctx, month, compare):
    """
    Generate monthly summary report.

    Shows income, expenses, savings, category breakdown, and top merchants.

    Example: finance report monthly --month 2024-12 --compare
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Parse month
        if month:
            if "-" in month:
                year, mon = map(int, month.split("-"))
            else:
                mon = int(month)
                year = date.today().year
        else:
            today = date.today()
            year = today.year
            mon = today.month

        if compare:
            # Get comparison data
            comparison = container.analytics_service().compare_to_previous_month(user_id, year, mon)
            current = comparison["current"]
            previous = comparison["previous"]

            # Display current month summary
            _print_monthly_summary(current, f"{year}-{mon:02d} vs {previous['year']}-{previous['month']:02d}")

            # Display comparison
            console = Console()
            print_info("\nComparison to Previous Month:")

            table = Table()
            table.add_column("Metric")
            table.add_column("Current", justify="right")
            table.add_column("Previous", justify="right")
            table.add_column("Change", justify="right")

            # Income comparison
            income_color = "green" if comparison["income_change"] >= 0 else "red"
            table.add_row(
                "Income",
                format_currency(current["total_income"]),
                format_currency(previous["total_income"]),
                f"[{income_color}]{format_currency(comparison['income_change'])} ({float(comparison['income_change_pct']):.1f}%)[/{income_color}]"
            )

            # Expense comparison
            expense_color = "green" if comparison["expense_change"] <= 0 else "red"
            table.add_row(
                "Expenses",
                format_currency(current["total_expenses"]),
                format_currency(previous["total_expenses"]),
                f"[{expense_color}]{format_currency(comparison['expense_change'])} ({float(comparison['expense_change_pct']):.1f}%)[/{expense_color}]"
            )

            # Savings comparison
            savings_color = "green" if comparison["savings_change"] >= 0 else "red"
            table.add_row(
                "Savings",
                format_currency(current["savings"]),
                format_currency(previous["savings"]),
                f"[{savings_color}]{format_currency(comparison['savings_change'])}[/{savings_color}]"
            )

            console.print(table)

        else:
            # Just current month
            summary = container.analytics_service().get_monthly_summary(user_id, year, mon)
            _print_monthly_summary(summary, f"{year}-{mon:02d}")

    except Exception as e:
        print_error(f"Failed to generate monthly report: {str(e)}")
        raise


def _print_monthly_summary(summary: dict, title: str):
    """Helper to print monthly summary."""
    console = Console()

    # Overview
    print_info(f"\n=== Monthly Summary: {title} ===\n")

    table = Table(title="Overview")
    table.add_column("Metric", style="cyan")
    table.add_column("Amount", justify="right", style="yellow")

    table.add_row("Income", f"[green]{format_currency(summary['total_income'])}[/green]")
    table.add_row("Expenses", f"[red]{format_currency(summary['total_expenses'])}[/red]")

    savings_color = "green" if summary["savings"] >= 0 else "red"
    table.add_row(
        "Savings",
        f"[{savings_color}]{format_currency(summary['savings'])} ({float(summary['savings_rate']):.1f}%)[/{savings_color}]"
    )
    table.add_row("Transactions", str(summary["transaction_count"]))

    console.print(table)

    # Category breakdown
    if summary["category_breakdown"]:
        print_info("\n=== Category Breakdown ===\n")
        cat_table = Table(title="Spending by Category")
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Amount", justify="right", style="yellow")
        cat_table.add_column("% of Expenses", justify="right")

        for cat in summary["category_breakdown"][:10]:  # Top 10
            cat_table.add_row(
                cat["category"],
                format_currency(cat["amount"]),
                f"{float(cat['percentage']):.1f}%"
            )

        console.print(cat_table)

    # Top merchants
    if summary["top_merchants"]:
        print_info("\n=== Top Merchants ===\n")
        merchant_table = Table(title="Top 10 Merchants")
        merchant_table.add_column("Merchant", style="cyan")
        merchant_table.add_column("Amount", justify="right", style="yellow")

        for merch in summary["top_merchants"]:
            merchant_table.add_row(
                merch["merchant"],
                format_currency(merch["amount"])
            )

        console.print(merchant_table)


@report.command("category")
@click.argument("category_name")
@click.option("--months", "-m", default=6, type=int, help="Number of months to analyze")
@click.pass_context
def category_analysis(ctx, category_name, months):
    """
    Detailed analysis for a specific category.

    Shows trends, top merchants, and statistics over time.

    Example: finance report category "Food & Dining - Restaurants" --months 12
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        analysis = container.analytics_service().get_category_analysis(user_id, category_name, months)

        console = Console()
        print_info(f"\n=== Category Analysis: {category_name} ===\n")

        # Statistics
        stats_table = Table(title=f"Statistics (Last {months} Months)")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", justify="right", style="yellow")

        stats_table.add_row("Total Spent", format_currency(analysis["total_spent"]))
        stats_table.add_row("Total Transactions", str(analysis["total_transactions"]))
        stats_table.add_row("Average Amount", format_currency(analysis["avg_amount"]))
        stats_table.add_row("Min Amount", format_currency(analysis["min_amount"]))
        stats_table.add_row("Max Amount", format_currency(analysis["max_amount"]))

        trend_color = "red" if analysis["trend_direction"] == "increasing" else "green"
        stats_table.add_row(
            "Trend",
            f"[{trend_color}]{analysis['trend_direction'].capitalize()}[/{trend_color}]"
        )

        console.print(stats_table)

        # Monthly trend
        if analysis["monthly_totals"]:
            print_info("\n=== Monthly Trend ===\n")
            trend_table = Table()
            trend_table.add_column("Month", justify="center")
            trend_table.add_column("Amount", justify="right", style="yellow")
            trend_table.add_column("Transactions", justify="right")

            for month_data in analysis["monthly_totals"]:
                trend_table.add_row(
                    f"{month_data['year']}-{month_data['month']:02d}",
                    format_currency(month_data["total"]),
                    str(month_data["count"])
                )

            console.print(trend_table)

        # Top merchants
        if analysis["top_merchants"]:
            print_info("\n=== Top Merchants ===\n")
            merchant_table = Table(title="Top 5 Merchants in Category")
            merchant_table.add_column("Merchant", style="cyan")
            merchant_table.add_column("Amount", justify="right", style="yellow")
            merchant_table.add_column("% of Category", justify="right")

            for merch in analysis["top_merchants"]:
                merchant_table.add_row(
                    merch["merchant"],
                    format_currency(merch["amount"]),
                    f"{float(merch['percentage']):.1f}%"
                )

            console.print(merchant_table)

    except Exception as e:
        print_error(f"Failed to generate category analysis: {str(e)}")
        raise


@report.command("trends")
@click.option("--weeks", "-w", default=4, type=int, help="Number of weeks to analyze")
@click.pass_context
def spending_trends(ctx, weeks):
    """
    Analyze spending trends over recent weeks.

    Identifies week-over-week patterns and unusual spending.

    Example: finance report trends --weeks 8
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        trends = container.analytics_service().get_spending_trends(user_id, weeks)

        console = Console()
        print_info(f"\n=== Spending Trends (Last {weeks} Weeks) ===\n")

        # Weekly breakdown
        table = Table(title="Weekly Spending")
        table.add_column("Week", justify="center")
        table.add_column("Total", justify="right", style="yellow")
        table.add_column("Transactions", justify="right")
        table.add_column("Avg/Day", justify="right")

        for week in trends["weekly_data"]:
            # Highlight unusual weeks
            is_unusual = week in trends["unusual_weeks"]
            style = "bold red" if is_unusual else ""

            table.add_row(
                f"{week['week_start']} to {week['week_end']}",
                format_currency(week["total"]),
                str(week["count"]),
                format_currency(week["avg_per_day"]),
                style=style
            )

        console.print(table)

        # Summary
        print_info(f"\nAverage weekly spending: {format_currency(trends['avg_weekly_spending'])}")

        if trends["unusual_weeks"]:
            print_info(f"Unusual weeks detected: {len(trends['unusual_weeks'])} (>20% above average)")

    except Exception as e:
        print_error(f"Failed to generate spending trends: {str(e)}")
        raise


@report.command("accounts")
@click.pass_context
def account_summary(ctx):
    """
    Summary of all accounts with balances and recent activity.

    Shows net worth, account balances, and income/expenses per account.

    Example: finance report accounts
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        summary = container.analytics_service().get_account_summary(user_id)

        console = Console()
        print_info("\n=== Account Summary ===\n")

        # Net worth
        net_worth_color = "green" if summary["net_worth"] >= 0 else "red"
        print_info(f"Net Worth: [{net_worth_color}]{format_currency(summary['net_worth'])}[/{net_worth_color}]")
        print_info(f"Active Accounts: {summary['account_count']}\n")

        # Account details
        table = Table(title="Account Details (Last 30 Days)")
        table.add_column("Account", style="cyan")
        table.add_column("Type")
        table.add_column("Balance", justify="right", style="yellow")
        table.add_column("Income", justify="right", style="green")
        table.add_column("Expenses", justify="right", style="red")
        table.add_column("Net", justify="right")
        table.add_column("Txns", justify="right")

        for acc in summary["accounts"]:
            balance_color = "green" if acc["balance"] >= 0 else "red"
            net_color = "green" if acc["last_30_days"]["net"] >= 0 else "red"

            table.add_row(
                acc["name"],
                acc["type"].replace("_", " ").title(),
                f"[{balance_color}]{format_currency(acc['balance'])}[/{balance_color}]",
                format_currency(acc["last_30_days"]["income"]),
                format_currency(acc["last_30_days"]["expenses"]),
                f"[{net_color}]{format_currency(acc['last_30_days']['net'])}[/{net_color}]",
                str(acc["last_30_days"]["transaction_count"])
            )

        console.print(table)

    except Exception as e:
        print_error(f"Failed to generate account summary: {str(e)}")
        raise
