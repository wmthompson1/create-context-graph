---
sidebar_position: 6
title: Connect GitHub Copilot
---

# Connect GitHub Copilot via MCP

Generated projects can optionally include an MCP (Model Context Protocol) server configuration that lets GitHub Copilot in VS Code query the same knowledge graph as your web application. Copilot is the interactive MCP client; it is not a model API used by the generated FastAPI application.

## Prerequisites

- Visual Studio Code with GitHub Copilot enabled
- A generated project created with `--with-mcp`
- Backend dependencies installed with `make install-backend`

## 1. Generate the MCP configuration

```bash
create-context-graph manufacturing-graph --domain manufacturing --self-hosted --with-mcp
```

The generated project includes:

- `mcp/vscode_mcp.json` - pre-configured VS Code MCP server definition
- `mcp/README.md` - project-specific setup and tool list

## 2. Configure VS Code

Create or edit `.vscode/mcp.json` in the generated project. Copy the `servers` entry from `mcp/vscode_mcp.json` into it. VS Code prompts for the Neo4j password or NAMS API key when it starts the server, so credentials are not stored in the workspace configuration.

## 3. Start and use the server

Run the server manually to verify its dependencies and graph connection:

```bash
make mcp-server
```

Then start the configured server from VS Code and use GitHub Copilot Chat to discover and invoke its tools. Use read-only graph queries first; introduce write tools only after implementing authorization, auditing, idempotency, and a Cypher allowlist.

## Runtime Model Provider

The generated FastAPI application has a separate runtime agent and model provider. Configuring GitHub Copilot for MCP does not provide a model credential to that application. Configure the in-app provider independently when you enable web-chat agent responses.