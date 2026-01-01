"""Tag management CLI commands."""

import click
from rich.console import Console
from rich.table import Table
from ..formatters import print_success, print_error, print_info


@click.group()
def tag():
    """Manage transaction tags."""
    pass


@tag.command("list")
@click.pass_context
def list_tags(ctx):
    """List all tags with usage statistics."""
    container = ctx.obj["container"]

    try:
        tag_stats = container.tag_repo().get_tag_stats()

        if not tag_stats:
            print_info("No tags found.")
            print_info("Create tags with: finance tag create <name>")
            print_info("Or tag transactions with: finance tag add <transaction_id> <tag>")
            return

        console = Console()
        table = Table(title="Tags")

        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Color", justify="center")
        table.add_column("Usage Count", justify="right")

        for tag_data in tag_stats:
            table.add_row(
                tag_data["name"],
                tag_data.get("description") or "",
                tag_data.get("color") or "-",
                str(tag_data["usage_count"])
            )

        console.print(table)

        total_tags = len(tag_stats)
        total_uses = sum(t["usage_count"] for t in tag_stats)
        print_info(f"\nTotal tags: {total_tags}, Total uses: {total_uses}")

    except Exception as e:
        print_error(f"Failed to list tags: {str(e)}")
        raise


@tag.command("create")
@click.argument("name")
@click.option("--description", "-d", help="Tag description")
@click.option("--color", "-c", help="Display color")
@click.pass_context
def create_tag(ctx, name, description, color):
    """
    Create a new tag.

    Examples:
        finance tag create business --description "Business expenses"
        finance tag create gift -d "Gift purchases" -c blue
    """
    container = ctx.obj["container"]

    try:
        # Check if tag already exists
        existing = container.tag_repo().get_by_name(name)
        if existing:
            print_error(f"Tag '{name}' already exists")
            return

        # Create tag
        tag_id = container.tag_repo().create(name, description, color)
        tag = container.tag_repo().get_by_id(tag_id)

        print_success(f"Created tag: {tag['name']}")
        if description:
            print_info(f"Description: {description}")

    except Exception as e:
        print_error(f"Failed to create tag: {str(e)}")
        raise


@tag.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_tag(ctx, name, yes):
    """
    Delete a tag.

    This will remove the tag from all transactions.

    Examples:
        finance tag delete old-tag
        finance tag delete temp -y
    """
    container = ctx.obj["container"]

    try:
        tag = container.tag_repo().get_by_name(name)
        if not tag:
            print_error(f"Tag '{name}' not found")
            return

        # Get usage count
        tag_stats = container.tag_repo().get_tag_stats()
        usage_count = next((t["usage_count"] for t in tag_stats if t["id"] == tag["id"]), 0)

        print_info(f"Tag: {tag['name']}")
        if tag.get("description"):
            print_info(f"Description: {tag['description']}")
        print_info(f"Usage count: {usage_count}")

        if not yes:
            if not click.confirm(f"\nAre you sure you want to delete this tag?"):
                print_info("Deletion cancelled")
                return

        # Delete tag
        container.tag_repo().delete(tag["id"])

        print_success(f"Deleted tag: {name}")
        if usage_count > 0:
            print_info(f"Removed from {usage_count} transactions")

    except Exception as e:
        print_error(f"Failed to delete tag: {str(e)}")
        raise


@tag.command("add")
@click.argument("transaction_id", type=int)
@click.argument("tags", nargs=-1, required=True)
@click.pass_context
def add_tags(ctx, transaction_id, tags):
    """
    Add tags to a transaction.

    Tags will be created if they don't exist.

    Examples:
        finance tag add 123 business
        finance tag add 456 business tax-deductible
    """
    container = ctx.obj["container"]

    try:
        # Verify transaction exists
        tx = container.transaction_repo().get_by_id(transaction_id)
        if not tx:
            print_error(f"Transaction {transaction_id} not found")
            return

        added_tags = []
        for tag_name in tags:
            # Get or create tag
            tag = container.tag_repo().get_or_create(tag_name)

            # Add to transaction
            container.tag_repo().add_tag_to_transaction(transaction_id, tag["id"])
            added_tags.append(tag["name"])

        print_success(f"Added tags to transaction {transaction_id}: {', '.join(added_tags)}")

        # Show transaction summary
        print_info(f"Transaction: {tx.get('merchant') or tx.get('description', 'N/A')} - ${tx['amount']:.2f}")

    except Exception as e:
        print_error(f"Failed to add tags: {str(e)}")
        raise


