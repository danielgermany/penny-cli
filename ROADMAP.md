# Finance Tracker - Development Roadmap

## Project Status

**Current Version:** v0.4.0
**Last Updated:** 2025-12-29

---

## ✅ Completed Phases

### Phase 0.1: Core MVP
- ✅ Database schema and migrations
- ✅ Transaction logging with AI categorization
- ✅ Account management (create, list, view)
- ✅ Basic budget tracking (add, list, status)
- ✅ CLI infrastructure with Click
- ✅ Rich terminal formatting

### Phase 0.3: Enhanced Transaction Management
- ✅ Advanced search and filtering (text, dates, amounts, category, account, type)
- ✅ Transaction editing with automatic balance adjustment
- ✅ CSV import/export (generic, Mint, YNAB formats)
- ✅ Comprehensive category management (list, rename, merge, stats, show)

### Phase 0.4: Complete Budget Management
- ✅ Budget edit (limits and alert thresholds)
- ✅ Budget delete with confirmation
- ✅ Budget alerts (show approaching/over budget items)
- ✅ Enhanced status display with visual indicators and summaries

---

## 🚧 Phase 0.5: Enhanced Account Management

**Priority:** Medium
**Estimated Effort:** Small (~2-3 hours)

### Features
1. **Account Edit Command**
   - Update account name, institution
   - Change account type
   - Manual balance adjustments
   - Example: `finance account edit "Checking" --name "Primary Checking"`

2. **Account Delete Command**
   - Soft delete with confirmation
   - Prevent deletion if transactions exist (or cascade delete with warning)
   - Example: `finance account delete "Old Savings" -y`

3. **Account Transfer Command**
   - Move money between accounts
   - Creates paired transfer transactions
   - Updates both account balances
   - Example: `finance account transfer "Checking" "Savings" 500`

### Files to Modify
- `src/cli/commands/account.py`
- `src/core/services/account_service.py` (may need `edit_account()` method)

---

## 🎯 Phase 1.1: Category Rules Management

**Priority:** Medium
**Estimated Effort:** Small (~2 hours)

### Background
Category rules infrastructure already exists (database table, repository) but has no CLI commands.

### Features
1. **List Category Rules**
   - Show learned/manual categorization rules
   - Display usage statistics
   - Example: `finance category rules`

2. **Add Manual Rule**
   - Create merchant → category mapping
   - Override AI categorization
   - Example: `finance category rule add "Amazon" "Shopping - Online"`

3. **Delete Rule**
   - Remove categorization rule
   - Fall back to AI categorization
   - Example: `finance category rule delete "Amazon"`

### Files to Modify
- `src/cli/commands/category.py` (add `rules` subgroup)
- Uses existing `CategoryRuleRepository`

---

## 🎯 Phase 1.2: Recurring Charge Detection

**Priority:** High
**Estimated Effort:** Large (~6-8 hours)

### Background
This is a key feature from the original plan but requires new database infrastructure.

