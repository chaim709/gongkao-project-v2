# Shiye Recommendation Reasons And PDF Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refine detail-page recommendation explanations for `同单位 / 同城同类 / 低风险替代` and render the same grouped recommendations in the selection report PDF.

**Architecture:** Extend the detail recommendation service so each grouped item carries a concise recommendation summary derived from the grouping rule and candidate signals. Reuse the same grouped recommendation payload inside PDF generation so the PDF and详情页 share one backend decision source instead of duplicating business rules.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy async, ReportLab, React, TypeScript, pytest

---

### Task 1: Add grouped recommendation reason fields

**Files:**
- Modify: `backend/app/schemas/position.py`
- Modify: `backend/app/services/position_detail_extension_service.py`
- Test: `backend/tests/unit/test_position_detail_extension_service.py`

**Step 1: Write the failing test**
- Assert each returned grouped item contains a human-readable recommendation reason.
- Assert `低风险替代` reason includes lower-risk evidence.

**Step 2: Run test to verify it fails**
Run: `docker exec gongkao-guanli-backend sh -lc "cd /app && python -m pytest tests/unit/test_position_detail_extension_service.py -q"`
Expected: FAIL because the new field is missing.

**Step 3: Write minimal implementation**
- Add optional recommendation reason field to related item schema.
- Build reason text from grouping key plus similarity/risk signals.
- Keep `related_items` backward compatible.

**Step 4: Run test to verify it passes**
Run: `docker exec gongkao-guanli-backend sh -lc "cd /app && python -m pytest tests/unit/test_position_detail_extension_service.py -q"`
Expected: PASS.

**Step 5: Commit**
```bash
git add backend/app/schemas/position.py backend/app/services/position_detail_extension_service.py backend/tests/unit/test_position_detail_extension_service.py
git commit -m "feat(shiye): explain grouped recommendations"
```

### Task 2: Render refined recommendation reasons in detail drawer

**Files:**
- Modify: `frontend/src/types/position.ts`
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`

**Step 1: Write the failing UI expectation**
- Expect each recommendation item to show a short explanation line, not only tags.

**Step 2: Implement minimal rendering**
- Add the new field to frontend type.
- Show it below item title/meta in the grouped list.

**Step 3: Build frontend**
Run: `cd frontend && npm run build`
Expected: PASS.

**Step 4: Commit**
```bash
git add frontend/src/types/position.ts frontend/src/pages/positions/ShiyePositionList.tsx
git commit -m "feat(shiye): show recommendation summaries in detail drawer"
```

### Task 3: Sync grouped recommendations into PDF report

**Files:**
- Modify: `backend/app/services/pdf_report_service.py`
- Modify: `backend/app/routes/positions.py` only if request plumbing needs extension
- Optionally modify: `backend/app/services/position_detail_extension_service.py`

**Step 1: Trace current report data flow**
- Identify where selected positions are fetched and rendered.
- Reuse the detail extension service per selected position or build a shared helper if needed.

**Step 2: Implement minimal PDF section**
- Add a section after each selected position or after the main analysis block.
- Render `同单位 / 同城同类 / 低风险替代` headings.
- Under each heading, show 1-3 items with岗位名、单位、地点、推荐原因、风险/相似度摘要.

**Step 3: Run backend smoke test**
- Generate one real PDF through the API.
- Confirm the PDF is non-empty and generation succeeds.

**Step 4: Commit**
```bash
git add backend/app/services/pdf_report_service.py backend/app/services/position_detail_extension_service.py
git commit -m "feat(shiye): add grouped recommendations to pdf report"
```

### Task 4: Deploy and verify

**Files:**
- Modify deployed artifacts only

**Step 1: Sync backend files to container**
Run `docker cp ... gongkao-guanli-backend:/app/...` and restart container.

**Step 2: Build and sync frontend dist**
Run `cd frontend && npm run build && docker cp frontend/dist/. gongkao-guanli-frontend:/usr/share/nginx/html`

**Step 3: Verify**
- API returns grouped reasons.
- 浏览器详情页 shows grouped reasons.
- PDF download succeeds and contains grouped recommendation section.

**Step 4: Final commit if needed**
- Create one integration commit if the work was not already committed.
