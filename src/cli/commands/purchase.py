"""Planned purchase CLI commands."""

import click
from datetime import datetime
from decimal import Decimal
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..formatters import print_success, print_error, print_info, format_currency


@click.group()
def purchase():
    """Manage planned purchases and shopping list."""
    pass


@purchase.command("add")
@click.argument("name")
@click.option("--cost", "-c", required=True, type=float, help="Estimated cost")
@click.option("--priority", "-p", type=int, default=3, help="Priority (1=Critical, 2=High, 3=Moderate, 4=Low, 5=Want)")
@click.option("--category", help="Category (e.g., Groceries, Electronics)")
@click.option("--deadline", "-d", help="Target date (YYYY-MM-DD)")
@click.option("--description", help="Description")
@click.option("--notes", "-n", help="Additional notes")
@click.option("--url", "-u", help="Product URL")
@click.pass_context
def add_purchase(ctx, name, cost, priority, category, deadline, description, notes, url):
    """
    Add a planned purchase to your shopping list.

    Priority levels:
      1 = Critical/Necessity (bills, medical, safety)
      2 = High Priority (hygiene, work-related)
      3 = Moderate (needed but can wait)
      4 = Low Priority (nice to have)
      5 = Want/Luxury

    Examples:
        finance purchase add "Rent" --cost 1200 --priority 1 --deadline 2026-01-15
        finance purchase add "Toothpaste" -c 5 -p 2
        finance purchase add "New Headphones" -c 150 -p 5 --url "https://..."
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

        # Create purchase
        purchase = container.planned_purchase_service().create_purchase(
            user_id=user_id,
            name=name,
            estimated_cost=Decimal(str(cost)),
            priority=priority,
            description=description,
            category=category,
            deadline=deadline_date,
            notes=notes,
            url=url
        )

        priority_label = container.planned_purchase_service().get_priority_label(priority)

        print_success(f"Added to shopping list: {purchase['name']}")
        print_info(f"Cost: {format_currency(cost)}")
        print_info(f"Priority: {priority} - {priority_label}")

        if deadline_date:
            print_info(f"Target date: {deadline_date}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to add purchase: {str(e)}")
        raise


@purchase.command("list")
@click.option("--priority", "-p", type=int, help="Filter by priority level")
@click.option("--affordable", "-a", is_flag=True, help="Show only affordable items")
@click.option("--status", "-s", type=click.Choice(["planned", "purchased", "cancelled"]), default="planned")
@click.pass_context
def list_purchases(ctx, priority, affordable, status):
    """
    List planned purchases in your shopping list.

    By default, shows all planned purchases sorted by priority.
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        purchases = container.planned_purchase_service().list_purchases(
            user_id=user_id,
            status=status,
            priority=priority,
            show_affordability=affordable or True  # Always calculate for display
        )

        if not purchases:
            filter_msg = f" with priority {priority}" if priority else ""
            print_info(f"No {status} purchases found{filter_msg}.")
            print_info("Add items with: finance purchase add <name> --cost <amount>")
            return

        # Filter if affordable flag is set
        if affordable:
            purchases = [p for p in purchases if p.get("can_afford", False)]
            if not purchases:
                print_info("No affordable purchases in your list.")
                print_info("Save more or reduce priorities to afford planned items.")
                return

        console = Console()
        table = Table(title=f"{status.capitalize()} Purchases")

        table.add_column("ID", style="dim", width=4)
        table.add_column("Name", style="cyan")
        table.add_column("Cost", justify="right")
        table.add_column("Priority", justify="center", width=10)
        table.add_column("Category")
        table.add_column("Deadline", justify="center")
        table.add_column("Affordable", justify="center", width=10)

        for p in purchases:
            # Priority display
            priority_icons = {1: "!!!", 2: "!!", 3: "!", 4: "-", 5: "~"}
            priority_icon = priority_icons.get(p["priority"], "?")
            priority_label = container.planned_purchase_service().get_priority_label(p["priority"])
            priority_str = f"{priority_icon} {p['priority']}"

            # Deadline display
            deadline_str = p["deadline"] if p.get("deadline") else "-"
            if p.get("deadline"):
                from datetime import datetime, date
                deadline_date = datetime.strptime(p["deadline"], "%Y-%m-%d").date() if isinstance(p["deadline"], str) else p["deadline"]
                days_until = (deadline_date - date.today()).days
                if days_until < 0:
                    deadline_str += " (!)"
                elif days_until <= 7:
                    deadline_str += f" ({days_until}d)"

            # Affordability
            can_afford = p.get("can_afford", False)
            affordable_str = "Yes" if can_afford else "No"

            table.add_row(
                str(p["id"]),
                p["name"],
                format_currency(p["estimated_cost"]),
                priority_str,
                p.get("category") or "-",
                deadline_str,
                affordable_str
            )

        console.print(table)

        # Summary
        total_cost = sum(Decimal(str(p["estimated_cost"])) for p in purchases)
        affordable_count = sum(1 for p in purchases if p.get("can_afford", False))

        print_info(f"\nTotal: {len(purchases)} items, {format_currency(total_cost)}")
        print_info(f"Affordable now: {affordable_count}/{len(purchases)}")

    except Exception as e:
        print_error(f"Failed to list purchases: {str(e)}")
        raise


