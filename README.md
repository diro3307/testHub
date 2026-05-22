# TestHUB QE Portal

A full-stack test management and QA intelligence platform designed to streamline test case management, execution tracking, automation inventory, and quality analytics.

## 🎯 Overview

**TestHUB QE Portal** is an enterprise-grade QA portal that integrates with GitHub, Jenkins, and JIRA to provide comprehensive test management capabilities. It enables QA teams to:

- **Manage test cases** across multiple projects, user stories, and applications
- **Track test execution** with detailed run history and status updates
- **Monitor automation inventory** across repositories with tool/framework/language analysis
- **Generate test documentation** in Markdown and sync to GitHub
- **Access rich dashboards** for quality metrics, automation coverage, and repo health
- **Calculate ROI** on automation investments
- **Audit test activities** with complete execution history
- **Integrate with DevOps tools** (GitHub, Jenkins, JIRA) for seamless workflow

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.10+, Flask 3.x, Flask-SQLAlchemy |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | Vanilla HTML + CSS + JavaScript (no build step) |
| **Authentication** | Session-based, SHA-256 salted password hashing |
| **Integrations** | GitHub API, Jenkins REST API, JIRA REST API, Azure OpenAI |
| **Utilities** | openpyxl (Excel), psycopg2-binary (PostgreSQL) |

---

## 📦 Project Structure

```
/
├── app.py                    # Flask app factory, blueprints, DB init
├── models.py                 # SQLAlchemy models (12 core tables)
├── requirements.txt          # Python dependencies
├── style.css                 # Global stylesheet
├── nav.js                    # Sidebar navigation & session timeout loader
├── session-timeout.js        # Idle timeout warning & auto-logout
├── app.js                    # Shared JS utilities
├── marked.min.js             # Markdown renderer (vendored)
├── chart.min.js              # Chart.js (vendored)
├── site_config.json          # Admin-editable runtime configuration
├── git_token.secure          # GitHub PAT (secure file)
├── jenkins_token.secure      # Jenkins credentials (secure file)
├── jira_token.secure         # JIRA credentials (secure file)
│
├── HTML Pages
│   ├── index.html                      # Login page
│   ├── dashboard.html                  # Main QA metrics dashboard
│   ├── test_execution.html             # Test execution management
│   ├── testsuite.html                  # Read-only test suite viewer
│   ├── GenerateMDFile.html             # Generate & push MD files
│   ├── settings.html                   # Admin-only settings
│   ├── automation_inventory.html       # Automation tech inventory
│   ├── project_dashboard.html          # Per-project metrics
│   ├── savings_calculator.html         # Automation ROI calculator
│   ├── audit_report.html               # Test execution audit trail
│   ├── ai_analysis.html                # AI-powered insights
│   ├── user_profile.html               # User profile & preferences
│   └── faq.html, testhub_howto.html, testhub_architecture.html
│
├── JavaScript Modules
│   ├── testExecution.js                # Test execution logic
│   ├── testsuite.js                    # Test suite viewer logic
│   ├── mdGenerator.js / mdUpload.js    # MD file generation
│   ├── pushMdToGit.js                  # GitHub push logic
│   ├── repoScanner.js                  # Repo scanning utilities
│   ├── dashboardSummary.js             # Dashboard data loading
│   ├── dashboardCharts.js              # Chart rendering
│   ├── automationInventory.js          # Automation inventory UI
│   ├── projectDashboard.js             # Project metrics UI
│   ├── auditReport.js                  # Audit report UI
│   ├── savingsCalculator.js            # ROI calculations
│   └── aiAnalysis.js                   # AI interaction
│
├── components/
│   ├── sidebar.html                    # Shared sidebar navigation
│   ├── portalheader.html               # Shared top header
│   └── footer.html                     # Shared footer
│
└── blueprints/
    ├── auth_bp.py                      # Authentication & user CRUD
    ├── github_bp.py                    # GitHub API integration
    ├── jenkins_bp.py                   # Jenkins integration
    ├── jira_bp.py                      # JIRA integration
    ├── arts_bp.py                      # ART-Git mapping CRUD
    ├── test_mgmt.py                    # Test project/story/app/case management
    ├── test_execution.py               # Test execution runs & results
    ├── reports_bp.py                   # Dashboard data & analytics
    ├── ai_bp.py                        # Azure OpenAI integration
    └── static_bp.py                    # Static file serving + RBAC
```

---

## 🗄️ Database Models

