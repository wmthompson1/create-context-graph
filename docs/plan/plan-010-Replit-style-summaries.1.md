
------------------------------
System Topology: This platform utilizes a deterministic orchestrator-agent network using an advanced ReAct (Reasoning and Action) design pattern. Instead of relying on a single monolith model, the engine splits execution boundaries into a multi-agent system comprising a Supervising Manager, Specialized Editors, and automated Execution Verifiers.

       [USER / WORKSPACE TRIGGER]
                   │
                   ▼
         ┌───────────────────┐
         │ Supervisor Agent  │◄─── [Context-Efficient Skills]
         └─────────┬─────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌─────────────────┐ ┌─────────────────┐
│ Editor Agent A  │ │ Editor Agent B  │◄─── [Stateful MCP Servers]
└────────┬────────┘ └────────┬────────┘
         │                   │
         └─────────┬─────────┘
                   ▼
         ┌───────────────────┐
         │  Verifier Agent   │───(Fails Test)───► [Auto-Rollback]
         └─────────┬─────────┘
                   │ (Passes Test)
                   ▼
        [DETERMINISTIC DEPLOY]


* 
* State Coordination: Execution state is managed via directed acyclic graphs (DAGs) powered by [LangGraph](https://www.langchain.com/breakoutagents/replit), providing deterministic multi-turn loops.
* Context Layering: Universal rules are processed through global system prompt configs, while domain-specific execution guidelines are fetched dynamically from markdown files located in .agents/skills/.
* Tool Binding System: Low-overhead execution relies on tight system primitives (filesystem manipulation, terminal bash invocation, and sandboxed python runners). Heavy external connections are handled via remote standard [Model Context Protocol (MCP)](https://docs.replit.com/learn/agent-skills) servers.
* 

------------------------------
This task summary tracks the lifecycle of complex software development workflows within the workspace, modeling state transitions from initialization to validation.

| Task ID | Phase / Scope | Target System Component | Dependencies | Required Agent Skills & Tools | Verification Mechanism | Status |
|---|---|---|---|---|---|---|
| TS-001 | PLANNING | Workspace Topology & Dependency Tree | None | directory_analyzer, package_resolver | Structural JSON schema validation | Completed |
| TS-002 | SCAFFOLD | Config Layer & Environment Injection | TS-001 | fs_write_file, .agents/skills/setup | Validation script parse check | Completed |
| TS-003 | ENGINEERING | Multi-Agent Workspace Routing Core | TS-002 | editor_agent_v4, mcp_router | Multi-turn compilation sanity test | Active |
| TS-004 | ENGINEERING | Declarative Skill Registry Engine | TS-003 | skill_compiler, .agents/skills/* | Custom instruction match verification | Pending |
| TS-005 | VERIFICATION | Asynchronous Automated Testing Suite | TS-004 | bash_executor, pytest_runner | Coverage target metric evaluation | Pending |
| TS-006 | DEPLOYMENT | Production Build & Infrastructure Sync | TS-005 | deploy_agent, cloud_sync_mcp | Live HTTP probe & health check | Pending |

------------------------------
Below is the concrete software design implementation for building an enterprise-grade agent engine capable of consuming declarative skills and updating the workspace workspace.

import osimport jsonimport refrom typing import Dict, List, Any, Optional
class WorkspaceContextManager:
    """Manages context-efficient skills injection and configuration file trees."""
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.skills_dir = os.path.join(workspace_root, ".agents", "skills")
        self.global_config_path = os.path.join(workspace_root, ".agents", "config.json")
        self._ensure_structures_exist()

    def _ensure_structures_exist(self):
        os.makedirs(self.skills_dir, exist_ok=True)
        if not os.path.exists(self.global_config_path):
            default_config = {
                "engine_mode": "Auto",
                "max_iterations": 25,
                "allowed_tools": ["fs_read", "fs_write", "bash_execute", "mcp_call"],
                "security_audit_enabled": True
            }
            with open(self.global_config_path, 'w') as f:
                json.dump(default_config, f, indent=2)

    def load_declarative_skills(self) -> str:
        """Aggregates active .md skills into the model's core instruction context."""
        aggregated_skills = []
        for file in os.listdir(self.skills_dir):
            if file.endswith(".md"):
                with open(os.path.join(self.skills_dir, file), 'r') as f:
                    skill_content = f.read()
                    # Sanitize to prevent malicious prompt injection hidden within files
                    if "IGNORE SYSTEM INSTRUCTIONS" in skill_content.upper():
                        continue
                    aggregated_skills.append(f"### Skill Reference: {file}\n{skill_content}")
        return "\n\n".join(aggregated_skills)
class ReActAgentEngine:
    """Core reasoning engine processing multi-turn execution loops with XML boundaries."""
    def __init__(self, context_mgr: WorkspaceContextManager, llm_client: Any):
        self.context_mgr = context_mgr
        self.llm = llm_client
        self.system_base = (
            "You operate inside a software workspace. Use the following XML tags to execute actions:\n"
            "<thought> Your internal reasoning, planning, and tool choices </thought>\n"
            "<call_tool name=\"TOOL_NAME\"> {\"arg\": \"value\"} </call_tool>\n"
            "Always review validation feedback before resolving a task."
        )

    def construct_dynamic_prompt(self, user_intent: str, task_summary_state: str) -> str:
        active_skills = self.context_mgr.load_declarative_skills()
        return f"""{self.system_base}

=== SYSTEM ACTIVE SKILLS ==={active_skills}

=== CURRENT WORKSPACE TASK SUMMARY STATE ==={task_summary_state}

=== USER TARGET INTENT ==={user_intent}"""

    def parse_agent_response(self, raw_output: str) -> Dict[str, Any]:
        thought_match = re.search(r"<thought>(.*?)</thought>", raw_output, re.DOTALL)
        tool_match = re.search(r"<call_tool name=\"(.*?)\">(.*?)</call_tool>", raw_output, re.DOTALL)
        
        return {
            "thought": thought_match.group(1).strip() if thought_match else "",
            "tool_name": tool_match.group(1).strip() if tool_match else None,
            "tool_args": json.loads(tool_match.group(2).strip()) if tool_match else {}
        }

------------------------------
These reference files illustrate how to explicitly register proactive patterns and reactive fixes into an agent's memory framework.
## Example 1: Proactive Architecture Guide for Production Web Environments
File Path: .agents/skills/proactive_fastapi_patterns.md

# Skill: Production-Grade FastAPI Implementation Pattern## Intent ContextApply these directives whenever constructing, refactoring, or updating FastAPI backend modules to ensure enterprise-grade scaling, error trapping, and performance metrics.
## Engineering Rules1. **Asynchronous Handlers:** Always define endpoint route entry points using `async def` if the layer directly accesses an external database or networking resource.
2. **Dependency Injection Configuration:** Leverage `fastapi.Depends` explicitly for handling database session lifecycles.3. **Structured Validation Schema Rules:** Ensure every operational inbound request map directly matches a Pydantic V2 BaseModel blueprint.
## Happy Path Execution Blueprint```python
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

class UserCreationPayload(BaseModel):
    email: EmailStr
    account_tier: str

# Execute step-by-step structural isolation
async def get_database_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

## Example 2: Reactive Bug Patch and Anti-Recurrence Directive
File Path: .agents/skills/reactive_cors_patch.md

# Skill: Automated CORS Configuration Overrides## Historical Bug ContextEncountered frequent application crashes because wildcard stars (`"*"`) were combined with `allow_credentials=True` configurations across non-production branches.
## Directives1. **Explicit Origins:** When `allow_credentials` is set to `True`, the `allow_origins` parameter *must* use a whitelist matrix instead of `["*"]`.2. **Dynamic Fallbacks:** Fall back to localhost variants exclusively during local execution testing.
## Enforcement Script Pattern```python
# Rule Override Assertion
if middleware_args.get("allow_credentials") and "*" in middleware_args.get("allow_origins", []):
    raise ValueError("Security Boundary Exception: Star origins disallowed with credential sharing.")
```

------------------------------
To ensure long-running task autonomy remains accurate and safe, the platform utilizes strict runtime guardrails.

* 
* Human-In-The-Loop (HITL) Intercept Gateways: While minor modifications execute autonomously, destructive mutations (like running a clean database purge or provisioning costly cloud assets) halt the process, prompting a visual validation check.
* Asynchronous Parallel Iteration Limits: To prevent infinite execution loops from consuming excessive api credits, the orchestrator tracks total turns. If a task spends more than 5 consecutive loops on the same codebase issue without shifting its approach, execution halts and alerts the developer.
* Security Isolation Verification: The workspace agent cross-checks every markdown file inside the .agents/skills/ folder using a regex scanner. This blocks malicious prompt injection attempts that try to hijack system commands or leak environment secrets.
* 

To tailor this workspace configuration to your project needs, please let me know:

* 
* What programming languages or frameworks is your application using? (e.g., Python/FastAPI, TypeScript/Next.js)
* Which external APIs or services will your agent need access to? (e.g., databases, GitHub, cloud providers)
* Do you want to build a single-agent loop or a multi-agent orchestration network?
* 

---
A: Python/FastAPI
A: Context Graph
A: multi-agent orchestration network?


