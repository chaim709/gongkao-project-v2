import { useState, useEffect } from 'react';
import { Table, Input, Select, Tag, Card, Row, Col, Statistic, Space, Drawer, Button, Modal, Checkbox, Switch, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, TeamOutlined, TrophyOutlined, SettingOutlined, AimOutlined, SwapOutlined, FilePdfOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { positionApi } from '../../api/positions';
import SelectionModePanel from '../../components/positions/SelectionModePanel';
import PositionCompare from '../../components/positions/PositionCompare';
import type { Position, MatchSummary } from '../../types/position';
import type { ColumnsType } from 'antd/es/table';

export default function ShiyePositionList() {
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [search, setSearch] = useState('');
  const [year, setYear] = useState<number>();
  const [city, setCity] = useState<string>();
  const [location, setLocation] = useState<string>();
  const [education, setEducation] = useState<string>();
  const [examCategory, setExamCategory] = useState<string>();
  const [fundingSource, setFundingSource] = useState<string>();
  const [recruitmentTarget, setRecruitmentTarget] = useState<string>();
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

  const allColumns = [
    { key: 'title', label: '岗位名称', width: 140 },
    { key: 'department', label: '招聘单位', width: 180 },
    { key: 'supervising_dept', label: '主管部门', width: 160 },
    { key: 'city', label: '地市', width: 80 },
    { key: 'location', label: '区县', width: 90 },
    { key: 'exam_category', label: '笔试类别', width: 90 },
    { key: 'position_level', label: '岗位等级', width: 100 },
    { key: 'description', label: '岗位说明', width: 150 },
    { key: 'education', label: '学历', width: 110 },
    { key: 'degree', label: '学位', width: 90 },
    { key: 'major', label: '专业要求', width: 150 },
    { key: 'recruitment_count', label: '招录', width: 60 },
    { key: 'funding_source', label: '经费来源', width: 100 },
    { key: 'recruitment_target', label: '招聘对象', width: 100 },
    { key: 'apply_count', label: '报名人数', width: 90 },
    { key: 'competition_ratio', label: '竞争比', width: 80 },
    { key: 'min_interview_score', label: '进面最低分', width: 100 },
    { key: 'max_interview_score', label: '进面最高分', width: 100 },
    { key: 'exam_ratio', label: '开考比例', width: 90 },
    { key: 'exam_weight_ratio', label: '笔面试占比', width: 130 },
    { key: 'interview_ratio', label: '面试比例', width: 100 },
    { key: 'remark', label: '备注', width: 150 },
  ];

  useEffect(() => {
    const saved = localStorage.getItem('shiye_position_columns');
    if (saved) {
      setVisibleColumns(JSON.parse(saved));
    } else {
      setVisibleColumns(['title', 'department', 'city', 'location', 'exam_category', 'education', 'recruitment_count', 'apply_count', 'competition_ratio', 'min_interview_score', 'max_interview_score']);
    }
  }, []);

  const saveColumnConfig = () => {
    localStorage.setItem('shiye_position_columns', JSON.stringify(visibleColumns));
    setColumnSettingOpen(false);
  };

  const { data: filterOptions } = useQuery({
    queryKey: ['shiye-filters', year],
    queryFn: () => positionApi.filterOptions({ year, exam_type: '事业单位' }),
  });

  const { data: stats } = useQuery({
    queryKey: ['shiye-stats', year],
    queryFn: () => positionApi.stats({ year, exam_type: '事业单位' }),
  });

  const { data: browseData, isLoading: browseLoading } = useQuery({
    queryKey: ['shiye-positions', params, search, year, city, location, education, examCategory, fundingSource, recruitmentTarget, sortBy, sortOrder],
    queryFn: () => positionApi.list({
      ...params, search: search || undefined, year, exam_type: '事业单位',
      city, location, education, exam_category: examCategory,
      funding_source: fundingSource, recruitment_target: recruitmentTarget,
      sort_by: sortBy, sort_order: sortOrder,
    }),
    enabled: !selectionMode,
  });

  const handleMatch = async (conditions: any) => {
    setMatchLoading(true);
    setMatchConditions(conditions);
    try {
      const result = await positionApi.match({
        year: matchYear,
        exam_type: '事业单位',
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

  useEffect(() => {
    if (selectionMode && matchConditions) {
      handleMatch(matchConditions);
    }
  }, [params.page, params.page_size, sortBy, sortOrder, city, examCategory]);

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
        exam_type: '事业单位',
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

  const columnMap: Record<string, any> = {
    title: {
      title: '岗位名称', dataIndex: 'title', width: 140, ellipsis: true,
      render: (v: string, record: Position) => (
        <a onClick={() => { setSelectedPosition(record); setDetailOpen(true); }}>
          {v || record.department || '-'}
        </a>
      ),
    },
    department: { title: '招聘单位', dataIndex: 'department', width: 180, ellipsis: true },
    supervising_dept: { title: '主管部门', dataIndex: 'supervising_dept', width: 160, ellipsis: true },
    city: { title: '地市', dataIndex: 'city', width: 80 },
    location: { title: '区县', dataIndex: 'location', width: 90 },
    exam_category: {
      title: '笔试类别', dataIndex: 'exam_category', width: 90,
      render: (v: string) => {
        const colors: Record<string, string> = { '管理类': 'blue', '技术类': 'green', '工勤技能类': 'orange' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
    education: { title: '学历', dataIndex: 'education', width: 110, ellipsis: true },
    major: { title: '专业要求', dataIndex: 'major', width: 150, ellipsis: true },
    recruitment_count: { title: '招录', dataIndex: 'recruitment_count', width: 60, align: 'center' },
    funding_source: {
      title: '经费来源', dataIndex: 'funding_source', width: 100,
      render: (v: string) => {
        const colors: Record<string, string> = { '全额拨款': 'green', '差额拨款': 'orange', '自收自支': 'red' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
    recruitment_target: { title: '招聘对象', dataIndex: 'recruitment_target', width: 100 },
    apply_count: {
      title: '报名人数', dataIndex: 'apply_count', width: 90, align: 'center',
      render: (v: number) => v ?? '-',
      sorter: true,
      sortOrder: sortBy === 'apply_count' ? (sortOrder === 'asc' ? 'ascend' : 'descend') : undefined,
    },
    competition_ratio: {
      title: '竞争比', dataIndex: 'competition_ratio', width: 80, align: 'center',
      render: (v: number) => v ? `${v.toFixed(0)}:1` : '-',
      sorter: true,
      sortOrder: sortBy === 'competition_ratio' ? (sortOrder === 'asc' ? 'ascend' : 'descend') : undefined,
    },
    min_interview_score: {
      title: '进面最低分', dataIndex: 'min_interview_score', width: 100, align: 'center',
      render: (v: number) => v ? v.toFixed(1) : '-',
    },
    max_interview_score: {
      title: '进面最高分', dataIndex: 'max_interview_score', width: 100, align: 'center',
      render: (v: number) => v ? v.toFixed(1) : '-',
    },
    exam_ratio: { title: '开考比例', dataIndex: 'exam_ratio', width: 90 },
    position_level: { title: '岗位等级', dataIndex: 'position_level', width: 100, ellipsis: true },
    description: { title: '岗位说明', dataIndex: 'description', width: 150, ellipsis: true },
    degree: { title: '学位', dataIndex: 'degree', width: 90 },
    exam_weight_ratio: { title: '笔面试占比', dataIndex: 'exam_weight_ratio', width: 130, ellipsis: true },
    interview_ratio: { title: '面试比例', dataIndex: 'interview_ratio', width: 100 },
    remark: { title: '备注', dataIndex: 'remark', width: 150, ellipsis: true },
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
              if (!checked) { setMatchResult(null); setMatchSummary(undefined); setMatchConditions(null); }
            }}
            checkedChildren="选岗模式"
            unCheckedChildren="浏览模式"
          />
          {selectionMode && <Tag color="green">选岗模式已开启 - 输入学员条件后自动匹配可报岗位</Tag>}
        </Space>
      </div>

      {selectionMode && (
        <SelectionModePanel
          year={matchYear} examType="事业单位"
          onYearChange={setMatchYear} onExamTypeChange={() => {}}
          onMatch={handleMatch}
          onClear={() => { setSelectionMode(false); setMatchResult(null); setMatchSummary(undefined); setMatchConditions(null); }}
          matchSummary={matchSummary} loading={matchLoading}
          yearOptions={filterOptions?.years || []} examTypeOptions={['事业单位']}
        />
      )}

      {!selectionMode && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small"><Statistic title="岗位总数" value={stats?.total_positions || 0} prefix={<TrophyOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card size="small"><Statistic title="招录总人数" value={stats?.total_recruitment || 0} prefix={<TeamOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card size="small"><Statistic title="覆盖地区" value={stats?.by_city?.length || 0} prefix={<EnvironmentOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card size="small"><Statistic title="筛选结果" value={currentData?.total || 0} suffix="条" /></Card>
          </Col>
        </Row>
      )}

      {/* 筛选区 */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {!selectionMode && (
          <>
            <Select
              placeholder="选择年份" value={year} allowClear style={{ width: 110 }}
              onChange={(v) => { setYear(v); setCity(undefined); setLocation(undefined); setParams(p => ({ ...p, page: 1 })); }}
              options={(filterOptions?.years || []).map((y: number) => ({ value: y, label: `${y}年` }))}
            />
            <Input
              placeholder="搜索岗位/单位/专业" prefix={<SearchOutlined />} style={{ width: 220 }} allowClear
              onChange={(e) => { setSearch(e.target.value); setParams(p => ({ ...p, page: 1 })); }}
            />
          </>
        )}
        <Select
          placeholder="选择地市" value={city} allowClear style={{ width: 130 }} showSearch
          onChange={(v) => { setCity(v); setLocation(undefined); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.cities || []).map((c: string) => ({ value: c, label: c }))}
        />
        {city && filterOptions?.city_locations?.[city]?.length > 0 && (
          <Select
            placeholder="选择区县" value={location} allowClear style={{ width: 130 }} showSearch
            onChange={(v) => { setLocation(v); setParams(p => ({ ...p, page: 1 })); }}
            options={filterOptions.city_locations[city].map((l: string) => ({ value: l, label: l }))}
          />
        )}
        <Select
          placeholder="笔试类别" value={examCategory} allowClear style={{ width: 120 }}
          onChange={(v) => { setExamCategory(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.exam_categories || []).map((c: string) => ({ value: c, label: c }))}
        />
        <Select
          placeholder="经费来源" value={fundingSource} allowClear style={{ width: 120 }}
          onChange={(v) => { setFundingSource(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.funding_sources || []).map((f: string) => ({ value: f, label: f }))}
        />
        <Select
          placeholder="招聘对象" value={recruitmentTarget} allowClear style={{ width: 120 }}
          onChange={(v) => { setRecruitmentTarget(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.recruitment_targets || []).map((r: string) => ({ value: r, label: r }))}
        />
        {!selectionMode && (
          <Select
            placeholder="学历要求" value={education} allowClear style={{ width: 140 }}
            onChange={(v) => { setEducation(v); setParams(p => ({ ...p, page: 1 })); }}
            options={(filterOptions?.educations || []).map((e: string) => ({ value: e, label: e }))}
          />
        )}
        <Button icon={<SettingOutlined />} onClick={() => setColumnSettingOpen(true)}>列设置</Button>
      </div>

      <Table<Position>
        columns={columns}
        dataSource={currentData?.items || []}
        rowKey="id"
        loading={isLoading}
        rowSelection={selectionMode ? {
          selectedRowKeys,
          onChange: (keys) => {
            if (keys.length > 5) { message.warning('最多选择5个岗位进行对比'); return; }
            setSelectedRowKeys(keys as number[]);
          },
        } : undefined}
        onChange={(_pagination, _filters, sorter) => {
          if (!Array.isArray(sorter) && sorter.field) {
            const field = String(sorter.field);
            if (sorter.order) { setSortBy(field); setSortOrder(sorter.order === 'ascend' ? 'asc' : 'desc'); }
            else { setSortBy(undefined); setSortOrder(undefined); }
          }
        }}
        pagination={{
          current: params.page, pageSize: params.page_size,
          total: currentData?.total || 0,
          showTotal: (total) => `共 ${total} 个岗位`,
          showSizeChanger: true, pageSizeOptions: ['20', '50', '100'],
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
        width={520}
      >
        {selectedPosition && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Card size="small" title="基本信息">
              <p><b>招聘单位：</b>{selectedPosition.department || '-'}</p>
              <p><b>主管部门：</b>{selectedPosition.supervising_dept || '-'}</p>
              <p><b>岗位代码：</b>{selectedPosition.position_code || '-'}</p>
              <p><b>地市：</b>{selectedPosition.city || '-'}</p>
              <p><b>区县：</b>{selectedPosition.location || '-'}</p>
              <p><b>经费来源：</b>{selectedPosition.funding_source || '-'}</p>
              <p><b>笔试类别：</b>{selectedPosition.exam_category || '-'}</p>
              <p><b>招录人数：</b>{selectedPosition.recruitment_count}</p>
              <p><b>开考比例：</b>{selectedPosition.exam_ratio || '-'}</p>
              <p><b>招聘对象：</b>{selectedPosition.recruitment_target || '-'}</p>
            </Card>
            <Card size="small" title="报考条件">
              <p><b>学历要求：</b>{selectedPosition.education || '-'}</p>
              <p><b>专业要求：</b>{selectedPosition.major || '不限'}</p>
              <p><b>其他条件：</b>{selectedPosition.other_requirements || '无'}</p>
            </Card>
            <Card size="small" title="竞争数据">
              <Row gutter={16}>
                <Col span={8}><Statistic title="报名人数" value={selectedPosition.apply_count ?? '-'} /></Col>
                <Col span={8}>
                  <Statistic title="竞争比" value={selectedPosition.competition_ratio ? `${selectedPosition.competition_ratio.toFixed(0)}:1` : '-'} />
                </Col>
                <Col span={8}><Statistic title="进面最低分" value={selectedPosition.min_interview_score ? selectedPosition.min_interview_score.toFixed(1) : '-'} /></Col>
              </Row>
            </Card>
            {selectedPosition.description && (
              <Card size="small" title="岗位描述">
                <p>{selectedPosition.description}</p>
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
            <Button type="primary" icon={<SwapOutlined />} disabled={selectedRowKeys.length < 2} onClick={() => setCompareOpen(true)}>对比岗位</Button>
            <Button icon={<FilePdfOutlined />} loading={reportLoading} onClick={handleGenerateReport}>生成报告</Button>
          </Space>
        </div>
      )}

      <PositionCompare open={compareOpen} onClose={() => setCompareOpen(false)} positionIds={selectedRowKeys} />

      <Modal title="列设置" open={columnSettingOpen} onOk={saveColumnConfig} onCancel={() => setColumnSettingOpen(false)} width={500}>
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          <Checkbox.Group value={visibleColumns} onChange={(values) => setVisibleColumns(values as string[])} style={{ width: '100%' }}>
            <Row gutter={[16, 16]}>
              {allColumns.map(col => (
                <Col span={12} key={col.key}><Checkbox value={col.key}>{col.label}</Checkbox></Col>
              ))}
            </Row>
          </Checkbox.Group>
        </div>
      </Modal>
    </div>
  );
}
