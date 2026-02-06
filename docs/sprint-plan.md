# Cisco Neural Language (CNL) - Sprint Plan

> **Version:** 2.0.0
> **Created:** 2026-02-05
> **Updated:** 2026-02-05
> **Author:** River (SM Agent) + jspetrucio
> **PRD:** [docs/prd.md](./prd.md)
> **Architecture:** [docs/architecture.md](./architecture.md)
> **Execution Model:** Wave-based parallel execution
> **Timeline:** 6 waves (~5-6 weeks with parallel dev agents)
> **Sprint Cadence:** Wave completion triggers next wave (not fixed-week)

---

## Execution Model: Waves vs Sprints

This plan uses **wave-based parallel execution** instead of sequential weekly sprints. Stories within the same wave have no dependencies on each other and can be developed simultaneously by multiple dev agents.

**Key principle:** A wave starts only when ALL its blocking dependencies (previous waves) are complete.

---

## Wave Overview

| Wave | Stories | Points | Parallel Capacity | Focus | Milestone |
|------|---------|--------|-------------------|-------|-----------|
| **W1** | 1.4 | 3 | 1 dev | Settings foundation | Config operational |
| **W2** | 1.1, 3.1, 5.1 | 10 | 3 devs | Server + AI + N8N | API + AI Engine running |
| **W3** | 1.3, 2.1, 5.2, 6.1, 6.4 | 19 | 5 devs | Router + Frontend + Dist | NL routing + React scaffold |
| **W4** | 1.2, 3.2, 2.2, 2.4, 2.5, 4.1, 5.3, 6.2, 6.3 | 37 | 9 devs | Full integration | WebSocket + Desktop + Frontend |
| **W5** | 2.3, 3.3, 4.2, 4.3, 6.5 | 24 | 5 devs | Polish + Security + CI | Chat UI + Safety + Release |
| **Total** | **23 stories** | **93 pts** | | | **MVP Complete** |

---

## Dependency Graph

```
W1:  1.4 ─────────────────────────────────────────────────────────
           │              │              │
W2:       1.1            3.1            5.1
           │  ╲            │              │
           │    ╲          │              │
W3:       1.3 ←──(1.1+3.1) 2.1          5.2        6.1    6.4
           │  ╲             │  ╲  ╲  ╲     │          │  ╲
           │    ╲           │    ╲  ╲  ╲   │          │    ╲
W4:       1.2  3.2        2.2  2.4  2.5  4.1  5.3  6.2  6.3
                            │                  │  ╲
                            │                  │    ╲
W5:                        2.3    3.3        4.2  4.3  6.5
```

**Critical path:** 1.4 → 1.1 → 1.3 → 1.2 → 2.3 (5 waves, longest chain)

---

## Wave 1: Foundation (1 story)

**Goal:** Settings and credential management operational. This is the root dependency for the entire project.

**Capacity:** 1 dev agent

### Story 1.4: Settings & Credential Management
**Priority:** P0 | **Points:** 3 | **Type:** Backend/API | **Agent:** @dev

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create `scripts/settings.py` with Settings dataclass and SettingsManager | AC1-2 |
| T2 | Implement Fernet encryption for API keys at rest | AC2 |
| T3 | Implement `is_onboarding_complete()` check | AC2 |
| T4 | Create REST endpoints: `GET/PUT /api/v1/settings` | AC3 |
| T5 | Create REST endpoints: `GET/POST /api/v1/credentials/*` | AC4 |
| T6 | Implement credential validation (Meraki + AI provider) | AC5 |
| T7 | Verify existing `~/.meraki/credentials` backward compatibility | AC6, IV1 |
| T8 | Write unit tests for settings.py | - |

**Done when:** `~/.cnl/settings.json` created, API keys encrypted, REST endpoints respond, existing CLI works.

### Wave 1 Acceptance Checklist

- [ ] `curl localhost:3141/api/v1/settings` returns settings JSON
- [ ] `curl -X POST localhost:3141/api/v1/credentials/validate` works
- [ ] `meraki discover full --client test` still works (CLI backward compat)
- [ ] `pytest tests/test_settings.py` passes
- [ ] No modifications to existing 10 Python modules

---

## Wave 2: Server + AI Engine + N8N Base (3 stories parallel)

