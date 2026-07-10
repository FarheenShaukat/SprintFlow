SPRINTFLOW AI — FULL IMPLEMENTATION PLAN (A to Z)
====================================================
Chat-based, per-project AI agent for SprintFlow

------------------------------------------------------
0. CHANGELOG — WHAT CHANGED FROM THE ORIGINAL SPRINT PLAN
------------------------------------------------------

The original document (AI Project Planner Feature Sprint Plan) was
a form-based wizard: Input Panel → Preview Panel → Apply Panel,
generic "Planner" naming, workspace-scoped, one-shot generation
with a separate /regenerate endpoint. Everything below is what was
changed and why, in the order the changes were made:

1) FORM UI → CHAT UI
   Was: Input/Preview/Apply panels on a static page.
   Now: A conversational chat interface. Editing a plan is done by
   describing changes in plain language ("make sprint 2 shorter")
   instead of clicking into form fields — much lower friction,
   works better on mobile, no separate editable-table UI to build.

2) FIXED PIPELINE → TOOL-CALLING AGENT
   Was: A strict linear LangGraph DAG (summarize → product_plan →
   technical_plan → sprint_plan → validate → repair).
   Now: A ReAct-style agent loop with an `agent_node` that decides
   what to do next (read context, draft, revise, write) based on
   conversation history. Fixed pipelines don't handle a user
   interrupting mid-plan well; an agent loop does. DB-mutating
   tools are still gated behind LangGraph interrupt() for approval,
   same safety property as before, just not forced into one rigid
   sequence.

3) GENERIC "PLANNER" NAMING → "SPRINTFLOW AI" NAMING
   Was: PlannerRequest, GeneratedPlan, /planner/ endpoints, generic
   branding.
   Now: SprintFlowConversation, SprintFlowMessage, /sprintflow-ai/
   endpoints — named specifically after the product, since this is
   built for SprintFlow, not a generic reusable planner.

4) ONE-SHOT REQUEST → PERSISTENT PER-PROJECT CONTEXT
   Was: A planner request was a single job: submit → generate →
   apply → done.
   Now: The bot holds a live, evolving understanding of one
   specific project — including sprints/tasks the user created
   manually, not just what the AI generated. load_project_context_
   tool re-pulls the current DB state at the start of every turn,
   so "make a plan again" means "replan relative to what actually
   exists now," not "regenerate from zero."

5) DROPDOWN PROJECT SELECTOR IN THE CHAT HEADER
   Added: The chat header shows "SprintFlow AI · [Project ▾]".
   Switching the dropdown swaps the bot's entire context to that
   project. This makes it unambiguous which project the user is
   talking about — no more guessing from conversation text.

6) "+ NEW PROJECT" OPTION + NAME RESOLUTION RULE
   Added: The dropdown includes a "+ New Project" entry for
   starting a brand-new project from scratch (conversation.project
   = null until applied). Naming rule: the project name is derived
   from the generated plan by default, but any name the user
   explicitly states in chat always overrides the derived one.

7) ONE SHARED CHAT PER PROJECT → ONE PRIVATE CHAT PER (PROJECT, USER)
   Was (briefly): a single shared conversation thread per project,
   visible to the whole team.
   Now: Each user gets their own private conversation thread per
   project (unique constraint on (project, user)). Reason: a
   single shared thread causes message interleaving between users
   chatting at the same time, and creates approval ambiguity (who
   is allowed to click Approve on someone else's draft plan?). The
   underlying project DATA is still fully shared — only the chat
   thread itself is private per user.

8) ACCESS RESTRICTED TO ADMIN ROLE ONLY
   Added: Only users with an admin role can access SprintFlow AI
   at all. Regular members never see the chat entry point and get
   a 403 if they call the API directly. This didn't change the
   (project, user) data model from point 7 — a workspace can still
   have multiple admins, each still gets their own private thread —
   it just narrows who is eligible to have one.

9) BOTH FRONTEND HIDE AND BACKEND 403 KEPT TOGETHER
   Clarified: hiding the button is UX (prevents member confusion);
   the backend 403 is the actual security enforcement (prevents a
   member from calling the API directly, bypassing the UI). Both
   are required together — hiding the button alone is not real
   access control.

Everything from here down is the current, up-to-date plan
reflecting all of the above.

------------------------------------------------------
1. CONCEPT
------------------------------------------------------

