import { useState, useEffect } from 'react';
import { Card, Table, Select, Input, Tag, Badge, Modal, Button, Space, Row, Col, DatePicker, Descriptions } from 'antd';
import { SearchOutlined, EyeOutlined, LinkOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { recruitmentInfoApi } from '../../api/recruitmentInfo';
import type { RecruitmentInfo, RecruitmentInfoFilterOptions } from '../../types/recruitmentInfo';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

// 考试类型颜色映射
const examTypeColorMap: Record<string, string> = {
  '公务员': 'blue',
  '事业单位': 'green',
  '教师': 'orange',
  '国企': 'purple',
  '军队文职': 'red',
  '银行': 'cyan',
  '医疗': 'magenta',
};

export default function RecruitmentInfoList() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [examType, setExamType] = useState<string[]>([]);
  const [province, setProvince] = useState<string>();
  const [city, setCity] = useState<string>();
  const [status, setStatus] = useState<string>();
  const [keyword, setKeyword] = useState('');
  const [dateRange, setDateRange] = useState<[string, string] | undefined>();
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedInfo, setSelectedInfo] = useState<RecruitmentInfo | null>(null);
  const [filterOptions, setFilterOptions] = useState<RecruitmentInfoFilterOptions>({
    exam_types: [],
    provinces: [],
    cities: [],
    statuses: [],
  });

  // 加载筛选选项
  const { data: filterData } = useQuery({
    queryKey: ['recruitment-info-filters'],
    queryFn: () => recruitmentInfoApi.getFilters(),
  });

  useEffect(() => {
    if (filterData) {
      setFilterOptions(filterData as unknown as RecruitmentInfoFilterOptions);
    }
  }, [filterData]);

  // 加载列表数据
  const { data, isLoading } = useQuery({
    queryKey: ['recruitment-info', page, pageSize, examType, province, city, status, keyword, dateRange],
    queryFn: () => recruitmentInfoApi.getList({
      page,
      page_size: pageSize,
      exam_type: examType.length > 0 ? examType.join(',') : undefined,
      province,
      city,
      status,
      keyword: keyword || undefined,
      start_date: dateRange?.[0],
      end_date: dateRange?.[1],
    }),
  });

  const listData = data as any;

  // 解析附件
  const parseAttachments = (attachments: string): { name: string; url: string }[] => {
    try {
      return JSON.parse(attachments || '[]');
    } catch {
      return [];
    }
  };

  // 省份变更时清空城市
  const handleProvinceChange = (value: string | undefined) => {
    setProvince(value);
    setCity(undefined);
    setPage(1);
  };

  // 获取城市列表（可按省份过滤）
  const cityOptions = filterOptions.cities || [];

  const columns: ColumnsType<RecruitmentInfo> = [
    {
      title: '标题',
      dataIndex: 'title',
      width: 300,
      ellipsis: true,
      render: (v: string, record: RecruitmentInfo) => (
        <span>
          <a onClick={() => { setSelectedInfo(record); setDetailOpen(true); }}>
            {v || '-'}
          </a>
          {!record.content && <Tag color="orange" style={{ marginLeft: 4, fontSize: 10 }}>内容缺失</Tag>}
          {record.ai_summary && <Tag color="green" style={{ marginLeft: 4, fontSize: 10 }}>AI</Tag>}
        </span>
      ),
    },
    {
      title: '考试类型',
      dataIndex: 'exam_type',
      width: 100,
      align: 'center',
      render: (v: string) => (
        <Tag color={examTypeColorMap[v] || 'default'}>{v || '-'}</Tag>
      ),
    },
    {
      title: '地区',
      width: 140,
      render: (_: unknown, record: RecruitmentInfo) => {
        const parts = [record.province, record.city].filter(Boolean);
        return parts.join(' / ') || '-';
      },
    },
    {
      title: '招录人数',
      dataIndex: 'recruitment_count',
      width: 90,
      align: 'center',
      render: (v: number) => v || '-',
    },
    {
      title: '发布时间',
      dataIndex: 'publish_date',
      width: 110,
      align: 'center',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      align: 'center',
      render: (v: string) => (
        <Badge
          status={v === '报名中' ? 'success' : v === '即将开始' ? 'processing' : 'default'}
          text={v || '-'}
        />
      ),
    },
    {
      title: '操作',
      width: 160,
      align: 'center',
      render: (_: unknown, record: RecruitmentInfo) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => { setSelectedInfo(record); setDetailOpen(true); }}
          >
            查看详情
          </Button>
          {record.source_url && (
            <Button
              type="link"
              size="small"
              icon={<LinkOutlined />}
              href={record.source_url}
              target="_blank"
            >
              查看原文
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card title="招考公告" style={{ marginBottom: 16 }}>
        {/* 筛选区 */}
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={6} lg={4}>
            <Select
              placeholder="考试类型"
              value={examType.length > 0 ? examType : undefined}
              allowClear
              mode="multiple"
              maxTagCount={1}
              style={{ width: '100%' }}
              onChange={(v: string[]) => { setExamType(v || []); setPage(1); }}
              options={filterOptions.exam_types.map(t => ({ value: t, label: t }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Select
              placeholder="省份"
              value={province}
              allowClear
              showSearch
              style={{ width: '100%' }}
              onChange={handleProvinceChange}
              options={filterOptions.provinces.map(p => ({ value: p, label: p }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Select
              placeholder="城市"
              value={city}
              allowClear
              showSearch
              style={{ width: '100%' }}
              onChange={(v) => { setCity(v); setPage(1); }}
              options={cityOptions.map(c => ({ value: c, label: c }))}
            />
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Select
              placeholder="状态"
              value={status}
              allowClear
              style={{ width: '100%' }}
              onChange={(v) => { setStatus(v); setPage(1); }}
              options={filterOptions.statuses.map(s => ({ value: s, label: s }))}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={5}>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['开始日期', '结束日期']}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  setDateRange([dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')]);
                } else {
                  setDateRange(undefined);
                }
                setPage(1);
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Input.Search
              placeholder="搜索标题/关键词"
              prefix={<SearchOutlined />}
              allowClear
              onSearch={(v) => { setKeyword(v); setPage(1); }}
              onChange={(e) => { if (!e.target.value) { setKeyword(''); setPage(1); } }}
            />
          </Col>
        </Row>

        {/* 数据表格 */}
        <Table<RecruitmentInfo>
          columns={columns}
          dataSource={listData?.items || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: listData?.total || 0,
            showTotal: (total) => `共 ${total} 条公告`,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100'],
            onChange: (p, ps) => { setPage(p); setPageSize(ps); },
          }}
          scroll={{ x: 1000 }}
          size="middle"
        />
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title={selectedInfo?.title || '公告详情'}
        open={detailOpen}
        onCancel={() => { setDetailOpen(false); setSelectedInfo(null); }}
        footer={[
          selectedInfo?.source_url && (
            <Button key="source" type="link" href={selectedInfo.source_url} target="_blank" icon={<LinkOutlined />}>
              查看原文
            </Button>
          ),
          <Button key="close" onClick={() => { setDetailOpen(false); setSelectedInfo(null); }}>
            关闭
          </Button>,
        ]}
        width={720}
      >
        {selectedInfo && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="考试类型">
                <Tag color={examTypeColorMap[selectedInfo.exam_type] || 'default'}>
                  {selectedInfo.exam_type || '-'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Badge
                  status={selectedInfo.status === '报名中' ? 'success' : selectedInfo.status === '即将开始' ? 'processing' : 'default'}
                  text={selectedInfo.status || '-'}
                />
              </Descriptions.Item>
              <Descriptions.Item label="省份">{selectedInfo.province || '-'}</Descriptions.Item>
              <Descriptions.Item label="城市">{selectedInfo.city || '-'}</Descriptions.Item>
              <Descriptions.Item label="招录人数">{selectedInfo.recruitment_count || '-'}</Descriptions.Item>
              <Descriptions.Item label="来源站点">{selectedInfo.source_site || '-'}</Descriptions.Item>
              <Descriptions.Item label="发布日期">{selectedInfo.publish_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="报名开始">{selectedInfo.registration_start || '-'}</Descriptions.Item>
              <Descriptions.Item label="报名截止">{selectedInfo.registration_end || '-'}</Descriptions.Item>
              <Descriptions.Item label="考试日期">{selectedInfo.exam_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="创建时间" span={2}>{selectedInfo.created_at || '-'}</Descriptions.Item>
            </Descriptions>

            {/* 附件列表 */}
            {parseAttachments(selectedInfo.attachments).length > 0 && (
              <Card size="small" title="附件列表">
                <Space direction="vertical">
                  {parseAttachments(selectedInfo.attachments).map((att, idx) => (
                    <a key={idx} href={att.url} target="_blank" rel="noopener noreferrer">
                      <LinkOutlined style={{ marginRight: 4 }} />
                      {att.name || `附件 ${idx + 1}`}
                    </a>
                  ))}
                </Space>
              </Card>
            )}

            {/* AI 分析摘要 */}
            {selectedInfo.ai_summary && (
              <Card size="small" title="AI 分析摘要" style={{ background: '#f6ffed', borderColor: '#b7eb8f' }}>
                <div
                  style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
                  dangerouslySetInnerHTML={{
                    __html: selectedInfo.ai_summary
                      .replace(/## /g, '<strong style="font-size:15px">')
                      .replace(/\n(?=- )/g, '</strong>\n')
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  }}
                />
              </Card>
            )}

            {/* 正文内容 */}
            {selectedInfo.content && (
              <Card size="small" title="公告内容">
                <div
                  style={{ maxHeight: 400, overflow: 'auto' }}
                  dangerouslySetInnerHTML={{ __html: selectedInfo.content }}
                />
              </Card>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
}