**Goal:** FastAPI server running with REST endpoints. LiteLLM connects to AI providers. N8N client ready.

**Capacity:** 3 dev agents in parallel
**Blocked by:** Wave 1 (1.4)

### Story 1.1: FastAPI Server Bootstrap
**Priority:** P0 | **Points:** 5 | **Type:** Backend/API | **Agent:** @dev
**Blocked by:** 1.4

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create `scripts/server.py` with FastAPI app, CORS, static file mount | AC1 |
| T2 | Implement `GET /api/v1/health` health check | AC2 |
| T3 | Implement discovery endpoints wrapping `scripts.discovery` | AC3 |
| T4 | Implement config endpoints wrapping `scripts.config` | AC4 |
| T5 | Implement workflow endpoints wrapping `scripts.workflow` | AC5 |
| T6 | Implement report endpoints wrapping `scripts.report` | AC6 |
| T7 | Implement profile endpoints wrapping `scripts.auth` | AC7 |
| T8 | Add error handling middleware mapping module exceptions to HTTP errors | AC8 |
| T9 | Use `asyncio.to_thread()` for all sync module calls | - |
| T10 | Verify existing CLI still works: `meraki discover`, `meraki config` | IV1 |
| T11 | Write integration tests for all endpoints | - |

**Done when:** `uvicorn scripts.server:app` starts on :3141, all REST endpoints respond, existing CLI unaffected.

---

### Story 3.1: LiteLLM Integration
**Priority:** P0 | **Points:** 3 | **Type:** Backend/Integration | **Agent:** @dev
**Blocked by:** 1.4

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create `scripts/ai_engine.py` with AIEngine class | AC1 |
| T2 | Implement provider mapping (Anthropic, OpenAI, Google, Ollama) | AC2 |
| T3 | Implement async streaming `chat_completion()` | AC3 |
| T4 | Implement provider switching from user settings | AC4 |
| T5 | Add retry logic with exponential backoff | AC5 |
| T6 | Add token usage tracking per session | AC6 |
| T7 | Handle invalid key / quota exceeded gracefully | AC7 |
| T8 | Write unit tests with mocked LiteLLM responses | - |

**Done when:** AIEngine can stream completions from Claude, GPT, and Gemini with proper error handling.

---

### Story 5.1: N8N Connection Manager
**Priority:** P2 | **Points:** 2 | **Type:** Backend/Integration | **Agent:** @dev
**Blocked by:** 1.4

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create `scripts/n8n_client.py` with N8NClient class | AC1 |
| T2 | Implement connection test endpoint | AC2 |
| T3 | Add N8N status to sidebar indicator | AC3 |
| T4 | Graceful disable when not connected | AC4 |
| T5 | Support self-hosted + n8n.cloud | AC5 |

---

### Wave 2 Acceptance Checklist

- [ ] `python -m uvicorn scripts.server:app --port 3141` starts successfully
- [ ] `curl localhost:3141/api/v1/health` returns `{"status": "ok"}`
- [ ] LiteLLM streams from at least 1 provider (Claude primary)
- [ ] N8N client connects when configured, graceful when not
- [ ] All tests pass: `pytest tests/test_server.py tests/test_ai_engine.py tests/test_n8n_client.py`
- [ ] Existing CLI still works

---

## Wave 3: Router + Frontend Scaffold + Distribution Base (5 stories parallel)

**Goal:** Agent Router classifies NL intent. React app scaffolded. pip and Docker distribution ready.

**Capacity:** up to 5 dev agents in parallel
**Blocked by:** Wave 2 (1.1 + 3.1 + 5.1)