Appearance: a chatbot named "SprintFlow AI".
Behavior: an agent — it reads project data, plans sprints/tasks,
writes to the database, and holds a live, evolving understanding
of one specific project.

Core rule: ONE PERSISTENT CHAT PER (PROJECT, USER).
The chat is not a one-off "generate a plan" tool, and it is NOT a
single shared team channel either. Each team member gets their own
private conversation thread with SprintFlow AI about a given
project — this avoids message interleaving between multiple users
talking to the bot at once, and avoids approval ambiguity (a user
should only ever approve their own draft plan, never one another
teammate is mid-conversation with).

What IS shared across users: the underlying project data. The
bot's context (§5) always pulls the current live Sprint/Task/
SubTask rows regardless of whose private chat is asking. So if
Alice creates Sprint 3 manually, and Bob opens his own separate
chat later, Bob's bot instance still knows about Sprint 3 — the
CHAT is personal, the PROJECT TRUTH is not. When anyone approves a
plan in their own chat, the resulting writes land in the same
shared tables everyone sees on the project board.

The project selected (via a dropdown in the chat header) decides
what the bot knows and can act on at that moment. Switching the
dropdown = switching the bot's entire context to a different
project's chat thread.

------------------------------------------------------
2. UI / UX
------------------------------------------------------

2.1 Chat Header
- Shows: "SprintFlow AI" + a PROJECT DROPDOWN (not free text).
  Example: "SprintFlow AI  ·  [ MediEase v ]"
- Dropdown lists all projects in the current workspace the user
  has access to, PLUS a fixed option at the top/bottom:
  "+ New Project". Selecting an existing project:
    a) switches to that project's persistent chat thread
    b) triggers a context reload (see 4.3) so the bot's next
       reply reflects that project's CURRENT live state
- If the user opens the assistant directly from a project board
  page, the dropdown pre-selects that project automatically.

2.1.1 Selecting "+ New Project"
- Opens a fresh, unscoped chat thread (conversation.project = null,
  see 4.4). Dropdown label temporarily reads "+ New Project" until
  a project is actually created.
- Naming rule:
    - By default, the project name is DERIVED from the generated
      plan itself (draft_plan.project.name, produced by
      draft_plan_tool from whatever the user pasted/uploaded/
      described) — the user doesn't have to name it up front.
    - If the user explicitly states a name at any point in the
      conversation ("call it MediEase Sprint 2", "name the project
      Inventory Tool"), that stated name always overrides the
      derived one. Explicit user naming wins over inferred naming,
      whether said before, during, or after plan drafting.
    - The name shown on the plan_card before approval reflects
      whichever name currently applies (derived or user-overridden),
      so the user can correct it in chat before creating anything.
- On approval, create_project_tool creates the Project using this
  resolved name, then the dropdown updates in place: "+ New Project"
  is replaced by the new project's real name, and this conversation
  becomes that project's permanent chat (see 4.4).
- A small context strip under the header shows a live snapshot,
  e.g.: "4 sprints · 22 tasks · 3 overdue" — pulled fresh on load,
  not cached from the last AI-generated plan.

2.2 Chat Body
- Standard chat bubbles (user / SprintFlow AI).
- Assistant messages can be one of several types:
    - text            → plain reply
    - progress         → "Reading your document…", "Checking
                          existing sprints…", "Drafting Sprint 3…"
    - plan_card        → structured, editable sprint/task
                          preview with Approve / Edit / Regenerate
                          buttons
    - confirmation     → result after a DB write, e.g.
                          "Created 3 sprints, 14 tasks. Open board →"
    - context_summary  → optional card showing what the bot
                          currently sees for the project (sprints,
                          tasks, statuses) — useful the first time
                          a user opens the chat, or after "what do
                          you know about this project?"

2.3 Composer
- Textarea + file attach button (PDF, DOCX, TXT, MD) in one bar,
  like any normal chat app. No separate "form" page.

2.4 Editing model
- Primary edit path: natural language ("make sprint 2 shorter",
  "merge tasks 3 and 4", "this should be high priority").
- Secondary (later, optional): lightweight inline edit on the
  plan_card itself for small tweaks (title typo, estimate number)
  without round-tripping through the LLM. Keep plan_card payload
  structured JSON from day one so this can be added later without
  a data model change.

------------------------------------------------------
3. NAMING (project-specific, not generic)
------------------------------------------------------

Use "SprintFlow AI" consistently instead of generic "planner":

- Django app:        backend/apps/sprintflow_ai/
- Models:             SprintFlowConversation, SprintFlowMessage,
                       GeneratedPlan
- Graph module:       backend/apps/sprintflow_ai/graph.py
- Endpoint prefix:    /api/projects/{project_id}/sprintflow-ai/
- Frontend route:     frontend/app/workspace/[id]/sprintflow-ai/page.tsx
  (or embedded panel on the project board, see 8.5)

------------------------------------------------------
3.1 ACCESS CONTROL — ADMIN ONLY
------------------------------------------------------

Only workspace/project ADMINS can access SprintFlow AI. Regular
members do not see or use the agent at all — they just work on
sprints/tasks normally on the board. Rationale: planning/replanning
a project is an admin decision; members shouldn't need (or be able
to) regenerate sprints via chat.

