"""Account CLI commands."""

import click
from decimal import Decimal
from ..formatters import print_success, print_error, print_account_table, print_info


@click.group()
def account():
    """Manage accounts."""
    pass


@account.command("add")
@click.argument("name")
@click.option("--type", "-t", type=click.Choice(["checking", "savings", "credit_card", "investment"]), default="checking")
@click.option("--institution", "-i", help="Financial institution name")
@click.option("--balance", "-b", type=float, default=0.0, help="Initial balance")
@click.pass_context
def add_account(ctx, name, type, institution, balance):
    """
    Add a new account.

    Example: finance account add "Chase Checking" --type checking --balance 1000
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        account = container.account_service().create_account(
            user_id=user_id,
            name=name,
            type=type,
            institution=institution,
            initial_balance=Decimal(str(balance)),
        )

        print_success(f"Account created: {account['name']}")
        print_info(f"Type: {account['type']}")
        print_info(f"Balance: ${account['current_balance']:.2f}")

    except Exception as e:
        print_error(f"Failed to create account: {str(e)}")
        raise


@account.command("list")
@click.pass_context
def list_accounts(ctx):
    """List all accounts."""
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        accounts = container.account_service().list_accounts(user_id)
        print_account_table(accounts)

        # Show total
        total = container.account_service().get_total_balance(user_id)
        print_info(f"\nTotal balance: ${total:.2f}")

    except Exception as e:
        print_error(f"Failed to list accounts: {str(e)}")
        raise


@account.command("balance")
@click.argument("name")
@click.argument("amount", type=float)
@click.pass_context
def update_balance(ctx, name, amount):
    """
    Update account balance.

    Example: finance account balance "Cash" 500.00
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        account = container.account_service().get_account_by_name(user_id, name)
        old_balance = account["current_balance"]

        container.account_service().update_balance(account["id"], Decimal(str(amount)))

        print_success(f"Balance updated for {name}")
        print_info(f"Old balance: ${old_balance:.2f}")
        print_info(f"New balance: ${amount:.2f}")

    except Exception as e:
        print_error(f"Failed to update balance: {str(e)}")
        raise