### Story 1.3: Agent Router
**Priority:** P0 | **Points:** 5 | **Type:** Backend/AI | **Agent:** @dev
**Blocked by:** 1.1, 3.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create `scripts/agent_router.py` with AgentRouter class | AC1 |
| T2 | Define AGENTS dict with 3 agent definitions (from .claude/agents/*.md) | AC2 |
| T3 | Implement `_quick_classify()` regex/keyword fallback | AC2 |
| T4 | Implement `_llm_classify()` via LiteLLM function-calling | AC3 |
| T5 | Implement confidence scoring | AC4 |
| T6 | Add low-confidence user confirmation flow | AC5 |
| T7 | Add explicit `@agent` prefix routing | AC6 |
| T8 | Implement conversation context for multi-turn | AC7 |
| T9 | Create FUNCTION_REGISTRY mapping names to Python callables | IV1 |
| T10 | Create test set of 50 common commands, verify >90% accuracy | AC3 |
| T11 | Write unit + integration tests | - |

**Done when:** Router correctly classifies "discover my network" -> network-analyst, "block telnet" -> meraki-specialist, "create alert workflow" -> workflow-creator with >90% accuracy.

---

### Story 2.1: React App Scaffold & Design System
**Priority:** P0 | **Points:** 3 | **Type:** Frontend | **Agent:** @dev
**Blocked by:** 1.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create React 19 + TypeScript app with Vite in `frontend/` | AC1-2 |
| T2 | Install and configure Tailwind CSS + shadcn/ui | AC3 |
| T3 | Set up dark mode default with theme toggle | AC4 |
| T4 | Create base layout: sidebar + main + optional right panel | AC5 |
| T5 | Add Lucide icons | AC6 |
| T6 | Configure Vite build output to `frontend/dist/` | AC7 |
| T7 | Configure Vite dev proxy for `/api/*` and `/ws/*` | AC8 |
| T8 | Verify FastAPI serves built frontend | IV2 |

**Done when:** `npm run dev` shows base layout with dark theme, `npm run build` creates dist/ that FastAPI serves.

---

### Story 5.2: Pre-Built N8N Workflow Templates
**Priority:** P2 | **Points:** 3 | **Type:** Backend/Integration | **Agent:** @dev
**Blocked by:** 5.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create 5 N8N workflow template JSONs | AC1 |
| T2 | Include CNL webhook nodes in templates | AC3 |
| T3 | Implement one-click deploy to N8N via API | AC4 |
| T4 | Add chat command routing for N8N workflows | AC5 |

---

### Story 6.1: pip Distribution
**Priority:** P1 | **Points:** 3 | **Type:** Infrastructure | **Agent:** @devops
**Blocked by:** 1.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Configure pyproject.toml for `cnl` package | AC1, AC7 |
| T2 | Bundle frontend static files in Python package | AC2, AC6 |
| T3 | Create `cnl` entry point -> launch FastAPI + open browser | AC3 |
| T4 | Add `--cli` flag for CLI-only mode | AC4 |
| T5 | Add `--version` flag | AC5 |
| T6 | Test clean install in fresh virtualenv | IV1 |

---

### Story 6.4: Docker Distribution
**Priority:** P1 | **Points:** 3 | **Type:** Infrastructure | **Agent:** @devops
**Blocked by:** 1.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create `docker/Dockerfile` with Python + Node + frontend | AC1 |
| T2 | Configure port mapping and volume mounts | AC2-5 |
| T3 | Create docker-compose.yml | AC2 |
| T4 | Optimize image size (< 500MB) | AC6 |
| T5 | Add health check to Dockerfile | AC7 |
| T6 | Test full functionality in container | IV1 |

---

### Wave 3 Acceptance Checklist

- [ ] Agent Router correctly classifies at least 45/50 test commands
- [ ] `cd frontend && npm run dev` launches React app on :5173
- [ ] `npm run build` creates dist/ that FastAPI serves
- [ ] N8N templates deploy successfully (when N8N connected)
- [ ] `pip install -e .` -> `cnl` -> server starts + browser opens
- [ ] `docker build` -> `docker run` -> web UI accessible on :3141

---

## Wave 4: Full Integration (9 stories parallel)

**Goal:** WebSocket streaming. Agent prompts. Complete frontend (onboarding, sidebar, settings). Tauri shell. Workflow monitor. npm + Homebrew.

**Capacity:** up to 9 dev agents in parallel (biggest wave)
**Blocked by:** Wave 3 (1.3 + 2.1 + 5.2 + 6.1 + 6.4)

### Story 1.2: WebSocket Chat Endpoint
**Priority:** P0 | **Points:** 5 | **Type:** Backend/API | **Agent:** @dev
**Blocked by:** 1.1, 1.3

| Task | Description | AC |
|------|-------------|-----|
| T1 | Add WebSocket endpoint `ws://localhost:3141/ws/chat` to server.py | AC1 |
| T2 | Implement JSON message parsing from client | AC2 |
| T3 | Connect to AgentRouter for message processing | AC3 |
| T4 | Stream response chunks with metadata (type, agent, content) | AC4 |
| T5 | Handle graceful disconnect and reconnection | AC5 |
| T6 | Support concurrent WebSocket connections | AC6 |
| T7 | Add confirmation request/response flow for config changes | - |
| T8 | Verify REST endpoints still work alongside WebSocket | IV1 |
| T9 | Write WebSocket integration tests | - |

**Done when:** WebSocket connects, user sends NL message, Router classifies, Agent executes function, response streams back token-by-token.

---

### Story 3.2: Agent Prompt Engineering
**Priority:** P0 | **Points:** 5 | **Type:** Backend/AI | **Agent:** @dev, @architect
**Blocked by:** 1.3

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create system prompts for each agent incorporating Meraki context | AC1 |
| T2 | Inject current network context (org, networks, devices) per request | AC2 |
| T3 | Define tool call schemas for all operations (discover, config, workflow) | AC3-4 |
| T4 | Implement confirmation flow for destructive operations | AC5 |
| T5 | Add explanation generation in agent responses | AC6 |
| T6 | Implement 20-message conversation history window | AC7 |
| T7 | Test prompts across all 3 AI providers | IV2 |
| T8 | Write tests for prompt generation and tool call parsing | - |

**Done when:** All 3 agents respond intelligently with function calls that execute real Meraki operations.

---

### Story 2.2: Onboarding Wizard
**Priority:** P0 | **Points:** 3 | **Type:** Frontend | **Agent:** @dev
**Blocked by:** 2.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create OnboardingWizard component with step state machine | AC1, AC7 |
| T2 | Create Welcome step with skip button | AC2 |
| T3 | Create MerakiKeyStep with API key + Org ID inputs + validation | AC3 |
| T4 | Create AIProviderStep with provider selector + key input + validation | AC4 |
| T5 | Create Success step with "Start Discovery" CTA | AC5 |
| T6 | Implement real API calls for validation (call backend) | AC6 |
| T7 | Save credentials via backend REST API | AC8 |
| T8 | Test onboarding flow end-to-end | - |

**Done when:** First launch shows wizard, credentials validate against real APIs, saved to backend, discovery starts.

---

### Story 2.4: Agent Sidebar
**Priority:** P1 | **Points:** 3 | **Type:** Frontend | **Agent:** @dev
**Blocked by:** 2.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create AgentSidebar component with agent cards | AC1-2 |
| T2 | Implement click-to-select agent routing | AC3 |
| T3 | Add auto-routing toggle switch | AC4 |
| T4 | Add ProfileSwitcher component | AC5-6 |
| T5 | Add connection status indicator | AC7 |
| T6 | Make sidebar collapsible for small screens | AC8 |
| T7 | Connect to backend for dynamic agent list | IV1 |

**Done when:** Sidebar shows 3 agents + profile switcher, clicking agent changes routing mode, profile switch works.

---

### Story 2.5: Settings Panel
**Priority:** P1 | **Points:** 5 | **Type:** Frontend | **Agent:** @dev
**Blocked by:** 2.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create SettingsPanel with tabbed sections | AC1-2 |
| T2 | Meraki Profiles section: CRUD with validation | AC3 |
| T3 | AI Provider section: provider switch + key update | AC4 |
| T4 | N8N Connection section: URL + test + toggle | AC5 |
| T5 | Appearance section: dark/light toggle + font size | AC6 |
| T6 | Implement instant save via REST API | AC7 |
| T7 | Add confirmation for dangerous operations (delete profile) | AC8 |
| T8 | End-to-end test all settings sections | - |

**Done when:** All settings save to backend, reflect immediately in UI, profile changes work.

---

### Story 4.1: Tauri App Shell
**Priority:** P0 | **Points:** 5 | **Type:** Desktop/Infrastructure | **Agent:** @dev, @devops
**Blocked by:** 1.1, 2.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Initialize Tauri 2.0 project in `src-tauri/` | AC1 |
| T2 | Implement FastAPI sidecar launch from Rust | AC2 |
| T3 | Load frontend from embedded assets | AC3 |
| T4 | Configure window: 1200x800, resizable, min 900x600 | AC4 |
| T5 | Set app title and placeholder icon | AC5-6 |
| T6 | Implement graceful shutdown (kill FastAPI on close) | AC7 |
| T7 | Build macOS .app bundle | AC8 |
| T8 | Test: launch -> use -> close cycle | - |

**Done when:** Double-click .app -> FastAPI starts -> WebView loads UI -> all features work -> close kills all processes.

---

### Story 5.3: Workflow Monitoring
**Priority:** P2 | **Points:** 2 | **Type:** Frontend/Backend | **Agent:** @dev
**Blocked by:** 5.1, 2.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create N8N panel in sidebar (when connected) | AC1 |
| T2 | Show workflow status: name, schedule, last run | AC2 |
| T3 | Add pause/resume quick actions | AC3 |
| T4 | Error notifications in chat | AC4 |
| T5 | Chat command: "show my automated workflows" | AC5 |

---

### Story 6.2: npm/npx Distribution
**Priority:** P2 | **Points:** 5 | **Type:** Infrastructure | **Agent:** @devops
**Blocked by:** 6.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create npm package wrapper in `dist/` | AC1 |
| T2 | Embed or download Python runtime | AC2 |
| T3 | Create `npx cnl` entry point | AC3 |
| T4 | Add `--setup` flag | AC4 |
| T5 | Cross-platform support (Mac/Win/Linux) | AC5 |
| T6 | Optimize download size (< 100MB) | AC6 |

---

### Story 6.3: Homebrew Distribution
**Priority:** P2 | **Points:** 3 | **Type:** Infrastructure | **Agent:** @devops
**Blocked by:** 6.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create Homebrew formula in `homebrew/cnl.rb` | AC1 |
| T2 | Configure to install Tauri .app | AC2 |
| T3 | Add `cnl` command to PATH | AC3 |
| T4 | Test upgrade flow | AC4 |
| T5 | Set up custom tap repository | AC5 |

---

### Wave 4 Acceptance Checklist

- [ ] WebSocket connects at `ws://localhost:3141/ws/chat`
- [ ] Send `{"type":"message","content":"discover my network"}` -> streams agent response
- [ ] All 3 agents respond intelligently with function calls
- [ ] Onboarding wizard appears on fresh install
- [ ] Agent sidebar shows 3 agents with correct descriptions
- [ ] Settings panel: all 4 sections functional
- [ ] `tauri build` produces .app/.dmg for macOS
- [ ] Double-click .app -> app launches in < 5 seconds
- [ ] N8N monitoring panel shows workflows (when connected)
- [ ] `npx cnl` starts on machine without Python
- [ ] `brew install cisco/cnl/cnl` installs app

---

## Wave 5: Polish + Security + CI (5 stories parallel)

**Goal:** Main Chat UI with full rendering. Safety layer. System tray. Auto-updater. Release pipeline. MVP complete.

**Capacity:** up to 5 dev agents in parallel
**Blocked by:** Wave 4 (1.2 + 3.2 + 2.2 + 4.1)

### Story 2.3: Main Chat Interface
**Priority:** P0 | **Points:** 8 | **Type:** Frontend | **Agent:** @dev
**Blocked by:** 1.2, 2.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create ChatView component with message list | AC1-2 |
| T2 | Create ChatInput with send button + Enter submit | AC1 |
| T3 | Implement WebSocket hook (useWebSocket) with auto-reconnect | AC3 |
| T4 | Create StreamingText component for token-by-token rendering | AC3 |
| T5 | Show active agent in message header with icon | AC4 |
| T6 | Add syntax highlighting for code blocks (Shiki or Prism) | AC5 |
| T7 | Implement inline HTML report rendering (collapsible) | AC6 |
| T8 | Create diff-style config change preview | AC7 |
| T9 | Create ConfirmDialog for destructive operations | AC8 |
| T10 | Implement Zustand chatStore for message persistence | AC9 |
| T11 | Add auto-scroll + "scroll to bottom" button | AC10 |
| T12 | Test all message types render correctly | - |

**Done when:** User types message -> streams from backend -> renders markdown/code/tables/reports inline with proper formatting.

---

### Story 3.3: Safety Layer
**Priority:** P0 | **Points:** 5 | **Type:** Backend/Security | **Agent:** @dev
**Blocked by:** 3.2

| Task | Description | AC |
|------|-------------|-----|
| T1 | Classify operations into safe/moderate/dangerous categories | AC1 |
| T2 | Implement immediate execution for safe operations | AC2 |
| T3 | Implement preview + confirm flow for moderate operations | AC3 |
| T4 | Implement impact analysis + type-to-confirm for dangerous operations | AC4 |
| T5 | Integrate with existing backup_config() before any write | AC5 |
| T6 | Implement "undo last change" via rollback | AC6 |
| T7 | Implement dry-run mode | AC7 |
| T8 | Add rate limiter for bulk operations | AC8 |
| T9 | Write tests for each safety classification level | - |

**Done when:** Read operations execute freely, config changes require confirmation, backups happen automatically, rollback works.

---

### Story 4.2: System Tray & Native Features
**Priority:** P1 | **Points:** 3 | **Type:** Desktop | **Agent:** @dev
**Blocked by:** 4.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Add system tray icon with CNL logo | AC1 |
| T2 | Create tray menu: Open, Quick Discovery, Settings, Quit | AC2 |
| T3 | Implement Quick Discovery from tray | AC3 |
| T4 | Add native notifications | AC4 |
| T5 | Add launch-on-startup option | AC5 |
| T6 | Add global keyboard shortcut (Cmd+Shift+M) | AC6 |

**Done when:** Tray icon visible, menu works, Quick Discovery sends notification, keyboard shortcut focuses app.

---

### Story 4.3: Auto-Update & Versioning
**Priority:** P2 | **Points:** 3 | **Type:** Desktop/Infrastructure | **Agent:** @dev, @devops
**Blocked by:** 4.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Configure Tauri updater for GitHub Releases | AC1 |
| T2 | Implement background update check on launch | AC2 |
| T3 | Create update notification banner UI | AC3 |
| T4 | Implement one-click update flow | AC4 |
| T5 | Add version display in Settings > About | AC5 |
| T6 | Show changelog in update dialog | AC6 |

**Done when:** App checks for updates on launch, shows banner when available, one-click installs.

---

### Story 6.5: Tauri Release Pipeline
**Priority:** P1 | **Points:** 5 | **Type:** Infrastructure/CI | **Agent:** @devops
**Blocked by:** 4.1

| Task | Description | AC |
|------|-------------|-----|
| T1 | Create `.github/workflows/release.yml` | AC1 |
| T2 | Configure trigger on git tag push | AC2 |
| T3 | Build macOS .dmg (primary) | AC3 |
| T4 | Upload to GitHub Releases | AC3 |
| T5 | Generate Tauri auto-updater manifest | AC4 |
| T6 | Configure code signing (or skip for internal) | AC5 |
| T7 | Verify build completes in < 15 min | AC6 |

---

### Wave 5 Acceptance Checklist

- [ ] Chat messages send via WebSocket and stream responses
- [ ] Code blocks have syntax highlighting
- [ ] Discovery reports render inline
- [ ] Config change confirmations render as interactive buttons
- [ ] "Show my network devices" executes immediately (safe)
- [ ] "Change SSID name" shows preview + confirm (moderate)
- [ ] Backup created automatically before any config change
- [ ] "Undo last change" triggers rollback successfully
- [ ] Dry-run mode works
- [ ] All 3 agents work with Claude, GPT, and Gemini
- [ ] System tray persists when window closed
- [ ] Quick Discovery from tray works
- [ ] No orphan Python processes after app quit
- [ ] Auto-updater configured (can test with mock release)
- [ ] GitHub Actions builds .dmg on tag push
- [ ] Auto-updater manifest published
- [ ] All 5 distribution channels working:
  - [ ] Tauri .app/.dmg
  - [ ] pip install cnl
  - [ ] npx cnl
  - [ ] brew install cnl
  - [ ] docker run cnl

---

## MVP Milestone Checkpoints

| Checkpoint | Wave | Validation |
|------------|------|-----------|
| **M1: Backend foundation** | End W2 | FastAPI + AI Engine + N8N client running |
| **M2: NL routing works** | End W3 | Agent Router classifies >90% commands |
| **M3: Full integration** | End W4 | WebSocket streaming + Desktop + Frontend complete |
| **M4: MVP complete** | End W5 | Safety layer + Chat UI + All 5 distribution channels |

---

## Timeline Comparison

### Previous: Sequential Sprints (8 weeks)

```
S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7 -> S8
W1    W2    W3    W4    W5    W6    W7    W8
                                    ↑
                             S7 ────┘ (only parallel)
```

### Current: Wave-Based Parallel (5-6 weeks)

```
W1 -> W2 -----> W3 ----------> W4 -----------------> W5
      (3 par)   (5 parallel)   (9 parallel!)          (5 parallel)
~3d   ~5d       ~5d            ~7d                     ~5d
                                                       ≈ 5 weeks
```

**Savings:** ~2-3 weeks compared to sequential execution.

**Bottleneck:** Wave 4 has 9 parallel stories (37 points). With 2-3 dev agents, it takes ~2 weeks. With 5+ agents, ~1 week.

---

## Parallel Capacity Planning

| Wave | Stories | Points | With 1 Dev | With 2 Devs | With 3+ Devs |
|------|---------|--------|-----------|-------------|--------------|
| W1 | 1 | 3 | 3 days | 3 days | 3 days |
| W2 | 3 | 10 | 10 days | 5 days | 4 days |
| W3 | 5 | 19 | 12 days | 6 days | 4 days |
| W4 | 9 | 37 | 20 days | 10 days | 7 days |
| W5 | 5 | 24 | 14 days | 7 days | 5 days |
| **Total** | **23** | **93** | **~12 wks** | **~6 wks** | **~5 wks** |

---

## Story Points Summary

| Epic | Stories | Total Points | Waves |
|------|---------|-------------|-------|
| E1: API Foundation | 1.1, 1.2, 1.3, 1.4 | 18 | W1-W4 |
| E2: Chat Frontend | 2.1, 2.2, 2.3, 2.4, 2.5 | 22 | W3-W5 |
| E3: AI Engine | 3.1, 3.2, 3.3 | 13 | W2-W5 |
| E4: Tauri Desktop | 4.1, 4.2, 4.3 | 11 | W4-W5 |
| E5: N8N Integration | 5.1, 5.2, 5.3 | 7 | W2-W4 |
| E6: Distribution | 6.1, 6.2, 6.3, 6.4, 6.5 | 19 | W3-W5 |
| **Total** | **23 stories** | **90 points** | **5 waves** |

---

## Risk Register

| Risk | Impact | Wave | Mitigation |
|------|--------|------|-----------|
| LiteLLM streaming issues | W2 blocked | W2 | Fallback to direct provider SDK |
| Agent Router < 90% accuracy | User frustration | W3 | Improve prompts iteratively; manual fallback always available |
| Wave 4 capacity bottleneck | W4 takes too long | W4 | Prioritize P0 stories first (1.2, 3.2, 4.1); P1/P2 can slip to W5 |
| Tauri + Python sidecar complexity | W4-W5 delayed | W4 | Build web-only first (W1-W3 deliver standalone value) |
| N8N API changes | W3-W4 scope creep | W3-W4 | N8N is optional - skip if blocked |
| npm embedded Python size | W4 UX impact | W4 | Require system Python as fallback |

---

## Story File Naming Convention

Stories are in `docs/stories/` following this pattern:

```
docs/stories/{epic}.{story}.story.md

Examples:
docs/stories/1.1.story.md  # FastAPI Server Bootstrap
docs/stories/1.2.story.md  # WebSocket Chat Endpoint
docs/stories/2.1.story.md  # React App Scaffold
```

---

## Next Steps

1. **Start Wave 1** — Story 1.4 (Settings & Credential Management)
2. **On W1 complete** — Launch Wave 2: Stories 1.1, 3.1, 5.1 in parallel
3. **Handoff to @dev** — Begin implementation

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-02-05 | 1.0.0 | Initial sprint plan (8 sequential sprints) | River (SM) |
| 2026-02-05 | 2.0.0 | Reorganized to wave-based parallel execution (5 waves) | River (SM) |

---

*Generated by River (SM Agent) | CNL Sprint Plan v2.0.0*
*-- River, removendo obstaculos*
