import { useState, useEffect } from 'react';
import { Input, Select, Tag, Card, Row, Col, Statistic, Space, Button, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, TeamOutlined, TrophyOutlined, SettingOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { positionApi } from '../../api/positions';
import SelectionModePanel from '../../components/positions/SelectionModePanel';
import PositionPageFrame from '../../components/positions/PositionPageFrame';
import type { Position, MatchResult, MatchSummary } from '../../types/position';
import type { ColumnsType } from 'antd/es/table';

interface SelectionConditions {
  education: string;
  major: string;
  political_status?: string;
  work_years?: number;
  gender?: string;
  student_id?: number;
}

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
  const [postNatures, setPostNatures] = useState<string[]>([]);
  const [recommendationTiers, setRecommendationTiers] = useState<string[]>([]);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [sortBy, setSortBy] = useState<string>();
  const [sortOrder, setSortOrder] = useState<string>();
  const [columnSettingOpen, setColumnSettingOpen] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);

  // 选岗模式状态
  const [selectionMode, setSelectionMode] = useState(false);
  const [matchYear, setMatchYear] = useState(2025);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [matchSummary, setMatchSummary] = useState<MatchSummary>();
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchConditions, setMatchConditions] = useState<SelectionConditions | null>(null);

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
    { key: 'eligibility_status', label: '匹配状态', width: 110 },
    { key: 'match_source', label: '匹配来源', width: 120 },
    { key: 'recommendation_tier', label: '推荐层级', width: 100 },
    { key: 'post_nature', label: '岗位性质', width: 100 },
    { key: 'risk_tags', label: '风险标签', width: 180 },
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
      setVisibleColumns(['title', 'department', 'city', 'location', 'match_source', 'recommendation_tier', 'post_nature', 'risk_tags', 'exam_category', 'education', 'recruitment_count', 'apply_count', 'competition_ratio', 'min_interview_score']);
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

  const { data: shiyeFilterOptions } = useQuery({
    queryKey: ['shiye-selection-filters', selectionMode ? matchYear : year],
    queryFn: () => positionApi.shiyeFilterOptions({ year: selectionMode ? matchYear : (year || 2025) }),
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

  const buildSelectionCriteria = (conditions: SelectionConditions) => ({
    year: matchYear,
    education: conditions.education,
    major: conditions.major,
    political_status: conditions.political_status,
    work_years: conditions.work_years,
    gender: conditions.gender,
    city,
    location,
    exam_category: examCategory,
    funding_source: fundingSource,
    recruitment_target: recruitmentTarget,
    post_natures: postNatures,
    recommendation_tiers: recommendationTiers,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const buildSelectionPayload = (conditions: SelectionConditions) => ({
    ...buildSelectionCriteria(conditions),
    page: params.page,
    page_size: params.page_size,
  });

  const clearSelectionState = () => {
    setMatchResult(null);
    setMatchSummary(undefined);
    setMatchConditions(null);
    setRecommendationTiers([]);
    setSelectedRowKeys([]);
    setCompareOpen(false);
  };

  const handleMatch = async (conditions: SelectionConditions) => {
    setMatchLoading(true);
    setMatchConditions(conditions);
    try {
      const selectionResult = await positionApi.shiyeSelectionSearch(buildSelectionPayload(conditions));
      setMatchResult(selectionResult);
      setMatchSummary(selectionResult.summary);
    } catch {
      // ignore
    } finally {
      setMatchLoading(false);
    }
  };

  useEffect(() => {
    if (selectionMode && matchConditions) {
      void handleMatch(matchConditions);
    }
  }, [selectionMode, matchYear, params.page, params.page_size, sortBy, sortOrder, city, location, examCategory, fundingSource, recruitmentTarget, postNatures, recommendationTiers]);

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
        exam_type: '事业单位',
        ...buildSelectionCriteria(matchConditions || { education: '', major: '' }),
        include_manual_review: true,
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
    eligibility_status: {
      title: '匹配状态', dataIndex: 'eligibility_status', width: 110,
      render: (v: string) => {
        if (v === 'hard_pass') return <Tag color="green">硬匹配</Tag>;
        if (v === 'manual_review_needed') return <Tag color="gold">需人工确认</Tag>;
        return '-';
      },
    },
    match_source: {
      title: '匹配来源', dataIndex: 'match_source', width: 120,
      render: (v: string) => {
        const colors: Record<string, string> = {
          '专业精确匹配': 'green',
          '专业大类匹配': 'blue',
          '专业不限': 'cyan',
          '专业需人工确认': 'gold',
        };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
    recommendation_tier: {
      title: '推荐层级', dataIndex: 'recommendation_tier', width: 100,
      render: (v: string) => {
        const colors: Record<string, string> = { '冲刺': 'red', '稳妥': 'green', '保底': 'blue' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
    post_nature: {
      title: '岗位性质', dataIndex: 'post_nature', width: 100,
      render: (v: string) => {
        const colors: Record<string, string> = { '管理岗': 'blue', '专技岗': 'green', '工勤岗': 'orange', '待确认': 'default' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
    risk_tags: {
      title: '风险标签', dataIndex: 'risk_tags', width: 180,
      render: (tags: string[]) => tags?.length ? (
        <Space size={[0, 4]} wrap>
          {tags.map(tag => <Tag key={tag} color={tag === '高竞争' || tag === '高分线' ? 'red' : 'orange'}>{tag}</Tag>)}
        </Space>
      ) : '-',
    },
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

  const statsCards = [
    { key: 'total_positions', title: '岗位总数', value: stats?.total_positions || 0, prefix: <TrophyOutlined /> },
    { key: 'total_recruitment', title: '招录总人数', value: stats?.total_recruitment || 0, prefix: <TeamOutlined /> },
    { key: 'coverage', title: '覆盖地区', value: stats?.by_city?.length || 0, prefix: <EnvironmentOutlined /> },
    { key: 'filtered_total', title: '筛选结果', value: currentData?.total || 0, suffix: '条' },
  ];

  const filters = (
    <>
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
        options={((selectionMode ? shiyeFilterOptions?.cities : filterOptions?.cities) || []).map((c: string) => ({ value: c, label: c }))}
      />
      {city && !selectionMode && filterOptions?.city_locations?.[city]?.length > 0 && (
        <Select
          placeholder="选择区县" value={location} allowClear style={{ width: 130 }} showSearch
          onChange={(v) => { setLocation(v); setParams(p => ({ ...p, page: 1 })); }}
          options={filterOptions.city_locations[city].map((l: string) => ({ value: l, label: l }))}
        />
      )}
      {city && selectionMode && (
        <Select
          placeholder="选择区县" value={location} allowClear style={{ width: 130 }} showSearch
          onChange={(v) => { setLocation(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(shiyeFilterOptions?.locations || []).map((l: string) => ({ value: l, label: l }))}
        />
      )}
      <Select
        placeholder="笔试类别" value={examCategory} allowClear style={{ width: 120 }}
        onChange={(v) => { setExamCategory(v); setParams(p => ({ ...p, page: 1 })); }}
        options={((selectionMode ? shiyeFilterOptions?.exam_categories : filterOptions?.exam_categories) || []).map((c: string) => ({ value: c, label: c }))}
      />
      <Select
        placeholder="经费来源" value={fundingSource} allowClear style={{ width: 120 }}
        onChange={(v) => { setFundingSource(v); setParams(p => ({ ...p, page: 1 })); }}
        options={((selectionMode ? shiyeFilterOptions?.funding_sources : filterOptions?.funding_sources) || []).map((f: string) => ({ value: f, label: f }))}
      />
      <Select
        placeholder="招聘对象" value={recruitmentTarget} allowClear style={{ width: 120 }}
        onChange={(v) => { setRecruitmentTarget(v); setParams(p => ({ ...p, page: 1 })); }}
        options={((selectionMode ? shiyeFilterOptions?.recruitment_targets : filterOptions?.recruitment_targets) || []).map((r: string) => ({ value: r, label: r }))}
      />
      {selectionMode && (
        <Select
          mode="multiple"
          placeholder="岗位性质偏好"
          value={postNatures}
          allowClear
          style={{ width: 220 }}
          onChange={(v) => { setPostNatures(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(shiyeFilterOptions?.post_natures || ['管理岗', '专技岗', '工勤岗', '待确认']).map((nature: string) => ({ value: nature, label: nature }))}
        />
      )}
      {selectionMode && (
        <Select
          mode="multiple"
          placeholder="推荐层级筛选"
          value={recommendationTiers}
          allowClear
          style={{ width: 220 }}
          onChange={(v) => { setRecommendationTiers(v); setParams(p => ({ ...p, page: 1 })); }}
          options={['冲刺', '稳妥', '保底'].map((tier) => ({ value: tier, label: tier }))}
        />
      )}
      {!selectionMode && (
        <Select
          placeholder="学历要求" value={education} allowClear style={{ width: 140 }}
          onChange={(v) => { setEducation(v); setParams(p => ({ ...p, page: 1 })); }}
          options={(filterOptions?.educations || []).map((e: string) => ({ value: e, label: e }))}
        />
      )}
      <Button icon={<SettingOutlined />} onClick={() => setColumnSettingOpen(true)}>列设置</Button>
    </>
  );

  const detailContent = selectedPosition ? (
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
      {selectionMode && (
        <Card size="small" title="匹配结果">
          <p><b>匹配状态：</b>{selectedPosition.eligibility_status === 'hard_pass' ? '硬匹配' : selectedPosition.eligibility_status === 'manual_review_needed' ? '需人工确认' : '-'}</p>
          <p><b>匹配来源：</b>{selectedPosition.match_source || '-'}</p>
          <p><b>推荐层级：</b>{selectedPosition.recommendation_tier || '-'}</p>
          <p><b>岗位性质：</b>{selectedPosition.post_nature || '-'}</p>
          <p><b>风险标签：</b>{selectedPosition.risk_tags?.length ? selectedPosition.risk_tags.join('、') : '无'}</p>
          <p><b>人工确认：</b>{selectedPosition.manual_review_flags?.length ? selectedPosition.manual_review_flags.join('、') : '无'}</p>
        </Card>
      )}
      <Card size="small" title="报考条件">
        <p><b>学历要求：</b>{selectedPosition.education || '-'}</p>
        <p><b>专业要求：</b>{selectedPosition.major || '不限'}</p>
        <p><b>其他条件：</b>{selectedPosition.other_requirements || '无'}</p>
        <p><b>备注：</b>{selectedPosition.remark || '无'}</p>
      </Card>
      {selectionMode && selectedPosition.match_reasons?.length ? (
        <Card size="small" title="匹配依据">
          <Space size={[0, 8]} wrap>
            {selectedPosition.match_reasons.map(reason => <Tag key={reason}>{reason}</Tag>)}
          </Space>
        </Card>
      ) : null}
      {selectionMode && selectedPosition.sort_reasons?.length ? (
        <Card size="small" title="排序依据">
          <Space size={[0, 8]} wrap>
            {selectedPosition.sort_reasons.map(reason => <Tag key={reason} color="blue">{reason}</Tag>)}
          </Space>
        </Card>
      ) : null}
      {selectionMode && selectedPosition.recommendation_reasons?.length ? (
        <Card size="small" title="推荐分层依据">
          <Space size={[0, 8]} wrap>
            {selectedPosition.recommendation_reasons.map(reason => <Tag key={reason} color="purple">{reason}</Tag>)}
          </Space>
        </Card>
      ) : null}
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
  ) : null;

  return (
    <PositionPageFrame
      selectionMode={selectionMode}
      onSelectionModeChange={(checked) => {
        setSelectionMode(checked);
        if (!checked) {
          clearSelectionState();
        }
      }}
      selectionPanel={selectionMode ? (
        <SelectionModePanel
          year={matchYear} examType="事业单位"
          onYearChange={setMatchYear} onExamTypeChange={() => {}}
          onMatch={handleMatch}
          onClear={() => { setSelectionMode(false); clearSelectionState(); }}
          matchSummary={matchSummary} loading={matchLoading}
          yearOptions={filterOptions?.years || []} examTypeOptions={['事业单位']}
        />
      ) : null}
      stats={statsCards}
      filters={filters}
      columns={columns}
      dataSource={currentData?.items || []}
      loading={isLoading}
      rowSelection={selectionMode ? {
        selectedRowKeys,
        onChange: (keys) => {
          if (keys.length > 5) { message.warning('最多选择5个岗位进行对比'); return; }
          setSelectedRowKeys(keys as number[]);
        },
      } : undefined}
      onTableChange={(_pagination, _filters, sorter) => {
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
      tableScroll={{ x: 1200 }}
      detailTitle={selectedPosition?.title || '岗位详情'}
      detailOpen={detailOpen}
      onDetailClose={() => { setDetailOpen(false); setSelectedPosition(null); }}
      detailDrawerSize="large"
      detailContent={detailContent}
      selectedPositionIds={selectedRowKeys}
      compareOpen={compareOpen}
      onCloseCompare={() => setCompareOpen(false)}
      onOpenCompare={() => setCompareOpen(true)}
      onClearSelected={() => setSelectedRowKeys([])}
      onGenerateReport={handleGenerateReport}
      reportLoading={reportLoading}
      columnSettingOpen={columnSettingOpen}
      onSaveColumnSetting={saveColumnConfig}
      onCloseColumnSetting={() => setColumnSettingOpen(false)}
      allColumns={allColumns}
      visibleColumns={visibleColumns}
      onVisibleColumnsChange={setVisibleColumns}
    />
  );
}
