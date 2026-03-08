import { useState } from 'react';
import { Table, Button, Space, Tag, Select, DatePicker, Popconfirm, message, Tabs } from 'antd';
import { PlusOutlined, ReloadOutlined, BellOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supervisionApi } from '../../api/supervision';
import type { SupervisionLog, SupervisionLogListParams } from '../../types/supervision';
import SupervisionLogForm from './SupervisionLogForm';
import ReminderList from './ReminderList';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type { ColumnsType } from 'antd/es/table';

const { RangePicker } = DatePicker;

const moodMap: Record<string, { text: string; color: string }> = {
  positive: { text: '积极', color: 'green' },
  stable: { text: '稳定', color: 'blue' },
  anxious: { text: '焦虑', color: 'orange' },
  down: { text: '低落', color: 'red' },
};

const studyStatusMap: Record<string, { text: string; color: string }> = {
  excellent: { text: '优秀', color: 'green' },
  good: { text: '良好', color: 'blue' },
  average: { text: '一般', color: 'orange' },
  poor: { text: '较差', color: 'red' },
};

const contactMethodMap: Record<string, string> = {
  phone: '电话',
  wechat: '微信',
  meeting: '面谈',
};

export default function SupervisionLogList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState<SupervisionLogListParams>({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['supervision-logs', params],
    queryFn: () => supervisionApi.list(params),
  });

  const deleteMutation = useMutation({
    mutationFn: supervisionApi.delete,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['supervision-logs'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleDateRange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    if (dates && dates[0] && dates[1]) {
      const start = dates[0].format('YYYY-MM-DD');
      const end = dates[1].format('YYYY-MM-DD');
      setParams((prev) => ({
        ...prev,
        page: 1,
        start_date: start,
        end_date: end,
      }));
    } else {
      setParams((prev) => ({ ...prev, page: 1, start_date: undefined, end_date: undefined }));
    }
  };

  const handleReset = () => {
    setParams({ page: 1, page_size: 20 });
  };

  const columns: ColumnsType<SupervisionLog> = [
    {
      title: '学员',
      dataIndex: 'student_name',
      width: 100,
    },
    {
      title: '日期',
      dataIndex: 'log_date',
      width: 110,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD'),
    },
    {
      title: '联系方式',
      dataIndex: 'contact_method',
      width: 90,
      render: (v: string) => contactMethodMap[v] || v || '-',
    },
    {
      title: '心情',
      dataIndex: 'mood',
      width: 80,
      render: (v: string) => {
        const info = moodMap[v];
        return info ? <Tag color={info.color}>{info.text}</Tag> : '-';
      },
    },
    {
      title: '学习状态',
      dataIndex: 'study_status',
      width: 90,
      render: (v: string) => {
        const info = studyStatusMap[v];
        return info ? <Tag color={info.color}>{info.text}</Tag> : '-';
      },
    },
    {
      title: '内容',
      dataIndex: 'content',
      ellipsis: true,
    },
    {
      title: '下次跟进',
      dataIndex: 'next_followup_date',
      width: 110,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-',
    },
    {
      title: '督学老师',
      dataIndex: 'supervisor_name',
      width: 100,
      render: (v: string) => v || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Popconfirm
          title="确认删除该日志？"
          onConfirm={() => deleteMutation.mutate(record.id)}
          okText="确认"
          cancelText="取消"
        >
          <Button type="link" size="small" danger>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  const logTab = (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <Space wrap>
          <RangePicker onChange={handleDateRange} />
          <Select
            placeholder="联系方式"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => setParams((prev) => ({ ...prev, page: 1, contact_method: v }))}
            options={[
              { value: 'phone', label: '电话' },
              { value: 'wechat', label: '微信' },
              { value: 'meeting', label: '面谈' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={handleReset}>重置</Button>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormOpen(true)}>
          新增日志
        </Button>
      </div>

      <Table<SupervisionLog>
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: data?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => setParams((prev) => ({ ...prev, page, page_size: pageSize })),
        }}
        scroll={{ x: 950 }}
        size="middle"
      />

      <SupervisionLogForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSuccess={() => {
          setFormOpen(false);
          queryClient.invalidateQueries({ queryKey: ['supervision-logs'] });
        }}
      />
    </div>
  );

  return (
    <Tabs
      defaultActiveKey="logs"
      items={[
        { key: 'logs', label: '督学日志', children: logTab },
        { key: 'reminders', label: <span><BellOutlined /> 跟进提醒</span>, children: <ReminderList onCreateLog={() => setFormOpen(true)} /> },
      ]}
    />
  );
}
