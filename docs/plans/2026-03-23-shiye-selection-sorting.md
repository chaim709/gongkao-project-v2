# Jiangsu Shiye Selection Sorting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Jiangsu 事业编智能选岗 default ranking follow `硬匹配 > 岗位性质偏好 > 风险降权 > 竞争比/分数线`.

**Architecture:** Keep ranking logic inside `ShiyeSelectionService` so the frontend remains a thin client. Convert `post_natures` from a hard filter into an ordered preference signal used by the default ranking, while keeping explicit table column sorting available.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, React, Ant Design

---

### Task 1: Lock behavior with tests

**Files:**
- Modify: `backend/tests/unit/test_shiye_selection_service.py`

**Steps:**
1. Add unit coverage for default ranking chain.
2. Add async coverage proving `post_natures` no longer excludes non-preferred results.
3. Run targeted pytest for the new tests.

### Task 2: Implement backend smart ranking

**Files:**
- Modify: `backend/app/services/selection/shiye_selection_service.py`

**Steps:**
1. Replace hard `post_natures` filtering with preference ranking.
2. Add a deterministic default sort key for eligibility, post nature preference, risk score, competition ratio, and interview score.
3. Preserve explicit column sorting, but still keep eligibility priority stable.

### Task 3: Align frontend wording

**Files:**
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`

**Steps:**
1. Change the multi-select placeholder to communicate preference instead of hard filtering.
2. Verify the page still submits the same request shape.

### Task 4: Validate

**Files:**
- Test: `backend/tests/unit/test_shiye_selection_service.py`

**Steps:**
1. Run targeted backend tests.
2. If green, summarize the new ranking behavior and remaining tradeoffs.
