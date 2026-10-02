# AI Developer Intelligence Platform — Frontend

An **Angular 22** single-page application that provides a rich dashboard for monitoring AI-powered code reviews, managing SCM integrations, and exploring review findings with interactive impact graph visualizations.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Directory Structure](#directory-structure)
- [Features & Pages](#features--pages)
- [Core Services](#core-services)
- [Environment Configuration](#environment-configuration)
- [Getting Started](#getting-started)
- [Available Scripts](#available-scripts)
- [API Integration](#api-integration)
- [Routing](#routing)

---

## Overview

The frontend connects to the FastAPI backend and provides:

- A **live dashboard** with review metrics and recent job activity
- An interactive **review detail view** with impact graph, blast radius summary, and AI findings
- A **manual trigger** to kick off a PR review by pasting a GitHub PR URL
- An **integrations page** for linking GitHub accounts and configuring webhooks
- A **settings page** to configure the LLM model, severity threshold, and custom review instructions

---

## Tech Stack

| Technology | Purpose |
|:---|:---|
| **Angular 22** | Component-based SPA framework (standalone components) |
| **Angular Material 22** | UI component library (Material Design) |
| **Angular CDK** | Layout primitives and overlays |
| **RxJS 7** | Reactive streams for HTTP data |
| **Chart.js + ng2-charts** | Bar, doughnut, and line charts for metrics |
| **Cytoscape.js** | Graph rendering for impact / blast radius visualizations |
| **vis-network** | Alternative network graph renderer |
| **TypeScript 6** | Typed superset of JavaScript |
| **SCSS** | CSS preprocessor for component and global styles |
| **dayjs** | Lightweight date formatting |
| **xlsx + file-saver** | Export findings to Excel |
| **Karma + Jasmine** | Unit testing |

---

## Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   └── services/
│   │   │       ├── api.service.ts      # HTTP client wrapper — all backend API calls
│   │   │       └── scm.service.ts      # SCM account management service
│   │   ├── features/
│   │   │   ├── dashboard/
│   │   │   │   └── dashboard.component.ts   # Metrics cards + recent jobs table
│   │   │   ├── reviews/
│   │   │   │   └── reviews.component.ts     # Review detail: findings + impact graph
│   │   │   ├── jobs/
│   │   │   │   └── jobs.component.ts        # Full job history list
│   │   │   ├── integrations/
│   │   │   │   └── integrations.component.ts # SCM accounts + webhook setup
│   │   │   ├── settings/
│   │   │   │   └── settings.component.ts    # LLM model, severity, custom instructions
│   │   │   ├── metrics/
│   │   │   │   └── metrics.component.ts     # Extended analytics charts
│   │   │   └── trigger/
│   │   │       └── trigger.component.ts     # Manual PR review trigger
│   │   ├── layout/
│   │   │   ├── page-layout/
│   │   │   │   └── page-layout.component.ts # Shell layout wrapping all pages
│   │   │   ├── sidenav/
│   │   │   │   └── sidenav.component.ts     # Collapsible left navigation
│   │   │   └── toolbar/
│   │   │       └── toolbar.component.ts     # Top app bar
│   │   ├── app.component.ts            # Root component (router outlet only)
│   │   ├── app.config.ts               # Angular providers (HttpClient, Router)
│   │   └── app.routes.ts               # Lazy-loaded route definitions
│   ├── environments/
│   │   ├── environment.ts              # Production environment config
│   │   └── environment.development.ts  # Development environment config
│   ├── styles.scss                     # Global styles (Material theming)
│   ├── index.html                      # App HTML shell
│   └── main.ts                         # Bootstrap entrypoint
├── package.json
├── angular.json                        # Angular CLI configuration
└── tsconfig.json
```

---

## Features & Pages

### Dashboard (`/dashboard`)
- **KPI Cards** — Total Projects, Active Jobs, Total Issues Found, Average Review Latency, Total Tokens Used
- **Recent Jobs Table** — Live-updating list of the latest review runs with status, PR info, timing, and token usage
- Clicking a job navigates to the **Review Detail** page

### Review Detail (`/reviews/:jobId`)
- **PR Metadata** — PR title, author, commit SHA, changed/affected file counts, risk level
- **Blast Radius Summary** — LLM-generated natural language summary of the impact
- **Impact Graph** — Interactive Cytoscape.js graph visualizing changed symbols and their affected dependencies
- **Findings Table** — Sortable/filterable table of all AI-detected issues with:
  - Severity badge (Critical / High / Medium / Low)
  - Category (Security, Logic, Performance, Style)
  - File path and line number
  - Description, suggested fix, evidence, and confidence
- **Export** — Download findings as an Excel spreadsheet

### Jobs (`/jobs`)
- Paginated history of all review runs across all projects
- Filter by status (pending, processing, completed, failed)

### Integrations (`/integrations`)
- Add and remove **GitHub/GitLab/Bitbucket accounts** (OAuth token-based)
- Browse linked repositories and register **webhooks** per project
- Configure per-webhook LLM model override

### Settings (`/settings`)
- Select default **LLM model** (Ollama, OpenAI GPT, Google Gemini)
- Set minimum **severity threshold** for findings to be reported
- Enter **custom review instructions** sent to the LLM with every review

### Manual Trigger
- Paste a GitHub PR URL to instantly queue a review without waiting for a webhook
- Choose SCM account and LLM model override

---

## Core Services

### [`ApiService`](src/app/core/services/api.service.ts)

Central HTTP client. All backend calls are routed through this service.

| Method | Description |
|:---|:---|
| `getMetrics()` | Fetch dashboard KPI metrics |
| `getRecentJobs()` | Fetch recent review runs |
| `getJobFindings(jobId)` | Fetch full detail for a specific job (findings + impact graph) |
| `triggerReview(prUrl, scmAccountId?, llmModel?)` | Manually trigger a PR review |
| `getGithubRepositories(scmAccountId?)` | List GitHub repositories |
| `getGithubPullRequests(owner, repo, scmAccountId?)` | List open PRs for a repo |
| `getSettings()` | Fetch platform settings |
| `updateSettings(data)` | Update platform settings |

> **Mock Mode:** Set `enableMock: true` in the environment file to run the app entirely with local mock data — no backend required.

### [`ScmService`](src/app/core/services/scm.service.ts)

Handles SCM account CRUD operations (list, create, delete linked accounts).

---

## Environment Configuration

### Development (`src/environments/environment.development.ts`)

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  enableMock: false   // set to true for mock-only mode
};
```

### Production (`src/environments/environment.ts`)

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://your-production-api.example.com/api/v1',
  enableMock: false
};
```

---

## Getting Started

### Prerequisites

- **Node.js 20+** (LTS recommended)
- **npm 10+**
- Backend server running at `http://localhost:8000` (or update `apiUrl` in the environment file)

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm start
# or
ng serve
```

The app starts at **http://localhost:4200** with hot-reload enabled.

### 3. Build for Production

```bash
npm run build
```

Output is generated in `dist/frontend/`.

---

## Available Scripts

| Script | Command | Description |
|:---|:---|:---|
| `start` | `ng serve` | Start local dev server (port 4200) |
| `build` | `ng build` | Production build |
| `watch` | `ng build --watch --configuration development` | Rebuild on file change |
| `test` | `ng test` | Run unit tests with Karma |
| `lint` | `ng lint` | Lint TypeScript files |

---

## API Integration

The frontend communicates with the backend REST API:

| Feature | Endpoint |
|:---|:---|
| Dashboard metrics | `GET /api/v1/dashboard/metrics` |
| Recent jobs | `GET /api/v1/dashboard/jobs` |
| Job findings | `GET /api/v1/dashboard/jobs/{id}/findings` |
| Manual trigger | `POST /api/v1/reviews/trigger` |
| GitHub repos | `GET /api/v1/github/repos` |
| GitHub PRs | `GET /api/v1/github/repos/{owner}/{repo}/pulls` |
| SCM accounts | `GET/POST/DELETE /api/v1/scm-accounts` |
| Settings | `GET/PUT /api/v1/settings` |

All API requests include an `X-API-Key` header for authentication, configured in the API service.

---

## Routing

Routes are **lazy-loaded** for optimal bundle size:

| Path | Component |
|:---|:---|
| `/` → redirects to `/dashboard` | — |
| `/dashboard` | `DashboardComponent` |
| `/reviews/:jobId` | `ReviewsComponent` |
| `/jobs` | `JobsComponent` |
| `/integrations` | `IntegrationsComponent` |
| `/settings` | `SettingsComponent` |
| `/**` → redirects to `/` | — |

All routes are rendered inside the `PageLayoutComponent` shell, which includes the sidenav and top toolbar.
