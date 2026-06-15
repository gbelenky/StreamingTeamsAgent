# Project: Streaming Teams Agent

## Primary Goal
Build a **simple, working streaming agent** that delivers a true streaming response experience inside **Microsoft Teams**. The #1 priority is **SIMPLICITY** — this is a demo to show how streaming can be achieved in Teams using the **Microsoft 365 Agents SDK**.

> **Project status**: scaffolded as a **Microsoft 365 Agents Toolkit** project — the F5 experience in VS Code launches the agent into Teams or the Playground automatically (`m365agents.local.yml` / `m365agents.playground.yml`). Production deploy is owned by `azd` + Bicep in `infra/`.

## Tech Stack & Constraints
- **Language / Runtime**: Python, managed with **uv** (use `uv` for env, dependencies, and running the app — no `pip`, no `poetry`, no `venv` manually).
- **SDK**: **Python Microsoft 365 Agents SDK**.
- **AI Backend**: **Microsoft Foundry projects** (use a Foundry project for the model/inference).
- **No pre-release packages** — only stable, released versions of all dependencies.
- **Custom agent**: a simple agent that **streams responses about human history**.

## Deliverables

### 1. The Agent
- A minimal custom agent using the Python M365 Agents SDK.
- Streams responses (token/chunk streaming surfaced in the Teams client).
- Uses a Foundry project as the model backend.
- Keep the code small, readable, and demo-friendly.

### 2. Teams Deployment Package
- A deployment package including a **Teams app manifest** (`manifest.json`, color/outline icons, zipped package) ready to sideload or publish.

### 3. Infrastructure as Code (Bicep)
- Provide **Bicep** scripts targeting **Azure Developer CLI (`azd`)** workflows (`azd up` / `azd deploy`).
- Provision and wire up:
  - **Azure App Service** (host for the agent API)
  - **Azure Bot Service** (Teams channel enabled)
  - **Application Insights** (telemetry)
  - **Managed Identity** (preferred over keys/connection strings)
  - Any required App Settings (Foundry project endpoint, Bot IDs, etc.)
- Tag all resources with `purpose=demo` and `owner=gbelenky`.

### 4. Deploy & Test
- Deploy end-to-end to Azure and **verify it works in Teams** (streaming visible).
- Document validation steps for the deployed API, Bot Service, and App Insights traces.

### 5. Local Dev & Debug
- Clear instructions for running and debugging locally (uv commands, env vars, tunneling for Bot Framework, e.g. dev tunnels / ngrok).
- Show how to attach a debugger and how to test streaming locally.

### 6. M365 Agents Toolkit (VS Code) Walkthrough
- Add **step-by-step instructions** for building/running this same agent using the **Microsoft 365 Agents Toolkit** extension in VS Code, as an alternative path.

## Coding Standards
- Prefer **Managed Identity** for Azure auth — no secrets in code or config.
- Include **observability** (App Insights / OpenTelemetry) in the scaffolded code.
- Explicit error handling, no silent failures.
- No `TODO` placeholders — implement fully.
- Follow Azure Well-Architected Framework basics (least-privilege RBAC, diagnostics enabled).

## Documentation
- A single `README.md` at repo root with:
  - Prerequisites
  - Local run/debug steps (uv-based)
  - `azd` deployment steps
  - Teams sideload steps
  - M365 Agents Toolkit alternative path
  - Teardown (`azd down`)

## Out of Scope / Avoid
- Pre-release / preview packages.
- Deprecated Azure services (classic VMs, ASM, AzureRM PowerShell module).
- Complex multi-agent orchestration — keep it a **single, simple streaming agent**.
- Heavy frameworks or abstractions that obscure the streaming mechanics.

## Definition of Done
A reviewer can clone the repo, run `uv sync`, debug locally, then run `azd up`, sideload the Teams package, and **see a streamed answer about human history appear progressively in Teams**.
