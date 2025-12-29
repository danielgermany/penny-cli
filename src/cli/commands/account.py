"""Account CLI commands."""

import click
from decimal import Decimal
from datetime import date
from ..formatters import print_success, print_error, print_account_table, print_info, print_warning


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


@account.command("edit")
@click.argument("name")
@click.option("--new-name", "-n", help="New account name")
@click.option("--type", "-t", type=click.Choice(["checking", "savings", "credit_card", "investment"]), help="Account type")
@click.option("--institution", "-i", help="Financial institution name")
@click.option("--notes", help="Account notes")
@click.pass_context
def edit_account(ctx, name, new_name, type, institution, notes):
    """
    Edit an existing account.

    Example: finance account edit "Cash" --new-name "Primary Checking" --type checking
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Check if any fields are being updated
        if not any([new_name, type, institution, notes]):
            print_error("No fields to update. Use --help to see available options.")
            return

        # Get current account
        account = container.account_service().get_account_by_name(user_id, name)

        # Show current values
        print_info(f"Current account: {account['name']}")
        print_info(f"  Type: {account['type']}")
        print_info(f"  Institution: {account.get('institution', '-')}")

        # Build updates
        updates = {}
        if new_name is not None:
            updates["name"] = new_name
        if type is not None:
            updates["type"] = type
        if institution is not None:
            updates["institution"] = institution
        if notes is not None:
            updates["notes"] = notes

        # Update account
        updated = container.account_service().update_account(account["id"], **updates)

        print_success(f"Account updated")
        print_info(f"  Name: {updated['name']}")
        print_info(f"  Type: {updated['type']}")
        print_info(f"  Institution: {updated.get('institution', '-')}")

    except Exception as e:
        print_error(f"Failed to edit account: {str(e)}")
        raise


@account.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_account(ctx, name, yes):
    """
    Delete an account.

    Note: Deletes the account but preserves associated transactions.

    Example: finance account delete "Old Savings" -y
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get account
        account = container.account_service().get_account_by_name(user_id, name)

        # Show account details
        print_info(f"Account: {account['name']}")
        print_info(f"  Type: {account['type']}")
        print_info(f"  Balance: ${account['current_balance']:.2f}")
        print_warning("  Note: Associated transactions will be preserved")

        # Confirm deletion
        if not yes and not click.confirm(f"\nDelete this account?"):
            print_info("Cancelled")
            return

        # Delete account
        container.account_service().delete_account(account["id"])
        print_success(f"Account '{name}' deleted")

    except Exception as e:
        print_error(f"Failed to delete account: {str(e)}")
        raise


@account.command("transfer")
@click.argument("from_account")
@click.argument("to_account")
@click.argument("amount", type=float)
@click.option("--notes", "-n", help="Transfer notes")
@click.pass_context
def transfer_money(ctx, from_account, to_account, amount, notes):
    """
    Transfer money between accounts.

    Creates paired transfer transactions and updates both account balances.

    Example: finance account transfer "Checking" "Savings" 500
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get both accounts
        from_acc = container.account_service().get_account_by_name(user_id, from_account)
        to_acc = container.account_service().get_account_by_name(user_id, to_account)

        # Validate amount
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            print_error("Transfer amount must be positive")
            return

        # Check sufficient balance
        if Decimal(str(from_acc["current_balance"])) < amount_decimal:
            print_error(f"Insufficient balance in {from_account}")
            print_info(f"Available: ${from_acc['current_balance']:.2f}")
            print_info(f"Requested: ${amount:.2f}")
            return

        # Show transfer details
        print_info(f"Transfer ${amount:.2f}")
        print_info(f"  From: {from_account} (${from_acc['current_balance']:.2f})")
        print_info(f"  To: {to_account} (${to_acc['current_balance']:.2f})")

        # Create transfer transaction
        description = notes or "Transfer"

        outgoing, incoming = container.transaction_service().create_transfer(
            user_id=user_id,
            from_account_id=from_acc["id"],
            to_account_id=to_acc["id"],
            amount=amount_decimal,
            transaction_date=date.today(),
            description=description,
        )

        # Get updated balances
        from_acc_updated = container.account_service().get_account(from_acc["id"])
        to_acc_updated = container.account_service().get_account(to_acc["id"])

        print_success(f"Transfer completed")
        print_info(f"  {from_account}: ${from_acc_updated['current_balance']:.2f}")
        print_info(f"  {to_account}: ${to_acc_updated['current_balance']:.2f}")

    except Exception as e:
        print_error(f"Failed to transfer: {str(e)}")
        raise
