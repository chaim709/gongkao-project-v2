import { useState, useEffect } from 'react';
import { Table, Input, Select, Tag, Card, Row, Col, Statistic, Space, Drawer, Button, Modal, Checkbox, Switch, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, TeamOutlined, TrophyOutlined, SettingOutlined, AimOutlined, SwapOutlined, FilePdfOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { positionApi } from '../../api/positions';
import SelectionModePanel from '../../components/positions/SelectionModePanel';
import PositionCompare from '../../components/positions/PositionCompare';
import type { Position, MatchSummary } from '../../types/position';
import type { ColumnsType } from 'antd/es/table';

export default function GuokaoPositionList() {
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [search, setSearch] = useState('');
  const [year, setYear] = useState<number>();
  const [province, setProvince] = useState<string>();
  const [city, setCity] = useState<string>();
  const [education, setEducation] = useState<string>();
  const [examCategory, setExamCategory] = useState<string>();
  const [institutionLevel, setInstitutionLevel] = useState<string>();
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [sortBy, setSortBy] = useState<string>();
  const [sortOrder, setSortOrder] = useState<string>();
  const [columnSettingOpen, setColumnSettingOpen] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);

  // 选岗模式状态
  const [selectionMode, setSelectionMode] = useState(false);
  const [matchYear, setMatchYear] = useState(2025);
  const [matchResult, setMatchResult] = useState<any>(null);
  const [matchSummary, setMatchSummary] = useState<MatchSummary>();
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchConditions, setMatchConditions] = useState<any>(null);

  // 对比功能状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  // 国考特有列定义
  const allColumns = [
    { key: 'title', label: '招考职位', width: 160 },
    { key: 'department', label: '部门', width: 180 },
    { key: 'hiring_unit', label: '用人司局', width: 160 },
    { key: 'province', label: '省份', width: 100 },
    { key: 'city', label: '城市', width: 100 },
    { key: 'year', label: '年份', width: 70 },
    { key: 'institution_level', label: '机构层级', width: 110 },
    { key: 'education', label: '学历', width: 110 },
    { key: 'major', label: '专业要求', width: 150 },
    { key: 'exam_category', label: '考试类别', width: 160 },
    { key: 'recruitment_count', label: '招录', width: 60 },
    { key: 'political_status', label: '政治面貌', width: 90 },
    { key: 'work_experience', label: '基层经历', width: 100 },
    { key: 'interview_ratio', label: '面试比例', width: 90 },
    { key: 'position_attribute', label: '职位属性', width: 100 },
  ];

  useEffect(() => {
    const saved = localStorage.getItem('guokao_position_columns');
    if (saved) {
      setVisibleColumns(JSON.parse(saved));
    } else {
      setVisibleColumns(['title', 'department', 'hiring_unit', 'province', 'city', 'institution_level', 'education', 'recruitment_count', 'political_status', 'work_experience']);
    }
  }, []);

  const saveColumnConfig = () => {
    localStorage.setItem('guokao_position_columns', JSON.stringify(visibleColumns));
    setColumnSettingOpen(false);
  };

  // 筛选选项（锁定 exam_type='国考'）
  const { data: filterOptions } = useQuery({
    queryKey: ['guokao-filters', year],
    queryFn: () => positionApi.filterOptions({ year, exam_type: '国考' }),
  });

  // 统计
  const { data: stats } = useQuery({
    queryKey: ['guokao-stats', year],
    queryFn: () => positionApi.stats({ year, exam_type: '国考' }),
  });

  const { data: analysisData } = useQuery({
    queryKey: ['position-analysis', selectedPosition?.id],
    queryFn: () => selectedPosition ? positionApi.analysis(selectedPosition.id) : null,
    enabled: !!selectedPosition,
  });

  // 浏览模式数据
  const { data: browseData, isLoading: browseLoading } = useQuery({
    queryKey: ['guokao-positions', params, search, year, province, city, education, examCategory, institutionLevel, sortBy, sortOrder],
    queryFn: () => positionApi.list({
      ...params, search: search || undefined, year, exam_type: '国考',
      province, city, education, exam_category: examCategory,
      institution_level: institutionLevel,
      sort_by: sortBy, sort_order: sortOrder,
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
        exam_type: '国考',
        education: conditions.education,
        major: conditions.major,
        political_status: conditions.political_status,
        work_years: conditions.work_years,
        gender: conditions.gender,
        province, institution_level: institutionLevel,
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

  useEffect(() => {
    if (selectionMode && matchConditions) {
      handleMatch(matchConditions);
    }
  }, [params.page, params.page_size, sortBy, sortOrder, province, institutionLevel]);

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
        exam_type: '国考',
      });
      message.success('报告已生成并下载');
    } catch {
      message.error('报告生成失败');
    } finally {
      setReportLoading(false);
    }
  };

  const currentData = selectionMode ? matchResult : browseData;
  const isLoading = selectionMode ? matchLoading : browseLoading;

  // 列定义
  const columnMap: Record<string, any> = {
    title: {
      title: '招考职位', dataIndex: 'title', width: 160, ellipsis: true,
      render: (v: string, record: Position) => (
        <a onClick={() => { setSelectedPosition(record); setDetailOpen(true); }}>
          {v || record.department || '-'}
        </a>
      ),
    },
    department: { title: '部门', dataIndex: 'department', width: 180, ellipsis: true },
    hiring_unit: { title: '用人司局', dataIndex: 'hiring_unit', width: 160, ellipsis: true },
    province: { title: '省份', dataIndex: 'province', width: 100 },
    city: { title: '城市', dataIndex: 'city', width: 100 },
    year: { title: '年份', dataIndex: 'year', width: 70, align: 'center' },
    institution_level: {
      title: '机构层级', dataIndex: 'institution_level', width: 110,
      render: (v: string) => {
        const colors: Record<string, string> = { '中央': 'red', '省（副省）级': 'orange', '市（地）级': 'blue', '县（区）级及以下': 'green' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
    education: { title: '学历', dataIndex: 'education', width: 110, ellipsis: true },
    major: { title: '专业要求', dataIndex: 'major', width: 150, ellipsis: true },
    exam_category: { title: '考试类别', dataIndex: 'exam_category', width: 160, ellipsis: true },
    recruitment_count: { title: '招录', dataIndex: 'recruitment_count', width: 60, align: 'center' },
    political_status: { title: '政治面貌', dataIndex: 'political_status', width: 90 },
    work_experience: { title: '基层经历', dataIndex: 'work_experience', width: 100 },
    interview_ratio: { title: '面试比例', dataIndex: 'interview_ratio', width: 90 },
    position_attribute: { title: '职位属性', dataIndex: 'position_attribute', width: 100 },
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
          examType="国考"
          onYearChange={setMatchYear}
          onExamTypeChange={() => {}}
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
          examTypeOptions={['国考']}
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
              <Statistic title="覆盖省份" value={filterOptions?.provinces?.length || 0} prefix={<EnvironmentOutlined />} />
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
              onChange={(v) => { setYear(v); setProvince(undefined); setCity(undefined); setParams(p => ({ ...p, page: 1 })); }}
              options={(filterOptions?.years || []).map((y: number) => ({ value: y, label: `${y}年` }))}
            />
            <Input
              placeholder="搜索职位/部门/专业" prefix={<SearchOutlined />} style={{ width: 220 }} allowClear
              onChange={(e) => { setSearch(e.target.value); setParams(p => ({ ...p, page: 1 })); }}
            />
          </>
        )}
        <Select
          placeholder="选择省份" value={province} allowClear style={{ width: 180 }} showSearch
          onChange={(v) => { setProvince(v); setCity(undefined); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.provinces || []).map((p: string) => ({ value: p, label: p }))}
        />
        {province && filterOptions?.province_cities?.[province]?.length > 0 && (
          <Select
            placeholder="选择城市"
            value={city} allowClear style={{ width: 140 }} showSearch
            onChange={(v) => { setCity(v); setParams(p => ({ ...p, page: 1 })); }}
            options={filterOptions.province_cities[province].map((c: string) => ({ value: c, label: c }))}
          />
        )}
        <Select
          placeholder="机构层级" value={institutionLevel} allowClear style={{ width: 160 }}
          onChange={(v) => { setInstitutionLevel(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.institution_levels || []).map((l: string) => ({ value: l, label: l }))}
        />
        {!selectionMode && (
          <Select
            placeholder="学历要求" value={education} allowClear style={{ width: 140 }}
            onChange={(v) => { setEducation(v); setParams(p => ({ ...p, page: 1 })); }}
            options={(filterOptions?.educations || []).map((e: string) => ({ value: e, label: e }))}
          />
        )}
        <Select
          placeholder="考试类别" value={examCategory} allowClear style={{ width: 200 }}
          onChange={(v) => { setExamCategory(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.exam_categories || []).map((c: string) => ({ value: c, label: c }))}
        />
        <Button icon={<SettingOutlined />} onClick={() => setColumnSettingOpen(true)}>列设置</Button>
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
        scroll={{ x: 1200 }}
        size="middle"
      />

      {/* 岗位详情抽屉 */}
      <Drawer
        title={selectedPosition?.title || '岗位详情'}
        open={detailOpen}
        onClose={() => { setDetailOpen(false); setSelectedPosition(null); }}
        size={520}
      >
        {selectedPosition && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Card size="small" title="基本信息">
              <p><b>部门：</b>{selectedPosition.department || '-'}</p>
              <p><b>用人司局：</b>{selectedPosition.hiring_unit || '-'}</p>
              <p><b>职位代码：</b>{selectedPosition.position_code || '-'}</p>
              <p><b>机构层级：</b>{selectedPosition.institution_level || '-'}</p>
              <p><b>职位属性：</b>{selectedPosition.position_attribute || '-'}</p>
              <p><b>职位分布：</b>{selectedPosition.position_distribution || '-'}</p>
              <p><b>工作地点：</b>{selectedPosition.location || '-'}</p>
              <p><b>落户地点：</b>{selectedPosition.settlement_location || '-'}</p>
              <p><b>招录人数：</b>{selectedPosition.recruitment_count}</p>
              <p><b>面试比例：</b>{selectedPosition.interview_ratio || '-'}</p>
            </Card>
            <Card size="small" title="报考条件">
              <p><b>学历要求：</b>{selectedPosition.education || '-'}</p>
              <p><b>学位要求：</b>{selectedPosition.degree || '-'}</p>
              <p><b>专业要求：</b>{selectedPosition.major || '不限'}</p>
              <p><b>政治面貌：</b>{selectedPosition.political_status || '-'}</p>
              <p><b>基层工作年限：</b>{selectedPosition.work_experience || '-'}</p>
              <p><b>服务基层项目：</b>{selectedPosition.grassroots_project || '-'}</p>
              <p><b>其他要求：</b>{selectedPosition.other_requirements || '无'}</p>
              <p><b>备注：</b>{selectedPosition.remark || '无'}</p>
            </Card>
            <Card size="small" title="职位简介">
              <p>{selectedPosition.description || '暂无简介'}</p>
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
