"""Claude AI client for transaction categorization and analysis."""

import json
import re
from typing import Optional
from anthropic import Anthropic


class ClaudeClient:
    """Client for Claude API interactions."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key
            model: Model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def parse_transaction(self, description: str, categories: Optional[list[str]] = None) -> dict:
        """
        Parse transaction description into structured data.

        Args:
            description: Transaction description (e.g., "coffee $5" or "Starbucks $5.50")
            categories: List of valid categories (optional)

        Returns:
            Dict with:
                - merchant: Merchant name
                - amount: Transaction amount
                - category: Suggested category
                - confidence: Confidence level (0.0-1.0)

        Example:
            result = client.parse_transaction("Starbucks coffee $5.50")
            # Returns: {
            #     "merchant": "Starbucks",
            #     "amount": 5.50,
            #     "category": "Food & Dining - Restaurants",
            #     "confidence": 0.95
            # }
        """
        # Default categories if not provided
        if categories is None:
            categories = [
                "Food & Dining - Groceries",
                "Food & Dining - Restaurants",
                "Food & Dining - Fast Food",
                "Transportation - Gas",
                "Transportation - Public Transit",
                "Transportation - Rideshare",
                "Housing - Rent/Mortgage",
                "Housing - Utilities",
                "Shopping - Clothing",
                "Shopping - Electronics",
                "Shopping - General",
                "Entertainment - Streaming",
                "Entertainment - Activities",
                "Healthcare - Medical",
                "Healthcare - Fitness",
                "Other - Miscellaneous",
            ]

        prompt = f"""Parse this transaction and categorize it.

Transaction: "{description}"

Available categories:
{', '.join(categories)}

Extract:
1. Merchant name (or "Unknown" if unclear)
2. Amount in dollars (numeric value only)
3. Best matching category from the list
4. Your confidence (0.0 to 1.0)

Respond ONLY with valid JSON in this exact format:
{{
  "merchant": "...",
  "amount": 0.00,
  "category": "...",
  "confidence": 0.0
}}"""

        try:
            response = self.client.messages.create(
                model=self.model, max_tokens=200, messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Remove markdown code blocks if present
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```\s*", "", content)
            content = content.strip()

            # Parse JSON
            result = json.loads(content)

            # Validate required fields
            required_fields = ["merchant", "amount", "category", "confidence"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Ensure amount is float
            result["amount"] = float(result["amount"])

            # Ensure confidence is float between 0 and 1
            result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))

            return result

        except Exception as e:
            # Fallback to simple parsing if AI fails
            print(f"AI parsing failed: {e}. Using fallback parser.")
            return self._fallback_parse(description)

    def _fallback_parse(self, description: str) -> dict:
        """
        Fallback parser when AI is unavailable.

        Args:
            description: Transaction description

        Returns:
            Dict with parsed data
        """
        # Try to extract amount using regex
        # Prioritize $ sign patterns first
        amount_match = re.search(r'\$(\d+(?:\.\d+)?)', description)
        if not amount_match:
            # Fallback to any decimal number
            amount_match = re.search(r'(\d+\.\d+)', description)

        if amount_match:
            amount = float(amount_match.group(1))
        else:
            amount = 0.0

        # Remove amount from description to get merchant
        merchant = re.sub(r'\$\d+(?:\.\d+)?|\d+\.\d+', '', description).strip()
        merchant = merchant or "Unknown"

        return {
            "merchant": merchant,
            "amount": amount,
            "category": "Other - Miscellaneous",
            "confidence": 0.3,
        }

    def get_spending_insights(
        self, total_income: float, total_expenses: float, category_breakdown: dict, budget_limits: dict
    ) -> str:
        """
        Get AI-powered spending insights.

        Args:
            total_income: Total income for period
            total_expenses: Total expenses for period
            category_breakdown: Dict of category -> amount spent
            budget_limits: Dict of category -> budget limit

        Returns:
            Insights text
        """
        category_text = "\n".join([f"  - {cat}: ${amount:.2f}" for cat, amount in category_breakdown.items()])

        budget_text = "\n".join([f"  - {cat}: ${limit:.2f}" for cat, limit in budget_limits.items()])

        prompt = f"""Analyze this month's spending and provide insights.

Total Income: ${total_income:.2f}
Total Expenses: ${total_expenses:.2f}
Savings: ${total_income - total_expenses:.2f}

Category Breakdown:
{category_text}

Budget Limits:
{budget_text}

Provide:
1. Top 3 observations about spending patterns
2. Any concerning trends
3. One actionable recommendation

Be concise and helpful."""

        try:
            response = self.client.messages.create(
                model=self.model, max_tokens=500, messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            return f"Unable to generate insights: {str(e)}"

    def check_affordability(
        self,
        question: str,
        monthly_income: float,
        month_spent: float,
        budget_remaining: float,
        current_savings: float,
    ) -> str:
        """
        Check if user can afford a purchase.

        Args:
            question: User's question (e.g., "Can I afford $80 dinner?")
            monthly_income: Monthly income
            month_spent: Amount spent this month
            budget_remaining: Budget remaining
            current_savings: Current savings

        Returns:
            Advice text
        """
        prompt = f"""The user wants to know if they can afford a purchase.

Question: "{question}"

Current Financial State:
- Monthly income: ${monthly_income:.2f}
- Month to date spent: ${month_spent:.2f}
- Budget remaining: ${budget_remaining:.2f}
- Current savings: ${current_savings:.2f}

Respond with:
1. YES/MAYBE/NO
2. Brief reasoning
3. One alternative or suggestion

Be supportive but honest."""

        try:
            response = self.client.messages.create(
                model=self.model, max_tokens=300, messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            return f"Unable to provide advice: {str(e)}"
