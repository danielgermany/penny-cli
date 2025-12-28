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
@click.option("--search", "-s", help="Search in merchant, description, notes")
@click.option("--category", "-c", help="Filter by category")
@click.option("--account", "-a", help="Filter by account name")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option("--min-amount", type=float, help="Minimum amount")
@click.option("--max-amount", type=float, help="Maximum amount")
@click.option("--type", "tx_type", help="Transaction type (expense/income/transfer)")
@click.pass_context
def list_transactions(ctx, limit, month, search, category, account, start_date, end_date, min_amount, max_amount, tx_type):
    """List and filter transactions."""
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Check if any filters are applied
        has_filters = any([search, category, account, start_date, end_date, min_amount is not None, max_amount is not None, tx_type])

        if month and not has_filters:
            # Parse month
            if "-" in month:
                year, month_num = map(int, month.split("-"))
            else:
                year = datetime.now().year
                month_num = int(month)

            transactions = container.transaction_service().list_by_month(user_id, year, month_num)
        elif has_filters or search:
            # Use search functionality
            account_id = None
            if account:
                acc = container.account_service().get_account_by_name(user_id, account)
                account_id = acc["id"]

            # Parse dates
            parsed_start_date = None
            parsed_end_date = None
            if start_date:
                try:
                    parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    print_error("Invalid start date format. Use YYYY-MM-DD")
                    return

            if end_date:
                try:
                    parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    print_error("Invalid end date format. Use YYYY-MM-DD")
                    return

            # Convert amounts to Decimal
            min_amt = Decimal(str(min_amount)) if min_amount is not None else None
            max_amt = Decimal(str(max_amount)) if max_amount is not None else None

            transactions = container.transaction_service().search_transactions(
                user_id=user_id,
                search_text=search,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                min_amount=min_amt,
                max_amount=max_amt,
                category=category,
                account_id=account_id,
                transaction_type=tx_type,
                limit=limit,
            )
        else:
            transactions = container.transaction_service().list_recent(user_id, limit)

        print_transaction_table(transactions)

    except Exception as e:
        print_error(f"Failed to list transactions: {str(e)}")
        raise


@transaction.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Number of results to show")
@click.option("--category", "-c", help="Filter by category")
@click.option("--account", "-a", help="Filter by account name")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option("--min-amount", type=float, help="Minimum amount")
@click.option("--max-amount", type=float, help="Maximum amount")
@click.pass_context
def search_transactions(ctx, query, limit, category, account, start_date, end_date, min_amount, max_amount):
    """
    Search transactions by text.

    Searches in merchant names, descriptions, and notes.

    Example: finance transaction search "starbucks"
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        account_id = None
        if account:
            acc = container.account_service().get_account_by_name(user_id, account)
            account_id = acc["id"]

        # Parse dates
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            try:
                parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid start date format. Use YYYY-MM-DD")
                return

        if end_date:
            try:
                parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid end date format. Use YYYY-MM-DD")
                return

        # Convert amounts to Decimal
        min_amt = Decimal(str(min_amount)) if min_amount is not None else None
        max_amt = Decimal(str(max_amount)) if max_amount is not None else None

        transactions = container.transaction_service().search_transactions(
            user_id=user_id,
            search_text=query,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            min_amount=min_amt,
            max_amount=max_amt,
            category=category,
            account_id=account_id,
            limit=limit,
        )

        if not transactions:
            print_info(f"No transactions found matching '{query}'")
        else:
            print_info(f"Found {len(transactions)} matching transaction(s)")
            print_transaction_table(transactions)

    except Exception as e:
        print_error(f"Failed to search transactions: {str(e)}")
        raise


@transaction.command("edit")
@click.argument("transaction_id", type=int)
@click.option("--merchant", "-m", help="Update merchant name")
@click.option("--amount", "-a", type=float, help="Update amount")
@click.option("--category", "-c", help="Update category")
@click.option("--date", "-d", help="Update date (YYYY-MM-DD)")
@click.option("--notes", "-n", help="Update notes")
@click.option("--description", help="Update description")
@click.pass_context
def edit_transaction(ctx, transaction_id, merchant, amount, category, date, notes, description):
    """
    Edit an existing transaction.

    Example: finance transaction edit 5 --amount 12.50 --category "Food & Dining - Restaurants"
    """
    container = ctx.obj["container"]

    try:
        # Check if any fields are being updated
        if not any([merchant, amount, category, date, notes, description]):
            print_error("No fields to update. Use --help to see available options.")
            return

        # Get current transaction
        tx = container.transaction_service().get_transaction(transaction_id)
        print_info(f"Current: {tx['merchant']} - ${tx['amount']:.2f} - {tx['category']}")

        # Parse date if provided
        parsed_date = None
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid date format. Use YYYY-MM-DD")
                return

        # Convert amount to Decimal if provided
        new_amount = Decimal(str(amount)) if amount is not None else None

        # Edit transaction
        updated_tx = container.transaction_service().edit_transaction(
            transaction_id=transaction_id,
            merchant=merchant,
            amount=new_amount,
            category=category,
            transaction_date=parsed_date,
            notes=notes,
            description=description,
        )

        print_success(f"Transaction {transaction_id} updated")
        print_info(f"New: {updated_tx['merchant']} - ${updated_tx['amount']:.2f} - {updated_tx['category']}")

    except Exception as e:
        print_error(f"Failed to edit transaction: {str(e)}")
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
