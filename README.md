# Procura
Video Link -> https://drive.google.com/file/d/1gfGMAQnmqCIpt0f8XeJAF6C9PYo9ChTw/view?usp=sharing
> **Automate the purchase. Escalate the decision. Verify the outcome.**

Workflows regarding office purchases are very painful, Procura solves this problem through multi app agentic system which has a solution for every failure probability in a real system. (Check out the Evaluation Folder for the tests)
Procura is a reliable AI procurement decision and execution agent built for the **Lemma Multi-App AI Agent Hackathon**.

Instead of allowing an LLM to directly decide and execute purchases, Procura separates **reasoning from authorization and verification**:

- The LLM understands the natural-language request.
- Deterministic engines enforce procurement rules.
- External applications provide context and receive side effects.
- Human approval is required when authority thresholds are exceeded.
- An independent verification step checks the actual resulting application state.
- If execution fails, Procura can re-plan around the failed vendor.

The core principle is:

> **The LLM proposes. Deterministic systems authorize. Independent verification proves the outcome.**

---

## Table of Contents

- [Why Procura](#why-procura)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [End-to-End Flow](#end-to-end-flow)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [External Applications](#external-applications)
- [Deterministic Procurement Logic](#deterministic-procurement-logic)
- [Approval Model](#approval-model)
- [Reliability and Recovery](#reliability-and-recovery)
- [Evaluation](#evaluation)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Running Procura](#running-procura)
- [Using the Web UI](#using-the-web-ui)
- [API](#api)
- [Testing](#testing)
- [Demo Scenario](#demo-scenario)
- [Security Notes](#security-notes)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)

---

## Why Procura

Traditional AI agents can produce convincing explanations while still making incorrect external changes.

Procura treats external side effects as something that must be **authorized and verified**.

For a procurement request, the agent can:

1. Understand what the requester wants.
2. Retrieve budget and existing-order information.
3. Check duplicate orders.
4. Apply company procurement policy.
5. Determine whether the requester has sufficient authority.
6. Compare vendors against hard constraints.
7. Escalate the decision to a human when required.
8. Create the purchase order after approval.
9. Verify the purchase order against the vendor system.
10. Record the verified result in an audit system.
11. Recover from a deterministic vendor failure by selecting an alternate vendor.

This makes Procura an **agentic workflow with reliability controls**, rather than simply an LLM connected to APIs.

---

# Key Features

### 1. Natural-language procurement

Users can submit requests such as:

> We need 30 Engineering Laptops for new engineering hires. We need them within 10 days. Find the best option under company policy and handle the purchase.

The planner extracts structured procurement information using OpenAI.

### 2. Deterministic policy enforcement

The LLM does not decide whether a purchase is allowed.

Dedicated engines enforce:

- Budget limits
- Duplicate-order protection
- Vendor approval
- Inventory requirements
- Delivery deadlines
- Procurement authority

### 3. Multi-application workflow

Procura connects the workflow across:

- **Google Sheets** — budgets and existing orders
- **Slack** — human approval
- **Notion** — audit logging
- **Vendor Sandbox API** — procurement execution and state verification

### 4. Human-in-the-loop approval

High-value purchases are not silently executed.

Procura determines the required approval authority and sends an approval request through Slack.

### 5. Independent verification

Execution success is not accepted simply because an API returned successfully.

Procura queries the vendor system again and verifies:

- Request ID
- Vendor
- Amount
- Approval
- Purchase-order status

Only after verification does the workflow become `VERIFIED`.

### 6. Failure recovery

If the selected vendor returns a deterministic `503` failure, Procura:

1. Detects the execution failure.
2. Removes the failed vendor from the candidate set.
3. Re-runs vendor selection.
4. Re-checks policy and authority.
5. Executes against the alternate vendor.
6. Verifies the new purchase order.

---

# System Architecture

```text
                         ┌─────────────────────────┐
                         │       User / UI          │
                         │      Next.js Web App     │
                         └────────────┬────────────┘
                                      │
                                      │ Procurement request
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI API         │
                         │    /agent/procure        │
                         └────────────┬────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────┐
                    │          LangGraph Agent          │
                    │                                  │
                    │  Understand → Validate            │
                    │       ↓                          │
                    │  Gather Context                  │
                    │       ↓                          │
                    │  Duplicate / Budget / Policy     │
                    │       ↓                          │
                    │  Authority Check                 │
                    │       ↓                          │
                    │  Vendor Evaluation               │
                    │       ↓                          │
                    │  Decision / Approval              │
                    │       ↓                          │
                    │  Execute → Verify                │
                    └───────┬───────────┬──────────────┘
                            │           │
             ┌──────────────┘           └──────────────┐
             ▼                                         ▼
┌─────────────────────────┐                ┌─────────────────────────┐
│ Deterministic Engines   │                │     OpenAI Planner      │
│                         │                │       gpt-5-mini        │
│ • Policy                │                │                         │
│ • Budget                │                │ Extracts structured     │
│ • Duplicate             │                │ procurement information │
│ • Authority             │                │                         │
│ • Vendor Selection      │                │ Does NOT authorize      │
│ • Verification          │                │ or execute purchases    │
└─────────────────────────┘                └─────────────────────────┘
             │
             │
   ┌─────────┼──────────────┬─────────────────┐
   ▼         ▼              ▼                 ▼
┌───────┐ ┌───────┐    ┌────────┐      ┌───────────────┐
│Google │ │ Slack │    │ Notion │      │ Vendor Sandbox│
│Sheets │ │       │    │        │      │    FastAPI    │
└───────┘ └───────┘    └────────┘      └───────┬───────┘
                                                │
                                                │ actual state
                                                ▼
                                      ┌─────────────────────┐
                                      │ Independent         │
                                      │ Verification Engine │
                                      └─────────────────────┘
```

## Architectural principle

The most important boundary is:

```text
             LLM
              │
              │ proposes / extracts
              ▼
      Deterministic Engines
              │
              │ authorize / constrain
              ▼
       External Side Effect
              │
              │ actual state
              ▼
       Independent Verifier
```

The agent therefore does not use the LLM as the final authority over a financial side effect.

---

# End-to-End Flow

```text
1. User submits procurement request
                  │
                  ▼
2. LLM extracts structured request
                  │
                  ▼
3. Validate required fields
                  │
                  ▼
4. Gather external context
       ┌──────────┴──────────┐
       ▼                     ▼
 Google Sheets          Vendor Sandbox
       │
       ▼
5. Duplicate check
                  │
                  ▼
6. Budget check
                  │
                  ▼
7. Policy check
                  │
                  ▼
8. Authority check
                  │
                  ▼
9. Deterministic vendor selection
                  │
                  ▼
10. Human approval if required
                  │
                  ▼
11. Purchase execution
                  │
                  ▼
12. Independent verification
                  │
          ┌───────┴────────┐
          ▼                ▼
       VERIFIED          FAILED
          │                │
          ▼                ▼
13. Notion audit       Recovery /
    record             re-planning
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | FastAPI + Python |
| Agent orchestration | LangGraph |
| LLM | OpenAI `gpt-5-mini` |
| Business data | Google Sheets |
| Human approval | Slack |
| Audit log | Notion |
| Vendor environment | FastAPI deterministic sandbox |
| Testing | pytest |
| Evaluation | Custom scenario runner |
| Version control | Git / GitHub |

---

# Project Structure

```text
Procura/
│
├── agent/
│   ├── graph.py
│   ├── planner.py
│   ├── state.py
│   ├── tools.py
│   ├── openai_test.py
│   ├── test_graph.py
│   └── test_planner.py
│
├── apps/
│   ├── api/
│   │   └── main.py
│   │
│   └── web/
│       ├── src/
│       │   └── app/
│       │       ├── page.tsx
│       │       ├── layout.tsx
│       │       └── globals.css
│       └── package.json
│
├── engines/
│   ├── authority/
│   │   └── engine.py
│   ├── budget/
│   │   └── engine.py
│   ├── duplicate/
│   │   └── engine.py
│   ├── policy/
│   │   └── engine.py
│   ├── vendor/
│   │   └── engine.py
│   └── verification/
│       └── engine.py
│
├── integrations/
│   ├── google_sheets/
│   │   ├── client.py
│   │   └── test_sheets.py
│   ├── slack/
│   │   ├── client.py
│   │   └── test_slack.py
│   └── notion/
│       ├── client.py
│       └── test_notion.py
│
├── sandbox/
│   └── vendor/
│       └── main.py
│
├── evaluation/
│   ├── runner.py
│   ├── assertions/
│   ├── scenarios/
│   └── seeders/
│
├── tests/
│   └── unit/
│
├── pytest.ini
├── .gitignore
└── README.md
```

---

# External Applications

## Google Sheets

Google Sheets acts as Procura's business-data source.

The integration is used for:

### Budgets

Example:

| Department | Budget |
|---|---:|
| Engineering | ₹50,00,000 |
| Marketing | ₹20,00,000 |
| Operations | ₹30,00,000 |

### Existing Orders

Existing procurement records are checked before creating a new purchase.

This prevents the agent from purchasing items that are already sufficiently covered by an existing order.

---

## Slack

Slack is the human approval channel.

When a purchase requires approval, Procura creates an approval request containing:

- Request ID
- Selected vendor
- Purchase amount
- Approval authority
- Approval URL

The human decision becomes part of the execution workflow.

---

## Notion

Notion is used as the audit log.

After successful independent verification, Procura records:

- Request ID
- Vendor
- Amount
- Status
- Decision reason
- Verification result

This creates a human-readable record of completed procurement decisions.

---

# Deterministic Procurement Logic

Vendor selection uses hard constraints before ranking.

A vendor must satisfy **all** of the following:

```text
Vendor approved
        AND
Inventory >= requested quantity
        AND
Delivery <= required deadline
```

Only qualifying vendors are ranked.

The ranking is deterministic:

```text
1. Lowest unit price
2. Earliest delivery
3. Longer warranty
4. Higher rating
```

This means the LLM cannot simply claim that a vendor is the best option.

---

# Demo Vendor Scenario

The deterministic sandbox contains three approved laptop vendors:

| Vendor | Unit Price | Stock | Delivery | Warranty |
|---|---:|---:|---:|---:|
| Vendor A | ₹72,000 | 30 | 3 days | 3 years |
| Vendor B | ₹65,000 | 50 | 18 days | 2 years |
| Vendor C | ₹69,500 | 30 | 7 days | 3 years |

For:

```text
Quantity: 30
Deadline: 10 days
```

Vendor B is cheaper but fails the 10-day deadline.

Vendor A and Vendor C qualify.

Therefore:

```text
Vendor C
30 × ₹69,500
= ₹20,85,000
```

Vendor C is selected because it is the lowest-cost vendor that satisfies all constraints.

---

# Approval Model

Procura uses authority thresholds:

| Purchase Amount | Required Authority |
|---:|---|
| < ₹1,00,000 | Manager |
| ₹1,00,000 – ₹5,00,000 | Department Head |
| ₹5,00,000 – ₹15,00,000 | CTO |
| > ₹15,00,000 | CEO |

The demo purchase is:

```text
₹20,85,000
```

Therefore it requires **CEO approval**.

Procura does not bypass this authority requirement.

---

# Reliability and Recovery

## Independent verification

The execution API response is not treated as proof.

After creating a purchase order, Procura queries the vendor sandbox again and verifies the resulting state.

Conceptually:

```text
Agent says:
"Purchase created."

        ↓

Verifier asks:
"Does the vendor system actually contain
the expected purchase order?"

        ↓

Expected state:
Request ID matches
Vendor matches
Amount matches
Approval matches
Status is valid

        ↓

VERIFIED
```

## Vendor failure recovery

The sandbox supports deterministic vendor failures.

For example:

```text
Vendor C
   ↓
503 Service Unavailable
   ↓
Execution failure detected
   ↓
Remove Vendor C
   ↓
Re-run vendor selection
   ↓
Select Vendor A
   ↓
Execute
   ↓
Verify
   ↓
VERIFIED
```

The key property is that Procura does not report success when the external system did not complete the action.

---

# Evaluation

Procura includes five deterministic scenarios:

### 1. Happy Path

A valid procurement request should reach approval with the correct vendor selected.

### 2. Deadline Constraint

The cheapest vendor is intentionally too slow.

The agent must reject it and select a compliant alternative.

### 3. Duplicate Order

Existing orders already cover the requested quantity.

The agent must block the purchase.

### 4. Budget Exceeded

The available budget is intentionally too low.

The agent must block execution.

### 5. Insufficient Inventory

No vendor has sufficient inventory for the requested quantity.

The agent must refuse to select a vendor.

Run:

```powershell
python evaluation/runner.py
```

The expected evaluation result for the configured scenarios is:

```text
5 / 5 scenarios passed
```

---

# Prerequisites

Install:

- Python 3.11+
- Node.js 18+
- npm
- Git
- A Google account with access to the procurement spreadsheet
- Slack workspace/bot access
- Notion integration/database
- OpenAI API key

---

# Configuration

Create:

```text
.env
```

in the repository root.

Example structure:

```env
OPENAI_API_KEY=your_openai_api_key

SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_CHANNEL_ID=your_slack_channel_id

GOOGLE_SHEETS_CREDENTIALS_FILE=credentials/your-google-credentials.json
GOOGLE_SPREADSHEET_NAME=Procura Procurement Data

NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_notion_database_id
```

Use your actual project configuration.

**Never commit `.env` or credentials to GitHub.**

The repository's `.gitignore` excludes:

```text
.env
credentials/
.venv/
pending_approvals.json
```

---

# Running Procura

Procura has three local services:

```text
Frontend       http://localhost:3000
FastAPI API    http://localhost:8000
Vendor API     http://localhost:8001
```

## 1. Start the vendor sandbox

Open Terminal 1:

```powershell
cd E:\procura\sandbox\vendor
uvicorn main:app --reload --port 8001
```

Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

Expected:

```json
{
  "status": "ok",
  "service": "procura-vendor-sandbox"
}
```

---

## 2. Start the FastAPI backend

Open Terminal 2:

```powershell
cd E:\procura
uvicorn apps.api.main:app --reload --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

FastAPI documentation is available at:

```text
http://localhost:8000/docs
```

---

## 3. Start the Next.js frontend

Open Terminal 3:

```powershell
cd E:\procura\apps\web
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

---

# Using the Web UI

The default demo request is:

```text
We need 30 Engineering Laptops for new engineering hires.
We need them within 10 days.
Find the best option under company policy and handle the purchase.
```

Click:

```text
Run Procurement
```

Procura should:

1. Parse the request.
2. Retrieve business context.
3. Check duplicates.
4. Check budget.
5. Apply policy.
6. Determine authority.
7. Select Vendor C.
8. Show the approval requirement.
9. Provide the Slack approval workflow.
10. Execute after approval.
11. Verify the resulting purchase order.
12. Record the verified result in Notion.

---

# API

## Submit procurement request

```http
POST /agent/procure
```

Request:

```json
{
  "request": "We need 30 Engineering Laptops for new engineering hires. We need them within 10 days. Find the best option under company policy and handle the purchase."
}
```

## Pending approvals

```http
GET /agent/pending
```

## Approval page

```http
GET /agent/approve/{request_id}
```

## Approve and execute

```http
POST /agent/approve/{request_id}
```

## Vendor sandbox

```http
GET /vendors
GET /products
GET /quotes
GET /purchase-orders
GET /health
```

The vendor sandbox also exposes deterministic failure controls used for recovery testing.

---

# Testing

Run the unit tests:

```powershell
pytest
```

Run the evaluation suite:

```powershell
python evaluation/runner.py
```

Run individual integration tests when credentials are configured:

```powershell
pytest integrations/google_sheets/test_sheets.py
pytest integrations/slack/test_slack.py
pytest integrations/notion/test_notion.py
```

---

# Demo Scenario

For a short hackathon demonstration, use this flow:

### Step 1 — Submit request

```text
30 Engineering Laptops
Deadline: 10 days
```

### Step 2 — Show vendor reasoning

Point out:

```text
Vendor B = cheapest
BUT
Vendor B = 18-day delivery
```

Therefore Vendor B is rejected.

Vendor C satisfies the deadline at:

```text
₹20,85,000
```

### Step 3 — Show human approval

The amount exceeds the CEO threshold, so Procura escalates the decision through Slack.

### Step 4 — Approve

Open the approval workflow and approve the purchase.

### Step 5 — Show verification

Procura queries the vendor state independently.

Show:

```text
Purchase created
Verification passed
Audit recorded
```

### Step 6 — Explain recovery

Briefly mention:

> “We also test a vendor returning 503. Procura removes that vendor, replans, executes with the next valid option, and verifies the replacement purchase.”

---

# Security Notes

Never commit:

```text
.env
credentials/
API keys
Slack tokens
Google service-account credentials
Notion tokens
```

Use environment variables for secrets.

The included `.gitignore` is configured to prevent the main local secret/runtime files from being committed.

---

# Limitations

This hackathon implementation intentionally uses a deterministic local vendor sandbox.

The sandbox represents an external procurement system while providing:

- Stable API behavior
- Controlled vendor data
- Deterministic failures
- Reproducible evaluation scenarios
- Observable state changes

This makes reliability testing reproducible without depending on a real vendor's production purchasing API.

The approval state is also designed for the hackathon prototype rather than production-grade distributed persistence.

---

# Future Improvements

Potential production extensions include:

- Persistent approval/workflow state
- Enterprise identity and RBAC
- More procurement categories
- Real ERP/procurement-system integrations
- Multi-currency support
- Contract and supplier risk analysis
- More sophisticated approval policies
- Event-driven execution and verification
- Distributed workflow persistence
- Richer evaluation and observability dashboards
- Cryptographically stronger audit trails

---

# Design Philosophy

Procura is built around one rule:

> **Automate the work. Escalate the judgment. Verify the outcome.**

The LLM is useful for understanding messy human requests and coordinating a workflow.

It should not be trusted as the sole authority for:

- financial limits,
- policy enforcement,
- authorization,
- external side effects,
- or claims that an action succeeded.

Those responsibilities belong to deterministic systems and independent verification.

That separation is what makes Procura a **reliable multi-application AI agent**, rather than just an AI chatbot with API access.

---

## Hackathon

Built for the **Lemma Multi-App AI Agent Hackathon**.

**Project:** Procura  
**Tagline:** Automate the purchase. Escalate the decision. Verify the outcome.
