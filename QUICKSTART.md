# Finance Tracker - Quick Start Guide

## Installation

The package is already installed in editable mode. To set up on a new machine:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install package
pip install -e .
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
   ```

3. Get your API key from: https://console.anthropic.com/

## First Time Setup

Initialize the database and create your first account:

```bash
finance init
```

This will:
- Create the SQLite database
- Set up the schema
- Prompt you to create your first account

## Basic Usage

### Add Accounts

```bash
# Add a checking account
finance account add "Chase Checking" --type checking --balance 1000

# Add a credit card
finance account add "Amex" --type credit_card --balance 0

# List all accounts
finance account list
```

### Log Transactions

The AI will automatically categorize your transactions:

```bash
# Quick transaction logging
finance log "Starbucks coffee $5.50"
finance log "Whole Foods groceries $87.32"
finance log "Gas at Shell $45"

# Override category
finance log "Dinner $80" --category "Food & Dining - Restaurants"

# Specify account
finance log "Coffee $4" --account "Cash"

# Specify date
finance log "Movie tickets $30" --date 2025-01-15
```

### View Transactions

```bash
# Recent transactions
finance list

# Limit results
finance list -n 20

# Filter by month
finance list --month 01
finance list --month 2025-01
```

### Manage Budgets

```bash
# Create budgets
finance budget add "Food & Dining - Restaurants" 300
finance budget add "Transportation - Gas" 150
finance budget add "Shopping - General" 200

# View all budgets
finance budget list

# Check budget status
finance status
```

### Available Categories

The system includes these main categories:

- Food & Dining (Groceries, Restaurants, Fast Food)
- Transportation (Gas, Public Transit, Rideshare)
- Housing (Rent/Mortgage, Utilities)
- Shopping (Clothing, Electronics, General)
- Entertainment (Streaming, Activities)
- Healthcare (Medical, Fitness)
- Other (Miscellaneous)

You can customize categories in `config/categories.yaml`.

## Command Reference

### Core Commands

- `finance init` - Initialize database
- `finance log <description>` - Quick transaction entry
- `finance list` - Show recent transactions
- `finance status` - View budget status
- `finance version` - Show version info

### Account Commands

- `finance account add <name>` - Create account
- `finance account list` - List accounts
- `finance account balance <name> <amount>` - Update balance

### Transaction Commands

- `finance transaction log <description>` - Log transaction
- `finance transaction list` - List transactions
- `finance transaction delete <id>` - Delete transaction

### Budget Commands

- `finance budget add <category> <limit>` - Create budget
- `finance budget list` - List budgets
- `finance budget status` - View status

## Tips

1. **Natural Language**: The AI understands natural descriptions like "coffee $5" or "groceries at Whole Foods $87.32"

2. **Default Account**: If you don't specify an account, it uses the first one alphabetically

3. **Budgets**: Create budgets for categories you want to track closely

4. **Monthly Review**: Run `finance status` at the end of each month to review spending

## Known Issues

- The fallback parser (used when API key is invalid) has minor parsing issues. Always use a valid Anthropic API key for best results.

## Database Location

Your data is stored in: `data/finance.db`

To backup your data:
```bash
# Manual backup
cp data/finance.db data/finance_backup_$(date +%Y%m%d).db

# View database with SQLite
sqlite3 data/finance.db
```

## Next Steps

- Set up budgets for your spending categories
- Import existing transactions from CSV (coming in v0.3)
- Try the AI advisor feature (coming in v0.5)
- Track savings goals with projects (coming in v0.7)

## Support

For issues or questions:
- GitHub Issues: (your-repo-url)
- Documentation: See README.md

Happy tracking!
