Build a full-stack web application called "TestHUB QE Portal" — a test management and 
QA intelligence platform. Below is the complete specification. Implement every feature 
described. Do not ask clarifying questions — make reasonable decisions and build it all.
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TECH STACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend:  Python 3.10+, Flask 3.x, Flask-SQLAlchemy, SQLite (dev) / PostgreSQL (prod)
Frontend: Vanilla HTML + CSS + JavaScript (no React/Vue/Angular). No build step.
Auth:     Session-based (Flask sessions), SHA-256 salted password hashing
DB Migrations: Inline idempotent ALTER TABLE at app startup (not Alembic)
Dependencies: flask, flask-sqlalchemy, requests, openpyxl, psycopg2-binary, python-dotenv
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/
├── app.py                    # Flask app factory, blueprint registration, DB init
├── models.py                 # All SQLAlchemy models
├── requirements.txt
├── style.css                 # Single global stylesheet
├── nav.js                    # Sidebar active state, mobile toggle, session timeout loader
├── session-timeout.js        # Idle timeout: warn at N min, logout at M min (admin configurable)
├── app.js                    # Shared JS utilities
├── index.html                # Login page
├── dashboard.html            # Main QA metrics dashboard
├── test_execution.html       # Full test execution management page
├── testExecution.js          # All test execution JS logic
├── testsuite.html            # Read-only test suite tree viewer
├── testsuite.js
├── GenerateMDFile.html       # Generate + push MD files to GitHub
├── mdGenerator.js / mdUpload.js / pushMdToGit.js / repoScanner.js
├── settings.html             # Admin-only settings page
├── automation_inventory.html # Automation inventory dashboard
├── automationInventory.js
├── project_dashboard.html    # Per-project test metrics
├── projectDashboard.js
├── dashboard.html / dashboardSummary.js / dashboardCharts.js
├── savings_calculator.html / savingsCalculator.js
├── audit_report.html / auditReport.js
├── ai_analysis.html / aiAnalysis.js
├── user_profile.html
├── faq.html / testhub_howto.html / testhub_architecture.html
├── marked.min.js             # Vendored markdown renderer
├── chart.min.js              # Vendored Chart.js
├── site_config.json          # Admin-editable runtime config (session timeout, announcements)
├── git_token.secure          # GitHub PAT (one line plain text)
├── jenkins_token.secure      # Jenkins URL / user / password (3 lines)
├── jira_token.secure         # JIRA URL / email / PAT (3 lines)
├── components/
│   ├── sidebar.html          # Shared sidebar nav (fetched by all pages)
│   ├── portalheader.html     # Shared top header
│   └── footer.html           # Shared footer
└── blueprints/
    ├── auth_bp.py            # Login, logout, /api/me, user CRUD, site-config
    ├── github_bp.py          # GitHub API integration
    ├── jenkins_bp.py         # Jenkins integration
    ├── jira_bp.py            # JIRA integration
    ├── arts_bp.py            # ART-Git mapping CRUD
    ├── test_mgmt.py          # Test projects/stories/apps/test cases/MD generation
    ├── test_execution.py     # Test execution runs, results, history
    ├── reports_bp.py         # Dashboard data, audit reports, savings calc
    ├── ai_bp.py              # Azure OpenAI integration
    └── static_bp.py          # Static file serving + RBAC
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE MODELS  (models.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. UserManagement       (usr_mgmt_table)
   - id, user_id(unique), password_hash, assigned_role, last_login, account_status
   - Roles: testhub_admin | testhub_QA | testhub_dashboard_user
 
2. ArtGitMapping        (art_git_mapping)
   - id, art_name, git_repo, agile_team, last_updated
   - tool, framework, languages(csv), automation_types(csv)
   - smoke_job_jenkins, regression_smoke_job_jenkins
 
3. TestProject          (test_project)
   - id, project_name, initiative_id(JIRA epic key), art_name, agile_team
   - created_at, created_by
   - has_many: TestUserStory (cascade delete)
 
4. TestUserStory        (test_user_story)
   - id, project_id(FK), user_story_id(JIRA key), title, parent_feature
   - status, story_points, assigned_to, fetched_at, art_name, agile_team
   - has_many: TestApplication (cascade delete)
 
5. TestApplication      (test_application)
   - id, project_id(FK), user_story_id(FK), app_name, created_at
   - has_many: TestCase (cascade delete)
 
6. TestCase             (test_case)
   - id, application_id(FK), tc_id(e.g. TC-001), name, description
   - test_type(Smoke/Regression/E2E/Functional), priority, is_automated
   - created_at, created_by, extra_fields(JSON text)
   - has_many: TestStep, TestExecutionRun (cascade delete)
 
7. TestStep             (test_step)
   - id, test_case_id(FK), step_number, step_action, expected_result
 
8. TestExecutionRun     (test_execution_run)
   - id, test_case_id(FK), run_number, executed_by, executed_on
   - overall_status(No Run/Pass/Fail/Blocked/NA/In Progress/Modified)
   - environment, notes, bug_id(text), sharepoint_link, na_comment
   - has_many: TestStepResult (cascade delete)
 
9. TestStepResult       (test_step_result)
   - id, run_id(FK), step_id(FK), status, actual_result, bug_id, notes
 
10. TestCaseSummary     (testcase_summary)
    - id, repo_name, md_file_name
    - total/regression/smoke/e2e/functional/automated/manual test case counts
    - regression_automated, regression_manual, smoke_automated, smoke_manual
    - end_to_end_automated, end_to_end_manual, last_update
 
11. RepoHealthSummary   (repo_health_summary)
    - id, repo_name, repo_url, last_update, last_author
    - health_type(stale|no_main|direct_push|no_readme), branch, updated_at
 
12. GitIssue            (git_issues)
    - id, git_repo, issue_number, issue_title, issue_url, last_updated
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTHENTICATION & RBAC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Login page (index.html): username + password form, POST /api/login
- SHA-256 password with random salt stored as "salt$hash"
- Session cookie stores user_id + role
- /api/me returns current user or 401
- /api/logout clears session
- Role enforcement in serve_static():
    testhub_admin       → access to ALL pages including settings.html
    testhub_QA          → access to all pages EXCEPT settings.html
    testhub_dashboard_user → only: dashboard, automation_execution_dashboard,
                             savings_calculator, automation_inventory,
                             project_dashboard, audit_report, user_profile,
                             faq, testhub_howto, testhub_architecture,
                             testhub_workflow, testhub_licenses
- First admin user auto-created on startup if no users exist (admin/admin123)
- PERMANENT_SESSION_LIFETIME = 720 seconds (12 min server-side)
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SESSION TIMEOUT (session-timeout.js)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Loaded by nav.js on every authenticated page
- Fetches /api/site-config on load to get admin-configured timeouts
- Default: warn after 8 min idle, auto-logout after 10 min idle
- Activity events that reset timer: mousedown, keydown, touchstart, scroll, click
- Warning modal: dark gradient header, countdown timer, progress bar
  "Stay Logged In" button resets timers; "Log Out Now" button calls POST /api/logout
- isLoggingOut guard prevents click-event bubbling from cancelling logout
- stopPropagation on modal buttons prevents document-level click resetting timers
- __thTestWarning() global for testing in browser console
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SETTINGS PAGE (settings.html — admin only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dark-header accordion sections, each section loads data on expand:
 
1. Connect to Git Repository
   - Input: Git Token (PAT); saves to git_token.secure
   - POST /api/git-connect validates token against GitHub API
   - Shows "GitHub connected" + Disconnect button when active
 
2. Connect to Jenkins
   - Inputs: URL, username, password; saves to jenkins_token.secure
   - POST /api/jenkins-connect; GET /api/jenkins-token to check status
 
3. Connect to JIRA
   - Inputs: JIRA URL, email, PAT; saves to jira_token.secure
   - POST /api/jira-connect; GET /api/jira-token to check status
 
4. User & Access Management
   - Sortable + filterable table (all 4 columns)
   - Columns: Username, Role, Last Login, Status, Actions
   - Filter inputs above each column; sort arrows on header click
   - "📧 Email All Users" button opens mailto: with all userids in To field
   - Add User modal: username, password, role radio buttons (with descriptions)
   - Edit User modal: password (optional), role, active/inactive status
   - Delete with confirmation modal
 
5. Application-ART Mapping
   - Sortable + filterable table: Repository, ART (dropdown), Agile Team (text)
   - "Save All" button batch-saves all rows via POST /api/art-git-mapping/batch
   - Loads repos from /api/list-repos
 
6. Update Automation Inventory
   - Expandable rows per repo showing:
     Tool (UFT/Selenium/Power Automate/Appium/Others)
     Framework (TestNG BDD/TestNG/JUnit/CRAFT BDD/Others)
     Languages (chip input, "Fetch from Git" link)
     Automation Types (chip input: Smoke/Regression/E2E/API)
     Jenkins Smoke Job URL
     Jenkins Regression Job URL
   - Save per row via PATCH /api/art-git-mapping
 
7. ⚙️ Site Configuration
   - Session & Security: Idle Warning After (min), Auto-Logout After (min)
     Live validation hint: "Warning appears after X min, user gets Y min to respond"
     Error if warn >= logout
   - Admin Announcement Banner:
     Checkbox to enable/disable, banner type (Info/Warning/Danger),
     message textarea (500 char max with live counter), live preview
   - Save → POST /api/site-config → writes site_config.json
   - Banner injected by nav.js on every page load (dismissible per session via sessionStorage)
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GITHUB INTEGRATION (github_bp.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Token stored in git_token.secure (plain text, one line).
All calls use Authorization: token <pat> header.
GitHub org is configurable (default hard-set, can be made configurable via site_config).
 
Endpoints:
  POST /api/git-connect          → validate PAT, save to git_token.secure
  POST /api/git-disconnect       → delete git_token.secure
  GET  /api/git-token            → check if token file exists + valid
  POST /api/list-repos           → list all repos in org (paginated)
  GET  /api/repo-languages       → fetch language breakdown for a repo
  GET  /api/list-md-files        → list .md files in a repo/branch
  GET  /api/get-md-file          → fetch raw content of an .md file
  GET  /api/git-branches         → list branches for a repo (paginated)
  POST /api/git-issues/refresh   → scan all repos for open issues → save to DB
  GET  /api/git-issues           → return cached issues
  POST /api/repo-health-summary/refresh → scan repos for: stale(>90d),
       no README, direct push allowed, no main/master branch
  GET  /api/repo-health-summary  → return cached health data
 
MD file push (test_mgmt.py):
  Uses GitHub Contents API PUT to create or update .md files
  Fetches existing SHA before update to avoid conflicts
  Supports branch selection; builds fresh URL to avoid double ?ref= bug
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JENKINS INTEGRATION (jenkins_bp.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Token stored in jenkins_token.secure (3 lines: url, user, password).
 
Endpoints:
  POST /api/jenkins-connect      → test connection, save credentials
  GET  /api/jenkins-token        → check if configured
  GET  /api/jenkins-jobs         → list jobs in Smoke and Regression folders
  POST /api/jenkins-trigger      → trigger a build by job URL
  GET  /api/jenkins-build-status → poll build status by job URL + build number
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JIRA INTEGRATION (jira_bp.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Token stored in jira_token.secure (3 lines: url, email, PAT).
Uses Basic Auth: base64(email:pat).
 
Endpoints:
  POST /api/jira-connect         → validate, save to jira_token.secure
  POST /api/jira-disconnect      → delete file
  GET  /api/jira-token           → check if configured
  GET  /api/jira-issue/<key>     → fetch issue details (summary, status, assignee, parent)
 
When creating a TestUserStory, auto-fetches JIRA fields:
  summary → title, status name, story_points (customfield_10016),
  assignee displayName, parent/epic summary → parent_feature
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ART-GIT MAPPING API (arts_bp.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GET  /api/art-git-mapping          → list all mappings
  POST /api/art-git-mapping          → create/update mapping for one repo
  POST /api/art-git-mapping/batch    → upsert all repo mappings in one call
  GET  /api/agile-teams              → list distinct agile teams
  GET  /api/art-names                → list distinct ART names
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST MANAGEMENT API (blueprints/test_mgmt.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Projects:
  GET/POST /api/test-projects
  GET/PUT/DELETE /api/test-projects/<id>
  Duplicate check on initiative_id (JIRA key)
 
User Stories:
  GET/POST /api/test-user-stories?project_id=X
  PUT/DELETE /api/test-user-stories/<id>
  Duplicate check: same story_key + art + team under same project
  Auto-fetches JIRA metadata on create/update
 
Applications:
  GET/POST /api/test-applications?user_story_id=X
  DELETE /api/test-applications/<id>
  Duplicate check: same app_name under same story
 
Test Cases:
  GET /api/test-cases?application_id=X    → includes last run status
  GET/PUT/DELETE /api/test-cases/<id>
  POST /api/test-cases/upload             → import from .xlsx/.xls/.csv
  POST /api/test-cases/copy               → copy TCs to another application
  Each TC augmented with: last_run_status, last_executed_on, last_executed_by,
    run_count, last_bug_id, last_sharepoint_link
 
Spreadsheet Import (_parse_tc_spreadsheet):
  Accepts .xlsx, .xls, .csv
  Required columns (case-insensitive, multiple aliases):
    Test Case Name, Step Action, Expected Result
  Optional: Description, Step No, Test Type, Priority,
    Automated/Is Automated/Test Method
  Extra unknown columns saved in extra_fields JSON
  Multi-row test cases (one action per row, new TC on non-empty Name column)
  Detailed error messages listing found vs. required columns
 
MD Generation:
  GET /api/test-cases/generate-md?application_id=X&git_repo=Y&branch=Z
    → generates .md file and returns as download
    → fetches existing .md from GitHub first and merges/updates
    → X-MD-Found-Existing response header
  GET /api/test-cases/md-preview?application_id=X&git_repo=Y&branch=Z
    → returns {md_found, existing_count, new_count, duplicates[]}
  POST /api/test-cases/sync-md-to-git
    → generates MD and pushes directly to GitHub repo/branch
 
MD Format:
  Summary header block (# Test Case Summary) with counts:
    Total, Regression, E2E, Smoke, Functional,
    Automated, Manual, and all 6 type+method combinations
  Separator: ---
  Table: Test Case Name | Description | Steps | Type | Automated | User Story | Test Data | Added On | Updated On
  Steps joined with <br> for multiline support
  Existing TCs updated in-place; new TCs appended in new section
 
Branch support:
  GET /api/git-branches?git_repo=X → list branches
  All MD operations accept optional branch parameter
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST EXECUTION PAGE (test_execution.html + testExecution.js)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layout: 3-column — left tree, center TC table, right detail panel
 
Left tree (collapsible):
  Projects → User Stories → Applications → Test Cases
  Each level lazy-loaded on click
  Search box to filter projects
  "+" buttons at project, story, app levels to add children
  Edit/delete for each node
 
Center test case table:
  Columns: TC ID, Name, Type, Priority, Automated, Status,
           Last Run By, Last Run Date, Bug IDs, Evidence (SharePoint link)
  All columns sortable + filterable (dropdown/text filters per column)
  Row click → loads detail in right panel
  Checkbox column for bulk selection
  Status colored badges: Pass(green), Fail(red), Blocked(amber), NA(grey), No Run(light)
  Evidence column shows link icon when SharePoint URL present
  Export to Excel button (xlsx with all columns)
  Column visibility toggle (show/hide columns)
 
Bulk execution panel (shown when TCs selected):
  Statuses: Pass, Fail, Blocked, NA, In Progress
  Pass → prompts for SharePoint evidence link
  Fail → prompts for JIRA bug IDs (chip input, comma-separated), optional blocker ID
  Blocked → justification textarea + optional blocker ID
  NA → justification textarea (required)
  All bulk actions create TestExecutionRun records for all selected TCs
 
Individual TC execution:
  Right panel shows TC details: name, description, type, priority, steps table
  Execute buttons: Pass/Fail/Blocked/NA/In Progress icons
  Each opens status-specific modal
 
Execution history:
  Collapsible run history per TC showing all past runs
  Each run: date, executor, status, notes, bug IDs, evidence links
  "Modified" runs auto-logged when TC details updated
 
Append & Download MD modal:
  Searchable combobox for repo selection (from art-git-mapping)
    → type to filter, highlighted matches, keyboard navigation
  Branch selector checkbox → optional branch selection
  Live preview: shows existing TC count, new TC count, duplicate names
  "Append & Download MD" button generates merged .md file
 
TC Import modal:
  Upload .xlsx/.xls/.csv
  Shows import results (count + names)
 
TC Copy modal:
  Select target application (searchable)
  Copies selected TCs with their steps as new records
 
Edit TC modal:
  Edit name, description, test type, automated flag
  Add/remove/reorder test steps inline
 
Sidebar collapsible tree structure:
  Projects at root, stories nested, apps nested under stories
  TC count badges on application nodes
  ART/team displayed on story nodes
 
Right detail panel sections:
  TC metadata, step-by-step table with expected results
  Latest run status badge
  Execution history accordion (paginated)
  JIRA story info (fetched from JIRA if configured)
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST EXECUTION API (blueprints/test_execution.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  POST /api/test-execution/run
    → body: {test_case_ids[], status, executed_by, bug_id, sharepoint_link,
             na_comment, notes, environment}
    → creates TestExecutionRun for each TC
    → increments run_number per TC
  GET  /api/test-execution/history/<tc_id>  → full run history for one TC
  GET  /api/test-execution/summary?application_id=X
    → aggregate: total, pass, fail, blocked, na, no_run counts
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DASHBOARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Main Dashboard (dashboard.html):
  Summary cards: Total TCs, Automated, Manual, Repositories scanned
  Donut chart: TC type distribution (Smoke/Regression/E2E/Functional)
  Bar chart: Automation coverage by ART
  Repo health summary: stale repos, no-README, direct-push-enabled
  Open GitHub issues table
  Filter by ART → shows breakdown for that ART's repos
  All data from /api/dashboard-summary (aggregated from TestCaseSummary)
 
Project Dashboard (project_dashboard.html):
  Per-project execution status (pass/fail/blocked/na/no-run breakdown)
  Charts per project and per application
  Filterable by project, story, application
  Data from /api/project-dashboard-summary
 
Audit Report (audit_report.html):
  Timeline view of all test execution runs across the portal
  Filterable by date range, project, user, status
  Excel export
  Data from /api/audit-report
 
Automation Inventory (automation_inventory.html):
  Word cloud of languages and frameworks used across all mapped repos
  Tabbed breakdown: by tool, by framework, by language, by automation type
  Drill-down list for each technology showing which repos use it
  Data from ArtGitMapping
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAVINGS CALCULATOR (savings_calculator.html)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Input: manual test hours per cycle, automation %, hourly rate, runs per year
  Output: monthly/quarterly/yearly savings in hours and dollars
  Visual bar chart comparing manual vs automated effort
  Export to PDF/Excel
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATE MD FILE PAGE (GenerateMDFile.html)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 boxes side-by-side:
 
Box 1 — Generate from GitHub repo:
  Searchable combobox for repo (type to filter 194+ repos, yellow highlight on match,
  arrow key + Enter navigation, click to select)
  Branch dropdown (loaded on repo select via GitHub API)
  "Create MD File" button → calls /api/test-cases/generate-md → downloads .md
 
Box 2 — Generate from Spreadsheet:
  File input (.xlsx, .xls)
  "Generate MD File" → parses spreadsheet → downloads .md
 
Box 3 — Push MD File to Git:
  Text input for repo name
  File input for .md file
  Branch dropdown
  "Push & Commit" → base64 encodes file → GitHub Contents API PUT
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST SUITE VIEWER (testsuite.html)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Left panel: expandable tree of ARTs → Agile Teams → Git Repos
  Click a repo → searches for .md file (checks main then master branch)
  Parses .md table → shows TC list in center panel
  Click TC → shows detail in right panel (markdown rendered)
  Read-only view of test cases stored in GitHub
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI ANALYSIS (ai_analysis.html)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Integrates with Azure OpenAI (credentials in azure_openai.secure)
  Accepts user questions about test coverage, quality, risks
  Sends context (repo summaries, TC counts) with prompts
  Renders responses with marked.min.js markdown parser
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHARED UI COMPONENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
components/sidebar.html:
  Dark gradient sidebar with icons + labels
  Nav items: Dashboard, Test Execution, Test Suite, Generate MD, 
             Automation Inventory, Project Dashboard, Savings Calculator,
             Audit Report, AI Analysis, Settings (admin only),
             FAQ/Help pages
  Collapsible on mobile (hamburger toggle)
  Active page highlighted
 
components/portalheader.html:
  Logo + "TestHUB QE Portal" title
  Current user display + role badge
  Logout button
 
nav.js:
  Sets active sidebar item based on current URL
  Loads session-timeout.js dynamically (cache-busted)
  Fetches /api/site-config and injects announcement banner if enabled
  Banner: fixed top strip with dismiss button, colour from config (info/warning/danger)
  Dismissed state stored in sessionStorage
 
style.css:
  Dark sidebar (#1f2937 gradient)
  White main content area
  Card/box components with subtle shadows
  Status badges: green/red/amber/grey/blue
  Modal overlays with blur backdrop
  Dark gradient modal headers (linear-gradient 135deg #232946→#2980b9)
  Responsive grid layout
  Table styles with alternating rows, hover highlight
  Action buttons: dark blue gradient
  Sortable table headers with ⇅/▲/▼ arrows in amber
  Chip input component (tags with × remove)
  Confirm delete modal (shared across pages)
  Connection status pills (green/red rounded badges)
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SITE CONFIG API (auth_bp.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GET  /api/site-config  → reads site_config.json, returns config object
  POST /api/site-config  → validates + writes site_config.json (admin only)
 
Fields stored:
  session_idle_warn_minutes    (default 8)
  session_idle_logout_minutes  (default 10)
  announcement_enabled         (bool)
  announcement_type            (info|warning|danger)
  announcement_message         (string, max 500 chars)
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REPORTS API (reports_bp.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GET /api/dashboard-summary
    → aggregates TestCaseSummary records by ART
    → returns: total TCs, automated %, repo count, health issues,
      type breakdown, per-ART breakdown
 
  POST /api/testcase-summary/refresh
    → scans all configured repos, fetches .md files from GitHub,
      parses summary block, saves to TestCaseSummary
 
  GET /api/project-dashboard-summary
    → aggregates TestExecutionRun results grouped by project/story/app
    → returns pass/fail/blocked/na/no-run counts
 
  GET /api/audit-report?start=&end=&project_id=&user_id=&status=
    → returns all execution runs matching filters
 
  GET /api/execution-stats
    → returns portal-wide execution statistics
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY BEHAVIOURAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. All API responses: {success: true/false, ...} — frontend always checks data.success
2. Every page fetches /api/me on load; redirects to / if 401
3. No Alembic — all schema changes are idempotent ALTER TABLE in app.py _MIGRATIONS list
4. SQLite dev / PostgreSQL prod — auto-detect via DATABASE_URL env var
5. Token files read fresh on every API request (survive Flask reloader restarts)
6. GitHub MD file fetch: check root + MDfiles/ subfolder; match filename containing repo name
7. When pushing MD: always fetch current SHA first to avoid 422 conflict
8. TC auto-ID: TC-001, TC-002... — find highest existing tc_id number and increment
9. "Modified" run logged automatically when a TC is edited (for audit trail)
10. Pagination for GitHub API calls (100 per page) for repos, branches, issues
11. CORS not needed (same-origin Flask serving all HTML + API)
12. Session cookie: Secure=False (HTTP dev), HttpOnly=True, SameSite=Lax
 
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SETUP & RUN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pip install -r requirements.txt
python app.py
# → starts on http://localhost:5000
# → creates testhub.db automatically
# → creates default admin user: admin / admin123
 
Environment variables (optional):
  DATABASE_URL        → PostgreSQL connection string
  TESTHUB_SECRET_KEY  → Flask secret key (default: testhub-secret-key-change-in-prod)
 
 
START BUILDING. Implement all features described above completely.
Begin with: models.py → app.py → auth_bp.py → static_bp.py → index.html → style.css
then progressively add all other blueprints and pages.
