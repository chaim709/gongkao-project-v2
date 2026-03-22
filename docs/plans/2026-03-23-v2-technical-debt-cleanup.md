# V2 Technical Debt Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the highest-risk technical debt blocking stable V2 iteration: frontend Ant Design runtime warnings, active-page deprecated APIs, and backend migration/bootstrap inconsistency.

**Architecture:** Frontend debt is handled by introducing a single Ant Design app bridge for message/modal access and then replacing static calls in active code paths first. Backend debt is handled by stopping implicit schema creation on every boot and moving runtime bootstrap toward explicit, idempotent migration/init scripts.

**Tech Stack:** React 19, Ant Design 6, Zustand, FastAPI, SQLAlchemy 2.0, Alembic, Docker Compose

---

### Task 1: Frontend App Context Bridge

**Files:**
- Create: `frontend/src/lib/antdApp.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend` build + browser smoke for `/login`, `/settings`, `/shiye-positions`

**Step 1: Write the bridge component**
Create a provider that mounts `<App>` from `antd`, captures `message`, `modal`, and `notification` instances via `App.useApp()`, and exports safe helpers.

**Step 2: Wrap the application tree**
Mount the bridge once near the root so all dynamic theme/context consumers resolve through it.

**Step 3: Replace static calls in active paths**
Update current hot paths first: `Login.tsx`, `SettingsPage.tsx`, `ShiyePositionList.tsx`, `api/client.ts`.

**Step 4: Build and smoke test**
Run `npm run build` and load key routes to verify the warning disappears from the active flow.

### Task 2: Remove Active Frontend Deprecated Usage

**Files:**
- Modify: `frontend/src/pages/settings/SettingsPage.tsx`
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`
- Test: `npm run build`

**Step 1: Remove `InputNumber addonAfter`**
Replace with `Space.Compact` or adjacent suffix text for the active settings page.

**Step 2: Remove `Drawer width` deprecation in active page**
Switch the事业编详情抽屉 to supported API.

**Step 3: Remove fake/local settings block**
Either clearly isolate it as placeholder or remove the local-only save path from the active settings page.

**Step 4: Rebuild and smoke test**
Verify `/settings` and `/shiye-positions` still behave correctly.

### Task 3: Backend Migration / Bootstrap Debt

**Files:**
- Modify: `backend/start.sh`
- Modify: `backend/alembic/env.py`
- Modify: `docker-compose.yml` or deployment bootstrap if needed
- Create: `backend/scripts/bootstrap_db.py` or equivalent idempotent script
- Test: backend container boot + `/health` + settings API

**Step 1: Stop unconditional `Base.metadata.create_all` on every boot**
That masks missing migrations and diverges from Alembic-managed schema.

**Step 2: Introduce explicit bootstrap path**
Create an idempotent bootstrap script for local/dev emergency init, separate from normal app startup.

**Step 3: Keep runtime startup minimal**
Startup should run the app, not mutate schema unexpectedly.

**Step 4: Validate on current container flow**
Confirm container boots and `/api/v1/settings/shiye-tier-thresholds` still works.

### Task 4: Migration State Documentation

**Files:**
- Modify: `docs/DEPLOYMENT_GUIDE.md`
- Modify: `manual_sync_guide.md` or deployment docs in active use

**Step 1: Document current migration truth**
Describe how Alembic should be applied and how to bootstrap an old DB safely.

**Step 2: Document frontend sync truth**
Clarify when to use local Vite vs container dist sync.

**Step 3: Add rollback notes**
Document minimal recovery path for bad deploys.
