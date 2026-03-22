# Shiye Filter Tightening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Tighten the Jiangsu事业编 selection filters into a clearer decision-flow UI with less noise and faster reset/inspection.

**Architecture:** Keep backend semantics unchanged. Refine the frontend selection workbench so the filters read as a decision chain: location scope, post narrowing, risk avoidance, and result layering. Add explicit “active filter” feedback and one-click reset so advisors can iterate faster without guessing hidden state.

**Tech Stack:** React, TypeScript, Ant Design, TanStack Query.

---

### Task 1: Document the frontend filter-tightening scope

**Files:**
- Create: `docs/plans/2026-03-23-shiye-filter-tightening.md`

**Step 1: Write the plan**
- Record the UI-only scope:
  - group selection filters by decision phase
  - add one-click reset for selection filters
  - show active filter summary chips
  - keep existing API contracts unchanged

**Step 2: Save and continue execution**
- Continue in the current session because the user explicitly requested direct implementation.

### Task 2: Rebuild the事业编 selection filter bar into grouped decision sections

**Files:**
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`

**Step 1: Add grouped filter sections**
- Split the existing flat filter bar into labeled groups:
  - `地点范围`
  - `岗位收缩`
  - `风险避雷`
  - `结果分层`

**Step 2: Keep only decision-useful controls in selection mode**
- Keep: `地市 / 区县 / 岗位性质偏好 / 招聘对象限制 / 经费来源限制 / 风险避雷 / 结果层级筛选`
- Preserve browse-mode controls unchanged.

**Step 3: Add minimal layout polish**
- Use compact cards/containers and section labels so the filter row no longer reads as an arbitrary field pile.

### Task 3: Add explicit reset and active-filter feedback

**Files:**
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`

**Step 1: Add one-click reset**
- Add a `清空筛选` action for selection mode.
- Reset only the selection-mode narrowing filters, not the entered student/manual match conditions.

**Step 2: Add active filter summary chips**
- Show currently active narrowing filters as tags below the filter bar.
- Keep the output human-readable, not raw field/value dumps.

**Step 3: Keep pagination behavior correct**
- Reset to page 1 whenever filters are cleared.

### Task 4: Verify and deploy frontend

**Files:**
- Modify: none unless fixes are required

**Step 1: Build frontend**
Run: `cd frontend && npm run build`
Expected: PASS.

**Step 2: Sync assets to nginx container**
Run: `docker cp frontend/dist/. gongkao-guanli-frontend:/usr/share/nginx/html`
Expected: success.

**Step 3: Spot-check built bundle**
- Verify the generated assets contain the new grouped labels and reset action.

### Task 5: Commit

**Files:**
- Modify: frontend files touched above

**Step 1: Commit the refinement**
```bash
git add frontend/src/pages/positions/ShiyePositionList.tsx docs/plans/2026-03-23-shiye-filter-tightening.md
git commit -m "refactor(shiye): tighten selection filter workflow"
```
