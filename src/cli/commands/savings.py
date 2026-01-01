"""Savings goal CLI commands."""

import click
from datetime import datetime
from decimal import Decimal
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn
from ..formatters import print_success, print_error, print_info, format_currency


@click.group()
def savings():
    """Manage savings goals."""
    pass


@savings.command("add")
@click.argument("name")
@click.option("--target", "-t", required=True, type=float, help="Target amount to save")
@click.option("--deadline", "-d", help="Deadline (YYYY-MM-DD)")
@click.option("--description", help="Goal description")
@click.option("--category", "-c", help="Goal category (e.g., Emergency Fund, Vacation)")
@click.option("--priority", "-p", type=int, default=5, help="Priority (1-10, 1 is highest)")
@click.option("--notes", help="Additional notes")
@click.pass_context
def add_goal(ctx, name, target, deadline, description, category, priority, notes):
    """
    Create a new savings goal.

    Examples:
        finance savings add "Emergency Fund" --target 10000 --deadline 2024-12-31
        finance savings add "Vacation" -t 3000 -d 2024-06-01 -c Travel
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Parse deadline if provided
        deadline_date = None
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid deadline format. Use YYYY-MM-DD")
                return

        # Create goal
        goal = container.savings_goal_service().create_goal(
            user_id=user_id,
            name=name,
            target_amount=Decimal(str(target)),
            description=description,
            deadline=deadline_date,
            category=category,
            priority=priority,
            notes=notes
        )

        print_success(f"Savings goal created: {goal['name']}")
        print_info(f"Target: {format_currency(goal['target_amount'])}")
        if deadline_date:
            print_info(f"Deadline: {deadline_date}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to create savings goal: {str(e)}")
        raise


@savings.command("list")
@click.option("--status", "-s", type=click.Choice(["active", "completed", "paused", "cancelled"]), help="Filter by status")
@click.pass_context
def list_goals(ctx, status):
    """List all savings goals."""
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goals = container.savings_goal_service().list_goals(user_id, status)

        if not goals:
            status_msg = f" with status '{status}'" if status else ""
            print_info(f"No savings goals found{status_msg}.")
            print_info("Create one with: finance savings add <name> --target <amount>")
            return

        console = Console()
        table = Table(title="Savings Goals")

        table.add_column("Name", style="cyan")
        table.add_column("Progress", style="white")
        table.add_column("Current", justify="right")
        table.add_column("Target", justify="right")
        table.add_column("Remaining", justify="right")
        table.add_column("Deadline", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Priority", justify="center")

        for goal in goals:
            progress = goal.get("progress", {})
            percentage = progress.get("percentage", 0)

            # Progress bar
            bar_width = 10
            filled = int(bar_width * percentage / 100)
            bar = "#" * filled + "-" * (bar_width - filled)
            progress_str = f"{bar} {percentage:.0f}%"

            # Status icon
            status_map = {
                "active": "+",
                "completed": "V",
                "paused": "||",
                "cancelled": "X"
            }
            status_icon = status_map.get(goal["status"], "?")

            # Deadline formatting
            deadline_str = ""
            if goal["deadline"]:
                deadline_str = goal["deadline"]
                if "days_until_deadline" in progress:
                    days = progress["days_until_deadline"]
                    if days < 0:
                        deadline_str += f" (!{abs(days)}d)"
                    elif days < 30:
                        deadline_str += f" ({days}d)"

            table.add_row(
                goal["name"],
                progress_str,
                format_currency(goal["current_amount"]),
                format_currency(goal["target_amount"]),
                format_currency(progress["remaining"]),
                deadline_str,
                f"{status_icon} {goal['status']}",
                str(goal["priority"])
            )

        console.print(table)

        # Summary
        total_target = sum(Decimal(str(g["target_amount"])) for g in goals)
        total_current = sum(Decimal(str(g["current_amount"])) for g in goals)
        print_info(f"\nTotal: {format_currency(total_current)} of {format_currency(total_target)}")

    except Exception as e:
        print_error(f"Failed to list savings goals: {str(e)}")
        raise


@savings.command("view")
@click.argument("name")
@click.pass_context
def view_goal(ctx, name):
    """View detailed information about a savings goal."""
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goal = container.savings_goal_service().get_goal_by_name(user_id, name)

        if not goal:
            print_error(f"Savings goal '{name}' not found")
            return

        # Get recommendations
        recommendations = container.savings_goal_service().get_recommendations(user_id, goal["id"])
        progress = recommendations["progress"]

        console = Console()

        # Main panel
        panel_content = f"[bold]{goal['name']}[/bold]\n\n"

        if goal.get("description"):
            panel_content += f"{goal['description']}\n\n"

        panel_content += f"Target: {format_currency(goal['target_amount'])}\n"
        panel_content += f"Current: {format_currency(progress['current'])}\n"
        panel_content += f"Remaining: {format_currency(progress['remaining'])}\n"
        panel_content += f"Progress: {progress['percentage']:.1f}%\n\n"

        if goal.get("category"):
            panel_content += f"Category: {goal['category']}\n"

        panel_content += f"Priority: {goal['priority']}\n"
        panel_content += f"Status: {goal['status']}\n"

        if goal.get("deadline"):
            panel_content += f"Deadline: {goal['deadline']}\n"

            if "days_until_deadline" in progress:
                days = progress["days_until_deadline"]
                if days > 0:
                    panel_content += f"Days remaining: {days}\n"
                else:
                    panel_content += f"[red]Overdue by {abs(days)} days[/red]\n"

        console.print(Panel(panel_content, border_style="cyan"))

        # Required savings
        if recommendations.get("required_savings"):
            req = recommendations["required_savings"]
            print_info("\n=== Required Savings ===")
            print_info(f"Daily:   {format_currency(req['daily'])}")
            print_info(f"Weekly:  {format_currency(req['weekly'])}")
            print_info(f"Monthly: {format_currency(req['monthly'])}")

        # Suggestions
        if recommendations.get("suggestions"):
            print_info("\n=== Recommendations ===")
            for suggestion in recommendations["suggestions"]:
                print_info(f"+ {suggestion}")

        if goal.get("notes"):
            print_info(f"\nNotes: {goal['notes']}")

    except Exception as e:
        print_error(f"Failed to view savings goal: {str(e)}")
        raise


@savings.command("contribute")
@click.argument("name")
@click.argument("amount", type=float)
@click.option("--description", "-d", help="Contribution description")
@click.pass_context
def contribute(ctx, name, amount, description):
    """
    Add money to a savings goal.

    Examples:
        finance savings contribute "Emergency Fund" 500
        finance savings contribute Vacation 100 -d "Weekly savings"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goal = container.savings_goal_service().get_goal_by_name(user_id, name)

        if not goal:
            print_error(f"Savings goal '{name}' not found")
            return

        # Add contribution
        updated_goal = container.savings_goal_service().add_contribution(
            goal["id"],
            Decimal(str(amount)),
            description
        )

        progress = updated_goal["progress"]

        print_success(f"Added {format_currency(amount)} to {name}")
        print_info(f"New balance: {format_currency(progress['current'])} / {format_currency(progress['target'])} ({progress['percentage']:.1f}%)")

        if progress["is_complete"]:
            print_success("Goal completed! Congratulations!")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to add contribution: {str(e)}")
        raise


