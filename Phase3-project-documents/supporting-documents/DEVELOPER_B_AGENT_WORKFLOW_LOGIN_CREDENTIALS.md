# Developer B: Add Login Credentials and Gmail Credentials to Agent Workflow Page

**Purpose:** Handoff so Developer B (or Cursor AI agent) can implement credentials on the Agent Workflow page and start development immediately.

**Backend status:** ✅ Already done. `POST /api/v2/generate-tests` accepts both `login_credentials` and `gmail_credentials`. No backend changes required.

---

## Task Summary

Add **two credential sections** to the Agent Workflow form:

1. **Login credentials (website)** — **Required for workable test cases.** Email + password for the **target website**. When provided, generated test steps include these values in the step text (e.g. `Input 'user@example.com' into email field`), so the test is executable like Phase 2 test cases. Users should fill these whenever the flow involves website login.

2. **Gmail credentials (for OTP)** — **Optional; only when the flow uses OTP.** Email + password for **Gmail**. When the site sends an OTP or verification email, the agent can log into Gmail to retrieve the code. Send `gmail_credentials` only when the user needs OTP login; otherwise omit.

---

## 1. Where to Change

| Item | Path / detail |
|------|----------------|
| **Form component** | `frontend/src/features/agent-workflow/components/AgentWorkflowTrigger.tsx` |
| **Request type** | `frontend/src/types/agentWorkflow.types.ts` — `GenerateTestsRequest` already has `login_credentials` and `gmail_credentials` |
| **API** | `POST /api/v2/generate-tests` — request body already supports both. No API changes. |

---

## 2. Contract (Backend Expects)

**Login credentials (website)** — include when user fills both email and password:

```ts
login_credentials?: {
  email?: string;    // preferred
  username?: string; // alternative (backend accepts either)
  password: string;
}
```

**Gmail credentials (for OTP)** — include only when user fills both Gmail email and Gmail password (for flows that use OTP/email verification):

```ts
gmail_credentials?: {
  email: string;
  password: string;
}
```

- **Login credentials:** If the user fills website email and website password → send `login_credentials`. If either is empty → omit.
- **Gmail credentials:** If the user fills Gmail email and Gmail password → send `gmail_credentials`. If either is empty → omit. Use only when the flow requires OTP retrieval from Gmail.

---

## 3. UI Requirements

**Section 1 — Login credentials (website)**  
- **Label:** e.g. "Login credentials (website)" with hint: "Required for flows that need login. Used to generate steps with real email/password (same as Phase 2)."
- **Fields:**
  - **Login email** — single-line input, placeholder e.g. `e.g. user@example.com`
  - **Password** — single-line input, `type="password"`, placeholder e.g. `Website password`
- **Behavior:** Optional in the form. When both are filled → send `login_credentials: { email, password }`. When either empty → omit `login_credentials`.

**Section 2 — Gmail credentials (for OTP)**  
- **Label:** e.g. "Gmail credentials (for OTP)" with hint: "Only if the flow uses OTP or email verification and the agent should retrieve the code from Gmail."
- **Fields:**
  - **Gmail email** — single-line input, placeholder e.g. `e.g. user@gmail.com`
  - **Gmail password** — single-line input, `type="password"`, placeholder e.g. `Gmail password`
- **Behavior:** Optional. When both are filled → send `gmail_credentials: { email, password }`. When either empty → omit `gmail_credentials`.

**Placement:** After "Instructions (optional)", before "Crawl depth". Order: Login credentials (website) first, then Gmail credentials (for OTP).

**Security:** Use `type="password"` for all password fields. Do not persist credentials (form state only).

---

## 4. Implementation Checklist

- [x] Add state: `loginEmail`, `loginPassword`, `gmailEmail`, `gmailPassword` in `AgentWorkflowTrigger.tsx`.
- [x] Add **Login credentials (website):** two inputs (email, password). On submit: if both non-empty → `request.login_credentials = { email: loginEmail.trim(), password: loginPassword }`; else omit.
- [x] Add **Gmail credentials (for OTP):** two inputs (Gmail email, Gmail password). On submit: if both non-empty → `request.gmail_credentials = { email: gmailEmail.trim(), password: gmailPassword }`; else omit.
- [x] Keep existing `url`, `depth`, `user_instruction` behavior.
- [x] Add/update unit tests: request includes `login_credentials` when website email+password filled; includes `gmail_credentials` when Gmail email+password filled; omits each when the corresponding fields are empty.

---

## ✅ COMPLETED — Implementation Summary (Developer B)

