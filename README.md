# Finance Tracker

A command-line personal finance tracker with AI-powered categorization using Claude API.

## Features

- Track expenses, income, and transfers across multiple accounts
- AI-powered transaction categorization
- Budget tracking with real-time status
- Project-based savings goals
- Local-first SQLite storage

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd finance-tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
```

### Usage

```bash
# Initialize the database
finance init

# Log a transaction
finance log "coffee $5"

# View recent transactions
finance list

# Check budget status
finance status
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## License

MIT
