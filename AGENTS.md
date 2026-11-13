# AssetTrack - Permanent Engineering Workflow and Repository Standards

> **MANDATORY REPOSITORY POLICY**  
> This document defines the binding software development workflow, git discipline, pull request review standards, and GitHub project management rules for **AssetTrack**.  
> Every AI agent, lead engineer, and contributor must consult and strictly adhere to this document at the start and throughout every development session.  
> This file must remain in the repository root, version-controlled in Git, and kept up to date as engineering practices evolve. It must never be deleted or ignored.

---

## 1. Daily Operating Routine

Before performing any development work:
1. **Read `AGENTS.md` and inspect the GitHub repository**:
   - `git status`
   - `gh issue list`
   - `gh pr list`
2. **GitHub Issues are the authoritative source of project work**:
   - Never begin a meaningful feature, bug fix, refactor, or improvement without an associated GitHub Issue.
3. **Traceability across all changes**:
   - Always branch from `main` using structured naming: `feature/<issue>-<desc>`, `bugfix/<issue>-<desc>`.
4. **Autonomous Self-Review and Rigorous Testing**:
   - When work is completed, create or update a Pull Request referencing the issue (`Closes #<id>`).
   - Perform a complete engineering self-review (documenting diff inspection, security checks, and test results).
   - Run all relevant automated tests (`pytest -v`) and build verifications.
   - Address any discovered defects directly on the branch.
   - Merge the PR using squash merging once all acceptance criteria and quality gates are satisfied.
5. **Continuous Backlog & Issue Hygiene**:
   - Update the associated GitHub Issue and project tracking information.
   - Maintain this workflow across every session. Do not rely on conversation history to remember project status.
   - Never falsely report completed work or bypass repository security protections.

---

## 2. Engineering Role and Governance

All development in this repository operates under the authority and standards of an enterprise lead software architect, engineering manager, repository maintainer, and code reviewer.

- **GitHub as the Source of Truth**: GitHub is the authoritative project management and development tracking system, not merely a place to store code.
- **Traceability**: Every line of production code, bugfix, refactor, and documentation update must trace back to a dedicated GitHub Issue, branch, self-reviewed Pull Request, and verified test suite.
- **Data Integrity & Security**: Enterprise data safety, OWASP compliance, role-based access control (RBAC), and migration discipline supersede speed.
- **Portfolio-Wide Consistency**: The same disciplined engineering standard applies across the organization's portfolio repositories (*AssetTrack*, *ReleaseOps*, *VulnWatch*, *InfraWatch*, *TeamFlow*).

---

## 3. Recommended GitHub Repository Settings

To enforce engineering rigor directly within GitHub:

| Setting | Standard Configuration | Implementation Status |
| :--- | :--- | :--- |
| **Default Branch** | `main` | Configured |
| **Squash Merging** | Enabled (preferred for clean linear history) | Configured |
| **Delete Merged Branches** | Automatically delete head branches upon merge | Configured |
| **Branch Protection** | Required status checks & PR requirement on `main` | Enforced via workflow |
| **Dependabot Alerts** | Enabled | Configured |
| **Secret Scanning** | Enabled on repository | Configured |
| **Code Scanning** | Enabled via GitHub Actions | In CI roadmap |
| **Single-Developer Exception** | Do not require independent second-party approvals when operating as an autonomous solo developer/agent, but strictly require self-review and passing automated tests before merging | Standard policy |

---

## 4. GitHub Project Management & Board Lifecycle

Work follows a visible 6-column lifecycle on the project board:

```
[ Backlog ] ──► [ Ready ] ──► [ In Progress ] ──► [ In Review ] ──► [ Testing ] ──► [ Done ]
```

1. **Backlog**: Approved future work and feature ideas.
2. **Ready**: Requirements clearly defined with acceptance criteria.
3. **In Progress**: Active development on a dedicated feature/bugfix branch.
4. **In Review**: Pull request opened with self-review documentation.
5. **Testing**: Automated test execution, regression verification, and CI checks.
6. **Done**: Pull request merged, tests verified passing, and issue closed.

### Standard Label Taxonomy
| Label Category | Labels | Description |
| :--- | :--- | :--- |
| **Type** | `type:feature`, `type:bug`, `type:refactor`, `type:security`, `type:documentation`, `type:testing`, `type:infrastructure` | Nature of the work |
| **Priority** | `priority:critical`, `priority:high`, `priority:medium`, `priority:low` | Urgency and impact |
| **Status** | `status:in-progress`, `status:blocked`, `status:ready-for-review`, `status:completed` | Execution lifecycle |
| **Component** | `area:backend`, `area:frontend`, `area:database`, `area:devops`, `area:security` | Subsystem affected |

### Milestone Architecture
- **v0.1.0 - Core Architecture & Backend Domain Services**: Models, migrations, auth/RBAC, asset registry, assignments, software licenses, maintenance.
- **v0.2.0 - Enterprise Web UI & Dashboard Analytics**: Modern React 19 + TypeScript + Tailwind CSS dashboard and workflows.
- **v0.3.0 - Advanced Workflows, QR/PDF & Data Exchange**: Depreciation calculation engine, QR generator, ReportLab PDF reports, CSV import/export.
- **v0.4.0 - Test Automation, CI/CD & Security Hardening**: Full automated test coverage, GitHub Actions CI workflow, security audit.
- **v1.0.0 - Production Release & Portfolio Documentation**: Docker Compose, production README, architecture diagrams, ERD, release notes.

---

## 5. Mandatory Branching Strategy

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
- `feature/7-enterprise-react-ui-dashboard`
- `infra/10-docker-compose-production-setup`

Branches must remain short-lived and focused on a single concern. Do not bundle unrelated tasks.

---

## 6. Pull Request Requirements & Autonomous Self-Review

Every code modification must be introduced via a GitHub Pull Request.

### Honest Review Distinction
> An AI agent cannot independently provide a genuinely independent second-person human code review.  
> Its self-review is valuable and mandatory, but must never be misrepresented as independent human approval.  
> Every PR merged autonomously must record a documented **Engineering Self-Review** detailing verification steps, test output, and checklist satisfaction.

### Self-Review Sequence
Before merging any pull request:
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

## 7. Definition of Done (DoD)

A task or issue is **never** considered done merely because code was written.

A task is officially **Done** only when:
- [x] Code is fully implemented according to specifications.
- [x] All acceptance criteria are satisfied.
- [x] Relevant unit and integration tests are written and passing.
- [x] Regression testing confirms no existing functionality is broken.
- [x] Code has undergone documented self-review or peer review.
- [x] Documentation (README, AGENTS.md, or architecture docs) is updated if applicable.
- [x] PR is merged cleanly into `main`.
- [x] The associated GitHub Issue is closed.

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

---

## 9. Safety Boundaries & Prohibited Actions

The following actions are strictly prohibited without explicit human authorization:
- Deleting or modifying production user data or dropping non-test databases.
- Bypassing branch protection or security constraints.
- Committing API keys, private tokens, or secrets.
- Introducing paid external services or proprietary third-party dependencies without review.
- Concealing failed test results or claiming completion of unverified features.