@tag.command("remove")
@click.argument("transaction_id", type=int)
@click.argument("tags", nargs=-1, required=True)
@click.pass_context
def remove_tags(ctx, transaction_id, tags):
    """
    Remove tags from a transaction.

    Examples:
        finance tag remove 123 business
        finance tag remove 456 business tax-deductible
    """
    container = ctx.obj["container"]

    try:
        # Verify transaction exists
        tx = container.transaction_repo().get_by_id(transaction_id)
        if not tx:
            print_error(f"Transaction {transaction_id} not found")
            return

        removed_tags = []
        for tag_name in tags:
            tag = container.tag_repo().get_by_name(tag_name)
            if not tag:
                print_info(f"Tag '{tag_name}' not found, skipping")
                continue

            container.tag_repo().remove_tag_from_transaction(transaction_id, tag["id"])
            removed_tags.append(tag["name"])

        if removed_tags:
            print_success(f"Removed tags from transaction {transaction_id}: {', '.join(removed_tags)}")
        else:
            print_info("No tags were removed")

    except Exception as e:
        print_error(f"Failed to remove tags: {str(e)}")
        raise


@tag.command("show")
@click.argument("transaction_id", type=int)
@click.pass_context
def show_transaction_tags(ctx, transaction_id):
    """
    Show all tags for a transaction.

    Examples:
        finance tag show 123
    """
    container = ctx.obj["container"]

    try:
        # Verify transaction exists
        tx = container.transaction_repo().get_by_id(transaction_id)
        if not tx:
            print_error(f"Transaction {transaction_id} not found")
            return

        tags = container.tag_repo().get_transaction_tags(transaction_id)

        print_info(f"Transaction {transaction_id}: {tx.get('merchant') or tx.get('description', 'N/A')}")
        print_info(f"Amount: ${tx['amount']:.2f}")

        if tags:
            print_info(f"\nTags: {', '.join(t['name'] for t in tags)}")
        else:
            print_info("\nNo tags")

    except Exception as e:
        print_error(f"Failed to show tags: {str(e)}")
        raise


@tag.command("find")
@click.argument("tag_name")
@click.option("--limit", "-n", default=10, help="Number of transactions to show")
@click.pass_context
def find_by_tag(ctx, tag_name, limit):
    """
    Find all transactions with a specific tag.

    Examples:
        finance tag find business
        finance tag find gift --limit 20
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        tag = container.tag_repo().get_by_name(tag_name)
        if not tag:
            print_error(f"Tag '{tag_name}' not found")
            return

        transaction_ids = container.tag_repo().get_transactions_by_tag(tag["id"])

        if not transaction_ids:
            print_info(f"No transactions found with tag '{tag_name}'")
            return

        print_info(f"Found {len(transaction_ids)} transaction(s) with tag '{tag_name}'\n")

        # Get full transaction details for first N
        displayed = 0
        for tx_id in transaction_ids[:limit]:
            tx = container.transaction_repo().get_by_id(tx_id)
            if tx:
                merchant = tx.get("merchant") or tx.get("description", "N/A")
                print_info(f"#{tx_id}: {merchant} - ${tx['amount']:.2f} ({tx['category']})")
                displayed += 1

        if len(transaction_ids) > limit:
            print_info(f"\n... and {len(transaction_ids) - limit} more")
            print_info(f"Use --limit {len(transaction_ids)} to see all")

    except Exception as e:
        print_error(f"Failed to find transactions: {str(e)}")
        raise


@tag.command("stats")
@click.pass_context
def tag_stats(ctx):
    """Show detailed tag usage statistics."""
    container = ctx.obj["container"]

    try:
        tag_stats = container.tag_repo().get_tag_stats()

        if not tag_stats:
            print_info("No tags found.")
            return

        console = Console()
        table = Table(title="Tag Statistics")

        table.add_column("Tag", style="cyan")
        table.add_column("Description")
        table.add_column("Uses", justify="right", style="yellow")
        table.add_column("% of Tags", justify="right")

        total_uses = sum(t["usage_count"] for t in tag_stats)

        for tag_data in sorted(tag_stats, key=lambda x: x["usage_count"], reverse=True):
            percentage = (tag_data["usage_count"] / total_uses * 100) if total_uses > 0 else 0

            table.add_row(
                tag_data["name"],
                tag_data.get("description") or "-",
                str(tag_data["usage_count"]),
                f"{percentage:.1f}%"
            )

        console.print(table)

        # Summary
        print_info(f"\nTotal tags: {len(tag_stats)}")
        print_info(f"Total tag uses: {total_uses}")
        if tag_stats:
            avg_uses = total_uses / len(tag_stats)
            print_info(f"Average uses per tag: {avg_uses:.1f}")

    except Exception as e:
        print_error(f"Failed to show tag statistics: {str(e)}")
        raise
