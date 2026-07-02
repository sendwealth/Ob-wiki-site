---
title: CC Workflow Studio
created: 2026-06-03
updated: 2026-06-03
type: entity
tags: [product, ai, platform, agentic-engineering, workflow-editor, vscode-extension, mcp, open-source, active]
sources:
  - https://github.com/breaking-brake/cc-wf-studio
  - https://marketplace.visualstudio.com/items?itemName=breaking-brake.cc-wf-studio
confidence: high
---

# CC Workflow Studio

> Visual workflow editor for designing AI agent orchestrations. pnpm monorepo with 4 packages (core, CLI, MCP server, VSCode extension), supporting 8 AI coding agents (Claude Code, Copilot, Codex, Gemini, Cursor, Roo, Antigravity). 47.7K LoC TypeScript + React, AGPL-3.0 (extension) / MIT (libraries).

---

## Overview

CC Workflow Studio is an open-source visual canvas for designing, editing, and running AI agent workflows. Users drag-and-drop node types (Prompt, SubAgent, Skill, MCP, Branch, IfElse, Switch, etc.) on a React Flow canvas inside VSCode, then export the resulting `workflow.json` to agent-specific skill files (`.claude/`, `.codex/`, `.cursor/`, `.github/`, `.roo/`, `.gemini/`, `.agent/`).

The project's core insight: **one workflow.json → many agent formats**. Rather than hand-crafting prompts for each AI coding tool, users design orchestration logic once and export to their preferred agent platform.

