# SSBJ Gap Analysis Tool

Internal tool for assessing organizational readiness against **SSBJ (Sustainability Standards Board of Japan)** disclosure standards, with built-in **limited assurance review** workflow.

## Features

- **Multi-user system** with role-based access (Admin, Assessor, Reviewer)
- **SSBJ Gap Assessment** — 22 criteria across 4 pillars:
  - Governance (board oversight, competence, management role)
  - Strategy (risks & opportunities, scenario analysis, transition plans)
  - Risk Management (identification, assessment, integration, internal controls)
  - Metrics & Targets (GHG Scope 1/2/3, climate targets, data quality)
- **Maturity scoring** on a 0-5 scale with evidence documentation
- **Limited Assurance Review** — 10-point checklist for reviewers to assess assurance readiness
- **Gap Analysis Reports** with visual charts (pillar scores, category breakdown, radar)
- **Review Reports** with opinion types (Unqualified, Qualified, Adverse, Disclaimer)
- **Dashboard** with aggregated statistics and progress tracking

## SSBJ Timeline Reference

| Fiscal Year | Scope | Status |
|---|---|---|
| FY2025 (ending March 2026) | All eligible companies | Voluntary |
| FY2026 (ending March 2027) | Market cap >= JPY 3 trillion | Mandatory |
| FY2027 (ending March 2028) | Market cap >= JPY 1 trillion | Mandatory |
| FY2028 (ending March 2029) | Market cap >= JPY 500 billion | Mandatory |

## Setup

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Ariuka

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

The app starts at `http://localhost:5000`.

### Default Admin Account

- **Username:** `admin`
- **Password:** `admin123`

> Change the admin password after first login.

## User Roles

| Role | Permissions |
|---|---|
| **Admin** | Full access: manage users, view all assessments and reviews |
| **Assessor** | Create and complete gap assessments |
| **Reviewer** | Conduct limited assurance reviews on completed assessments |

## Workflow

1. **Admin** creates user accounts with appropriate roles
2. **Assessor** creates a new gap assessment for an entity/fiscal year
3. **Assessor** scores each of the 22 SSBJ criteria (0-5 maturity scale) with evidence
4. **Assessor** marks the assessment as complete
5. **Reviewer** starts a limited assurance review on the completed assessment
6. **Reviewer** evaluates 10 assurance criteria (satisfactory / needs improvement / unsatisfactory)
7. **Reviewer** issues an overall opinion and submits the review report

## Maturity Scale

| Score | Level | Description |
|---|---|---|
| 0 | Not Started | No action taken |
| 1 | Initial / Ad-hoc | Some awareness, no formal processes |
| 2 | Developing | Basic processes, inconsistent application |
| 3 | Defined | Formal processes, consistently applied (limited assurance threshold) |
| 4 | Managed | Processes monitored and measured |
| 5 | Optimized | Continuous improvement, leading practice |

## Deployment

### Option 1: Docker (Recommended)

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) then run:

```bash
git clone https://github.com/ariukab0103-tech/Ariuka.git
cd Ariuka
docker compose up --build
```

Open `http://localhost:5000` in your browser. Works on Mac, Windows, and Linux.

To access from iPhone/iPad on the same Wi-Fi network, find your computer's IP address and open `http://<your-ip>:5000` in Safari.

### Option 2: Render (Free Cloud Hosting)

1. Fork this repo on GitHub
2. Go to [render.com](https://render.com) and sign up
3. Click **New > Web Service**
4. Connect your GitHub repo
5. Render auto-detects `render.yaml` — click **Deploy**
6. Access your app at the provided `https://....onrender.com` URL from any device

### Option 3: Railway

1. Go to [railway.app](https://railway.app) and sign up
2. Click **New Project > Deploy from GitHub Repo**
3. Select this repo — Railway auto-detects `railway.json`
4. Access your app at the provided URL

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, Gunicorn
- **Database:** SQLite (default, swappable to PostgreSQL)
- **Frontend:** Bootstrap 5, Chart.js
- **Auth:** Flask-Login with role-based access control
