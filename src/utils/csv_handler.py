"""CSV import/export utilities."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional


class CSVExporter:
    """Export transactions to CSV format."""

    def export_transactions(
        self,
        transactions: list[dict],
        file_path: str,
        include_columns: Optional[list[str]] = None,
    ) -> int:
        """
        Export transactions to CSV file.

        Args:
            transactions: List of transaction dicts
            file_path: Output CSV file path
            include_columns: Optional list of columns to include

        Returns:
            Number of transactions exported
        """
        if not transactions:
            return 0

        # Default columns
        default_columns = [
            "id",
            "date",
            "merchant",
            "category",
            "amount",
            "type",
            "account_id",
            "description",
            "notes",
        ]

        columns = include_columns or default_columns

        # Ensure path exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()

            for tx in transactions:
                # Convert date to string if needed
                row = tx.copy()
                if "date" in row and isinstance(row["date"], str):
                    pass
                elif "date" in row:
                    row["date"] = str(row["date"])

                writer.writerow({k: row.get(k, "") for k in columns})

        return len(transactions)


class CSVImporter:
    """Import transactions from CSV format."""

    def parse_csv(
        self, file_path: str, format_type: str = "generic"
    ) -> list[dict]:
        """
        Parse CSV file and return list of transaction dicts.

        Args:
            file_path: CSV file path
            format_type: Format type (generic, mint, ynab)

        Returns:
            List of parsed transaction dicts
        """
        if format_type == "mint":
            return self._parse_mint_format(file_path)
        elif format_type == "ynab":
            return self._parse_ynab_format(file_path)
        else:
            return self._parse_generic_format(file_path)

    def _parse_generic_format(self, file_path: str) -> list[dict]:
        """
        Parse generic CSV format.

        Expected columns: date, merchant, amount, category (optional), notes (optional)
        """
        transactions = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Parse date
                date_str = row.get("date", "")
                try:
                    tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    # Try alternative format
                    try:
                        tx_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                    except ValueError:
                        continue  # Skip invalid dates

                # Parse amount
                amount_str = row.get("amount", "0")
                try:
                    # Remove currency symbols and commas
                    amount_str = amount_str.replace("$", "").replace(",", "")
                    amount = abs(Decimal(amount_str))
                except (ValueError, InvalidOperation):
                    amount = Decimal("0")

                # Determine transaction type
                tx_type = row.get("type", "expense").lower()
                if tx_type not in ["expense", "income", "transfer"]:
                    # Check if amount was negative in original
                    if row.get("amount", "").startswith("-"):
                        tx_type = "expense"
                    else:
                        tx_type = "expense"  # Default

                transactions.append(
                    {
                        "date": tx_date,
                        "merchant": row.get("merchant", "Unknown"),
                        "amount": amount,
                        "category": row.get("category", "Other - Miscellaneous"),
                        "description": row.get("description", ""),
                        "notes": row.get("notes", ""),
                        "type": tx_type,
                    }
                )

        return transactions

    def _parse_mint_format(self, file_path: str) -> list[dict]:
        """
        Parse Mint CSV format.

        Mint columns: Date, Description, Original Description, Amount, Transaction Type, Category, Account Name, Labels, Notes
        """
        transactions = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Parse date (MM/DD/YYYY)
                date_str = row.get("Date", "")
                try:
                    tx_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                except ValueError:
                    continue

                # Parse amount
                amount_str = row.get("Amount", "0")
                try:
                    amount = abs(Decimal(amount_str))
                except (ValueError, InvalidOperation):
                    amount = Decimal("0")

                # Transaction type (debit = expense, credit = income)
                mint_type = row.get("Transaction Type", "debit").lower()
                tx_type = "income" if mint_type == "credit" else "expense"

                transactions.append(
                    {
                        "date": tx_date,
                        "merchant": row.get("Description", "Unknown"),
                        "amount": amount,
                        "category": row.get("Category", "Other - Miscellaneous"),
                        "description": row.get("Original Description", ""),
                        "notes": row.get("Notes", ""),
                        "type": tx_type,
                    }
                )

        return transactions

    def _parse_ynab_format(self, file_path: str) -> list[dict]:
        """
        Parse YNAB CSV format.

        YNAB columns: Date, Payee, Category, Memo, Outflow, Inflow
        """
        transactions = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Parse date
                date_str = row.get("Date", "")
                try:
                    tx_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                except ValueError:
                    # Try alternative format
                    try:
                        tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        continue

                # YNAB has separate Inflow/Outflow columns
                outflow = row.get("Outflow", "0").replace("$", "").replace(",", "")
                inflow = row.get("Inflow", "0").replace("$", "").replace(",", "")

                try:
                    outflow_amt = Decimal(outflow) if outflow else Decimal("0")
                    inflow_amt = Decimal(inflow) if inflow else Decimal("0")
                except (ValueError, InvalidOperation):
                    continue

                # Determine amount and type
                if inflow_amt > 0:
                    amount = inflow_amt
                    tx_type = "income"
                else:
                    amount = outflow_amt
                    tx_type = "expense"

                if amount == 0:
                    continue

                transactions.append(
                    {
                        "date": tx_date,
                        "merchant": row.get("Payee", "Unknown"),
                        "amount": amount,
                        "category": row.get("Category", "Other - Miscellaneous"),
                        "description": "",
                        "notes": row.get("Memo", ""),
                        "type": tx_type,
                    }
                )

        return transactions
