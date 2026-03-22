import { useState, useEffect } from 'react';
import { Input, Select, Space, Button, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, TeamOutlined, TrophyOutlined, UploadOutlined, SettingOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { positionApi } from '../../api/positions';
import SelectionModePanel from '../../components/positions/SelectionModePanel';
import PositionPageFrame from '../../components/positions/PositionPageFrame';
import {
  PositionAnalysisCard,
  PositionDetailInfoCard,
  PositionDetailStatsCard,
} from '../../components/positions/PositionDetailBlocks';
import usePositionPageState from '../../components/positions/usePositionPageState';
import type { Position, MatchSummary } from '../../types/position';
import type { ColumnsType } from 'antd/es/table';

const DEFAULT_VISIBLE_COLUMNS = [
  'title',
  'department',
  'city',
  'education',
  'exam_category',
  'recruitment_count',
  'successful_applicants',
  'competition_ratio',
  'min_interview_score',
  'max_interview_score',
];

export default function PositionList() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [year, setYear] = useState<number>();
  const [examType, setExamType] = useState<string>();
  const [city, setCity] = useState<string>();
  const [education, setEducation] = useState<string>();
  const [examCategory, setExamCategory] = useState<string>();
  const [difficulty, setDifficulty] = useState<string>();
  const [location, setLocation] = useState<string>();

  // ===== 选岗模式状态 =====
  const [selectionMode, setSelectionMode] = useState(false);
  const [matchYear, setMatchYear] = useState(2023);
  const [matchExamType, setMatchExamType] = useState('省考');
  const [matchResult, setMatchResult] = useState<any>(null);
  const [matchSummary, setMatchSummary] = useState<MatchSummary>();
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchConditions, setMatchConditions] = useState<any>(null);

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
    columnStorageKey: 'position_columns',
    defaultVisibleColumns: DEFAULT_VISIBLE_COLUMNS,
  });

  const clearSelectionState = () => {
    setMatchResult(null);
    setMatchSummary(undefined);
    setMatchConditions(null);
    clearSelectedRowKeys();
    closeCompare();
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
        <a onClick={() => openPositionDetail(record)}>
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
            onChange={(v) => { setYear(v); setCity(undefined); setEducation(undefined); setExamCategory(undefined); resetToFirstPage(); }}
            options={(filterOptions?.years || []).map((y: number) => ({ value: y, label: `${y}年` }))}
          />
          <Select
            placeholder="考试类型" value={examType} allowClear style={{ width: 140 }}
            onChange={(v) => { setExamType(v); setCity(undefined); setEducation(undefined); setExamCategory(undefined); resetToFirstPage(); }}
            options={(filterOptions?.exam_types || []).map((t: string) => ({ value: t, label: t === '省考' ? '江苏省考' : t }))}
          />
          <Input
            placeholder="搜索岗位/单位/专业" prefix={<SearchOutlined />} style={{ width: 220 }} allowClear
            onChange={(e) => { setSearch(e.target.value); resetToFirstPage(); }}
          />
        </>
      )}
      <Select
        placeholder="选择城市" value={city} allowClear style={{ width: 160 }} showSearch
        onChange={(v) => { setCity(v); setLocation(undefined); resetToFirstPage(); }}
        options={(filterOptions?.cities || []).map((c: string) => ({ value: c, label: c }))}
      />
      {city && filterOptions?.city_locations?.[city]?.length > 0 && (
        <Select
          placeholder="选择区县"
          value={location} allowClear style={{ width: 140 }} showSearch
          onChange={(v) => { setLocation(v); resetToFirstPage(); }}
          options={filterOptions.city_locations[city].map((l: string) => ({ value: l, label: l }))}
        />
      )}
      {!selectionMode && (
        <Select
          placeholder="学历要求" value={education} allowClear style={{ width: 140 }}
          onChange={(v) => { setEducation(v); resetToFirstPage(); }}
          options={[
            { value: '大专及以上', label: '大专及以上' },
            { value: '本科及以上', label: '本科及以上' },
            { value: '研究生及以上', label: '研究生及以上' },
          ]}
        />
      )}
      <Select
        placeholder="考试类别" value={examCategory} allowClear style={{ width: 160 }}
        onChange={(v) => { setExamCategory(v); resetToFirstPage(); }}
        options={(filterOptions?.exam_categories || []).map((c: string) => ({ value: c, label: c }))}
      />
      {!selectionMode && (
        <Select
          placeholder="难度等级" allowClear style={{ width: 110 }}
          onChange={(v) => { setDifficulty(v); resetToFirstPage(); }}
          options={[
            { value: 'easy', label: '容易' },
            { value: 'medium', label: '中等' },
            { value: 'hard', label: '困难' },
          ]}
        />
      )}
      <Button icon={<SettingOutlined />} onClick={openColumnSetting}>列设置</Button>
      <Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('/positions/import')} style={{ marginLeft: 'auto' }}>导入岗位</Button>
    </>
  );

  const detailContent = selectedPosition ? (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <PositionDetailInfoCard
        title="基本信息"
        items={[
          { key: 'department', label: '单位', value: selectedPosition.department || '-' },
          { key: 'position_code', label: '岗位代码', value: selectedPosition.position_code || '-' },
          { key: 'city', label: '地区', value: selectedPosition.city || '-' },
          { key: 'exam_category', label: '考试类别', value: selectedPosition.exam_category || '-' },
          { key: 'recruitment_count', label: '招录人数', value: selectedPosition.recruitment_count },
        ]}
      />
      <PositionDetailInfoCard
        title="报考条件"
        items={[
          { key: 'education', label: '学历要求', value: selectedPosition.education || '-' },
          { key: 'major', label: '专业要求', value: selectedPosition.major || '不限' },
          { key: 'other_requirements', label: '其他要求', value: selectedPosition.other_requirements || '无' },
          { key: 'remark', label: '备注', value: selectedPosition.remark || '无' },
        ]}
      />
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
            key: 'difficulty_level',
            title: '难度',
            value: difficultyLabel[selectedPosition.difficulty_level || ''] || '-',
          },
        ]}
      />
      {analysisData?.success ? <PositionAnalysisCard analysis={analysisData.data} /> : null}
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
          year={matchYear}
          examType={matchExamType}
          onYearChange={setMatchYear}
          onExamTypeChange={setMatchExamType}
          onMatch={handleMatch}
          onClear={() => {
            setSelectionMode(false);
            clearSelectionState();
          }}
          matchSummary={matchSummary}
          loading={matchLoading}
          yearOptions={filterOptions?.years || []}
          examTypeOptions={filterOptions?.exam_types || []}
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
          if (keys.length > 5) {
            message.warning('最多选择5个岗位进行对比');
            return;
          }
          setSelectedRowKeys(keys as number[]);
        },
      } : undefined}
      onTableChange={handleTableChange}
      pagination={buildPagination(currentData?.total || 0)}
      tableScroll={{ x: 1000 }}
      detailTitle={selectedPosition?.title || selectedPosition?.department || '岗位详情'}
      detailOpen={detailOpen}
      onDetailClose={closePositionDetail}
      detailDrawerSize={480}
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
