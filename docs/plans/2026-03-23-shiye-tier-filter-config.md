# Shiye Tier Filter And Threshold Config Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add frontend filtering for `冲刺 / 稳妥 / 保底` and make事业编 recommendation thresholds configurable.

**Architecture:** Keep tier computation in `ShiyeSelectionService` as the single source of truth. Read threshold configuration from a backend settings source, expose it through the existing settings/admin flow, and let the frontend only consume/filter returned tiers.

**Tech Stack:** FastAPI, SQLAlchemy, React, Ant Design, pytest

---

### Task 1: Inspect existing settings and selection flow

**Files:**
- Modify: `backend/app/services/selection/shiye_selection_service.py`
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`
- Inspect: `backend/app/routes/*.py`
- Inspect: `backend/app/models/*.py`

**Step 1:** Identify reusable settings/config storage.
**Step 2:** Identify where事业编分层 is computed.
**Step 3:** Identify where事业编页面 holds selection-mode filters.

### Task 2: Add failing tests for configurable thresholds

**Files:**
- Test: `backend/tests/unit/test_shiye_selection_service.py`

**Step 1:** Add a test proving custom thresholds change `recommendation_tier`.
**Step 2:** Add a test proving summary counts still add up under custom config.

### Task 3: Implement backend threshold config loading

**Files:**
- Create or modify backend settings service/model files after inspection
- Modify: `backend/app/services/selection/shiye_selection_service.py`

**Step 1:** Define threshold keys and defaults.
**Step 2:** Load configured thresholds before tier annotation.
**Step 3:** Use configured thresholds instead of hardcoded percentile cutoffs / weights.

### Task 4: Expose threshold config for admin maintenance

**Files:**
- Modify backend settings route/schema files after inspection
- Modify frontend settings/admin page files after inspection

**Step 1:** Add read/update API for事业编 tier thresholds.
**Step 2:** Add admin form fields with validation and save action.

### Task 5: Add事业编 tier filter in page

**Files:**
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`
- Modify if needed: `frontend/src/types/position.ts`

**Step 1:** Add local state for selected tier filters.
**Step 2:** Filter current data source by `recommendation_tier` in selection mode.
**Step 3:** Reflect filtered total in table/pagination without mutating backend ordering.

### Task 6: Verify end to end

**Files:**
- Validate live app and API

**Step 1:** Run backend unit tests.
**Step 2:** Run frontend build.
**Step 3:** Verify筛选器 and threshold updates affect returned tiers.
