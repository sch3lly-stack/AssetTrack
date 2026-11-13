# AssetTrack - Permanent Engineering Workflow and Repository Standards

> **MANDATORY REPOSITORY POLICY**  
> This document defines the binding software development workflow, git discipline, pull request review standards, and GitHub project management rules for **AssetTrack**.  
> Every AI agent, lead engineer, and contributor must consult and strictly adhere to this document at the start and throughout every development session.  
> This file must remain in the repository root, version-controlled in Git, and kept up to date as engineering practices evolve. It must never be deleted or ignored.

---

## 1. Engineering Role and Governance

All development in this repository operates under the authority and standards of an enterprise lead software architect, engineering manager, repository maintainer, and code reviewer.

- **GitHub as the Source of Truth**: GitHub is the authoritative project management and development tracking system, not merely a file backup.
- **Traceability**: Every line of production code, bugfix, refactor, and documentation update must trace back to a dedicated GitHub Issue, branch, self-reviewed Pull Request, and verified test suite.
- **Data Integrity & Security**: Enterprise data safety, OWASP compliance, role-based access control (RBAC), and migration discipline supersede speed.

---

## 2. GitHub Issue Tracking & Taxonomy

No development work may occur without a corresponding GitHub Issue.

### Issue Structure Requirements
Every GitHub Issue must clearly define:
1. **Title**: Structured and descriptive (e.g., `feat(auth): Implement OAuth2 JWT and Role-Based Access Control`).
2. **Objective / Problem Statement**: The business and architectural reason for the change.
3. **Background & Technical Context**: Architecture components, models, or endpoints involved.
4. **Scope of Work**: Specific bulleted deliverables.
5. **Acceptance Criteria**: Verifiable testable conditions.
6. **Definition of Done (DoD)**: Passing tests, linting, docs, and clean PR merge.
7. **Priority & Labels**: Proper taxonomy metadata.

### Standard Label Taxonomy
| Label Category | Labels | Description |
| :--- | :--- | :--- |
| **Type** | `type:feature`, `type:bug`, `type:refactor`, `type:security`, `type:documentation`, `type:testing`, `type:infrastructure` | Nature of the work |
| **Priority** | `priority:critical`, `priority:high`, `priority:medium`, `priority:low` | Urgency and impact |
| **Status** | `status:in-progress`, `status:blocked`, `status:ready-for-review`, `status:completed` | Execution lifecycle |
| **Component** | `area:backend`, `area:frontend`, `area:database`, `area:devops`, `area:security` | Subsystem affected |

### Milestone Architecture
Issues must be grouped into formal milestones:
- **Milestone 1: Core Architecture & Persistence Foundation** (Backend models, SQLAlchemy 2.0, Alembic migrations, Database setup)
- **Milestone 2: Security, Authentication & Audit Logging** (JWT auth, RBAC, structured audit trails)
- **Milestone 3: Core IT Asset Management & Personnel Engine** (Assets, Categories, Departments, Employees, Conflict-free Assignments)
- **Milestone 4: Software Licenses, Warranties & Maintenance** (Seat allocation pools, Maintenance calendar, Warranty tracking)
- **Milestone 5: Advanced Business Engines & Reporting** (Depreciation algorithms, QR generation, PDF spec sheets, CSV import/export)
- **Milestone 6: Enterprise User Interface & Dashboard** (React 19 + TypeScript + Vite + Tailwind CSS dashboard, analytics, forms)
- **Milestone 7: Comprehensive Testing & Quality Verification** (Pytest suite, API integration tests, E2E tests)
- **Milestone 8: Production Deployment, CI/CD & Portfolio Showcase** (Docker, Docker Compose, GitHub Actions, Portfolio documentation)

---

## 3. Mandatory Branching Strategy

Development must **never** occur directly on the `main` or production branch.

### Branch Naming Conventions
- `feature/<issue-number>-<short-description>`
- `bugfix/<issue-number>-<short-description>`
- `hotfix/<issue-number>-<short-description>`
- `refactor/<issue-number>-<short-description>`
- `test/<issue-number>-<short-description>`
- `docs/<issue-number>-<short-description>`
- `infra/<issue-number>-<short-description>`

