# Jiangsu Shiye Selection System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the Jiangsu institution-position selection flow around a rule-based eligibility engine that maximizes valid recall first, then compresses competition, then highlights hidden risks.

**Architecture:** Keep raw position rows intact, add a dedicated Jiangsu Shiye selection service and API layer, and build a new workbench-style frontend flow for `/shiye-positions`. Do not overload the current generic `/positions/match` behavior for all exam types; ship the new logic as an isolated Jiangsu事业编 path first, validate it with real data, then decide whether to generalize.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, React 19, TypeScript, TanStack Query, Ant Design, PostgreSQL.

---

## Understanding Summary

- The first question for most Jiangsu事业编 users is “我能报什么岗位”, not “我想走哪条职业路线”.
- Major matching must be recall-first: exact major match, official category match, and `不限` all count as candidate hits.
- One concrete major may belong to multiple official categories in the Jiangsu reference directory, so the engine must support one-to-many mappings.
- Education filtering must be rule-based rather than string-equality-based: higher education levels should satisfy lower minimum requirements.
- `管理岗 / 专技岗 / 工勤岗` is a second-stage narrowing dimension after eligibility, not the first screen.
- Hidden risk is part of decision support, not just data display. Historical competition, score lines, work intensity, and remote location must be surfaced.
- The first release should focus on Jiangsu事业编 only. 国考 / 省考 stay on current logic until this flow is validated.

## Assumptions

- First release serves both students and advisor-assisted selection, but UX should prioritize fast advisor operation.
- The provided `专业参考目录.doc` is the authoritative mapping source for the current design baseline.
- Five years of岗位表 will be available later, but implementation can start with 2023 and 2025 samples.
- Raw position import quality will remain inconsistent, so normalization must be explicit and testable.
- The initial version should prefer “do not漏掉能报岗位” over overly aggressive precision.

## Explicit Non-Goals

- Do not redesign 国考 / 省考 selection in this phase.
- Do not introduce LLM-based eligibility judgment in the core matching path.
- Do not attempt full automation of yearly reference directory import in phase 1.
- Do not replace the existing generic position list endpoints used by other modules.

## Decision Log

1. **Recall-first major matching**
   - Chosen: include exact major, official category, and `不限`.
   - Rejected: exact-only matching.
   - Reason: exact-only matching would incorrectly exclude many valid positions.

2. **One-to-many major mapping**
   - Chosen: allow one concrete major to map to multiple official categories.
   - Rejected: force a single “best” category.
   - Reason: the Jiangsu directory itself does not support one-to-one mapping.

3. **Education as rules, not text filter**
   - Chosen: normalize education text to minimum-level rules.
   - Rejected: direct text equality on `学历`.
   - Reason: the source tables contain multiple equivalent textual variants.

4. **岗位性质 after eligibility**
   - Chosen: users first see all eligible positions, then filter by `管理岗 / 专技岗 / 工勤岗`.
   - Rejected: force users to pick post nature before eligibility.
   - Reason: real user behavior starts from major-based eligibility.

5. **Risk as visible warning, not silent exclusion**
   - Chosen: high-risk positions remain visible but carry tags, ranking penalties, and explanations.
   - Rejected: auto-hide all risky positions.
   - Reason: risky does not always mean impossible; users and advisors need visibility.

6. **Dedicated Jiangsu事业编 flow**
   - Chosen: add a dedicated service/API/UI path for `shiye-positions`.
   - Rejected: mutate current generic `/positions/match` into a universal engine immediately.
   - Reason: this reduces regression risk and keeps scope controlled.

## Target Output for Phase 1

Users should be able to:

1. Enter a concrete major and education level.
2. Get a result set split by hit source:
   - `专业精确匹配`
   - `专业大类匹配`
   - `专业不限`
3. Further narrow results by:
   - `管理岗 / 专技岗 / 工勤岗`
   - 学历
   - 招聘对象
   - 政治面貌
   - 城市 / 区县
