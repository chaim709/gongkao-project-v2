# Shiye Selection Filter Rebuild Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the Jiangsu事业编 selection flow around decision-useful filters instead of raw source fields.

**Architecture:** Keep the existing `/positions/shiye-selection/search` endpoint and page shell, but change the search semantics and filter option payloads to use normalized decision-facing dimensions. Backend becomes responsible for standardizing岗位性质/招聘对象/经费来源 and applying风险排除 filters; frontend switches the selection panel and result filters to those normalized dimensions.

**Tech Stack:** FastAPI, SQLAlchemy, React, TypeScript, Ant Design, React Query.

---

### Task 1: Add normalization rules for事业编 decision filters

**Files:**
- Create: `backend/app/services/selection/shiye_filter_normalizers.py`
- Test: `backend/tests/unit/test_shiye_selection_service.py`

**Step 1: Write failing unit tests**
- Add tests for:
  - raw `exam_category` -> `管理岗 / 专技岗 / 工勤岗`
  - empty `funding_source` -> `不限`
  - raw `recruitment_target` normalization into `不限 / 应届毕业生 / 社会人员 / 定向专项`
  - risk tag exclusion predicate

**Step 2: Run targeted tests to verify failures**
Run: `pytest backend/tests/unit/test_shiye_selection_service.py -q`
Expected: FAIL on missing normalizer helpers.

**Step 3: Implement minimal normalization helpers**
- Provide pure functions for:
  - `normalize_post_nature(exam_category)`
  - `normalize_funding_source(value)`
  - `normalize_recruitment_target(value)`
  - `should_exclude_by_risk(tags, excluded_tags)`

**Step 4: Run targeted tests to verify pass**
Run: `pytest backend/tests/unit/test_shiye_selection_service.py -q`
Expected: PASS for new helper coverage.

**Step 5: Commit**
```bash
git add backend/app/services/selection/shiye_filter_normalizers.py backend/tests/unit/test_shiye_selection_service.py
git commit -m "feat(selection): normalize shiye decision filters"
```

### Task 2: Rebuild事业编搜索与筛选项接口语义

**Files:**
- Modify: `backend/app/services/selection/shiye_selection_service.py`
- Modify: `backend/app/routes/positions.py`
- Modify: `backend/app/schemas/position.py`
- Test: `backend/tests/unit/test_shiye_selection_service.py`

**Step 1: Add failing tests for new search semantics**
- Cover:
  - normalized filter options payload contains `post_natures / recruitment_targets / funding_sources / risk_tags`
  - search can filter by normalized `post_natures`
  - search can exclude `risk_tags`
  - summary still preserves hard/manual/fail counts

**Step 2: Run targeted tests to verify failures**
Run: `pytest backend/tests/unit/test_shiye_selection_service.py -q`
Expected: FAIL on old request shape / old filter option payload.

**Step 3: Implement minimal backend changes**
- Update `ShiyeSelectionSearchRequest` and report request to accept:
  - `recruitment_targets: list[str]`
  - `funding_sources: list[str]`
  - `excluded_risk_tags: list[str]`
  - optional `recommendation_tier`
- In `ShiyeSelectionService.search`:
  - stop using raw `exam_category` as top-level selection filter
  - derive normalized dimensions per item
  - apply normalized filters and risk exclusions after eligibility/risk evaluation
- In `get_filter_options`:
  - return normalized options, not raw `exam_categories`
  - treat blank funding/recruitment as `不限`

**Step 4: Run targeted tests to verify pass**
Run: `pytest backend/tests/unit/test_shiye_selection_service.py -q`
Expected: PASS.

**Step 5: Commit**
```bash
git add backend/app/services/selection/shiye_selection_service.py backend/app/routes/positions.py backend/app/schemas/position.py backend/tests/unit/test_shiye_selection_service.py
git commit -m "feat(selection): rebuild shiye filter semantics"
```

### Task 3: Rebuild事业编前端选岗输入和结果筛选

**Files:**
- Modify: `frontend/src/components/positions/SelectionModePanel.tsx`
- Modify: `frontend/src/pages/positions/ShiyePositionList.tsx`
- Modify: `frontend/src/types/position.ts`
- Modify: `frontend/src/api/positions.ts`

**Step 1: Update type definitions and request contracts**
- Add normalized filter option fields and request fields.
- Keep backward-compatible optional fields where needed for report generation.

**Step 2: Rebuild selection condition card**
- Replace old学历 selector with level-only choices: `大专 / 本科 / 研究生 / 博士`
- Add `包含需人工确认` toggle
- Keep专业/政治面貌/工龄/性别

**Step 3: Rebuild result filters**
- Use normalized filters:
  - `岗位性质`
  - `招聘对象`
  - `经费来源`
  - `风险避雷`
  - `推荐层级`
- Keep `地市 / 区县`
- Remove `笔试类别` from选岗模式主筛选

**Step 4: Wire requests and summary UI**
- Send new payload fields to search/report APIs.
- Keep current match summary and sort basis display.

**Step 5: Build frontend**
Run: `npm run build`
Expected: PASS.

**Step 6: Commit**
```bash
git add frontend/src/components/positions/SelectionModePanel.tsx frontend/src/pages/positions/ShiyePositionList.tsx frontend/src/types/position.ts frontend/src/api/positions.ts
git commit -m "feat(frontend): rebuild shiye selection filters"
```

### Task 4: Verify end-to-end and deploy local container assets

**Files:**
- Modify: none unless fixes are required

**Step 1: Run backend targeted tests**
Run: `pytest backend/tests/unit/test_shiye_selection_service.py -q`
Expected: PASS.

**Step 2: Run frontend build**
Run: `cd frontend && npm run build`
Expected: PASS.

**Step 3: Sync frontend dist to nginx container**
Run: `docker cp frontend/dist/. gongkao-guanli-frontend:/usr/share/nginx/html`
Expected: success.

**Step 4: Spot-check service**
Run: `curl -I http://127.0.0.1:8888`
Expected: `200 OK`.

**Step 5: Commit any follow-up fixes**
```bash
git add <files>
git commit -m "fix(selection): polish shiye decision filters"
```
