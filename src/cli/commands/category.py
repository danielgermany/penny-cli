"""Category CLI commands."""

import click
from ..formatters import print_success, print_error, print_info, print_warning
from rich.console import Console
from rich.table import Table


@click.group()
def category():
    """Manage categories."""
    pass


@category.command("list")
@click.option("--show-usage", is_flag=True, help="Show transaction counts")
@click.pass_context
def list_categories(ctx, show_usage):
    """
    List all categories with usage statistics.

    Example: finance category list --show-usage
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get all transactions to analyze categories
        transactions = container.transaction_service().search_transactions(
            user_id=user_id
        )

        # Count usage by category
        category_stats = {}
        for tx in transactions:
            cat = tx.get("category", "Uncategorized")
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "total": 0}
            category_stats[cat]["count"] += 1
            category_stats[cat]["total"] += float(tx.get("amount", 0))

        # Sort by usage
        sorted_categories = sorted(
            category_stats.items(), key=lambda x: x[1]["count"], reverse=True
        )

        if not sorted_categories:
            print_info("No categories found")
            return

        # Display table
        console = Console()
        table = Table(title="Categories")
        table.add_column("Category", style="cyan")

        if show_usage:
            table.add_column("Transactions", justify="right", style="green")
            table.add_column("Total Amount", justify="right", style="yellow")

        for cat, stats in sorted_categories:
            if show_usage:
                table.add_row(
                    cat, str(stats["count"]), f"${stats['total']:.2f}"
                )
            else:
                table.add_row(cat)

        console.print(table)
        print_info(f"\nTotal categories: {len(sorted_categories)}")

    except Exception as e:
        print_error(f"Failed to list categories: {str(e)}")
        raise


@category.command("rename")
@click.argument("old_name")
@click.argument("new_name")
@click.pass_context
def rename_category(ctx, old_name, new_name):
    """
    Rename a category and update all associated transactions.

    Example: finance category rename "Food & Dining - Restaurants" "Dining - Restaurants"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Find transactions with old category
        transactions = container.transaction_service().search_transactions(
            user_id=user_id, category=old_name
        )

        if not transactions:
            print_warning(f"No transactions found with category '{old_name}'")
            return

        print_info(f"Found {len(transactions)} transaction(s) with category '{old_name}'")

        if not click.confirm(f"Rename to '{new_name}'?"):
            print_info("Cancelled")
            return

        # Update each transaction
        updated_count = 0
        for tx in transactions:
            try:
                container.transaction_service().edit_transaction(
                    transaction_id=tx["id"], category=new_name
                )
                updated_count += 1
            except Exception as e:
                print_warning(f"Failed to update transaction {tx['id']}: {str(e)}")

        print_success(f"Renamed category for {updated_count} transaction(s)")

    except Exception as e:
        print_error(f"Failed to rename category: {str(e)}")
        raise


@category.command("merge")
@click.argument("source")
@click.argument("target")
@click.pass_context
def merge_categories(ctx, source, target):
    """
    Merge source category into target category.

    All transactions in source category will be recategorized to target.

    Example: finance category merge "Food - Restaurants" "Food & Dining - Restaurants"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Find transactions with source category
        source_txs = container.transaction_service().search_transactions(
            user_id=user_id, category=source
        )

        if not source_txs:
            print_warning(f"No transactions found with category '{source}'")
            return

        # Check if target category exists
        target_txs = container.transaction_service().search_transactions(
            user_id=user_id, category=target
        )

        print_info(f"Source category '{source}': {len(source_txs)} transaction(s)")
        print_info(f"Target category '{target}': {len(target_txs)} transaction(s)")
        print_info(f"\nMerging will move all {len(source_txs)} transactions from '{source}' to '{target}'")

        if not click.confirm("Continue with merge?"):
            print_info("Cancelled")
            return

        # Update each transaction
        merged_count = 0
        for tx in source_txs:
            try:
                container.transaction_service().edit_transaction(
                    transaction_id=tx["id"], category=target
                )
                merged_count += 1
            except Exception as e:
                print_warning(f"Failed to update transaction {tx['id']}: {str(e)}")

        print_success(f"Merged {merged_count} transaction(s) from '{source}' to '{target}'")

    except Exception as e:
        print_error(f"Failed to merge categories: {str(e)}")
        raise


@category.command("show")
@click.argument("name")
@click.option("--limit", "-n", default=10, help="Number of transactions to show")
@click.pass_context
def show_category(ctx, name, limit):
    """
    Show transactions in a specific category.

    Example: finance category show "Food & Dining - Restaurants"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get transactions in category
        from ..formatters import print_transaction_table

        transactions = container.transaction_service().search_transactions(
            user_id=user_id, category=name, limit=limit
        )

        if not transactions:
            print_info(f"No transactions found in category '{name}'")
            return

        print_info(f"Category: {name}")
        print_info(f"Found {len(transactions)} transaction(s)\n")
        print_transaction_table(transactions)

    except Exception as e:
        print_error(f"Failed to show category: {str(e)}")
        raise


@category.command("stats")
@click.option("--top", "-t", default=10, help="Show top N categories")
@click.pass_context
def category_stats(ctx, top):
    """
    Show category spending statistics.

    Example: finance category stats --top 5
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get all expense transactions
        transactions = container.transaction_service().search_transactions(
            user_id=user_id, transaction_type="expense"
        )

        # Calculate stats by category
        category_stats = {}
        total_spending = 0

        for tx in transactions:
            cat = tx.get("category", "Uncategorized")
            amount = float(tx.get("amount", 0))

            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "total": 0}

            category_stats[cat]["count"] += 1
            category_stats[cat]["total"] += amount
            total_spending += amount

        # Sort by total spending
        sorted_stats = sorted(
            category_stats.items(), key=lambda x: x[1]["total"], reverse=True
        )[:top]

        # Display table
        console = Console()
        table = Table(title=f"Top {top} Spending Categories")
        table.add_column("Rank", justify="right", style="dim")
        table.add_column("Category", style="cyan")
        table.add_column("Transactions", justify="right", style="green")
        table.add_column("Total", justify="right", style="yellow")
        table.add_column("% of Total", justify="right", style="magenta")

        for i, (cat, stats) in enumerate(sorted_stats, 1):
            percentage = (stats["total"] / total_spending * 100) if total_spending > 0 else 0
            table.add_row(
                str(i),
                cat,
                str(stats["count"]),
                f"${stats['total']:.2f}",
                f"{percentage:.1f}%",
            )

        console.print(table)
        print_info(f"\nTotal spending: ${total_spending:.2f}")

    except Exception as e:
        print_error(f"Failed to show category stats: {str(e)}")
        raise
