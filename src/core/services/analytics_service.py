"""Analytics service for reporting and insights."""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
from collections import defaultdict
from calendar import monthrange


class AnalyticsService:
    """Service for analytics and reporting operations."""

    def __init__(self, transaction_repo, account_repo):
        """
        Initialize analytics service.

        Args:
            transaction_repo: Transaction repository instance
            account_repo: Account repository instance
        """
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo

    def get_monthly_summary(self, user_id: int, year: int, month: int) -> dict:
        """
        Generate monthly summary report.

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)

        Returns:
            Dict with income, expenses, savings, category breakdown, top merchants
        """
        # Get transactions for the month
        transactions = self.transaction_repo.get_by_month(user_id, year, month)

        # Calculate totals by type
        total_income = Decimal("0")
        total_expenses = Decimal("0")
        category_totals = defaultdict(lambda: Decimal("0"))
        merchant_totals = defaultdict(lambda: Decimal("0"))

        for tx in transactions:
            amount = Decimal(str(tx["amount"]))

            if tx["type"] == "income":
                total_income += amount
            elif tx["type"] == "expense":
                total_expenses += amount

                # Category breakdown (expenses only)
                category = tx.get("category", "Uncategorized")
                category_totals[category] += amount

                # Merchant totals (expenses only)
                merchant = tx.get("merchant", "Unknown")
                merchant_totals[merchant] += amount

        # Calculate savings
        savings = total_income - total_expenses
        savings_rate = (savings / total_income * 100) if total_income > 0 else Decimal("0")

        # Sort categories by amount (descending)
        category_breakdown = [
            {"category": cat, "amount": amt, "percentage": (amt / total_expenses * 100) if total_expenses > 0 else Decimal("0")}
            for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        ]

        # Top merchants
        top_merchants = [
            {"merchant": merch, "amount": amt}
            for merch, amt in sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        return {
            "year": year,
            "month": month,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "savings": savings,
            "savings_rate": savings_rate,
            "transaction_count": len(transactions),
            "category_breakdown": category_breakdown,
            "top_merchants": top_merchants,
        }

    def compare_to_previous_month(self, user_id: int, year: int, month: int) -> dict:
        """
        Compare current month to previous month.

        Args:
            user_id: User ID
            year: Current year
            month: Current month (1-12)

        Returns:
            Dict with current vs previous comparison
        """
        current = self.get_monthly_summary(user_id, year, month)

        # Calculate previous month
        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1

        previous = self.get_monthly_summary(user_id, prev_year, prev_month)

        # Calculate changes
        income_change = current["total_income"] - previous["total_income"]
        income_change_pct = (income_change / previous["total_income"] * 100) if previous["total_income"] > 0 else Decimal("0")

        expense_change = current["total_expenses"] - previous["total_expenses"]
        expense_change_pct = (expense_change / previous["total_expenses"] * 100) if previous["total_expenses"] > 0 else Decimal("0")

        savings_change = current["savings"] - previous["savings"]

        return {
            "current": current,
            "previous": previous,
            "income_change": income_change,
            "income_change_pct": income_change_pct,
            "expense_change": expense_change,
            "expense_change_pct": expense_change_pct,
            "savings_change": savings_change,
        }

    def get_category_analysis(self, user_id: int, category: str, months: int = 6) -> dict:
        """
        Detailed analysis for a specific category.

        Args:
            user_id: User ID
            category: Category name
            months: Number of months to analyze

        Returns:
            Dict with trend, top merchants, statistics
        """
        # Get transactions for category across months
        today = date.today()
        monthly_totals = []
        all_transactions = []

        for i in range(months):
            month_date = today - timedelta(days=30 * i)
            year = month_date.year
            month = month_date.month

            # Get transactions for this month
            month_txs = self.transaction_repo.search(
                user_id=user_id,
                category=category,
                start_date=date(year, month, 1),
                end_date=date(year, month, monthrange(year, month)[1])
            )

            month_total = sum(Decimal(str(tx["amount"])) for tx in month_txs)
            monthly_totals.insert(0, {
                "year": year,
                "month": month,
                "total": month_total,
                "count": len(month_txs)
            })

            all_transactions.extend(month_txs)

        # Calculate statistics
        amounts = [Decimal(str(tx["amount"])) for tx in all_transactions]
        total_spent = sum(amounts)
        avg_amount = total_spent / len(amounts) if amounts else Decimal("0")
        min_amount = min(amounts) if amounts else Decimal("0")
        max_amount = max(amounts) if amounts else Decimal("0")

        # Top merchants in this category
        merchant_totals = defaultdict(lambda: Decimal("0"))
        for tx in all_transactions:
            merchant = tx.get("merchant", "Unknown")
            merchant_totals[merchant] += Decimal(str(tx["amount"]))

        top_merchants = [
            {"merchant": merch, "amount": amt, "percentage": (amt / total_spent * 100) if total_spent > 0 else Decimal("0")}
            for merch, amt in sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Calculate trend (simple linear)
        if len(monthly_totals) >= 2:
            first_half = monthly_totals[:len(monthly_totals)//2]
            second_half = monthly_totals[len(monthly_totals)//2:]
            first_half_avg = Decimal(str(sum(m["total"] for m in first_half) / len(first_half)))
            second_half_avg = Decimal(str(sum(m["total"] for m in second_half) / len(second_half)))
            trend_direction = "increasing" if second_half_avg > first_half_avg else "decreasing"
            trend_change = second_half_avg - first_half_avg
        else:
            trend_direction = "stable"
            trend_change = Decimal("0")

        return {
            "category": category,
            "months_analyzed": months,
            "total_spent": total_spent,
            "total_transactions": len(all_transactions),
            "avg_amount": avg_amount,
            "min_amount": min_amount,
            "max_amount": max_amount,
            "monthly_totals": monthly_totals,
            "top_merchants": top_merchants,
            "trend_direction": trend_direction,
            "trend_change": trend_change,
        }

    def get_spending_trends(self, user_id: int, weeks: int = 4) -> dict:
        """
        Analyze spending trends over recent weeks.

        Args:
            user_id: User ID
            weeks: Number of weeks to analyze

        Returns:
            Dict with weekly breakdown and trends
        """
        today = date.today()
        weekly_data = []

        for i in range(weeks):
            week_end = today - timedelta(days=7 * i)
            week_start = week_end - timedelta(days=6)

            # Get transactions for this week
            week_txs = self.transaction_repo.search(
                user_id=user_id,
                transaction_type="expense",
                start_date=week_start,
                end_date=week_end
            )

            week_total = sum(Decimal(str(tx["amount"])) for tx in week_txs)

            weekly_data.insert(0, {
                "week_start": week_start,
                "week_end": week_end,
                "total": week_total,
                "count": len(week_txs),
                "avg_per_day": week_total / 7,
            })

        # Calculate average weekly spending
        avg_weekly = sum(w["total"] for w in weekly_data) / len(weekly_data) if weekly_data else Decimal("0")

        # Find unusual weeks (> 20% above average)
        unusual_weeks = [
            w for w in weekly_data
            if w["total"] > avg_weekly * Decimal("1.2")
        ]

        return {
            "weeks_analyzed": weeks,
            "weekly_data": weekly_data,
            "avg_weekly_spending": avg_weekly,
            "unusual_weeks": unusual_weeks,
        }

    def get_account_summary(self, user_id: int) -> dict:
        """
        Summary of all accounts with balances and activity.

        Args:
            user_id: User ID

        Returns:
            Dict with account balances, net worth, income vs expenses by account
        """
        accounts = self.account_repo.get_all(user_id, active_only=True)

        # Calculate net worth
        net_worth = sum(Decimal(str(acc["current_balance"])) for acc in accounts)

        # Get activity for each account (last 30 days)
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        account_details = []
        for acc in accounts:
            # Get transactions for this account
            txs = self.transaction_repo.search(
                user_id=user_id,
                account_id=acc["id"],
                start_date=thirty_days_ago,
                end_date=today
            )

            income = sum(Decimal(str(tx["amount"])) for tx in txs if tx["type"] == "income")
            expenses = sum(Decimal(str(tx["amount"])) for tx in txs if tx["type"] == "expense")

            account_details.append({
                "id": acc["id"],
                "name": acc["name"],
                "type": acc["type"],
                "balance": Decimal(str(acc["current_balance"])),
                "last_30_days": {
                    "income": income,
                    "expenses": expenses,
                    "net": income - expenses,
                    "transaction_count": len(txs)
                }
            })

        # Sort by balance (descending)
        account_details.sort(key=lambda x: x["balance"], reverse=True)

        return {
            "net_worth": net_worth,
            "account_count": len(accounts),
            "accounts": account_details,
        }

    def get_top_spending_categories(self, user_id: int, limit: int = 10, days: int = 30) -> list[dict]:
        """
        Get top spending categories for recent period.

        Args:
            user_id: User ID
            limit: Number of categories to return
            days: Number of days to analyze

        Returns:
            List of category dicts with amounts and percentages
        """
        today = date.today()
        start_date = today - timedelta(days=days)

        # Get all expense transactions in period
        transactions = self.transaction_repo.search(
            user_id=user_id,
            transaction_type="expense",
            start_date=start_date,
            end_date=today
        )

        # Calculate totals by category
        category_totals = defaultdict(lambda: Decimal("0"))
        total_spending = Decimal("0")

        for tx in transactions:
            category = tx.get("category", "Uncategorized")
            amount = Decimal(str(tx["amount"]))
            category_totals[category] += amount
            total_spending += amount

        # Build result
        result = [
            {
                "category": cat,
                "amount": amt,
                "percentage": (amt / total_spending * 100) if total_spending > 0 else Decimal("0")
            }
            for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]

        return result