The system uses 12 core tables:

1. **UserManagement** - User accounts, roles, login tracking
2. **ArtGitMapping** - Application Release Train to Git repo mappings
3. **TestProject** - Test projects linked to JIRA epics
4. **TestUserStory** - User stories linked to JIRA stories
5. **TestApplication** - Applications within user stories
6. **TestCase** - Test cases with metadata (type, priority, automation flag)
7. **TestStep** - Individual steps within test cases
8. **TestExecutionRun** - Execution records with status and results
9. **TestStepResult** - Per-step execution results
10. **TestCaseSummary** - Parsed test case counts from GitHub MD files
11. **RepoHealthSummary** - Repository health metrics (staleness, branch protection, etc.)
12. **GitIssue** - Cached GitHub issues from monitored repos

All relationships use cascade delete for data integrity. Schema migrations are applied idempotently at startup via `app.py`.

---

## 👥 Authentication & RBAC

**Three role-based access levels:**

| Role | Access |
|------|--------|
| **testhub_admin** | All pages including Settings |
| **testhub_QA** | All pages except Settings |
| **testhub_dashboard_user** | Dashboard, Automation Inventory, Savings Calculator, Audit Report, FAQ/Help pages only |

**Session Management:**
- Server-side session lifetime: 720 seconds (12 minutes)
- Idle timeout warning configurable by admin (default 8 min)
- Auto-logout configurable by admin (default 10 min)
- First admin user auto-created on startup: `admin / admin123`

---

## 🔌 External Integrations

### GitHub Integration
- List repositories in configured organization
- Fetch & parse test case MD files
- Push generated MD files with conflict avoidance
- Scan repos for open issues and health metrics
- Track staleness, branch protection, README presence

### Jenkins Integration
- Connect to Jenkins server with credentials
- List jobs in Smoke and Regression folders
- Trigger test automation builds
- Poll build status in real-time

### JIRA Integration
- Fetch user story metadata (summary, status, story points, assignee)
- Link test projects to JIRA epics
- Maintain bidirectional story-to-test traceability
- Auto-populate test execution data from JIRA

### Azure OpenAI Integration
- Ask AI questions about test coverage
- Generate risk assessments based on repo data
- Provide quality improvement recommendations

---

## 📋 Core Features

### Test Execution Management
- **3-column layout**: tree navigation, test case table, detail panel
- **Bulk execution**: Select multiple test cases, execute with same status
- **Status tracking**: Pass, Fail, Blocked, NA, In Progress, Modified
- **Evidence tracking**: SharePoint links, JIRA bug IDs
- **Execution history**: Full audit trail per test case
- **Export**: Download test case data to Excel

### Test Case Management
- **Spreadsheet import**: Upload .xlsx, .xls, or .csv to bulk-add test cases
- **Copy test cases**: Clone to another application with full step hierarchy
- **Extra fields**: Custom JSON metadata support
- **Auto-ID generation**: TC-001, TC-002, etc.
- **Test steps**: Multiple action/expected-result pairs per test case

### Markdown Generation & Sync
- **Generate MD from repo**: Fetch existing test cases from GitHub, merge with new ones
- **Generate MD from spreadsheet**: Convert uploaded test data to standardized format
- **Push to GitHub**: Commit generated MD files with automatic conflict resolution
- **Branch support**: Target any branch for sync operations
- **MD Format**: Standardized summary header + metadata table with test step details

### Dashboards & Analytics
- **Main Dashboard**: Summary cards, donut charts, bar charts, repo health
- **Project Dashboard**: Per-project execution status breakdown
- **Automation Inventory**: Language/framework word cloud, tool breakdown tables
- **Audit Report**: Timeline of all test execution runs with filtering & export
- **Savings Calculator**: ROI analysis for automation investments

### Settings & Administration
- **Git/Jenkins/JIRA connection**: Test and manage credentials
- **User management**: Add/edit/delete users with role assignment
- **ART-Git mapping**: Associate Git repos with ARTs and agile teams
- **Automation inventory configuration**: Define tools, frameworks, languages per repo
- **Site configuration**: Session timeouts, admin announcements
- **Email all users**: Quick mass notification capability

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/diro3307/testHub.git
cd testHub

# Install dependencies
pip install -r requirements.txt

# Start the application
python app.py
```

The app will be available at `http://localhost:5000`

**Default credentials:**
- Username: `admin`
- Password: `admin123`

### Environment Variables (Optional)