### Database Changes Needed
1. Create migration: `002_recurring_charges.sql`
```sql
CREATE TABLE recurring_charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    merchant TEXT NOT NULL,
    category TEXT NOT NULL,
    typical_amount DECIMAL(12,2),
    frequency TEXT,  -- 'weekly', 'monthly', 'annual'
    day_of_period INTEGER,
    next_expected_date DATE,
    status TEXT DEFAULT 'active',
    first_seen DATE,
    last_seen DATE,
    occurrence_count INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Features
1. **Pattern Detection**
   - Analyze transactions to find recurring patterns
   - Match on merchant + similar amount + regular frequency
   - Confidence threshold (2-3 occurrences)

2. **Recurring Charge Management**
   - `finance recurring list` - Show all recurring charges
   - `finance recurring confirm <id>` - Confirm suspected recurring charge
   - `finance recurring upcoming` - Show charges due soon
   - `finance recurring cancel <id>` - Mark as cancelled

3. **Integration with Decision Support**
   - Factor upcoming recurring charges into affordability checks
   - Alert when recurring charge is late/missing

### Files to Create/Modify
- `src/data/migrations/002_recurring_charges.sql`
- `src/data/repositories/recurring_repo.py` (new)
- `src/core/services/recurring_service.py` (new)
- `src/cli/commands/recurring.py` (new)
- Update `src/cli/main.py` to register recurring commands

---

## 🎯 Phase 1.3: Reporting & Analytics

**Priority:** High
**Estimated Effort:** Medium (~4-5 hours)

### Features
1. **Monthly Summary Report**
   - Total income, expenses, savings
   - Category breakdown with percentages
   - Top merchants
   - Comparison to previous month
   - Example: `finance report monthly`

2. **Category Analysis**
   - Detailed breakdown for specific category
   - Trend over time
   - Top merchants in category
   - Example: `finance report category "Food & Dining - Restaurants"`

3. **Spending Trends**
   - Week-over-week comparison
   - Month-over-month trends
   - Identify unusual spending
   - Example: `finance trends`

4. **Account Summary**
   - Net worth calculation
   - Account balance history
   - Income vs expenses by account
   - Example: `finance report accounts`

### Files to Create
- `src/cli/commands/report.py` (new command group)
- `src/core/services/analytics_service.py` (new)

### Optional Enhancements
- Export reports to PDF/HTML
- Visualizations (charts) if we add plotting library
- Custom date ranges for reports

---

## 🎯 Phase 1.4: Decision Support ("Can I Afford?")

**Priority:** Very High
**Estimated Effort:** Medium (~5-6 hours)

### Background
This is a flagship feature from the original plan - AI-powered financial advice.

### Features
1. **Affordability Check**
   - Natural language question: `finance check "Can I afford $80 dinner tonight?"`
   - Considers:
     - Current budget status (remaining in category)
     - Upcoming recurring charges
     - Savings goals (if implemented)
     - Recent spending patterns
   - Returns: Yes/Maybe/No with reasoning

2. **Budget Impact Analysis**
   - Show how purchase affects budgets
   - Suggest alternatives if over budget
   - Recommend lower amount if borderline

3. **Smart Recommendations**
   - "You have $150 left in dining budget, so yes!"
   - "This would put you $20 over budget. Consider $60 instead."
   - "You have Netflix due in 3 days ($15.99). After that, you'd have $45 left."

### Implementation Approach
- Use Claude API with structured prompt
- Pass current budget status, upcoming bills, transaction history
- Parse response for Yes/No + reasoning
- Cache common queries to reduce API costs

### Files to Create/Modify
- `src/cli/commands/check.py` or add to `main.py`
- Enhance `src/core/claude_client.py` with decision support prompts
- Use existing `BudgetService` and `RecurringService` (Phase 1.2)

---

## 🔮 Phase 2: Advanced Features

### Phase 2.1: Savings Goals
- Define savings targets
- Track progress
- Project completion date
- Recommend savings amounts

### Phase 2.2: Tags & Notes
- Tag transactions (e.g., "business", "gift", "tax-deductible")
- Filter by tags
- Enhanced notes/attachments

### Phase 2.3: Multi-User Support
- User authentication
- Shared budgets
- Permissions

### Phase 2.4: Automated Bank Sync
- Plaid API integration
- Automatic transaction import
- Balance reconciliation
- Duplicate detection

### Phase 2.5: Web Interface
- FastAPI backend
- HTMX frontend (lightweight)
- Dashboard with charts
- Mobile-responsive

### Phase 2.6: Advanced Analytics
- Spending forecasting
- Budget recommendations
- Seasonal pattern detection
- Financial health score

---

## 🛠️ Technical Debt & Improvements

### Testing
- [ ] Add unit tests for repositories
- [ ] Add integration tests for services
- [ ] Add CLI command tests
- [ ] Set up pytest and coverage reporting

### Error Handling
- [ ] Custom exception hierarchy
- [ ] Better error messages
- [ ] Graceful fallbacks for AI failures
- [ ] Retry logic for API calls

### Performance
- [ ] Add database indexes for common queries
- [ ] Cache AI categorizations more aggressively
- [ ] Batch API calls where possible
- [ ] Add query result pagination

### Documentation
- [ ] API documentation (docstrings)
- [ ] User guide with examples
- [ ] Architecture documentation
- [ ] Contributing guidelines

### Code Quality
- [ ] Add type hints everywhere
- [ ] Linting with ruff/pylint
- [ ] Code formatting with black
- [ ] Pre-commit hooks

---

## 📊 Feature Priority Matrix

| Feature | Priority | Effort | Impact | Next Phase |
|---------|----------|--------|--------|------------|
| Decision Support | Very High | Medium | Very High | 1.4 |
| Reporting & Analytics | High | Medium | High | 1.3 |
| Recurring Charges | High | Large | High | 1.2 |
| Category Rules CLI | Medium | Small | Medium | 1.1 |
| Enhanced Accounts | Medium | Small | Low | 0.5 |
| Savings Goals | Low | Medium | Medium | 2.1 |
| Web Interface | Low | Very Large | Medium | 2.5 |

---

## 🎯 Recommended Next Steps

### Immediate (Phase 0.5-1.1)
1. **Enhanced Account Management** - Quick win, rounds out CRUD operations
2. **Category Rules CLI** - Infrastructure exists, just needs commands

### Short-term (Phase 1.2-1.4)
3. **Recurring Charge Detection** - High-value feature, requires database work
4. **Reporting & Analytics** - Leverage existing data for insights
5. **Decision Support** - Flagship AI feature, high user value

### Long-term (Phase 2)
6. **Savings Goals** - Natural extension of budgeting
7. **Automated Bank Sync** - Reduces manual entry friction
8. **Web Interface** - Better UX than CLI for some users

---

## 📝 Notes

### API Cost Considerations
- Current cost: ~$0.01-0.05/day with categorization caching
- Decision support will increase costs (more complex prompts)
- Consider: batch decisions, cache responses, use Haiku for simple checks

### Database Schema Evolution
- Plan migrations carefully (currently at 001_initial.sql)
- Next migration: recurring_charges (002)
- Future: savings_goals (003), tags (004)

### Backwards Compatibility
- Maintain CLI command backwards compatibility
- Deprecate with warnings before removing
- Document breaking changes in CHANGELOG.md

---

## 🤝 Contributing

When implementing new features:
1. Follow existing patterns (repository → service → CLI)
2. Add docstrings to all functions
3. Test manually before committing
4. Update this roadmap when completing phases
5. Keep commit messages descriptive

---

## 📚 References

- Original Project Plan: `PROJECT_PLAN.md`
- Database Schema: `src/data/migrations/001_initial.sql`
- Phase 0.4 Plan: `.claude/plans/atomic-greeting-cocke.md`