This does NOT collapse back to "one shared chat per project" —
a workspace can have more than one admin, and each admin should
still get their OWN private thread with the bot (same reasoning as
before: avoids interleaved messages and unclear approval ownership
if two admins use it at the same time). So the data model stays
(project, user) — the change is purely a permission gate on top of
it, restricting eligible users to those with the admin role.

Enforcement points:
- Backend: every SprintFlow AI endpoint (see §7) checks
  request.user has an admin role on the project's workspace before
  allowing access; non-admins get 403.
- Frontend: the "SprintFlow AI" nav button / project-dropdown entry
  point is only rendered for users with an admin role. Members
  never see it in the UI at all — not just blocked after clicking.
- If a user's role changes (promoted to admin, or demoted from
  admin), their existing conversation row (if any) is preserved but
  access is re-checked on every request — a demoted admin loses
  access immediately, a newly promoted admin gets a fresh
  conversation created lazily on first open.

------------------------------------------------------
4. DATA MODEL
------------------------------------------------------

4.1 SprintFlowConversation
One row per (project, user) pair — a private thread between one
user and the bot, scoped to one project. NOT one row per project
shared across the whole team (see rationale in §1).

Fields:
- workspace              FK
- project                FK, nullable (null only during the very
                          first exchange before a project exists —
                          see 4.4)
- user                   FK — owner of this private thread
- thread_id               string — LangGraph checkpoint thread key
- status                  active | archived
- last_context_synced_at  datetime — last time live project data
                          was pulled into the bot's working context
- created_at / updated_at

Constraint: unique(project, user) when project is not null —
enforces "one private chat per project per user." Different users
on the same project each get their own conversation row and their
own thread_id, but load_project_context_tool reads the same shared
Sprint/Task/SubTask data for all of them.

4.2 SprintFlowMessage
- conversation            FK
- role                    user | assistant
- message_type            text | progress | plan_card |
                          confirmation | context_summary
- content                 text (for text/progress)
- payload                 JSON (for plan_card / confirmation /
                          context_summary — structured data the
                          frontend renders as a card)
- created_at

4.3 GeneratedPlan (draft plan under discussion, not yet applied)
- conversation            FK
- plan_json               JSON — current draft (project meta,
                          sprints, tasks, subtasks, dependencies)
- validation_errors       JSON list
- status                  drafting | ready_for_approval | applied
- created_at / updated_at

4.4 Handling "no project yet"
- If user opens SprintFlow AI with no project selected (dropdown
  set to "+ New Project"), conversation.project = null.
- draft_plan.project.name is set by draft_plan_tool from the
  planning content by default. If the user explicitly names the
  project in chat at any point, that name is stored separately as
  draft_plan.user_specified_name and takes priority over the
  derived name whenever create_project_tool resolves the final
  name to use.
- Once the user approves a first plan and apply_plan_tool creates
  the Project row (using the resolved name above), the SAME
  conversation is patched:
  conversation.project = new_project.id
  — so the thread continues, now scoped, for all future messages,
  and the dropdown swaps "+ New Project" for the real project name.

4.5 Existing models reused (read + write targets)
- Workspace, Project, Sprint, Task, SubTask, TaskDependency,
  AIInsight

No duplicate "planning-only" task tables. The bot writes directly
into the same Sprint/Task/SubTask tables the rest of the app uses,
so manually created sprints/tasks are visible to the bot exactly
like AI-created ones — there is no separate source of truth.

------------------------------------------------------
5. CONTEXT LOADING — THE MOST IMPORTANT PART
------------------------------------------------------