*Examples:*
- `feature/2-role-based-access-control`
- `feature/5-asset-depreciation-engine`
- `bugfix/14-prevent-concurrent-active-assignment`

Branches must remain short-lived and focused on a single concern. Do not bundle unrelated tasks.

---

## 4. Pull Request (PR) Requirements & Traceability

Every code modification must be introduced via a GitHub Pull Request.

### PR Description Template
Every PR must include:
1. **Summary of Changes**: Clear explanation of what was built or altered.
2. **Problem / Motivation**: Why this change is necessary.
3. **Linked Issue**: GitHub closing syntax (e.g., `Closes #12`).
4. **Implementation Details**: Key classes, schemas, endpoints, or UI components modified.
5. **Testing Performed**: Output of automated test runs, edge cases verified, or manual verification steps.
6. **Security & Performance Considerations**: RBAC impacts, database query considerations, migration risks.
7. **Database Migrations**: Explicit notice if schema migrations are included.

---

## 5. Autonomous Pull Request Review & Merge Protocol

AI agents and maintainers have autonomous authority to manage, review, and merge eligible pull requests without interrupting the user for routine steps, provided the following rigorous review sequence is executed:

1. **Diff Inspection**: Inspect the complete git diff for unintentional modifications, debug code, or extraneous files.
2. **Requirements Verification**: Ensure all acceptance criteria of the linked issue are satisfied.
3. **Security Audit**: Verify inputs are validated with Pydantic/type checks, permissions are enforced at endpoints, and no secrets/tokens are exposed.
4. **Code Quality**: Check naming conventions, absence of duplication, proper typing, and docstrings.
5. **Automated Testing**: Run the full test suite (`pytest -v` for backend, build verification for frontend). All tests must pass with zero failures.
6. **Production Build & Linting**: Verify frontend compiles without TypeScript or build errors.
7. **Documented Self-Review**: Record a formal engineering self-review comment on the PR detailing verification steps.
8. **Squash and Merge**: Merge into `main` using squash merge with a conventional commit message.
9. **Issue Resolution**: Verify that the linked GitHub issue is closed upon merge.

---

## 6. Definition of Done (DoD)

A task or issue is **never** considered done merely because code was written.

A task is officially **Done** only when:
- [x] Code is fully implemented according to specifications.
- [x] All acceptance criteria are satisfied.
- [x] Relevant unit and integration tests are written and passing.
- [x] Regression testing confirms no existing functionality is broken.
- [x] Code has undergone self-review or peer review.
- [x] Documentation (README, AGENTS.md, or architecture docs) is updated if applicable.
- [x] PR is merged cleanly into `main`.
- [x] The associated GitHub Issue is closed.

---

## 7. Session Start & Continuation Protocol

At the start of every session:
1. Read `AGENTS.md`.
2. Inspect `git status`, branch state, and remotes.
3. Query open GitHub issues and milestones using `gh issue list`.
4. Check open pull requests using `gh pr list`.
5. Identify the next prioritized task from the backlog.
6. Create or checkout the appropriate feature branch.

At the end of every session:
1. Ensure all work in progress is cleanly committed or documented.
2. Verify all tests pass.
3. Update issue statuses and PR states.
4. Provide a clear status summary linking all relevant GitHub resources.

---

## 8. Commit Conventions & Semantic Versioning

All commits must follow the **Conventional Commits** specification:
- `feat(<scope>): <description>` (new feature)
- `fix(<scope>): <description>` (bug fix)
- `refactor(<scope>): <description>` (code refactoring)
- `test(<scope>): <description>` (adding or modifying tests)
- `docs(<scope>): <description>` (documentation updates)
- `chore(<scope>): <description>` (tooling, dependencies, config)
- `perf(<scope>): <description>` (performance optimizations)

*Example:* `feat(depreciation): implement straight-line and double-declining calculation engine`

---

## 9. Safety Boundaries & Prohibited Actions

The following actions are strictly prohibited without explicit human authorization:
- Deleting or modifying production user data or dropping non-test databases.
- Bypassing branch protection or security constraints.
- Committing API keys, private tokens, or secrets.
- Introducing paid external services or proprietary third-party dependencies without review.
- Concealing failed test results or claiming completion of unverified features.
