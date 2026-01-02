# Finance Tracker - Development Roadmap

## Project Status

**Current Version:** v2.3.0
**Last Updated:** 2026-01-01

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

### Phase 0.5: Enhanced Account Management
- ✅ Account edit (name, type, institution, notes)
- ✅ Account delete with soft delete (preserves transactions)
- ✅ Account transfer with paired transactions and balance updates

### Phase 1.1: Category Rules Management
- ✅ List category rules with usage statistics
- ✅ Add manual merchant → category mappings
- ✅ Delete rules with confirmation
- ✅ Shows rule source (Manual, AI, Learned)

### Phase 1.2: Recurring Charge Detection
- ✅ Database migration for recurring_charges table
- ✅ Pattern detection algorithm (weekly, monthly, annual)
- ✅ Confidence scoring based on consistency
- ✅ Recurring charge management (add, list, cancel, pause, resume)
- ✅ Upcoming charges with due date calculation
- ✅ Auto-detect patterns from transaction history

### Phase 1.3: Reporting & Analytics
- ✅ Monthly summary with income/expenses/savings
- ✅ Month-over-month comparison
- ✅ Category analysis with trends
- ✅ Weekly spending trends with anomaly detection
- ✅ Account summary with net worth
- ✅ Top spending categories

### Phase 1.4: Decision Support (AI-Powered)
- ✅ Natural language affordability questions
- ✅ AI-powered spending recommendations (YES/MAYBE/NO)
- ✅ Context gathering from budgets, bills, and spending
- ✅ Personalized advice with detailed reasoning
- ✅ Rich formatted output with financial context

### Phase 2.1: Savings Goals
- ✅ Database migration for savings_goals table
- ✅ SavingsGoalRepository with full CRUD operations
- ✅ SavingsGoalService with business logic and recommendations
- ✅ CLI commands (add, list, view, contribute, withdraw, edit, status, delete, recommend)
- ✅ Progress tracking with visual indicators
- ✅ AI-powered savings recommendations
- ✅ Auto-completion when target is reached

### Phase 2.2: Tags & Notes
- ✅ Database migration for tags and transaction_tags tables
- ✅ TagRepository with full CRUD and association management
- ✅ Tag filtering support in TransactionRepository search
- ✅ CLI commands (create, list, add, remove, show, find, stats, delete)
- ✅ Multi-tag filtering in transaction list (--tags option)
- ✅ Tag usage statistics
- ✅ Auto-create tags when tagging transactions

### Phase 2.3: Multi-User Support
- ✅ Database migration for user authentication fields
- ✅ UserRepository with full CRUD operations
- ✅ AuthService with password hashing (SHA-256) and session management
- ✅ Session file-based user switching (~/.finance_tracker_session)
- ✅ CLI commands (register, login, logout, current, list, delete, password)
- ✅ Per-user data isolation (all data scoped to user_id)
- ✅ Optional password protection per user
- ✅ Config integration for automatic session loading

---

## 🎯 Future Enhancements

---

## 🔮 Phase 2: Advanced Features

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

## 📊 Feature Priority Matrix (Remaining Features)

| Feature | Priority | Effort | Impact | Phase |
|---------|----------|--------|--------|-------|
| Savings Goals | Medium | Medium | Medium | 2.1 |
| Testing Suite | Medium | Large | High | Tech Debt |
| Tags & Notes | Low | Small | Low | 2.2 |
| Multi-User Support | Low | Large | Low | 2.3 |
| Automated Bank Sync | Low | Very Large | High | 2.4 |
| Web Interface | Low | Very Large | Medium | 2.5 |
| Advanced Analytics | Low | Medium | Medium | 2.6 |

---

## 🎯 Recommended Next Steps

### Core Features Complete! ✅
All Phase 0 and Phase 1 features (0.1-1.4) have been implemented! The finance tracker now has:
- Complete transaction, account, and budget management
- AI-powered categorization and decision support
- Recurring charge detection
- Comprehensive reporting and analytics

### Next Priority Options

#### Option A: Quality & Stability
**Testing Suite (High Impact, Medium Priority)**
- Add unit tests for repositories
- Integration tests for services
- CLI command tests
- Set up pytest and coverage reporting
- Estimated effort: Large (~8-10 hours)
- Impact: Ensures reliability as features grow

#### Option B: User Experience
**Savings Goals (Medium Priority)**
- Define and track savings targets
- Progress visualization
- Completion date projection
- Savings recommendations
- Estimated effort: Medium (~4-5 hours)
- Impact: Natural extension of budgeting features

#### Option C: Advanced Features
**Tags & Notes Enhancement (Low Priority)**
- Tag transactions for filtering
- Enhanced notes and attachments
- Business expense tracking
- Estimated effort: Small (~2-3 hours)
- Impact: Power user features

#### Option D: Scale & Deployment
**Multi-User Support or Web Interface (Low Priority)**
- Requires significant architectural changes
- Multi-user: Authentication, permissions, shared budgets
- Web: FastAPI backend, frontend, deployment
- Estimated effort: Very Large (20+ hours each)
- Impact: Opens to wider audience

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