The bot must always know the CURRENT real state of the project,
including anything the user built by hand, not just what the AI
previously generated.

5.1 load_project_context_tool (deterministic tool, not LLM)
Runs at the start of every turn (or when the project dropdown
changes). Pulls fresh from the DB:
- project: name, description, goals, deadline, tech stack
- sprints: name, sequence, dates, status, goal
- tasks: title, status, priority, estimate, assignee (if any),
  which sprint, dependency links
- subtasks: title, done/not done, parent task
- counts/summary: total sprints, total tasks, overdue count,
  completion %

5.2 Freshness rule
- Always re-run load_project_context_tool before the agent
  reasons about anything project-specific — never rely solely on
  the LangGraph checkpoint state, since the user (or a teammate)
  may have edited sprints/tasks outside the chat since the last
  message.
- For large projects, summarize (counts + top-level sprint/task
  titles) rather than dumping every row into the prompt; let the
  agent call a follow-up tool (e.g. get_task_details_tool) if it
  needs specifics about one task.

5.3 Manual creation is first-class
- If a user says "I already made Sprint 3 myself, can you fill in
  tasks for it?" — the agent must recognize Sprint 3 from the
  freshly loaded context and add tasks into it via create_task_tool,
  not propose a duplicate sprint.
- "Make a plan again" means: re-run context load, compare against
  current sprints/tasks, and propose changes/additions relative to
  what actually exists now — not regenerate from zero.

------------------------------------------------------
6. BACKEND ARCHITECTURE — AGENT, NOT FIXED PIPELINE
------------------------------------------------------

Use a LangGraph tool-calling agent loop (ReAct-style), not a rigid
linear DAG, since chat is inherently multi-turn and interruptible.

6.1 Files
backend/apps/sprintflow_ai/
  __init__.py
  models.py            (SprintFlowConversation, SprintFlowMessage,
                        GeneratedPlan)
  serializers.py
  views.py
  urls.py
  state.py             (typed graph state)
  graph.py             (agent graph assembly)
  agent_node.py         (central reasoning node)
  tools.py             (all deterministic tools)
  extractors.py         (PDF/DOCX/TXT/MD text extraction)
  llm.py                (LLM client + structured-output schemas)
  checkpoints.py        (LangGraph checkpointer config)
  tests.py

6.2 Typed state (state.py)
class SprintFlowState(TypedDict, total=False):
    conversation_id: int
    project_id: int | None
    workspace_id: int
    user_id: int
    messages: list            # chat history for this turn
    project_context: dict     # freshly loaded sprints/tasks/etc.
    uploaded_text: str
    draft_plan: dict
    validation_errors: list
    pending_write: dict        # queued DB action awaiting approval
    approval_status: str       # none | awaiting | approved | edited
    last_tool_result: dict

6.3 Agent loop
- agent_node: given conversation history + fresh project_context,
  decides the next action — reply in chat, call a read tool, draft
  or revise a plan, or request DB writes.
- Any DB-mutating tool call (create_sprint_tool, create_task_tool,
  create_subtask_tool, create_dependency_tool, update_task_tool,
  delete_task_tool) is gated behind a LangGraph interrupt() — the
  graph pauses, the chat renders a plan_card with Approve / Edit /
  Regenerate, and only resumes the write after explicit approval.
- Small, obviously safe reads (get_task_details_tool,
  load_project_context_tool) do not require approval.

6.4 Tools (tools.py)
Read-only:
  load_project_context_tool
  get_task_details_tool
  get_sprint_details_tool

Extraction:
  extract_plain_text_tool
  extract_pdf_text_tool
  extract_docx_text_tool

Planning (LLM-backed, structured output):
  draft_plan_tool          — produces/updates the working plan
                              JSON given context + user instructions
  validate_plan_tool        — deterministic schema + business rule
                              checks (limits, required fields)
  repair_plan_tool          — fixes invalid draft_plan output

Write (require approval / interrupt):
  create_project_tool
  create_sprint_tool
  create_task_tool
  create_subtask_tool
  create_dependency_tool
  update_task_tool
  log_activity_tool

Utility:
  calculate_sprint_dates_tool
  export_plan_markdown_tool

6.5 Checkpointing
- Use a REAL LangGraph checkpointer (PostgresSaver against the
  existing Postgres DB), keyed by conversation.thread_id — not a
  hand-rolled JSON blob on a model field. This is what makes
  pause-for-approval and resume-after-days-later actually reliable.
