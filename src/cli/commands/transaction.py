"""Transaction CLI commands."""

import click
from decimal import Decimal
from datetime import datetime
from ..formatters import print_success, print_error, print_transaction_table, print_info


@click.group()
def transaction():
    """Manage transactions."""
    pass


@transaction.command("log")
@click.argument("description")
@click.option("--account", "-a", help="Account name (defaults to first account)")
@click.option("--category", "-c", help="Override AI categorization")
@click.option("--date", "-d", help="Transaction date (YYYY-MM-DD)")
@click.pass_context
def log_transaction(ctx, description, account, category, date):
    """
    Log a new transaction with AI categorization.

    Example: finance transaction log "coffee $5"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get account
        if account:
            acc = container.account_service().get_account_by_name(user_id, account)
        else:
            accounts = container.account_service().list_accounts(user_id)
            if not accounts:
                print_error("No accounts found. Create one first with: finance account add")
                return
            acc = accounts[0]

        # Parse date if provided
        tx_date = None
        if date:
            try:
                tx_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid date format. Use YYYY-MM-DD")
                return

        # Create transaction
        print_info(f"Creating transaction in account: {acc['name']}")
        tx = container.transaction_service().create_from_text(
            user_id=user_id,
            account_id=acc["id"],
            description=description,
            transaction_date=tx_date,
            override_category=category,
        )

        print_success(f"Transaction logged: {tx['merchant']} - {tx['category']}")
        print_info(f"Amount: ${tx['amount']:.2f}")
        print_info(f"New balance: ${acc['current_balance'] - tx['amount']:.2f}")

    except Exception as e:
        print_error(f"Failed to log transaction: {str(e)}")
        raise


@transaction.command("list")
@click.option("--limit", "-n", default=10, help="Number of transactions to show")
@click.option("--month", "-m", help="Filter by month (MM or YYYY-MM)")
@click.pass_context
def list_transactions(ctx, limit, month):
    """List recent transactions."""
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        if month:
            # Parse month
            if "-" in month:
                year, month_num = map(int, month.split("-"))
            else:
                year = datetime.now().year
                month_num = int(month)

            transactions = container.transaction_service().list_by_month(user_id, year, month_num)
        else:
            transactions = container.transaction_service().list_recent(user_id, limit)

        print_transaction_table(transactions)

    except Exception as e:
        print_error(f"Failed to list transactions: {str(e)}")
        raise


@transaction.command("delete")
@click.argument("transaction_id", type=int)
@click.pass_context
def delete_transaction(ctx, transaction_id):
    """Delete a transaction."""
    container = ctx.obj["container"]

    try:
        # Get transaction to confirm
        tx = container.transaction_service().get_transaction(transaction_id)
        print_info(f"Transaction: {tx['merchant']} - ${tx['amount']:.2f}")

        if not click.confirm("Delete this transaction?"):
            print_info("Cancelled.")
            return

        container.transaction_service().delete_transaction(transaction_id)
        print_success(f"Transaction {transaction_id} deleted.")

    except Exception as e:
        print_error(f"Failed to delete transaction: {str(e)}")
        raise