4. See risk tags for positions such as:
   - `高竞争`
   - `高分线`
   - `加班/值班`
   - `一线/应急`
   - `偏远/驻外`
5. Understand why a position matched and why it is risky.

## Recommended Delivery Sequence

### Task 1: Create the Jiangsu Major Catalog Baseline

**Files:**
- Create: `backend/app/data/reference/jiangsu_major_catalog_2026.json`
- Create: `backend/app/services/selection/major_catalog_service.py`
- Create: `backend/tests/unit/services/test_major_catalog_service.py`

**Intent:**
Normalize the provided Word directory into a machine-readable mapping that supports:
- `major_name -> [category_names]`
- `category_name -> [major_names]`
- `education_level -> category -> majors`

**Implementation Notes:**
- Preserve original major strings exactly in the source dataset.
- Add normalized helper keys for lookup only.
- Support one major mapping to multiple categories.
- Do not infer mappings beyond the official directory in phase 1.

**Test Commands:**
- `pytest backend/tests/unit/services/test_major_catalog_service.py -v`

**Acceptance Criteria:**
- `财务管理` resolves to more than one official category.
- Category lookup can return all child majors.
- Unknown major returns an empty mapping, not an exception.

### Task 2: Replace the Simplified Major Matcher

**Files:**
- Modify: `backend/app/services/position_match_service.py`
- Create: `backend/app/services/selection/major_match_rules.py`
- Create: `backend/tests/unit/services/test_major_match_rules.py`

**Intent:**
Replace the current substring-based `check_major` logic with explicit matching buckets:
- `exact_major_match`
- `category_match`
- `unlimited_major_match`
- `manual_review_needed`

**Implementation Notes:**
- Use the official catalog service for category expansion.
- Continue to allow `不限`.
- Do not treat free-text fuzzy guesses as exact matches.
- For vague terms like `相关专业`, output `manual_review_needed` instead of hard pass.

**Test Commands:**
- `pytest backend/tests/unit/services/test_major_match_rules.py -v`
- `pytest backend/tests/unit/services/test_major_catalog_service.py -v`

**Acceptance Criteria:**
- Exact match outranks category match.
- `专业不限` is always included as a lower-priority match source.
- Ambiguous text is flagged rather than silently passed.

### Task 3: Normalize Education Rules

**Files:**
- Create: `backend/app/services/selection/education_rules.py`
- Modify: `backend/app/services/position_match_service.py`
- Create: `backend/tests/unit/services/test_education_rules.py`

**Intent:**
Convert messy `学历` text into deterministic minimum-level eligibility rules.

**Rule Baseline:**
- `大专/专科/高职` = level 1
- `本科/学士` = level 2
- `硕士/研究生` = level 3
- `博士` = level 4

**Implementation Notes:**
- Normalize variants such as `本科及 以上`, `本科及以上学历`, `研究生学历，取得相应学位`.
- Parse `仅限`, `及以上`, `或`, and equivalent separators.
- Return `manual_review_needed` if the requirement cannot be parsed safely.

**Test Commands:**
- `pytest backend/tests/unit/services/test_education_rules.py -v`

**Acceptance Criteria:**
- `研究生` candidate passes `本科及以上`.
- `本科` candidate passes `大专及以上`.
- malformed strings do not crash matching.

### Task 4: Normalize Post Nature for Jiangsu事业编

**Files:**
- Create: `backend/app/services/selection/post_nature_rules.py`
- Create: `backend/tests/unit/services/test_post_nature_rules.py`
- Optionally Modify: `backend/app/schemas/position.py`

**Intent:**
Derive a stable `post_nature` field from raw source columns, mainly `笔试类别`, with output values:
- `管理岗`
- `专技岗`
- `工勤岗`
- `待确认`

**Implementation Notes:**
- 2025 data can mostly map directly.
- 2023 variants must be normalized from strings like `管理`, `管理类`, `专业技术其他类`, `其他专技类`.
- Keep raw source untouched; expose normalized output via API.