@purchase.command("recommend")
@click.pass_context
def get_recommendations(ctx):
    """
    Get AI-powered recommendations for what to buy and when.

    Analyzes your priorities, budget, and deadlines to suggest:
    - What to buy now
    - What to buy soon
    - What to save for later
    - What to skip/delay
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        print_info("Analyzing your planned purchases...\n")

        result = container.planned_purchase_service().get_purchase_recommendations(user_id)

        if not result["recommendations"]["now"] and not result["recommendations"]["soon"] and not result["recommendations"]["later"]:
            print_info("No planned purchases found.")
            print_info("Add items with: finance purchase add <name> --cost <amount>")
            return

        console = Console()

        # Buy Now section
        if result["recommendations"]["now"]:
            print_info("=== BUY NOW (Critical/Urgent) ===")
            for p in result["recommendations"]["now"]:
                priority_label = container.planned_purchase_service().get_priority_label(p["priority"])
                print_info(f"  ! {p['name']} - {format_currency(p['estimated_cost'])} ({priority_label})")
            print()

        # Buy Soon section
        if result["recommendations"]["soon"]:
            print_info("=== BUY SOON (Next 1-2 weeks) ===")
            for p in result["recommendations"]["soon"]:
                priority_label = container.planned_purchase_service().get_priority_label(p["priority"])
                print_info(f"  + {p['name']} - {format_currency(p['estimated_cost'])} ({priority_label})")
            print()

        # Buy Later section
        if result["recommendations"]["later"]:
            print_info("=== SAVE FOR LATER ===")
            for p in result["recommendations"]["later"][:5]:  # Show first 5
                print_info(f"  - {p['name']} - {format_currency(p['estimated_cost'])}")
            if len(result["recommendations"]["later"]) > 5:
                print_info(f"  ... and {len(result['recommendations']['later']) - 5} more")
            print()

        # Skip section
        if result["recommendations"]["skip"]:
            print_info("=== SKIP/DELAY (Low priority or not affordable) ===")
            for p in result["recommendations"]["skip"][:3]:
                print_info(f"  ~ {p['name']} - {format_currency(p['estimated_cost'])}")
            if len(result["recommendations"]["skip"]) > 3:
                print_info(f"  ... and {len(result["recommendations"]["skip"]) - 3} more")
            print()

        # Financial summary
        analysis = result["analysis"]
        print_info("=== Financial Overview ===")
        print_info(f"Current balance: {format_currency(analysis['total_balance'])}")
        print_info(f"Total planned: {format_currency(analysis['total_planned'])}")

        if analysis["can_afford_all"]:
            print_success("You can afford all planned purchases!")
        else:
            shortfall = analysis["total_planned"] - analysis["total_balance"]
            print_info(f"Need to save: {format_currency(shortfall)}")

    except Exception as e:
        print_error(f"Failed to get recommendations: {str(e)}")
        raise


@purchase.command("bought")
@click.argument("purchase_id", type=int)
@click.option("--cost", "-c", type=float, help="Actual cost paid")
@click.option("--transaction", "-t", type=int, help="Link to transaction ID")
@click.pass_context
def mark_bought(ctx, purchase_id, cost, transaction):
    """
    Mark a planned purchase as bought.

    Examples:
        finance purchase bought 5 --cost 49.99
        finance purchase bought 3 -c 120 -t 456
    """
    container = ctx.obj["container"]

    try:
        purchase = container.planned_purchase_service().get_purchase(purchase_id)
        if not purchase:
            print_error(f"Purchase {purchase_id} not found")
            return

        if purchase["status"] != "planned":
            print_error(f"Purchase is already {purchase['status']}")
            return

        # Use estimated cost if actual not provided
        actual_cost = Decimal(str(cost)) if cost else Decimal(str(purchase["estimated_cost"]))

        # Mark as purchased
        updated = container.planned_purchase_service().mark_purchased(
            purchase_id,
            actual_cost,
            transaction
        )

        print_success(f"Marked as purchased: {updated['name']}")
        print_info(f"Actual cost: {format_currency(actual_cost)}")

        # Show savings if different
        estimated = Decimal(str(purchase["estimated_cost"]))
        if actual_cost < estimated:
            saved = estimated - actual_cost
            print_success(f"Saved: {format_currency(saved)}")
        elif actual_cost > estimated:
            over = actual_cost - estimated
            print_info(f"Over budget by: {format_currency(over)}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to mark as bought: {str(e)}")
        raise


@purchase.command("delete")
@click.argument("purchase_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_purchase(ctx, purchase_id, yes):
    """
    Delete a planned purchase.

    Examples:
        finance purchase delete 5
        finance purchase delete 3 -y
    """
    container = ctx.obj["container"]

    try:
        purchase = container.planned_purchase_service().get_purchase(purchase_id)
        if not purchase:
            print_error(f"Purchase {purchase_id} not found")
            return

        print_info(f"Purchase: {purchase['name']}")
        print_info(f"Cost: {format_currency(purchase['estimated_cost'])}")

        if not yes:
            if not click.confirm("\nDelete this purchase?"):
                print_info("Deletion cancelled")
                return

        container.planned_purchase_service().delete_purchase(purchase_id)
        print_success(f"Deleted: {purchase['name']}")

    except Exception as e:
        print_error(f"Failed to delete purchase: {str(e)}")
        raise


@purchase.command("view")
@click.argument("purchase_id", type=int)
@click.pass_context
def view_purchase(ctx, purchase_id):
    """View detailed information about a planned purchase."""
    container = ctx.obj["container"]

    try:
        purchase = container.planned_purchase_service().get_purchase(purchase_id)
        if not purchase:
            print_error(f"Purchase {purchase_id} not found")
            return

        console = Console()

        priority_label = container.planned_purchase_service().get_priority_label(purchase["priority"])

        panel_content = f"[bold]{purchase['name']}[/bold]\n\n"
        panel_content += f"Estimated cost: {format_currency(purchase['estimated_cost'])}\n"
        panel_content += f"Priority: {purchase['priority']} - {priority_label}\n"
        panel_content += f"Status: {purchase['status']}\n"

        if purchase.get("category"):
            panel_content += f"Category: {purchase['category']}\n"

        if purchase.get("deadline"):
            panel_content += f"Deadline: {purchase['deadline']}\n"

        if purchase.get("description"):
            panel_content += f"\n{purchase['description']}\n"

        if purchase.get("notes"):
            panel_content += f"\nNotes: {purchase['notes']}\n"

        if purchase.get("url"):
            panel_content += f"\nURL: {purchase['url']}\n"

        if purchase["status"] == "purchased":
            panel_content += f"\nPurchased at: {purchase['purchased_at']}\n"
            panel_content += f"Actual cost: {format_currency(purchase['actual_cost'])}\n"

        console.print(Panel(panel_content, border_style="cyan"))

    except Exception as e:
        print_error(f"Failed to view purchase: {str(e)}")
        raise


@purchase.command("update")
@click.argument("purchase_id", type=int)
@click.option("--priority", "-p", type=int, help="New priority (1-5)")
@click.option("--cost", "-c", type=float, help="New estimated cost")
@click.option("--deadline", "-d", help="New deadline (YYYY-MM-DD)")
@click.option("--category", help="New category")
@click.pass_context
def update_purchase(ctx, purchase_id, priority, cost, deadline, category):
    """
    Update a planned purchase.

    Examples:
        finance purchase update 5 --priority 2
        finance purchase update 3 -c 75 -d 2026-02-01
    """
    container = ctx.obj["container"]

    try:
        purchase = container.planned_purchase_service().get_purchase(purchase_id)
        if not purchase:
            print_error(f"Purchase {purchase_id} not found")
            return

        updates = {}

        if priority is not None:
            updates["priority"] = priority

        if cost is not None:
            updates["estimated_cost"] = Decimal(str(cost))

        if deadline:
            try:
                updates["deadline"] = datetime.strptime(deadline, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid deadline format. Use YYYY-MM-DD")
                return

        if category is not None:
            updates["category"] = category

        if not updates:
            print_error("No updates specified. Use --priority, --cost, --deadline, or --category")
            return

        updated = container.planned_purchase_service().update_purchase(purchase_id, **updates)

        print_success(f"Updated: {updated['name']}")

        for key, value in updates.items():
            if key == "priority":
                label = container.planned_purchase_service().get_priority_label(value)
                print_info(f"Priority: {value} - {label}")
            elif key == "estimated_cost":
                print_info(f"Cost: {format_currency(value)}")
            elif key == "deadline":
                print_info(f"Deadline: {value}")
            elif key == "category":
                print_info(f"Category: {value}")

    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to update purchase: {str(e)}")
        raise
