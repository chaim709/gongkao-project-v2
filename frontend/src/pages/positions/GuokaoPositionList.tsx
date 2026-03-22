import { useState, useEffect } from 'react';
import { Input, Select, Tag, Space, Button, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, TeamOutlined, TrophyOutlined, SettingOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { positionApi } from '../../api/positions';
import SelectionModePanel from '../../components/positions/SelectionModePanel';
import PositionPageFrame from '../../components/positions/PositionPageFrame';
import {
  PositionAnalysisCard,
  PositionDetailInfoCard,
  PositionDetailTextCard,
} from '../../components/positions/PositionDetailBlocks';
import usePositionPageState from '../../components/positions/usePositionPageState';
import type { Position, MatchSummary } from '../../types/position';
import type { ColumnsType } from 'antd/es/table';

const DEFAULT_VISIBLE_COLUMNS = [
  'title',
  'department',
  'hiring_unit',
  'province',
  'city',
  'institution_level',
  'education',
  'recruitment_count',
  'political_status',
  'work_experience',
];

export default function GuokaoPositionList() {
  const [search, setSearch] = useState('');
  const [year, setYear] = useState<number>();
  const [province, setProvince] = useState<string>();
  const [city, setCity] = useState<string>();
  const [education, setEducation] = useState<string>();
  const [examCategory, setExamCategory] = useState<string>();
  const [institutionLevel, setInstitutionLevel] = useState<string>();

  // 选岗模式状态
  const [selectionMode, setSelectionMode] = useState(false);
  const [matchYear, setMatchYear] = useState(2025);
  const [matchResult, setMatchResult] = useState<any>(null);
  const [matchSummary, setMatchSummary] = useState<MatchSummary>();
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchConditions, setMatchConditions] = useState<any>(null);

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
    columnStorageKey: 'guokao_position_columns',
    defaultVisibleColumns: DEFAULT_VISIBLE_COLUMNS,
  });

  const clearSelectionState = () => {
    setMatchResult(null);
    setMatchSummary(undefined);
    setMatchConditions(null);
    clearSelectedRowKeys();
    closeCompare();
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
        <a onClick={() => openPositionDetail(record)}>
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

  const statsCards = [
    { key: 'total_positions', title: '岗位总数', value: stats?.total_positions || 0, prefix: <TrophyOutlined /> },
    { key: 'total_recruitment', title: '招录总人数', value: stats?.total_recruitment || 0, prefix: <TeamOutlined /> },
    { key: 'coverage', title: '覆盖省份', value: filterOptions?.provinces?.length || 0, prefix: <EnvironmentOutlined /> },
    { key: 'filtered_total', title: '筛选结果', value: currentData?.total || 0, suffix: '条' },
  ];

  const filters = (
    <>
      {!selectionMode && (
        <>
          <Select
            placeholder="选择年份" value={year} allowClear style={{ width: 110 }}
            onChange={(v) => { setYear(v); setProvince(undefined); setCity(undefined); resetToFirstPage(); }}
            options={(filterOptions?.years || []).map((y: number) => ({ value: y, label: `${y}年` }))}
          />
          <Input
            placeholder="搜索职位/部门/专业" prefix={<SearchOutlined />} style={{ width: 220 }} allowClear
            onChange={(e) => { setSearch(e.target.value); resetToFirstPage(); }}
          />
        </>
      )}
      <Select
        placeholder="选择省份" value={province} allowClear style={{ width: 180 }} showSearch
        onChange={(v) => { setProvince(v); setCity(undefined); resetToFirstPage(); }}
        options={(filterOptions?.provinces || []).map((p: string) => ({ value: p, label: p }))}
      />
      {province && filterOptions?.province_cities?.[province]?.length > 0 && (
        <Select
          placeholder="选择城市"
          value={city} allowClear style={{ width: 140 }} showSearch
          onChange={(v) => { setCity(v); resetToFirstPage(); }}
          options={filterOptions.province_cities[province].map((c: string) => ({ value: c, label: c }))}
        />
      )}
      <Select
        placeholder="机构层级" value={institutionLevel} allowClear style={{ width: 160 }}
        onChange={(v) => { setInstitutionLevel(v); resetToFirstPage(); }}
        options={(filterOptions?.institution_levels || []).map((l: string) => ({ value: l, label: l }))}
      />
      {!selectionMode && (
        <Select
          placeholder="学历要求" value={education} allowClear style={{ width: 140 }}
          onChange={(v) => { setEducation(v); resetToFirstPage(); }}
          options={(filterOptions?.educations || []).map((e: string) => ({ value: e, label: e }))}
        />
      )}
      <Select
        placeholder="考试类别" value={examCategory} allowClear style={{ width: 200 }}
        onChange={(v) => { setExamCategory(v); resetToFirstPage(); }}
        options={(filterOptions?.exam_categories || []).map((c: string) => ({ value: c, label: c }))}
      />
      <Button icon={<SettingOutlined />} onClick={openColumnSetting}>列设置</Button>
    </>
  );

  const detailContent = selectedPosition ? (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <PositionDetailInfoCard
        title="基本信息"
        items={[
          { key: 'department', label: '部门', value: selectedPosition.department || '-' },
          { key: 'hiring_unit', label: '用人司局', value: selectedPosition.hiring_unit || '-' },
          { key: 'position_code', label: '职位代码', value: selectedPosition.position_code || '-' },
          { key: 'institution_level', label: '机构层级', value: selectedPosition.institution_level || '-' },
          { key: 'position_attribute', label: '职位属性', value: selectedPosition.position_attribute || '-' },
          { key: 'position_distribution', label: '职位分布', value: selectedPosition.position_distribution || '-' },
          { key: 'location', label: '工作地点', value: selectedPosition.location || '-' },
          { key: 'settlement_location', label: '落户地点', value: selectedPosition.settlement_location || '-' },
          { key: 'recruitment_count', label: '招录人数', value: selectedPosition.recruitment_count },
          { key: 'interview_ratio', label: '面试比例', value: selectedPosition.interview_ratio || '-' },
        ]}
      />
      <PositionDetailInfoCard
        title="报考条件"
        items={[
          { key: 'education', label: '学历要求', value: selectedPosition.education || '-' },
          { key: 'degree', label: '学位要求', value: selectedPosition.degree || '-' },
          { key: 'major', label: '专业要求', value: selectedPosition.major || '不限' },
          { key: 'political_status', label: '政治面貌', value: selectedPosition.political_status || '-' },
          { key: 'work_experience', label: '基层工作年限', value: selectedPosition.work_experience || '-' },
          { key: 'grassroots_project', label: '服务基层项目', value: selectedPosition.grassroots_project || '-' },
          { key: 'other_requirements', label: '其他要求', value: selectedPosition.other_requirements || '无' },
          { key: 'remark', label: '备注', value: selectedPosition.remark || '无' },
        ]}
      />
      <PositionDetailTextCard title="职位简介" content={selectedPosition.description} emptyText="暂无简介" />
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
          examType="国考"
          onYearChange={setMatchYear}
          onExamTypeChange={() => {}}
          onMatch={handleMatch}
          onClear={() => {
            setSelectionMode(false);
            clearSelectionState();
          }}
          matchSummary={matchSummary}
          loading={matchLoading}
          yearOptions={filterOptions?.years || []}
          examTypeOptions={['国考']}
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
      tableScroll={{ x: 1200 }}
      detailTitle={selectedPosition?.title || '岗位详情'}
      detailOpen={detailOpen}
      onDetailClose={closePositionDetail}
      detailDrawerSize={520}
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