**Test Commands:**
- `pytest backend/tests/unit/services/test_post_nature_rules.py -v`

**Acceptance Criteria:**
- Historical variants map consistently.
- Unknown category values degrade to `待确认`.

### Task 5: Parse Constraint Signals from `其他条件` and `招聘对象`

**Files:**
- Create: `backend/app/services/selection/constraint_rules.py`
- Create: `backend/tests/unit/services/test_constraint_rules.py`
- Modify: `backend/app/services/position_match_service.py`

**Intent:**
Extract hard filters and display signals from free-text conditions.

**Fields to Support First:**
- 党员要求
- 应届 / 毕业生要求
- 工作年限
- 性别
- 学位要求
- 教师资格证 / 法考 / 职称 as display tags only in phase 1

**Implementation Notes:**
- Separate `hard_pass`, `hard_fail`, and `manual_review_needed`.
- Do not auto-pass professional certificates unless there is explicit user input later.
- Keep extracted tags in a structured response for frontend display.

**Test Commands:**
- `pytest backend/tests/unit/services/test_constraint_rules.py -v`

**Acceptance Criteria:**
- `中共党员` and `2025年毕业生` are parsed reliably.
- Non-supported certificate text is surfaced as “需人工确认”, not discarded.

### Task 6: Add Risk Scoring and Risk Tags

**Files:**
- Create: `backend/app/services/selection/risk_rules.py`
- Create: `backend/tests/unit/services/test_risk_rules.py`

**Intent:**
Compute explainable risk tags from historical metrics and text fields.

**Initial Risk Dimensions:**
- `高竞争`: high `竞争比` / `报名人数`
- `高分线`: high `进面最低分` relative to same `笔试类别` / same year
- `工作强度大`: text hits in `备注` / `岗位说明` such as `加班`, `值班`, `夜班`, `应急`, `一线`
- `地点偏/驻外`: text hits such as `偏远`, `驻外`, plus configurable region list later

**Implementation Notes:**
- Risk should lower ranking priority, not remove positions.
- Output both `risk_tags` and `risk_reasons`.
- Thresholds should be configurable constants, not hardcoded inline everywhere.

**Test Commands:**
- `pytest backend/tests/unit/services/test_risk_rules.py -v`

**Acceptance Criteria:**
- A position can carry multiple risk tags.
- Users can see why a tag exists.

### Task 7: Introduce a Dedicated Jiangsu事业编 Selection API

**Files:**
- Create: `backend/app/services/selection/shiye_selection_service.py`
- Modify: `backend/app/routes/positions.py`
- Modify: `backend/app/schemas/position.py`
- Create: `backend/tests/integration/test_shiye_selection_api.py`

**Recommended Endpoint Shape:**
- `POST /api/v1/positions/shiye-selection/search`
- `GET /api/v1/positions/shiye-selection/filter-options`

**Response Shape Must Include:**
- raw position payload
- `match_source`
- `match_reasons`
- `post_nature`
- `risk_tags`
- `risk_reasons`
- `manual_review_flags`

**Implementation Notes:**
- Keep the current `/api/v1/positions/match` stable for non-江苏事业编 flows.
- The new endpoint should compose the major, education, constraints, and risk services.

**Test Commands:**
- `pytest backend/tests/integration/test_shiye_selection_api.py -v`

**Acceptance Criteria:**
- Endpoint returns grouped and explainable match results.
- Existing generic position APIs continue to work.

### Task 8: Build a New Workbench UI for `/shiye-positions`

**Files:**
- Create: `frontend/src/types/shiyeSelection.ts`
- Create: `frontend/src/api/shiyeSelection.ts`
- Create: `frontend/src/components/positions/shiye/MajorInputPanel.tsx`
- Create: `frontend/src/components/positions/shiye/EligibilitySummary.tsx`
- Create: `frontend/src/components/positions/shiye/PostNatureTabs.tsx`
- Create: `frontend/src/components/positions/shiye/RiskTagList.tsx`
- Create: `frontend/src/components/positions/shiye/MatchReasonList.tsx`
- Create: `frontend/src/components/positions/shiye/ManualReviewBanner.tsx`
- Create: `frontend/src/pages/positions/ShiyeSelectionWorkbench.tsx`
- Modify: `frontend/src/App.tsx`