**Branch:** `feature/credentials-agent-workflow`  
**Merged to:** `origin/main`  
**Commit:** Fast-forward merge, 230 insertions (+91 lines component, +139 lines tests)

### What was implemented:

**Component** (`AgentWorkflowTrigger.tsx`):
- Added 4 state variables: `loginEmail`, `loginPassword`, `gmailEmail`, `gmailPassword`
- **Login credentials section** (fieldset after Instructions):
  - Legend: "Login credentials (website, optional)"
  - Hint: "Required for flows that need login. Used to generate steps with real email/password (same as Phase 2)."
  - Two inputs: "Login email" (text, placeholder `e.g. user@example.com`) and "Password" (`type="password"`)
  - Sends `login_credentials: { email, password }` only when both fields non-empty; email trimmed
- **Gmail credentials section** (fieldset after Login credentials, before Crawl depth):
  - Legend: "Gmail credentials (for OTP, optional)"
  - Hint: "Only if the flow uses OTP or email verification and the agent should retrieve the code from Gmail."
  - Two inputs: "Gmail email" (text, placeholder `e.g. user@gmail.com`) and "Gmail password" (`type="password"`)
  - Sends `gmail_credentials: { email, password }` only when both fields non-empty; email trimmed
- All password fields use `type="password"`
- All inputs have `data-testid` attributes for testing

**Tests** (`AgentWorkflowTrigger.test.tsx`):
- 9 new test cases covering:
  - Renders login credential fields
  - Includes `login_credentials` when website email + password filled
  - Omits `login_credentials` when email empty
  - Omits `login_credentials` when password empty
  - Renders Gmail credential fields
  - Includes `gmail_credentials` when Gmail email + password filled
  - Omits `gmail_credentials` when Gmail email empty
  - Omits `gmail_credentials` when Gmail password empty
  - Includes both credential blocks when all fields filled
- **All 15 tests pass** (6 existing + 9 new)

---

## 5. Example Requests

**Example 1 — Website login only (no OTP)**  
User fills: URL, Instructions, Login email, Website password. Leaves Gmail fields empty.

```json
{
  "url": "https://www.three.com.hk/postpaid/en",
  "user_instruction": "Subscribe to $288/month plan. Complete flow until payment page.",
  "depth": 2,
  "login_credentials": {
    "email": "pmo.andrewchan+010@gmail.com",
    "password": "<website password>"
  }
}
```
Do **not** send `gmail_credentials`.

**Example 2 — Website login + OTP (Gmail)**  
User fills: URL, Instructions, Login email, Website password, Gmail email, Gmail password.

```json
{
  "url": "https://example.com/signup",
  "user_instruction": "Complete signup with email verification (OTP).",
  "depth": 2,
  "login_credentials": {
    "email": "user@example.com",
    "password": "<website password>"
  },
  "gmail_credentials": {
    "email": "user@gmail.com",
    "password": "<gmail password>"
  }
}
```

---

## 6. TypeScript Type (already defined)

From `frontend/src/types/agentWorkflow.types.ts`:

```ts
export interface GenerateTestsRequest {
  url: string;
  user_instruction?: string;
  depth?: number;
  login_credentials?: { username?: string; email?: string; password: string };
  gmail_credentials?: { email: string; password: string };
}
```

Use `login_credentials` for website login (email + password). Use `gmail_credentials` for Gmail (email + password) when OTP is needed.

---

## 7. One-Line Prompt for Cursor AI Agent

Copy-paste for Cursor so Developer B (or the agent) can start immediately:

```
Add two credential sections to the Agent Workflow form in frontend/src/features/agent-workflow/components/AgentWorkflowTrigger.tsx. (1) Login credentials (website): optional fields "Login email" and "Password" (type="password"). When both filled, send login_credentials: { email, password } in the GenerateTestsRequest. (2) Gmail credentials (for OTP): optional fields "Gmail email" and "Gmail password" (type="password"). When both filled, send gmail_credentials: { email, password }. Omit login_credentials or gmail_credentials when the corresponding fields are empty. Use GenerateTestsRequest from frontend/src/types/agentWorkflow.types.ts. Add unit tests: request includes login_credentials when website email+password filled; includes gmail_credentials when Gmail email+password filled; omits each when empty.
```

---

**Document owner:** Developer A | **Implementation:** Developer B ✅  
**Backend:** No changes required.  
**Frontend:** AgentWorkflowTrigger + tests — ✅ COMPLETE  
**Summary:** Login credentials = must for workable test cases with real values; Gmail credentials = only when the flow uses OTP and the agent should read the code from Gmail.