- SprintFlowConversation.thread_id is just the pointer into
  LangGraph's own checkpoint storage.

6.6 LLM layer (llm.py)
- langchain-openai with structured output (Pydantic schemas) for:
  draft_plan_tool, repair_plan_tool, and free-form chat replies.
- Provider order:
  1. Groq (`GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL`) as the
     primary OpenAI-compatible planning model.
  2. Deterministic fallback plan generator when Groq is unavailable,
     producing a basic 2-3 sprint plan from raw text so the feature
     still functions end-to-end without a key.

6.7 Validation limits (unchanged from earlier draft, keep these)
  max sprints: 12
  max tasks per sprint: 20
  max subtasks per task: 10
  max total tasks: 150
  normalize priority to: low | medium | high | critical

6.8 Safety
- Uploaded file content is treated strictly as untrusted
  requirements text, never as instructions. System prompt
  explicitly tells the agent to ignore any embedded instructions
  in uploaded files or pasted text that attempt to change its
  behavior, reveal secrets, or bypass approval gating.
- All DB writes happen inside one transaction; partial failures
  roll back completely.

------------------------------------------------------
7. API ENDPOINTS
------------------------------------------------------

GET  /api/workspaces/{workspace_id}/projects/
     — used to populate the chat header's project dropdown

GET  /api/projects/{project_id}/sprintflow-ai/
     — fetch (or lazily create) THE CALLING USER'S conversation for
       this project (scoped by request.user + project_id together),
       return message history + live context_summary

POST /api/projects/{project_id}/sprintflow-ai/messages/
     — send a user message (text and/or file attachment), returns
       the new assistant message(s); triggers async agent run

GET  /api/projects/{project_id}/sprintflow-ai/events/
     — poll (or SSE later) for agent progress: current step,
       plan_card readiness, pending approval, apply result

POST /api/projects/{project_id}/sprintflow-ai/approve/
     — approve current pending_write / draft_plan; resumes the
       LangGraph interrupt and performs DB writes

POST /api/projects/{project_id}/sprintflow-ai/switch-context/
     — optional explicit trigger to force-refresh project_context
       (also auto-runs on dropdown switch / new message)

For the "no project yet" case:
POST /api/workspaces/{workspace_id}/sprintflow-ai/new/
     — starts a conversation with project = null; once a plan is
       approved and applied, the created project id gets attached
       to this same conversation (see 4.4)

------------------------------------------------------
8. FRONTEND
------------------------------------------------------

8.1 Files
frontend/app/workspace/[id]/sprintflow-ai/page.tsx
frontend/components/sprintflow-ai/chat-thread.tsx
frontend/components/sprintflow-ai/chat-header.tsx        (dropdown here)
frontend/components/sprintflow-ai/message-bubble.tsx
frontend/components/sprintflow-ai/plan-card.tsx
frontend/components/sprintflow-ai/progress-bubble.tsx
frontend/components/sprintflow-ai/context-summary-card.tsx
frontend/components/sprintflow-ai/composer.tsx
frontend/lib/api.ts        (add sprintFlowAiApi client)

8.2 chat-header.tsx behavior
- Renders "SprintFlow AI" + <ProjectDropdown> populated from
  GET /workspaces/{id}/projects/
- On change: navigate/re-fetch conversation for the newly selected
  project_id; show a brief "Switching to {project name}…" loading
  state; then render that project's message history +
  context_summary.

8.3 API client shape
export const sprintFlowAiApi = {
  listProjects: (workspaceId) => ...,
  getConversation: (projectId) => ...,
  sendMessage: (projectId, data: FormData) => ...,
  getEvents: (projectId) => ...,
  approve: (projectId, payload) => ...,
};

8.4 Progress states shown in chat (as progress bubbles)
  reading input → checking existing project data →
  drafting plan → validating → waiting for approval → applying →
  done

8.5 Placement
Two reasonable options — pick one for v1:
  a) Standalone page (frontend/app/workspace/[id]/sprintflow-ai/)
     reached via a nav button, OR
  b) A slide-over/side panel launched from the project board
     itself (pre-scoped to that project, dropdown still present
     for switching).
Recommendation: build (a) first — simpler routing — and add (b)
as a shortcut later once the core chat works.

------------------------------------------------------
9. BUILD ORDER (compressed, vertical-slice first)
------------------------------------------------------