- **Repository**: [breaking-brake/cc-wf-studio](https://github.com/breaking-brake/cc-wf-studio)
- **License**: AGPL-3.0-or-later (VSCode extension), MIT (core, CLI, MCP, webview)
- **Version**: 0.1.x (early active development)
- **Code Size**: ~47,700 lines TypeScript/TSX across 302 files
- **Contributors**: ~5 active (primarily breaking-brake/b.b)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    workflow.json (single source of truth)     │
└────────┬─────────────┬──────────────┬────────────────────────┘
         │             │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼─────┐
    │ VSCode  │   │  CLI    │   │   MCP    │
    │Extension│   │  ccwf   │   │  Server  │
    │ (canvas)│   │ (stdio) │   │ (stdio)  │
    └────┬────┘   └────┬────┘   └────┬─────┘
         │             │              │
         └─────────────┼──────────────┘
                       ▼
          Agent Skills on Disk
   (.claude/, .codex/, .cursor/, .github/,
    .roo/, .gemini/, .agent/)
```

### Package Structure (pnpm monorepo)

| Package | Published to | Purpose |
|---|---|---|
| `@cc-wf-studio/core` | npm (MIT) | Shared types, validators, Mermaid/Markdown generators, workflow schema — no fs/UI/network deps |
| `@cc-wf-studio/cli` | npm (MIT) | `ccwf` binary: render, validate, export, run, preview, canvas, mcp commands |
| `@cc-wf-studio/mcp` | npm (MIT) | MCP server toolkit (`ccwf-mcp` stdio bin) — get_workflow, apply_workflow, list_agents, etc. |
| `cc-wf-studio` | GitHub Release (AGPL) | VSCode extension with React Flow canvas, Slack sharing, AI editing |

`cc-wf-studio-webview` is bundled into both the extension and CLI at build time — never published standalone.

---

## Workflow Data Model

### WorkflowNode Types (13 total)

```
WorkflowNode = SubAgent | AskUserQuestion | Branch (legacy) | IfElse
             | Switch | Start | End | Prompt | Skill | Mcp
             | SubAgentFlow | Codex | Group
```

### Workflow Schema

```typescript
interface Workflow {
  id: string;
  name: string;
  description?: string;
  version: string;
  schemaVersion?: string;  // "1.0.0" | "1.1.0" | "1.2.0"
  nodes: WorkflowNode[];
  connections: Connection[];
  createdAt: Date;
  updatedAt: Date;
  metadata?: WorkflowMetadata;
  conversationHistory?: ConversationHistory;
  subAgentFlows?: SubAgentFlow[];
  slashCommandOptions?: SlashCommandOptions;
}
```

Schema files live in `packages/core/resources/workflow-schema.json` (source of truth) with auto-generated `.toon` variant.

---

## Key Features

### Visual Canvas Editor
- React Flow based drag-and-drop canvas
- Edit mode (design) + Overview mode (Mermaid diagram + narrative)
- Node-specific dialogs for configuration
- Git versioning integration with historical version browsing

### Multi-Agent Export
| Agent | Export Format |
|---|---|
| Claude Code | `.claude/agents/` + `.claude/commands/` |
| GitHub Copilot Chat | `.github/prompts/` |
| GitHub Copilot CLI | `.github/skills/` |
| OpenAI Codex CLI | `.codex/skills/` |
| Roo Code | `.roo/skills/` |
| Gemini CLI | `.gemini/skills/` |
| Antigravity | `.agent/skills/` |
| Cursor | `.cursor/agents/` + `.cursor/skills/` |

### AI-Assisted Editing (via MCP)
- External AI agents (Claude Code, Copilot, etc.) can read/modify workflows through MCP tools
- Diff preview with accept/reject before applying changes
- Revision-based conflict detection
- 6 MCP tools: `get_current_workflow`, `get_workflow_schema`, `apply_workflow`, `list_available_agents`, `update_nodes`, `highlight_group_node`

### Slack Integration
- Share workflows to Slack channels as file attachments
- Import workflows from Slack via deep links (`vscode://cc-wf-studio/import`)
- OAuth + manual token authentication

---

## Technical Stack

| Layer | Technology |
|---|---|
| Extension Host | TypeScript 5.3, VSCode Extension API 1.80+ |
| Webview UI | React 18.2, React Flow (canvas), Zustand (state) |
| Dialogs | Radix UI Dialog (4-layer z-index: 9999–10002) |
| CLI | Commander.js, Node.js 20+ |
| MCP Server | @modelcontextprotocol/sdk, Zod validation |
| Build | pnpm 11, TypeScript, Vite (webview), tsc (packages) |
| CI/CD | GitHub Actions, Changesets for versioning |
| Release | OIDC Trusted Publishing (npm), GitHub Release (VSIX) |

---

## Data Flows

### Workflow Save
```
User → Canvas Toolbar → vscode-bridge.ts → save-workflow command
  → validate → file-service → .vscode/workflows/*.json
```

### AI Editing via MCP
```
AI Agent → MCP Server (stdio) → get_current_workflow
  → (agent modifies) → apply_workflow → validate → diff preview
  → user accepts → canvas updates
```

### Export & Run
```
Workflow JSON → planWorkflowExportFiles() → generate agent-specific files
  → write to .claude/, .codex/, etc. → `ccwf run` to execute
```

---

## Design Decisions & Trade-offs

| Decision | Rationale |
|---|---|
| **JSON as source of truth** (not YAML/MD) | Machine-readable, schema-validatable, diffable in git |
| **Core has no fs/network deps** | Reusable across CLI/MCP/extension without coupling |
| **TOON schema format for AI** | More token-efficient than JSON schema for LLM consumption |
| **Radix UI for dialogs** | ARIA compliance, focus management, z-index control out of the box |
| **Dual license** (AGPL extension + MIT libs) | Protects the extension itself while enabling library ecosystem |
| **Changesets over semantic-release** | Finer control per-package, better monorepo support after evaluation |
| **Agent-agnostic export** | Same workflow → 8 agent formats; avoids vendor lock-in |

---

## Comparison with Similar Tools

| Aspect | CC Workflow Studio | [[n8n]] | [[langflow]] | [[ruflo]] |
|---|---|---|---|---|
| Focus | AI coding agent workflows | General automation | LLM chain builder | Multi-agent orchestration |
| Interface | VSCode canvas + CLI + MCP | Web UI | Web UI | Web UI + MCP |
| Agent Support | 8 coding agents | 400+ integrations | LangChain ecosystem | 100+ agents, 300+ MCP tools |
| Runtime | Export → run in agent | Self-hosted execution | Self-hosted execution | Platform runtime |
| License | AGPL + MIT | Fair-code | MIT | Proprietary + OSS |

---

## See Also

- [[claude-code-workflow]] — Claude Code workflow patterns and conventions
- [[mcp-server-patterns]] — MCP server design patterns used in this project
- [[ecc]] — ECC superpowers system (197K⭐), a consumer of cc-wf-studio workflows
- [[ruflo]] — 48.9K⭐ multi-agent orchestration platform for comparison
- [[n8n]] — General workflow automation for comparison
- [[context-mode]] — Context-mode MCP plugin, related MCP tooling patterns
