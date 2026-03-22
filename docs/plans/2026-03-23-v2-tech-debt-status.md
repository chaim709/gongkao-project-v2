# V2 技术债状态 - 2026-03-23

## 本次已处理

### 前端活跃路径

- 已在根组件统一配置 antd `holderRender`，消除 `message/modal/notification` 的主题上下文告警。
- 已移除设置页本地假配置块，仅保留真实生效的系统配置。
- 已清理事业编、国考、通用选岗页及岗位对比中的 `Drawer width` 废弃用法，统一改为 `size`。
- 已将事业编选岗页收口为单请求链路，只走 `/api/v1/positions/shiye-selection/search`。
- 已对齐事业编选岗页与 PDF 报告的筛选条件，`exam_category` 不再只在界面上显示、实际未生效。
- 已清理前端 `positions` 模块未使用 API 包装（`get` / `create` / `matchForStudent`）。

### 后端启动与迁移

- 正常启动不再隐式执行 `create_all + seed_data`。
- 新增显式数据库初始化脚本 `scripts/bootstrap_db.py`。
- legacy 数据库默认只补表，不自动纳入 Alembic。
- 新增 `--adopt-legacy`，允许在人工确认后显式执行 `stamp head`。
- Alembic 环境补齐 `compare_type` 与 `compare_server_default`，减少迁移漏检。

### 运维文档

- 部署手册已改为当前真实运行方式：`docker-compose.yml + .env + 8888/8001/5433`。
- 已补充空库初始化、旧库补表、legacy 显式纳管三类操作说明。

## 当前有效主链路

### 事业编选岗

- 前端：`frontend/src/pages/positions/ShiyePositionList.tsx`
- 接口：`POST /api/v1/positions/shiye-selection/search`
- 服务：`backend/app/services/selection/shiye_selection_service.py`
- 规则：专业目录扩展、学历兼容、限制条件筛选、岗位性质偏好、风险降权、竞争比/分数线、冲刺/稳妥/保底分层

### 选岗报告

- 前端调用：`generateReport`
- 后端接口：`POST /api/v1/positions/report/pdf`
- 服务：`backend/app/services/pdf_report_service.py`
- 事业编报告现已与选岗页共用同一套筛选条件输入，包括 `exam_category`

## 仍然存在的高优先技术债

### P1：三套岗位页面高度复制

- `PositionList.tsx`
- `GuokaoPositionList.tsx`
- `ShiyePositionList.tsx`

同类交互和详情抽屉改动需要三处同步，已经是维护风险源头。建议抽公共列表骨架和详情展示组件。

### P1：legacy DB 仍需人工确认后纳入 Alembic

- 当前已经提供安全入口，但未默认接管。
- 这仍然是架构层技术债，不是运行时故障。
- 建议在一次数据库结构核对后，按环境逐步执行：
  - `python scripts/bootstrap_db.py`
  - `python scripts/bootstrap_db.py --adopt-legacy`
  - `python -m alembic current`

## 建议归档或后续清理

### 建议归档

- `backend/import_2023_shiye.py`
- `backend/import_2024_shiye.py`
- `backend/import_2025_shiye.py`
- `backend/merge_*.py`
- `backend/format_2026_full.py`
- `backend/import_shiye_data.py`
- `backend/import_guokao_data.py`
- `backend/export_shiye_tables.py`
- 一次性输出文档和临时产物

### 建议清理

- 历史残留服务层：`backend/app/services/position_service.py`
- 历史残留类型：`PositionMatchRequest`、`PositionMatchResponse`
- 失真文档：`docs/API_DESIGN.md`
- 若确认外部没有隐藏调用，可继续下线历史接口 `/positions/match` 的事业编使用场景

## 本轮新增处理

- 已删除前端未使用 API：`positionApi.get`、`positionApi.create`、`positionApi.matchForStudent`
- 已删除后端死入口：`GET /api/v1/positions/match-for-student/{student_id}`

## 建议的下一批技术债顺序

1. 抽离三套岗位页面公共骨架
2. 清理旧服务层与历史残留类型
3. 修正文档与真实接口返回差异
4. 评估 legacy DB 分环境纳入 Alembic 的执行窗口
