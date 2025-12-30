"""Main CLI entry point."""

import click
from pathlib import Path
from ..utils.config import Config
from ..utils.container import ServiceContainer
from .formatters import print_error, print_success, print_info
from .commands.transaction import transaction
from .commands.account import account
from .commands.budget import budget
from .commands.import_export import import_cmd, export_cmd
from .commands.category import category
from .commands.recurring import recurring
from .commands.report import report


@click.group()
@click.pass_context
def cli(ctx):
    """Finance Tracker - AI-powered personal finance management."""
    # Initialize config
    config = Config()

    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["container"] = ServiceContainer(config)
    ctx.obj["user_id"] = config.user_id


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the finance tracker database."""
    config = ctx.obj["config"]
    container = ctx.obj["container"]

    # Check if already initialized
    if config.is_initialized:
        if not click.confirm("Database already exists. Reinitialize (will delete all data)?"):
            print_info("Initialization cancelled.")
            return

    # Validate configuration
    is_valid, error = config.validate()
    if not is_valid:
        print_error(error)
        print_info("Please set up your .env file. See .env.example for reference.")
        return

    try:
        # Initialize database
        print_info("Initializing database...")
        container.db.init_schema()

        print_success("Database initialized successfully!")
        print_info(f"Database location: {config.db_path}")

        # Create a default account if none exists
        accounts = container.account_service().list_accounts(config.user_id)
        if not accounts:
            print_info("\nLet's create your first account.")
            name = click.prompt("Account name", default="Cash")
            acc_type = click.prompt(
                "Account type", type=click.Choice(["checking", "savings", "credit_card", "investment"]), default="checking"
            )
            balance = click.prompt("Initial balance", type=float, default=0.0)

            account = container.account_service().create_account(
                user_id=config.user_id, name=name, type=acc_type, initial_balance=balance
            )

            print_success(f"Created account: {account['name']}")

    except Exception as e:
        print_error(f"Initialization failed: {str(e)}")
        raise


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    print_info("Finance Tracker v0.1.0")
    print_info("Powered by Claude AI")


# Register command groups
cli.add_command(transaction)
cli.add_command(account)
cli.add_command(budget)
cli.add_command(import_cmd)
cli.add_command(export_cmd)
cli.add_command(category)
cli.add_command(recurring)
cli.add_command(report)


# Convenience aliases for common operations
@cli.command("log")
@click.argument("description")
@click.option("--account", "-a", help="Account name")
@click.option("--category", "-c", help="Override AI categorization")
@click.pass_context
def log(ctx, description, account, category):
    """Quick shortcut for logging a transaction."""
    ctx.invoke(transaction.commands["log"], description=description, account=account, category=category, date=None)


@cli.command("list")
@click.option("--limit", "-n", default=10)
@click.pass_context
def list_txn(ctx, limit):
    """Quick shortcut for listing transactions."""
    ctx.invoke(transaction.commands["list"], limit=limit, month=None)


@cli.command("status")
@click.pass_context
def status(ctx):
    """Show budget status for current month."""
    ctx.invoke(budget.commands["status"], month=None)


if __name__ == "__main__":
    cli()