@savings.command("withdraw")
@click.argument("name")
@click.argument("amount", type=float)
@click.option("--reason", "-r", help="Reason for withdrawal")
@click.pass_context
def withdraw(ctx, name, amount, reason):
    """
    Withdraw money from a savings goal.

    Examples:
        finance savings withdraw "Emergency Fund" 200 -r "Medical expense"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goal = container.savings_goal_service().get_goal_by_name(user_id, name)

        if not goal:
            print_error(f"Savings goal '{name}' not found")
            return

        # Withdraw
        updated_goal = container.savings_goal_service().withdraw(
            goal["id"],
            Decimal(str(amount)),
            reason
        )

        progress = updated_goal["progress"]

        print_success(f"Withdrew {format_currency(amount)} from {name}")
        print_info(f"New balance: {format_currency(progress['current'])} / {format_currency(progress['target'])} ({progress['percentage']:.1f}%)")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to withdraw: {str(e)}")
        raise


@savings.command("edit")
@click.argument("name")
@click.option("--target", "-t", type=float, help="New target amount")
@click.option("--deadline", "-d", help="New deadline (YYYY-MM-DD)")
@click.option("--priority", "-p", type=int, help="New priority (1-10)")
@click.option("--description", help="New description")
@click.option("--category", "-c", help="New category")
@click.option("--notes", help="New notes")
@click.pass_context
def edit_goal(ctx, name, target, deadline, priority, description, category, notes):
    """
    Edit a savings goal.

    Examples:
        finance savings edit "Emergency Fund" --target 15000
        finance savings edit Vacation -d 2024-08-01 -p 3
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goal = container.savings_goal_service().get_goal_by_name(user_id, name)

        if not goal:
            print_error(f"Savings goal '{name}' not found")
            return

        # Build updates dict
        updates = {}

        if target is not None:
            updates["target_amount"] = Decimal(str(target))

        if deadline:
            try:
                updates["deadline"] = datetime.strptime(deadline, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid deadline format. Use YYYY-MM-DD")
                return

        if priority is not None:
            updates["priority"] = priority

        if description is not None:
            updates["description"] = description

        if category is not None:
            updates["category"] = category

        if notes is not None:
            updates["notes"] = notes

        if not updates:
            print_error("No updates specified. Use --target, --deadline, --priority, etc.")
            return

        # Update goal
        updated_goal = container.savings_goal_service().update_goal(goal["id"], **updates)

        print_success(f"Updated savings goal: {name}")

        # Show what changed
        for key, value in updates.items():
            if key == "target_amount":
                print_info(f"Target: {format_currency(value)}")
            elif key == "deadline":
                print_info(f"Deadline: {value}")
            elif key == "priority":
                print_info(f"Priority: {value}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to edit savings goal: {str(e)}")
        raise


@savings.command("status")
@click.argument("name")
@click.argument("new_status", type=click.Choice(["active", "completed", "paused", "cancelled"]))
@click.pass_context
def change_status(ctx, name, new_status):
    """
    Change savings goal status.

    Examples:
        finance savings status "Emergency Fund" paused
        finance savings status Vacation active
        finance savings status "Old Goal" cancelled
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goal = container.savings_goal_service().get_goal_by_name(user_id, name)

        if not goal:
            print_error(f"Savings goal '{name}' not found")
            return

        old_status = goal["status"]

        if old_status == new_status:
            print_info(f"Goal is already {new_status}")
            return

        # Update status
        container.savings_goal_service().update_status(goal["id"], new_status)

        print_success(f"Changed {name} status: {old_status} -> {new_status}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to change status: {str(e)}")
        raise


@savings.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_goal(ctx, name, yes):
    """
    Delete a savings goal.

    Examples:
        finance savings delete "Old Goal"
        finance savings delete "Emergency Fund" -y
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goal = container.savings_goal_service().get_goal_by_name(user_id, name)

        if not goal:
            print_error(f"Savings goal '{name}' not found")
            return

        # Show goal details
        current = Decimal(str(goal["current_amount"]))
        target = Decimal(str(goal["target_amount"]))

        print_info(f"Goal: {goal['name']}")
        print_info(f"Balance: {format_currency(current)} / {format_currency(target)}")
        print_info(f"Status: {goal['status']}")

        if current > 0 and not yes:
            print_info(f"\nWarning: This goal has {format_currency(current)} saved.")

        # Confirm deletion
        if not yes:
            if not click.confirm("\nAre you sure you want to delete this goal?"):
                print_info("Deletion cancelled")
                return

        # Delete goal
        container.savings_goal_service().delete_goal(goal["id"])

        print_success(f"Deleted savings goal: {name}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to delete savings goal: {str(e)}")
        raise


@savings.command("recommend")
@click.argument("name")
@click.pass_context
def get_recommendations(ctx, name):
    """
    Get AI-powered savings recommendations for a goal.

    Examples:
        finance savings recommend "Emergency Fund"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        goal = container.savings_goal_service().get_goal_by_name(user_id, name)

        if not goal:
            print_error(f"Savings goal '{name}' not found")
            return

        recommendations = container.savings_goal_service().get_recommendations(user_id, goal["id"])

        console = Console()

        # Title
        print_info(f"Recommendations for: {goal['name']}\n")

        # Required savings
        if recommendations.get("required_savings"):
            req = recommendations["required_savings"]
            panel_content = f"Daily:   {format_currency(req['daily'])}\n"
            panel_content += f"Weekly:  {format_currency(req['weekly'])}\n"
            panel_content += f"Monthly: {format_currency(req['monthly'])}\n"
            panel_content += f"\nDays remaining: {req['days_remaining']}"

            console.print(Panel(panel_content, title="Required Savings", border_style="yellow"))

        # Suggestions
        if recommendations.get("suggestions"):
            print_info("\n=== Tips ===")
            for i, suggestion in enumerate(recommendations["suggestions"], 1):
                print_info(f"{i}. {suggestion}")

    except Exception as e:
        print_error(f"Failed to get recommendations: {str(e)}")
        raise
