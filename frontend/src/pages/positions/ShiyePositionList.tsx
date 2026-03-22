import { useState, useEffect } from 'react';
import { Input, Select, Tag, Space, Button, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, TeamOutlined, TrophyOutlined, SettingOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { positionApi } from '../../api/positions';
import ShiyeSelectionPanel, { type ShiyeSelectionConditions } from '../../components/positions/ShiyeSelectionPanel';
import PositionPageFrame from '../../components/positions/PositionPageFrame';
import {
  PositionDetailInfoCard,
  PositionDetailStatsCard,
  PositionDetailTagListCard,
  PositionDetailTextCard,
} from '../../components/positions/PositionDetailBlocks';
import usePositionPageState from '../../components/positions/usePositionPageState';
import type { Position, MatchResult, MatchSummary } from '../../types/position';
import type { ColumnsType } from 'antd/es/table';

const DEFAULT_VISIBLE_COLUMNS = [
  'city',
  'title',
  'match_source',
  'eligibility_status',
  'recommendation_tier',
  'post_nature',
  'exam_category',
  'education',
  'major',
  'recruitment_count',
  'apply_count',
  'competition_ratio',
  'risk_tags',
  'remark',
];

const COLUMN_STORAGE_KEY = 'shiye_position_columns_v2';

const EXAM_CATEGORY_COLORS: Record<string, string> = {
  管理类: 'blue',
  工勤类: 'orange',
  工勤技能类: 'orange',
  法律类: 'green',
  其他专技类: 'green',
  专技类: 'green',
  计算机类: 'cyan',
  岗位专业知识: 'cyan',
  学科专业知识: 'geekblue',
};

const FILTER_LABEL_OVERRIDES: Record<string, string> = {
  待确认: '待确认（原表未规范）',
};

function formatEducationText(value?: string) {
  if (!value) return '-';

  const normalized = value.replace(/\s+/g, '');
  if (normalized.includes('不限')) return '不限';
  if (normalized.includes('博士')) return normalized.includes('以上') ? '博士及以上' : '博士';
  if (normalized.includes('研究生') || normalized.includes('硕士')) {
    return normalized.includes('以上') ? '研究生及以上' : '研究生';
  }
  if (normalized.includes('本科')) {
    return normalized.includes('以上') ? '本科及以上' : '本科';
  }
  if (normalized.includes('大专') || normalized.includes('专科') || normalized.includes('高职')) {
    return normalized.includes('以上') ? '大专及以上' : '大专';
  }

  return normalized;
}

function formatFilterLabel(value: string) {
  return FILTER_LABEL_OVERRIDES[value] || value;
}

function buildSelectionFilterOptions(values: string[] | undefined, options?: {
  excludeUnlimited?: boolean;
}) {
  return (values || [])
    .filter((item) => !options?.excludeUnlimited || item !== '不限')
    .map((item) => ({ value: item, label: formatFilterLabel(item) }));
}

export default function ShiyePositionList() {
  const [search, setSearch] = useState('');
  const [year, setYear] = useState<number>();
  const [city, setCity] = useState<string>();
  const [location, setLocation] = useState<string>();
  const [education, setEducation] = useState<string>();
  const [examCategory, setExamCategory] = useState<string>();
  const [postNatures, setPostNatures] = useState<string[]>([]);
  const [fundingSource, setFundingSource] = useState<string>();
  const [recruitmentTarget, setRecruitmentTarget] = useState<string>();
  const [excludedRiskTags, setExcludedRiskTags] = useState<string[]>([]);
  const [recommendationTier, setRecommendationTier] = useState<string>();

  // 选岗模式状态
  const [selectionMode, setSelectionMode] = useState(false);
  const [matchYear, setMatchYear] = useState(2025);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [matchSummary, setMatchSummary] = useState<MatchSummary>();
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchConditions, setMatchConditions] = useState<ShiyeSelectionConditions | null>(null);

  const [reportLoading, setReportLoading] = useState(false);

  const allColumns = [
    { key: 'city', label: '地市', width: 80 },
    { key: 'title', label: '岗位名称', width: 140 },
    { key: 'match_source', label: '匹配来源', width: 120 },
    { key: 'eligibility_status', label: '匹配状态', width: 110 },
    { key: 'recommendation_tier', label: '推荐层级', width: 100 },
    { key: 'post_nature', label: '岗位性质', width: 100 },
    { key: 'exam_category', label: '笔试类别', width: 90 },
    { key: 'education', label: '学历', width: 110 },
    { key: 'major', label: '专业要求', width: 150 },
    { key: 'recruitment_count', label: '招录', width: 60 },
    { key: 'apply_count', label: '报名人数', width: 90 },
    { key: 'competition_ratio', label: '竞争比', width: 80 },
    { key: 'risk_tags', label: '风险标签', width: 180 },
    { key: 'remark', label: '备注', width: 150 },
    { key: 'department', label: '招聘单位', width: 180 },
    { key: 'location', label: '区县', width: 90 },
    { key: 'supervising_dept', label: '主管部门', width: 160 },
    { key: 'funding_source', label: '经费来源', width: 100 },
    { key: 'recruitment_target', label: '招聘对象', width: 100 },
    { key: 'min_interview_score', label: '进面最低分', width: 100 },
    { key: 'max_interview_score', label: '进面最高分', width: 100 },
    { key: 'exam_ratio', label: '开考比例', width: 90 },
    { key: 'position_level', label: '岗位等级', width: 100 },
    { key: 'description', label: '岗位说明', width: 150 },
    { key: 'degree', label: '学位', width: 90 },
    { key: 'exam_weight_ratio', label: '笔面试占比', width: 130 },
    { key: 'interview_ratio', label: '面试比例', width: 100 },
  ];

  const {
    params,
    resetToFirstPage,
    detailOpen,
    selectedPosition,
    openPositionDetail,
    closePositionDetail,
    sortBy,
    sortOrder,
    handleTableChange,
    columnSettingOpen,
    openColumnSetting,
    closeColumnSetting,
    visibleColumns,
    setVisibleColumns,
    saveColumnConfig,
    selectedRowKeys,
    setSelectedRowKeys,
    compareOpen,
    openCompare,
    closeCompare,
    clearSelectedRowKeys,
    buildPagination,
  } = usePositionPageState<Position>({
    columnStorageKey: COLUMN_STORAGE_KEY,
    defaultVisibleColumns: DEFAULT_VISIBLE_COLUMNS,
  });

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

  const buildSelectionCriteria = (conditions: ShiyeSelectionConditions) => ({
    year: matchYear,
    education: conditions.education,
    major: conditions.major,
    political_status: conditions.political_status,
    work_years: conditions.work_years,
    gender: conditions.gender,
    city,
    location,
    funding_sources: fundingSource ? [fundingSource] : [],
    recruitment_targets: recruitmentTarget ? [recruitmentTarget] : [],
    post_natures: postNatures,
    preferred_post_natures: postNatures,
    excluded_risk_tags: excludedRiskTags,
    recommendation_tier: recommendationTier,
    include_manual_review: conditions.include_manual_review ?? true,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const buildSelectionPayload = (conditions: ShiyeSelectionConditions) => ({
    ...buildSelectionCriteria(conditions),
    page: params.page,
    page_size: params.page_size,
  });

  const clearSelectionState = () => {
    setMatchResult(null);
    setMatchSummary(undefined);
    setMatchConditions(null);
    setPostNatures([]);
    setFundingSource(undefined);
    setRecruitmentTarget(undefined);
    setExcludedRiskTags([]);
    setRecommendationTier(undefined);
    clearSelectedRowKeys();
    closeCompare();
  };

  const handleMatch = async (conditions: ShiyeSelectionConditions) => {
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
  }, [selectionMode, matchYear, params.page, params.page_size, sortBy, sortOrder, city, location, fundingSource, recruitmentTarget, postNatures, excludedRiskTags, recommendationTier]);

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
        <a onClick={() => openPositionDetail(record)}>
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
        if (!v) return '-';
        let color = EXAM_CATEGORY_COLORS[v];
        if (!color) {
          if (v.includes('管理')) color = 'blue';
          else if (v.includes('工勤')) color = 'orange';
          else if (v.includes('法律') || v.includes('专技') || v.includes('经济') || v.includes('计算机')) color = 'green';
          else color = 'default';
        }
        return <Tag color={color}>{v}</Tag>;
      },
    },
    education: {
      title: '学历',
      dataIndex: 'education',
      width: 110,
      ellipsis: true,
      render: (v: string) => {
        const label = formatEducationText(v);
        return (
          <span title={v || label}>
            {label}
          </span>
        );
      },
    },
    major: { title: '专业要求', dataIndex: 'major', width: 150, ellipsis: true },
    recruitment_count: { title: '招录', dataIndex: 'recruitment_count', width: 60, align: 'center' },
    funding_source: {
      title: '经费来源', dataIndex: 'funding_source', width: 100,
      render: (v: string, record: Position) => {
        const colors: Record<string, string> = { '全额拨款': 'green', '差额拨款': 'orange', '自收自支': 'red' };
        const label = record.normalized_funding_source || v;
        return label ? <Tag color={colors[label] || 'default'}>{formatFilterLabel(label)}</Tag> : '-';
      },
    },
    recruitment_target: {
      title: '招聘对象',
      dataIndex: 'recruitment_target',
      width: 100,
      render: (v: string, record: Position) =>
        formatFilterLabel(record.normalized_recruitment_target || v || '-'),
    },
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
            onChange={(v) => { setYear(v); setCity(undefined); setLocation(undefined); resetToFirstPage(); }}
            options={(filterOptions?.years || []).map((y: number) => ({ value: y, label: `${y}年` }))}
          />
          <Input
            placeholder="搜索岗位/单位/专业" prefix={<SearchOutlined />} style={{ width: 220 }} allowClear
            onChange={(e) => { setSearch(e.target.value); resetToFirstPage(); }}
          />
        </>
      )}
      <Select
        placeholder="选择地市" value={city} allowClear style={{ width: 130 }} showSearch
        onChange={(v) => { setCity(v); setLocation(undefined); resetToFirstPage(); }}
        options={((selectionMode ? shiyeFilterOptions?.cities : filterOptions?.cities) || []).map((c: string) => ({ value: c, label: c }))}
      />
      {city && !selectionMode && filterOptions?.city_locations?.[city]?.length > 0 && (
        <Select
          placeholder="选择区县" value={location} allowClear style={{ width: 130 }} showSearch
          onChange={(v) => { setLocation(v); resetToFirstPage(); }}
          options={filterOptions.city_locations[city].map((l: string) => ({ value: l, label: l }))}
        />
      )}
      {city && selectionMode && (
        <Select
          placeholder="选择区县" value={location} allowClear style={{ width: 130 }} showSearch
          onChange={(v) => { setLocation(v); resetToFirstPage(); }}
          options={(
            shiyeFilterOptions?.city_locations?.[city] ||
            shiyeFilterOptions?.locations ||
            []
          ).map((l: string) => ({ value: l, label: l }))}
        />
      )}
      {selectionMode && (
        <Select
          mode="multiple"
          placeholder="岗位性质偏好"
          value={postNatures}
          allowClear
          style={{ width: 200 }}
          onChange={(v) => { setPostNatures(v); resetToFirstPage(); }}
          options={buildSelectionFilterOptions(
            shiyeFilterOptions?.post_natures || ['管理岗', '专技岗', '工勤岗'],
          )}
        />
      )}
      {selectionMode && (
        <Select
          placeholder="招聘对象限制"
          value={recruitmentTarget}
          allowClear
          style={{ width: 160 }}
          onChange={(v) => { setRecruitmentTarget(v === '不限' ? undefined : v); resetToFirstPage(); }}
          options={buildSelectionFilterOptions(
            shiyeFilterOptions?.recruitment_targets,
            { excludeUnlimited: true },
          )}
        />
      )}
      {selectionMode && (
        <Select
          placeholder="经费来源限制"
          value={fundingSource}
          allowClear
          style={{ width: 170 }}
          onChange={(v) => { setFundingSource(v === '不限' ? undefined : v); resetToFirstPage(); }}
          options={buildSelectionFilterOptions(
            shiyeFilterOptions?.funding_sources,
            { excludeUnlimited: true },
          )}
        />
      )}
      {selectionMode && (
        <Select
          mode="multiple"
          placeholder="风险避雷"
          value={excludedRiskTags}
          allowClear
          style={{ width: 220 }}
          onChange={(v) => { setExcludedRiskTags(v); resetToFirstPage(); }}
          options={buildSelectionFilterOptions(shiyeFilterOptions?.risk_tags)}
        />
      )}
      {selectionMode && (
        <Select
          placeholder="结果层级筛选"
          value={recommendationTier}
          allowClear
          style={{ width: 150 }}
          onChange={(v) => { setRecommendationTier(v); resetToFirstPage(); }}
          options={['冲刺', '稳妥', '保底'].map((tier) => ({ value: tier, label: tier }))}
        />
      )}
      {!selectionMode && (
        <Select
          placeholder="笔试类别" value={examCategory} allowClear style={{ width: 120 }}
          onChange={(v) => { setExamCategory(v); resetToFirstPage(); }}
          options={(filterOptions?.exam_categories || []).map((c: string) => ({ value: c, label: c }))}
        />
      )}
      {!selectionMode && (
        <Select
          placeholder="经费来源" value={fundingSource} allowClear style={{ width: 120 }}
          onChange={(v) => { setFundingSource(v); resetToFirstPage(); }}
          options={(filterOptions?.funding_sources || []).map((f: string) => ({ value: f, label: f }))}
        />
      )}
      {!selectionMode && (
        <Select
          placeholder="招聘对象" value={recruitmentTarget} allowClear style={{ width: 120 }}
          onChange={(v) => { setRecruitmentTarget(v); resetToFirstPage(); }}
          options={(filterOptions?.recruitment_targets || []).map((r: string) => ({ value: r, label: r }))}
        />
      )}
      {!selectionMode && (
        <Select
          placeholder="学历要求" value={education} allowClear style={{ width: 140 }}
          onChange={(v) => { setEducation(v); resetToFirstPage(); }}
          options={(filterOptions?.educations || []).map((e: string) => ({ value: e, label: e }))}
        />
      )}
      <Button icon={<SettingOutlined />} onClick={openColumnSetting}>列设置</Button>
    </>
  );

  const detailContent = selectedPosition ? (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <PositionDetailInfoCard
        title="基本信息"
        items={[
          { key: 'department', label: '招聘单位', value: selectedPosition.department || '-' },
          { key: 'supervising_dept', label: '主管部门', value: selectedPosition.supervising_dept || '-' },
          { key: 'position_code', label: '岗位代码', value: selectedPosition.position_code || '-' },
          { key: 'city', label: '地市', value: selectedPosition.city || '-' },
          { key: 'location', label: '区县', value: selectedPosition.location || '-' },
          { key: 'funding_source', label: '经费来源', value: selectedPosition.normalized_funding_source || selectedPosition.funding_source || '-' },
          { key: 'exam_category', label: '笔试类别', value: selectedPosition.exam_category || '-' },
          { key: 'recruitment_count', label: '招录人数', value: selectedPosition.recruitment_count },
          { key: 'exam_ratio', label: '开考比例', value: selectedPosition.exam_ratio || '-' },
          { key: 'recruitment_target', label: '招聘对象', value: selectedPosition.normalized_recruitment_target || selectedPosition.recruitment_target || '-' },
        ]}
      />
      {selectionMode && (
        <PositionDetailInfoCard
          title="匹配结果"
          items={[
            {
              key: 'eligibility_status',
              label: '匹配状态',
              value:
                selectedPosition.eligibility_status === 'hard_pass'
                  ? '硬匹配'
                  : selectedPosition.eligibility_status === 'manual_review_needed'
                    ? '需人工确认'
                    : '-',
            },
            { key: 'match_source', label: '匹配来源', value: selectedPosition.match_source || '-' },
            { key: 'recommendation_tier', label: '推荐层级', value: selectedPosition.recommendation_tier || '-' },
            { key: 'post_nature', label: '岗位性质', value: selectedPosition.post_nature || '-' },
            { key: 'risk_tags', label: '风险标签', value: selectedPosition.risk_tags?.length ? selectedPosition.risk_tags.join('、') : '无' },
            { key: 'manual_review_flags', label: '人工确认', value: selectedPosition.manual_review_flags?.length ? selectedPosition.manual_review_flags.join('、') : '无' },
          ]}
        />
      )}
      <PositionDetailInfoCard
        title="报考条件"
        items={[
          { key: 'education', label: '学历要求', value: selectedPosition.education || '-' },
          { key: 'major', label: '专业要求', value: selectedPosition.major || '不限' },
          { key: 'other_requirements', label: '其他条件', value: selectedPosition.other_requirements || '无' },
          { key: 'remark', label: '备注', value: selectedPosition.remark || '无' },
        ]}
      />
      {selectionMode ? <PositionDetailTagListCard title="匹配依据" items={selectedPosition.match_reasons} /> : null}
      {selectionMode ? <PositionDetailTagListCard title="排序依据" items={selectedPosition.sort_reasons} tagColor="blue" /> : null}
      {selectionMode ? <PositionDetailTagListCard title="推荐分层依据" items={selectedPosition.recommendation_reasons} tagColor="purple" /> : null}
      <PositionDetailStatsCard
        title="竞争数据"
        items={[
          { key: 'apply_count', title: '报名人数', value: selectedPosition.apply_count ?? '-' },
          {
            key: 'competition_ratio',
            title: '竞争比',
            value: selectedPosition.competition_ratio ? `${selectedPosition.competition_ratio.toFixed(0)}:1` : '-',
          },
          {
            key: 'min_interview_score',
            title: '进面最低分',
            value: selectedPosition.min_interview_score ? selectedPosition.min_interview_score.toFixed(1) : '-',
          },
        ]}
      />
      {selectedPosition.description ? (
        <PositionDetailTextCard title="岗位描述" content={selectedPosition.description} />
      ) : null}
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
        <ShiyeSelectionPanel
          year={matchYear}
          onYearChange={setMatchYear}
          onMatch={handleMatch}
          onClear={() => { setSelectionMode(false); clearSelectionState(); }}
          matchSummary={matchSummary}
          loading={matchLoading}
          yearOptions={filterOptions?.years || []}
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
      onTableChange={handleTableChange}
      pagination={buildPagination(currentData?.total || 0)}
      tableScroll={{ x: 1200 }}
      detailTitle={selectedPosition?.title || '岗位详情'}
      detailOpen={detailOpen}
      onDetailClose={closePositionDetail}
      detailDrawerSize="large"
      detailContent={detailContent}
      selectedPositionIds={selectedRowKeys}
      compareOpen={compareOpen}
      onCloseCompare={closeCompare}
      onOpenCompare={openCompare}
      onClearSelected={clearSelectedRowKeys}
      onGenerateReport={handleGenerateReport}
      reportLoading={reportLoading}
      columnSettingOpen={columnSettingOpen}
      onSaveColumnSetting={saveColumnConfig}
      onCloseColumnSetting={closeColumnSetting}
      allColumns={allColumns}
      visibleColumns={visibleColumns}
      onVisibleColumnsChange={setVisibleColumns}
    />
  );
}
