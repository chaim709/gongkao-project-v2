import { useState, useEffect } from 'react';
import { Table, Input, Select, Tag, Card, Row, Col, Statistic, Space, Drawer, Button, Modal, Checkbox, Switch, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, TeamOutlined, TrophyOutlined, UploadOutlined, SettingOutlined, AimOutlined, SwapOutlined, FilePdfOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { positionApi } from '../../api/positions';
import SelectionModePanel from '../../components/positions/SelectionModePanel';
import PositionCompare from '../../components/positions/PositionCompare';
import type { Position, MatchSummary } from '../../types/position';
import type { ColumnsType } from 'antd/es/table';

export default function PositionList() {
  const navigate = useNavigate();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [search, setSearch] = useState('');
  const [year, setYear] = useState<number>();
  const [examType, setExamType] = useState<string>();
  const [city, setCity] = useState<string>();
  const [education, setEducation] = useState<string>();
  const [examCategory, setExamCategory] = useState<string>();
  const [difficulty, setDifficulty] = useState<string>();
  const [location, setLocation] = useState<string>();
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [sortBy, setSortBy] = useState<string>();
  const [sortOrder, setSortOrder] = useState<string>();
  const [columnSettingOpen, setColumnSettingOpen] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);

  // ===== 选岗模式状态 =====
  const [selectionMode, setSelectionMode] = useState(false);
  const [matchYear, setMatchYear] = useState(2023);
  const [matchExamType, setMatchExamType] = useState('省考');
  const [matchResult, setMatchResult] = useState<any>(null);
  const [matchSummary, setMatchSummary] = useState<MatchSummary>();
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchConditions, setMatchConditions] = useState<any>(null);

  // ===== 对比功能状态 =====
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  // 所有可用列定义
  const allColumns = [
    { key: 'title', label: '岗位名称', width: 160 },
    { key: 'department', label: '单位', width: 180 },
    { key: 'city', label: '地区', width: 80 },
    { key: 'year', label: '年份', width: 80 },
    { key: 'exam_type', label: '考试类型', width: 100 },
    { key: 'education', label: '学历', width: 110 },
    { key: 'major', label: '专业要求', width: 150 },
    { key: 'exam_category', label: '考试类别', width: 100 },
    { key: 'recruitment_count', label: '招录', width: 60 },
    { key: 'location', label: '工作地点', width: 120 },
    { key: 'successful_applicants', label: '成功报名', width: 90 },
    { key: 'competition_ratio', label: '竞争比', width: 80 },
    { key: 'min_interview_score', label: '最低分', width: 80 },
    { key: 'max_interview_score', label: '最高分', width: 80 },
    { key: 'max_xingce_score', label: '最高行测', width: 90 },
    { key: 'max_shenlun_score', label: '最高申论', width: 90 },
    { key: 'professional_skills', label: '专业技能', width: 100 },
  ];

  // 加载列配置
  useEffect(() => {
    const saved = localStorage.getItem('position_columns');
    if (saved) {
      setVisibleColumns(JSON.parse(saved));
    } else {
      setVisibleColumns(['title', 'department', 'city', 'education', 'exam_category', 'recruitment_count', 'successful_applicants', 'competition_ratio', 'min_interview_score', 'max_interview_score']);
    }
  }, []);

  // 保存列配置
  const saveColumnConfig = () => {
    localStorage.setItem('position_columns', JSON.stringify(visibleColumns));
    setColumnSettingOpen(false);
  };

  // 动态获取筛选选项
  const { data: filterOptions } = useQuery({
    queryKey: ['position-filters', year, examType],
    queryFn: () => positionApi.filterOptions({ year, exam_type: examType }),
  });

  // 统计
  const { data: stats } = useQuery({
    queryKey: ['position-stats', year, examType],
    queryFn: () => positionApi.stats({ year, exam_type: examType }),
  });

  const { data: analysisData } = useQuery({
    queryKey: ['position-analysis', selectedPosition?.id],
    queryFn: () => selectedPosition ? positionApi.analysis(selectedPosition.id) : null,
    enabled: !!selectedPosition,
  });

  // ===== 浏览模式数据 =====
  const { data: browseData, isLoading: browseLoading } = useQuery({
    queryKey: ['positions', params, search, year, examType, city, education, examCategory, difficulty, location, sortBy, sortOrder],
    queryFn: () => positionApi.list({
      ...params, search: search || undefined, year, exam_type: examType,
      city, education, exam_category: examCategory, difficulty_level: difficulty,
      location, sort_by: sortBy, sort_order: sortOrder,
    }),
    enabled: !selectionMode,
  });

  // 选岗模式匹配
  const handleMatch = async (conditions: any) => {
    setMatchLoading(true);
    setMatchConditions(conditions);
    try {
      const result = await positionApi.match({
        year: matchYear,
        exam_type: matchExamType,
        education: conditions.education,
        major: conditions.major,
        political_status: conditions.political_status,
        work_years: conditions.work_years,
        gender: conditions.gender,
        city, exam_category: examCategory,
        page: params.page,
        page_size: params.page_size,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setMatchResult(result);
      setMatchSummary(result.match_summary);
    } catch {
      // ignore
    } finally {
      setMatchLoading(false);
    }
  };

  // 选岗模式下翻页/排序时重新匹配
  useEffect(() => {
    if (selectionMode && matchConditions) {
      handleMatch(matchConditions);
    }
  }, [params.page, params.page_size, sortBy, sortOrder, city, examCategory]);

  // 生成选岗报告
  const handleGenerateReport = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先勾选岗位后再生成报告');
      return;
    }
    setReportLoading(true);
    try {
      await positionApi.generateReport({
        student_id: matchConditions?.student_id || 0,
        position_ids: selectedRowKeys,
        year: matchYear,
        exam_type: matchExamType,
      });
      message.success('报告已生成并下载');
    } catch {
      message.error('报告生成失败');
    } finally {
      setReportLoading(false);
    }
  };

  // 当前数据源
  const currentData = selectionMode ? matchResult : browseData;
  const isLoading = selectionMode ? matchLoading : browseLoading;

  const difficultyLabel: Record<string, string> = {
    easy: '容易', medium: '中等', hard: '困难',
  };

  // 列定义映射
  const columnMap: Record<string, any> = {
    title: {
      title: '岗位名称', dataIndex: 'title', width: 160, ellipsis: true,
      render: (v: string, record: Position) => (
        <a onClick={() => { setSelectedPosition(record); setDetailOpen(true); }}>
          {v || record.department || '-'}
        </a>
      ),
    },
    department: { title: '单位', dataIndex: 'department', width: 180, ellipsis: true },
    city: { title: '地区', dataIndex: 'city', width: 80 },
    year: { title: '年份', dataIndex: 'year', width: 80, align: 'center' },
    exam_type: { title: '考试类型', dataIndex: 'exam_type', width: 100 },
    education: { title: '学历', dataIndex: 'education', width: 110, ellipsis: true },
    major: { title: '专业要求', dataIndex: 'major', width: 150, ellipsis: true },
    exam_category: { title: '考试类别', dataIndex: 'exam_category', width: 100 },
    recruitment_count: { title: '招录', dataIndex: 'recruitment_count', width: 60, align: 'center' },
    location: { title: '工作地点', dataIndex: 'location', width: 120, ellipsis: true },
    successful_applicants: {
      title: '成功报名', dataIndex: 'successful_applicants', width: 90, align: 'center',
      render: (v: number) => v ?? '-',
    },
    competition_ratio: {
      title: '竞争比', dataIndex: 'competition_ratio', width: 80, align: 'center',
      render: (v: number) => v ? `${v.toFixed(0)}:1` : '-',
      sorter: true,
      sortOrder: sortBy === 'competition_ratio' ? (sortOrder === 'asc' ? 'ascend' : 'descend') : undefined,
    },
    min_interview_score: {
      title: '最低分', dataIndex: 'min_interview_score', width: 80, align: 'center',
      render: (v: number) => v ? v.toFixed(1) : '-',
    },
    max_interview_score: {
      title: '最高分', dataIndex: 'max_interview_score', width: 80, align: 'center',
      render: (v: number) => v ? v.toFixed(1) : '-',
    },
    max_xingce_score: {
      title: '最高行测', dataIndex: 'max_xingce_score', width: 90, align: 'center',
      render: (v: number) => v ? v.toFixed(1) : '-',
    },
    max_shenlun_score: {
      title: '最高申论', dataIndex: 'max_shenlun_score', width: 90, align: 'center',
      render: (v: number) => v ? v.toFixed(1) : '-',
    },
    professional_skills: {
      title: '专业技能', dataIndex: 'professional_skills', width: 100, ellipsis: true,
      render: (v: string) => v || '-',
    },
  };

  const columns: ColumnsType<Position> = visibleColumns
    .map(key => columnMap[key])
    .filter(Boolean);

  return (
    <div>
      {/* 模式切换 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <AimOutlined style={{ color: selectionMode ? '#52c41a' : '#999' }} />
          <Switch
            checked={selectionMode}
            onChange={(checked) => {
              setSelectionMode(checked);
              if (!checked) {
                setMatchResult(null);
                setMatchSummary(undefined);
                setMatchConditions(null);
              }
            }}
            checkedChildren="选岗模式"
            unCheckedChildren="浏览模式"
          />
          {selectionMode && (
            <Tag color="green">选岗模式已开启 - 输入学员条件后自动匹配可报岗位</Tag>
          )}
        </Space>
      </div>

      {/* 选岗模式面板 */}
      {selectionMode && (
        <SelectionModePanel
          year={matchYear}
          examType={matchExamType}
          onYearChange={setMatchYear}
          onExamTypeChange={setMatchExamType}
          onMatch={handleMatch}
          onClear={() => {
            setSelectionMode(false);
            setMatchResult(null);
            setMatchSummary(undefined);
            setMatchConditions(null);
          }}
          matchSummary={matchSummary}
          loading={matchLoading}
          yearOptions={filterOptions?.years || []}
          examTypeOptions={filterOptions?.exam_types || []}
        />
      )}

      {/* 统计卡片（浏览模式） */}
      {!selectionMode && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic title="岗位总数" value={stats?.total_positions || 0} prefix={<TrophyOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="招录总人数" value={stats?.total_recruitment || 0} prefix={<TeamOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="覆盖地区" value={stats?.by_city?.length || 0} prefix={<EnvironmentOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="筛选结果" value={currentData?.total || 0} suffix="条" />
            </Card>
          </Col>
        </Row>
      )}

      {/* 筛选区 */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {!selectionMode && (
          <>
            <Select
              placeholder="选择年份" value={year} allowClear style={{ width: 110 }}
              onChange={(v) => { setYear(v); setCity(undefined); setEducation(undefined); setExamCategory(undefined); setParams(p => ({ ...p, page: 1 })); }}
              options={(filterOptions?.years || []).map((y: number) => ({ value: y, label: `${y}年` }))}
            />
            <Select
              placeholder="考试类型" value={examType} allowClear style={{ width: 140 }}
              onChange={(v) => { setExamType(v); setCity(undefined); setEducation(undefined); setExamCategory(undefined); setParams(p => ({ ...p, page: 1 })); }}
              options={(filterOptions?.exam_types || []).map((t: string) => ({ value: t, label: t === '省考' ? '江苏省考' : t }))}
            />
            <Input
              placeholder="搜索岗位/单位/专业" prefix={<SearchOutlined />} style={{ width: 220 }} allowClear
              onChange={(e) => { setSearch(e.target.value); setParams(p => ({ ...p, page: 1 })); }}
            />
          </>
        )}
        <Select
          placeholder="选择城市" value={city} allowClear style={{ width: 160 }} showSearch
          onChange={(v) => { setCity(v); setLocation(undefined); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.cities || []).map((c: string) => ({ value: c, label: c }))}
        />
        {city && filterOptions?.city_locations?.[city]?.length > 0 && (
          <Select
            placeholder="选择区县"
            value={location} allowClear style={{ width: 140 }} showSearch
            onChange={(v) => { setLocation(v); setParams(p => ({ ...p, page: 1 })); }}
            options={filterOptions.city_locations[city].map((l: string) => ({ value: l, label: l }))}
          />
        )}
        {!selectionMode && (
          <>
            <Select
              placeholder="学历要求" value={education} allowClear style={{ width: 140 }}
              onChange={(v) => { setEducation(v); setParams(p => ({ ...p, page: 1 })); }}
              options={[
                { value: '大专及以上', label: '大专及以上' },
                { value: '本科及以上', label: '本科及以上' },
                { value: '研究生及以上', label: '研究生及以上' },
              ]}
            />
          </>
        )}
        <Select
          placeholder="考试类别" value={examCategory} allowClear style={{ width: 160 }}
          onChange={(v) => { setExamCategory(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.exam_categories || []).map((c: string) => ({ value: c, label: c }))}
        />
        {!selectionMode && (
          <Select
            placeholder="难度等级" allowClear style={{ width: 110 }}
            onChange={(v) => { setDifficulty(v); setParams(p => ({ ...p, page: 1 })); }}
            options={[
              { value: 'easy', label: '容易' },
              { value: 'medium', label: '中等' },
              { value: 'hard', label: '困难' },
            ]}
          />
        )}
        <Button icon={<SettingOutlined />} onClick={() => setColumnSettingOpen(true)}>列设置</Button>
        <Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('/positions/import')} style={{ marginLeft: 'auto' }}>导入岗位</Button>
      </div>

      {/* 岗位表格 */}
      <Table<Position>
        columns={columns}
        dataSource={currentData?.items || []}
        rowKey="id"
        loading={isLoading}
        rowSelection={selectionMode ? {
          selectedRowKeys,
          onChange: (keys) => {
            if (keys.length > 5) {
              message.warning('最多选择5个岗位进行对比');
              return;
            }
            setSelectedRowKeys(keys as number[]);
          },
        } : undefined}
        onChange={(_pagination, _filters, sorter) => {
          if (!Array.isArray(sorter) && sorter.field) {
            const field = String(sorter.field);
            if (sorter.order) {
              setSortBy(field);
              setSortOrder(sorter.order === 'ascend' ? 'asc' : 'desc');
            } else {
              setSortBy(undefined);
              setSortOrder(undefined);
            }
          }
        }}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: currentData?.total || 0,
          showTotal: (total) => `共 ${total} 个岗位`,
          showSizeChanger: true,
          pageSizeOptions: ['20', '50', '100'],
          onChange: (page, pageSize) => setParams(p => ({ ...p, page, page_size: pageSize })),
        }}
        scroll={{ x: 1000 }}
        size="middle"
      />

      {/* 岗位详情抽屉 */}
      <Drawer
        title={selectedPosition?.title || selectedPosition?.department || '岗位详情'}
        open={detailOpen}
        onClose={() => { setDetailOpen(false); setSelectedPosition(null); }}
        width={480}
      >
        {selectedPosition && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Card size="small" title="基本信息">
              <p><b>单位：</b>{selectedPosition.department || '-'}</p>
              <p><b>岗位代码：</b>{selectedPosition.position_code || '-'}</p>
              <p><b>地区：</b>{selectedPosition.city || '-'}</p>
              <p><b>考试类别：</b>{selectedPosition.exam_category || '-'}</p>
              <p><b>招录人数：</b>{selectedPosition.recruitment_count}</p>
            </Card>
            <Card size="small" title="报考条件">
              <p><b>学历要求：</b>{selectedPosition.education || '-'}</p>
              <p><b>专业要求：</b>{selectedPosition.major || '不限'}</p>
              <p><b>其他要求：</b>{selectedPosition.other_requirements || '无'}</p>
            </Card>
            <Card size="small" title="竞争数据">
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="报名人数" value={selectedPosition.apply_count ?? '-'} />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="竞争比"
                    value={selectedPosition.competition_ratio ? `${selectedPosition.competition_ratio.toFixed(0)}:1` : '-'}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="难度"
                    value={difficultyLabel[selectedPosition.difficulty_level || ''] || '-'}
                  />
                </Col>
              </Row>
            </Card>
            {analysisData?.success && (
              <Card size="small" title="智能分析">
                <Row gutter={16} style={{ marginBottom: 16 }}>
                  <Col span={12}>
                    <Statistic
                      title="竞争度"
                      value={analysisData.data.competition.score}
                      suffix={<Tag color={analysisData.data.competition.level === 'high' ? 'red' : analysisData.data.competition.level === 'medium' ? 'orange' : 'green'}>{analysisData.data.competition.level_text}</Tag>}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="性价比"
                      value={analysisData.data.value.score}
                      suffix={<Tag color={analysisData.data.value.level === 'high' ? 'green' : analysisData.data.value.level === 'medium' ? 'orange' : 'red'}>{analysisData.data.value.level_text}</Tag>}
                    />
                  </Col>
                </Row>
                <p style={{ color: '#666', fontSize: '14px' }}>{analysisData.data.recommendation}</p>
              </Card>
            )}
          </Space>
        )}
      </Drawer>

      {/* 选岗对比浮动栏 */}
      {selectionMode && selectedRowKeys.length > 0 && (
        <div style={{
          position: 'fixed', bottom: 0, left: 0, right: 0,
          background: '#fff', borderTop: '2px solid #1890ff',
          padding: '12px 24px', zIndex: 100,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
        }}>
          <Space>
            <Tag color="blue">已选 {selectedRowKeys.length} 个岗位</Tag>
            <Button size="small" onClick={() => setSelectedRowKeys([])}>清空选择</Button>
          </Space>
          <Space>
            <Button
              type="primary"
              icon={<SwapOutlined />}
              disabled={selectedRowKeys.length < 2}
              onClick={() => setCompareOpen(true)}
            >
              对比岗位
            </Button>
            <Button
              icon={<FilePdfOutlined />}
              loading={reportLoading}
              onClick={handleGenerateReport}
            >
              生成报告
            </Button>
          </Space>
        </div>
      )}

      {/* 对比 Drawer */}
      <PositionCompare
        open={compareOpen}
        onClose={() => setCompareOpen(false)}
        positionIds={selectedRowKeys}
      />

      {/* 列设置Modal */}
      <Modal
        title="列设置"
        open={columnSettingOpen}
        onOk={saveColumnConfig}
        onCancel={() => setColumnSettingOpen(false)}
        width={500}
      >
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          <Checkbox.Group
            value={visibleColumns}
            onChange={(values) => setVisibleColumns(values as string[])}
            style={{ width: '100%' }}
          >
            <Row gutter={[16, 16]}>
              {allColumns.map(col => (
                <Col span={12} key={col.key}>
                  <Checkbox value={col.key}>{col.label}</Checkbox>
                </Col>
              ))}
            </Row>
          </Checkbox.Group>
        </div>
      </Modal>
    </div>
  );
}
