"""Decision support service for AI-powered spending advice."""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
import re


class DecisionSupportService:
    """Service for AI-powered spending decisions."""

    def __init__(self, budget_service, recurring_service, analytics_service, account_service, ai_client):
        """
        Initialize decision support service.

        Args:
            budget_service: Budget service instance
            recurring_service: Recurring service instance
            analytics_service: Analytics service instance
            account_service: Account service instance
            ai_client: Claude AI client instance
        """
        self.budget_service = budget_service
        self.recurring_service = recurring_service
        self.analytics_service = analytics_service
        self.account_service = account_service
        self.ai_client = ai_client

    def can_afford(self, user_id: int, question: str) -> dict:
        """
        Determine if user can afford a purchase using AI analysis.

        Args:
            user_id: User ID
            question: Natural language question (e.g., "Can I afford $80 dinner?")

        Returns:
            Dict with recommendation, reasoning, and supporting data
        """
        # Extract amount from question
        amount = self._extract_amount(question)
        if not amount:
            return {
                "success": False,
                "error": "Could not extract amount from question. Please include a dollar amount like '$50' or '50 dollars'."
            }

        # Gather financial context
        context = self._gather_context(user_id, amount, question)

        # Build prompt for Claude
        prompt = self._build_decision_prompt(question, amount, context)

        # Get AI recommendation
        try:
            response = self.ai_client.client.messages.create(
                model=self.ai_client.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            ai_response = response.content[0].text.strip()
            recommendation = self._parse_ai_response(ai_response)

            return {
                "success": True,
                "amount": amount,
                "recommendation": recommendation["decision"],
                "reasoning": recommendation["reasoning"],
                "context": context,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get AI recommendation: {str(e)}"
            }

    def _extract_amount(self, question: str) -> Optional[Decimal]:
        """
        Extract dollar amount from natural language question.

        Args:
            question: Natural language question

        Returns:
            Decimal amount or None if not found
        """
        # Look for $XX.XX or $XX patterns
        dollar_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', question)
        if dollar_match:
            return Decimal(dollar_match.group(1))

        # Look for XX dollars/bucks
        word_match = re.search(r'(\d+(?:\.\d{2})?)\s*(?:dollars|bucks|usd)', question, re.IGNORECASE)
        if word_match:
            return Decimal(word_match.group(1))

        return None

    def _gather_context(self, user_id: int, amount: Decimal, question: str) -> dict:
        """
        Gather financial context for decision making.

        Args:
            user_id: User ID
            amount: Purchase amount
            question: Original question

        Returns:
            Dict with budget status, upcoming bills, balances, etc.
        """
        today = date.today()
        context = {}

        # Get account balances
        try:
            accounts = self.account_service.list_accounts(user_id)
            total_balance = sum(Decimal(str(acc["current_balance"])) for acc in accounts)
            context["total_balance"] = total_balance
            context["account_count"] = len(accounts)
        except:
            context["total_balance"] = Decimal("0")
            context["account_count"] = 0

        # Get budget status for current month
        try:
            today = date.today()
            budget_statuses = self.budget_service.get_budget_status(user_id, today.year, today.month)
            context["budgets"] = []

            for status in budget_statuses:
                if status:
                    context["budgets"].append({
                        "category": status["budget"]["category"],
                        "spent": status["spent"],
                        "limit": status["limit"],
                        "remaining": status["remaining"],
                        "percentage": status["percentage"],
                        "is_over": status["is_over"],
                    })
        except:
            context["budgets"] = []

        # Get upcoming recurring charges (next 7 days)
        try:
            upcoming = self.recurring_service.get_upcoming_charges(user_id, days_ahead=7)
            upcoming_total = sum(Decimal(str(charge["typical_amount"])) for charge in upcoming)
            context["upcoming_charges"] = [{
                "merchant": charge["merchant"],
                "amount": Decimal(str(charge["typical_amount"])),
                "due_date": charge.get("next_expected_date"),
            } for charge in upcoming]
            context["upcoming_total"] = upcoming_total
        except:
            context["upcoming_charges"] = []
            context["upcoming_total"] = Decimal("0")

        # Get recent spending (last 7 days)
        try:
            week_ago = today - timedelta(days=7)
            trends = self.analytics_service.get_spending_trends(user_id, weeks=1)
            if trends["weekly_data"]:
                context["last_week_spending"] = trends["weekly_data"][0]["total"]
            else:
                context["last_week_spending"] = Decimal("0")
        except:
            context["last_week_spending"] = Decimal("0")

        return context

    def _build_decision_prompt(self, question: str, amount: Decimal, context: dict) -> str:
        """
        Build prompt for Claude AI.

        Args:
            question: User's question
            amount: Purchase amount
            context: Financial context

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a financial advisor helping someone make a spending decision.

USER QUESTION: {question}
PURCHASE AMOUNT: ${amount}

FINANCIAL CONTEXT:
- Total Account Balance: ${context.get('total_balance', 0)}
- Active Accounts: {context.get('account_count', 0)}

BUDGETS (Current Month):
"""
        if context.get("budgets"):
            for budget in context["budgets"]:
                prompt += f"  - {budget['category']}: ${budget['spent']:.2f} of ${budget['limit']:.2f} spent ({budget['percentage']:.1f}%)\n"
                prompt += f"    Remaining: ${budget['remaining']:.2f}\n"
        else:
            prompt += "  - No budgets set\n"

        prompt += f"\nUPCOMING RECURRING CHARGES (Next 7 Days): ${context.get('upcoming_total', 0):.2f}\n"
        if context.get("upcoming_charges"):
            for charge in context["upcoming_charges"]:
                prompt += f"  - {charge['merchant']}: ${charge['amount']:.2f} on {charge.get('due_date', 'soon')}\n"

        prompt += f"\nRECENT SPENDING (Last 7 Days): ${context.get('last_week_spending', 0):.2f}\n"

        prompt += """
Based on this information, provide a spending recommendation. Your response should be in this exact format:

DECISION: [YES/MAYBE/NO]
REASONING: [1-2 sentences explaining your recommendation, considering budgets, upcoming bills, and overall financial health]

Guidelines:
- YES: If they can comfortably afford it without impacting budgets or upcoming bills
- MAYBE: If it's affordable but would strain budgets or leave little buffer
- NO: If it would exceed budgets, prevent paying upcoming bills, or severely impact financial health
- Be practical and consider both the immediate impact and near-term obligations
"""

        return prompt

    def _parse_ai_response(self, response: str) -> dict:
        """
        Parse Claude AI response into structured format.

        Args:
            response: Raw AI response

        Returns:
            Dict with decision and reasoning
        """
        # Extract decision
        decision_match = re.search(r'DECISION:\s*(YES|MAYBE|NO)', response, re.IGNORECASE)
        decision = decision_match.group(1).upper() if decision_match else "MAYBE"

        # Extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?:\n\n|\Z)', response, re.DOTALL | re.IGNORECASE)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else response.strip()

        return {
            "decision": decision,
            "reasoning": reasoning
        }