```bash
# PostgreSQL connection string (uses SQLite if not provided)
export DATABASE_URL="postgresql://user:password@localhost/testhub"

# Flask secret key (change in production)
export TESTHUB_SECRET_KEY="your-secret-key-here"
```

---

## 🔐 Secure Credentials

The portal stores external service credentials in secure files (one line or three lines each):

- **git_token.secure** - GitHub Personal Access Token
- **jenkins_token.secure** - Jenkins URL, username, password (3 lines)
- **jira_token.secure** - JIRA URL, email, PAT (3 lines)

These files are read fresh on every API request and are excluded from version control.

---

## 🎨 User Interface

### Sidebar Navigation
- Dark gradient sidebar with icon labels
- Mobile-responsive hamburger toggle
- Active page highlighting
- Admin-only Settings link

### Shared Components
- **Header**: Logo, user display, logout button
- **Session timeout warning**: Dark modal with countdown & dismissible actions
- **Admin announcements**: Fixed-position banner (dismissible per session)
- **Status badges**: Color-coded (Pass=green, Fail=red, Blocked=amber, NA=grey)

### Responsive Design
- Grid-based layout
- Mobile-friendly card components
- Sortable/filterable tables with keyboard navigation
- Accessible modals with blur backdrop

---

## 📝 API Endpoints

The backend exposes RESTful APIs organized by feature:

**Authentication**
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/me` - Current user info

**Configuration**
- `GET /api/site-config` - Fetch portal settings
- `POST /api/site-config` - Update settings (admin only)

**Test Management**
- `GET/POST /api/test-projects` - Projects CRUD
- `GET/POST /api/test-user-stories` - Stories CRUD
- `GET/POST /api/test-applications` - Applications CRUD
- `GET/POST /api/test-cases` - Test cases CRUD
- `POST /api/test-cases/upload` - Bulk import from spreadsheet
- `POST /api/test-cases/copy` - Clone test cases
- `GET /api/test-cases/generate-md` - Generate markdown
- `POST /api/test-cases/sync-md-to-git` - Push to GitHub

**Test Execution**
- `POST /api/test-execution/run` - Create execution records
- `GET /api/test-execution/history/<tc_id>` - Execution history
- `GET /api/test-execution/summary` - Aggregate statistics

**Dashboards & Reports**
- `GET /api/dashboard-summary` - Main dashboard data
- `GET /api/project-dashboard-summary` - Project metrics
- `GET /api/audit-report` - Execution audit trail
- `GET /api/execution-stats` - Portal-wide statistics

**GitHub Integration**
- `POST /api/git-connect` - Validate & save token
- `GET /api/list-repos` - List organization repos
- `GET /api/git-issues` - Fetch cached issues
- `POST /api/git-issues/refresh` - Scan repos for issues
- `GET /api/repo-health-summary` - Repository health metrics
- `POST /api/repo-health-summary/refresh` - Rescan health

**Jenkins Integration**
- `POST /api/jenkins-connect` - Test connection
- `GET /api/jenkins-jobs` - List jobs
- `POST /api/jenkins-trigger` - Trigger build

**JIRA Integration**
- `POST /api/jira-connect` - Test connection
- `GET /api/jira-issue/<key>` - Fetch issue details

---

## 🏆 Key Highlights

✅ **No build step** - Pure HTML/CSS/JavaScript frontend  
✅ **Lightweight & fast** - Vanilla JS, no heavy frameworks  
✅ **Secure by design** - Session-based auth, salted password hashing  
✅ **Multi-database support** - SQLite dev, PostgreSQL production  
✅ **Complete audit trail** - Every test execution logged with user & timestamp  
✅ **Markdown-first** - Test cases stored & versioned in Git  
✅ **Rich integrations** - GitHub, Jenkins, JIRA, Azure OpenAI  
✅ **Admin-configurable** - Session timeouts, announcements, mappings  
✅ **Mobile responsive** - Works on desktop, tablet, mobile  
✅ **Production-ready** - Error handling, validation, pagination  

---

## 📄 License

This project is part of the TestHUB platform. See LICENSE file for details.

---

## 👤 Contributing

For questions or contributions, please reach out to the project maintainers.

---

## 🙋 Support & Documentation

- **FAQ Page** - In-app FAQ (accessible to all roles)
- **Architecture Guide** - Technical overview (accessible to all roles)
- **How-To Guide** - Feature walkthroughs (accessible to all roles)
- **In-App Help** - Context-sensitive help within each feature