Sprint 1 — Skeleton + one working round trip
  - SprintFlowConversation/Message/GeneratedPlan models + migrations
  - Admin-only permission check on all sprintflow-ai endpoints and
    on the frontend entry point (nav button hidden for non-admins)
  - Project dropdown + basic chat UI (text only, no files yet)
  - Agent graph with PostgresSaver checkpointing wired up
  - load_project_context_tool + a plain text-in → fallback plan out
  - Background job execution (Celery/RQ/etc.) from day one —
    do NOT attempt synchronous request/response for agent runs
  - Manual "one conversation per (project, user)" enforced at DB
    level

Sprint 2 — File input
  - extract_plain_text_tool / extract_pdf_text_tool /
    extract_docx_text_tool wired into the agent's toolset
  - File size/type validation, clear error messages

Sprint 3 — Real planning quality
  - draft_plan_tool with structured output via langchain-openai
  - validate_plan_tool + repair_plan_tool loop
  - Respect settings: sprint length, deadline, team size, tech stack

Sprint 4 — Approval + apply (the agentic write path)
  - interrupt() before any create/update tool
  - plan_card UI with Approve / Edit / Regenerate
  - create_sprint_tool / create_task_tool / create_subtask_tool /
    create_dependency_tool, all transactional
  - Prevent duplicate apply; log activity

Sprint 5 — "Already has data" handling
  - Context loading proven against projects with manually created
    sprints/tasks (not just AI-created ones)
  - "Make a plan again" correctly diffs against current state
    instead of regenerating from scratch
  - context_summary_card on chat open

Sprint 6 — Polish & safety
  - Rate limiting per user/project
  - Prompt-injection guardrails on uploaded content
  - Export plan as Markdown / copy action
  - Tests: permissions, extraction, agent routing, approval/apply,
    duplicate-project-conversation constraint
  - Docs: API.md, ARCHITECTURE.md, README env vars (OPENAI + Groq)

------------------------------------------------------
10. RISKS AND MITIGATIONS
------------------------------------------------------

Risk: Bot context goes stale if user edits sprints/tasks outside
      chat.
Mitigation: always re-run load_project_context_tool at the start
      of each turn; never trust only the LangGraph checkpoint for
      "current" project state.

Risk: LLM returns invalid/malformed plan JSON.
Mitigation: validate_plan_tool + repair_plan_tool loop, retry
      limit, deterministic fallback.

Risk: Agent creates duplicate sprints/tasks that already exist
      manually.
Mitigation: context load happens BEFORE planning; agent prompt
      explicitly instructed to check existing sprints/tasks first
      and prefer updating/adding over duplicating.

Risk: DB writes happen without user consent.
Mitigation: every write tool gated behind interrupt(); resumed
      only on explicit approval.

Risk: Partial project creation on failure.
Mitigation: all writes inside one DB transaction per apply.

Risk: Prompt injection via uploaded files.
Mitigation: uploaded content always treated as untrusted data, not
      instructions; explicit system prompt rule.

Risk: Long agent runs blocking HTTP requests.
Mitigation: background job execution + polling/SSE events endpoint
      from Sprint 1, not deferred to later.

------------------------------------------------------
11. DEFINITION OF DONE
------------------------------------------------------

- Only users with an admin role can access SprintFlow AI at all —
  enforced both in the API (403 for non-admins) and hidden from
  the UI for regular members.
- Each project has a private SprintFlow AI chat per ADMIN (one
  conversation per project+admin-user, not one shared thread, and
  not accessible to non-admin members).
- Chat header lets user switch projects via dropdown; switching
  reloads full live context for that project — context is shared
  across all users' chats even though the threads themselves are
  private.
- Bot's knowledge includes both AI-generated AND manually created
  sprints/tasks — no blind spots — regardless of which teammate's
  chat is asking.
- User can paste text or upload PDF/DOCX/TXT/MD in the chat.
- Bot proposes plans as chat plan_cards; user edits via natural
  language; nothing is written to the DB until approved.
- Approved plans create real Sprint/Task/SubTask/Dependency rows,
  transactionally, without duplicating existing items.
- "Make a plan again" re-evaluates against current project state,
  not from a blank slate.
- Background execution + progress polling in place from the start.
- Tests cover: one-conversation-per-(project,user) constraint,
  context freshness, approval gating, duplicate-apply prevention.
