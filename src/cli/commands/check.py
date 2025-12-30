"""Decision support CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from ..formatters import print_success, print_error, print_info, print_warning, format_currency


@click.command("check")
@click.argument("question", nargs=-1, required=True)
@click.pass_context
def check_affordability(ctx, question):
    """
    AI-powered spending decision support.

    Ask if you can afford a purchase and get intelligent recommendations
    based on your budgets, upcoming bills, and financial health.

    Examples:
        finance check Can I afford $80 dinner tonight?
        finance check Should I spend $150 on shoes?
        finance check Can I afford a $50 gift?
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    # Join question parts into single string
    question_str = " ".join(question)

    if not question_str:
        print_error("Please provide a question.")
        print_info("Example: finance check Can I afford $80 dinner?")
        return

    try:
        print_info("Analyzing your financial situation...")

        # Get AI-powered recommendation
        result = container.decision_support_service().can_afford(user_id, question_str)

        if not result.get("success"):
            print_error(result.get("error", "Failed to analyze affordability"))
            return

        # Display result with rich formatting
        console = Console()

        # Color code based on decision
        decision = result["recommendation"]
        if decision == "YES":
            decision_color = "green"
            icon = "+"
        elif decision == "MAYBE":
            decision_color = "yellow"
            icon = "!"
        else:
            decision_color = "red"
            icon = "X"

        # Main recommendation panel
        panel_content = f"[{decision_color} bold]{icon} {decision}[/{decision_color} bold]\n\n"
        panel_content += f"{result['reasoning']}"

        console.print(Panel(
            panel_content,
            title=f"Spending Check: ${result['amount']:.2f}",
            border_style=decision_color
        ))

        # Show supporting context
        context = result.get("context", {})

        if context:
            print_info("\n=== Financial Context ===")

            # Account balance
            print_info(f"Total Balance: {format_currency(context.get('total_balance', 0))}")

            # Budgets
            if context.get("budgets"):
                print_info("\nRelevant Budgets:")
                for budget in context["budgets"][:3]:  # Top 3 most relevant
                    status_icon = "X" if budget["is_over"] else ("!" if budget["percentage"] > 80 else "+")
                    print_info(f"  {status_icon} {budget['category']}: "
                             f"{format_currency(budget['remaining'])} remaining of {format_currency(budget['limit'])}")

            # Upcoming bills
            if context.get("upcoming_charges"):
                print_info(f"\nUpcoming Bills (7 days): {format_currency(context['upcoming_total'])}")
                for charge in context["upcoming_charges"][:3]:  # Show first 3
                    print_info(f"  - {charge['merchant']}: {format_currency(charge['amount'])} on {charge.get('due_date', 'soon')}")

            # Recent spending
            if context.get("last_week_spending"):
                print_info(f"\nLast Week Spending: {format_currency(context['last_week_spending'])}")

    except Exception as e:
        print_error(f"Failed to check affordability: {str(e)}")
        raise
