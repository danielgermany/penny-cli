"""Import/Export CLI commands."""

import click
from datetime import datetime
from ..formatters import print_success, print_error, print_info, print_warning
from ...utils.csv_handler import CSVExporter, CSVImporter


@click.group(name="export")
def export_cmd():
    """Export data to files."""
    pass


@export_cmd.command("transactions")
@click.argument("file_path")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option("--category", "-c", help="Filter by category")
@click.option("--account", "-a", help="Filter by account name")
@click.pass_context
def export_transactions(ctx, file_path, start_date, end_date, category, account):
    """
    Export transactions to CSV file.

    Example: finance export transactions my_transactions.csv
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Parse dates if provided
        parsed_start = None
        parsed_end = None

        if start_date:
            try:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid start date format. Use YYYY-MM-DD")
                return

        if end_date:
            try:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                print_error("Invalid end date format. Use YYYY-MM-DD")
                return

        # Get account ID if specified
        account_id = None
        if account:
            acc = container.account_service().get_account_by_name(user_id, account)
            account_id = acc["id"]

        # Fetch transactions with filters
        transactions = container.transaction_service().search_transactions(
            user_id=user_id,
            start_date=parsed_start,
            end_date=parsed_end,
            category=category,
            account_id=account_id,
        )

        if not transactions:
            print_warning("No transactions found to export")
            return

        # Export to CSV
        exporter = CSVExporter()
        count = exporter.export_transactions(transactions, file_path)

        print_success(f"Exported {count} transactions to {file_path}")

    except Exception as e:
        print_error(f"Failed to export transactions: {str(e)}")
        raise


@click.group(name="import")
def import_cmd():
    """Import data from files."""
    pass


@import_cmd.command("transactions")
@click.argument("file_path")
@click.option("--account", "-a", required=True, help="Account name to import into")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["generic", "mint", "ynab"], case_sensitive=False),
    default="generic",
    help="CSV format type",
)
@click.option("--dry-run", is_flag=True, help="Preview import without saving")
@click.pass_context
def import_transactions(ctx, file_path, account, format, dry_run):
    """
    Import transactions from CSV file.

    Supported formats:
    - generic: date, merchant, amount, category, notes
    - mint: Mint.com export format
    - ynab: YNAB export format

    Example: finance import transactions transactions.csv --account "Checking" --format mint
    """
    container = ctx.obj["container"]
    user_id = ctx.obj["user_id"]

    try:
        # Get account
        acc = container.account_service().get_account_by_name(user_id, account)
        account_id = acc["id"]

        # Parse CSV
        print_info(f"Parsing CSV file with format: {format}")
        importer = CSVImporter()
        parsed_txs = importer.parse_csv(file_path, format_type=format)

        if not parsed_txs:
            print_warning("No valid transactions found in file")
            return

        print_info(f"Found {len(parsed_txs)} transactions")

        if dry_run:
            print_info("DRY RUN - No transactions will be saved")
            print_info("\nPreview of first 5 transactions:")
            for i, tx in enumerate(parsed_txs[:5], 1):
                print_info(
                    f"{i}. {tx['date']} - {tx['merchant']} - ${tx['amount']:.2f} - {tx['category']}"
                )
            return

        # Confirm import
        if not click.confirm(
            f"Import {len(parsed_txs)} transactions into '{acc['name']}'?"
        ):
            print_info("Import cancelled")
            return

        # Import transactions
        imported_count = 0
        skipped_count = 0

        for tx in parsed_txs:
            try:
                container.transaction_service().create_transaction(
                    user_id=user_id,
                    account_id=account_id,
                    amount=tx["amount"],
                    type=tx["type"],
                    transaction_date=tx["date"],
                    merchant=tx["merchant"],
                    category=tx["category"],
                    description=tx.get("description"),
                    notes=tx.get("notes"),
                )
                imported_count += 1
            except Exception as e:
                print_warning(f"Skipped transaction: {tx['merchant']} - {str(e)}")
                skipped_count += 1

        print_success(f"Imported {imported_count} transactions")
        if skipped_count > 0:
            print_warning(f"Skipped {skipped_count} transactions due to errors")

    except FileNotFoundError:
        print_error(f"File not found: {file_path}")
    except Exception as e:
        print_error(f"Failed to import transactions: {str(e)}")
        raise