**Intent:**
Replace the current table-first experience with a workbench that follows the real user sequence:
1. Enter major + education + hard constraints.
2. See eligibility buckets.
3. Narrow by post nature.
4. Inspect risk and match reasons.
5. Compare or save positions.

**Page Sections:**
- Top input panel: major, education, graduate status, political status, city, etc.
- Eligibility summary cards: exact match / category match / unlimited / manual review.
- Main result area: tabs for `全部 / 管理岗 / 专技岗 / 工勤岗`.
- Position card or table row with visible match source and risk tags.
- Detail drawer with `为什么能报` and `为什么有风险`.

**Implementation Notes:**
- Keep the route `/shiye-positions`.
- Preserve compare/report actions only after the new matching path is stable.
- Do not mix this page with 国考/省考 generic filters.

**Test Commands:**
- `npm run build`
- if test setup exists later: `npm test -- shiye-selection`

**Acceptance Criteria:**
- A user can understand match source without opening code or docs.
- The UI explicitly separates `专业精确匹配 / 专业大类匹配 / 专业不限`.
- Users can filter by `管理岗 / 专技岗 / 工勤岗` after eligibility is calculated.

### Task 9: Add Data Audit Utilities

**Files:**
- Create: `backend/scripts/profile_shiye_positions.py`
- Create: `backend/scripts/profile_major_catalog.py`
- Create: `docs/selection-data-audit.md`

**Intent:**
Make messy data visible before and after normalization.

**Audit Output Should Include:**
- top raw `学历` variants
- top raw `笔试类别` variants
- unparsed `其他条件` samples
- unmapped majors from imported data
- risk-text keyword hit counts

**Commands:**
- `python backend/scripts/profile_shiye_positions.py`
- `python backend/scripts/profile_major_catalog.py`

**Acceptance Criteria:**
- The team can inspect normalization coverage before trusting the engine.

### Task 10: Rollout and Validation

**Files:**
- Modify: `docs/开发起点文档_2026-03-23.md`
- Create: `docs/shiye-selection-validation-checklist.md`

**Validation Checklist:**
- 20 real majors sampled across multiple categories
- 20 positions with exact major requirements
- 20 positions with category requirements
- 20 `专业不限` positions
- 20 jobs with known hidden risks
- advisor review on false positives vs false negatives

**Acceptance Criteria:**
- false negatives are materially reduced vs current system
- major-category matches are explainable to users
- high-risk positions are visible and not silently discarded

## Recommended Milestones

### Milestone A: Rule Engine Ready
- Tasks 1–5 complete
- No UI redesign yet
- Backend can already return structured eligibility results

### Milestone B: Risk + Dedicated API Ready
- Tasks 6–7 complete
- Jiangsu事业编 matching can be consumed separately from generic position APIs

### Milestone C: New Workbench Ready
- Task 8 complete
- `/shiye-positions` becomes the new guided flow

### Milestone D: Validation Ready
- Tasks 9–10 complete
- Ready for advisor and student trial usage

## Recommended First Build Order

1. Build the catalog and major matcher.
2. Build education normalization.
3. Add post nature normalization.
4. Add constraints parsing.
5. Add risk rules.
6. Expose the dedicated API.
7. Build the new `ShiyeSelectionWorkbench` page.

## What Should Happen Immediately After This Plan Is Accepted

1. Import the provided Word directory into a normalized JSON mapping file.
2. Write failing tests for major mapping and education normalization.
3. Replace the current simplified major matcher in `position_match_service.py`.
4. Only after backend rule outputs stabilize, start the new frontend workbench.

