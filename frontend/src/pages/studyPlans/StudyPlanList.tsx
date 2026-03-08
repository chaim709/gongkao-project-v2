import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Button, Space, Tag, Modal, Form, Input, DatePicker, Select, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studyPlanApi } from '../../api/studyPlans';
import type { StudyPlan } from '../../types/studyPlan';
import { studentApi } from '../../api/students';
import dayjs from 'dayjs';

export default function StudyPlanList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: students } = useQuery({
    queryKey: ['students-select'],
    queryFn: () => studentApi.list({ page: 1, page_size: 100 }),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['study-plans', params],
    queryFn: () => studyPlanApi.list(params),
  });

  const createMutation = useMutation({
    mutationFn: studyPlanApi.create,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['study-plans'] });
    },
    onError: () => message.error('创建失败'),
  });

  const handleCreate = async () => {
    const values = await form.validateFields();
    values.start_date = values.start_date.format('YYYY-MM-DD');
    if (values.end_date) values.end_date = values.end_date.format('YYYY-MM-DD');
    createMutation.mutate(values);
  };

  const columns = [
    { title: '计划名称', dataIndex: 'name', ellipsis: true },
    { title: '学员', dataIndex: 'student_name', width: 100, render: (v: string) => v || '-' },
    { title: '阶段', dataIndex: 'phase', width: 80, render: (v: string) => v || '-' },
    {
      title: '开始日期',
      dataIndex: 'start_date',
      width: 110,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD'),
    },
    {
      title: '结束日期',
      dataIndex: 'end_date',
      width: 110,
      render: (v: string) => (v ? dayjs(v).format('YYYY-MM-DD') : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          active: 'green',
          completed: 'blue',
          cancelled: 'default',
        };
        return <Tag color={colorMap[status]}>{status}</Tag>;
      },
    },
    {
      title: '任务进度',
      key: 'progress',
      width: 100,
      render: (_: any, record: StudyPlan) => (
        <span>
          {record.completed_task_count} / {record.task_count}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: StudyPlan) => (
        <Space>
          <Button type="link" size="small" onClick={() => navigate(`/study-plans/${record.id}`)}>
            详情
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Select
            placeholder="按学员筛选"
            allowClear
            style={{ width: 200 }}
            onChange={(v) => setParams((prev) => ({ ...prev, page: 1, student_id: v }))}
            options={(students?.items || []).map((s: any) => ({ value: s.id, label: s.name }))}
          />
          <Select
            placeholder="按状态筛选"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => setParams((prev) => ({ ...prev, page: 1, status: v }))}
            options={[
              { value: 'active', label: '进行中' },
              { value: 'completed', label: '已完成' },
              { value: 'cancelled', label: '已取消' },
            ]}
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormOpen(true)}>
          新建计划
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: data?.total || 0,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => setParams((prev) => ({ ...prev, page, page_size: pageSize })),
        }}
        scroll={{ x: 900 }}
      />

      <Modal
        title="新建学习计划"
        open={formOpen}
        onOk={handleCreate}
        onCancel={() => setFormOpen(false)}
        confirmLoading={createMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="student_id" label="学员" rules={[{ required: true, message: '请选择学员' }]}>
            <Select
              placeholder="选择学员"
              options={(students?.items || []).map((s: any) => ({ value: s.id, label: s.name }))}
            />
          </Form.Item>
          <Form.Item name="name" label="计划名称" rules={[{ required: true, message: '请输入计划名称' }]}>
            <Input placeholder="如：国考冲刺计划" />
          </Form.Item>
          <Form.Item name="phase" label="阶段">
            <Select
              placeholder="选择阶段"
              allowClear
              options={[
                { value: '基础', label: '基础' },
                { value: '强化', label: '强化' },
                { value: '冲刺', label: '冲刺' },
              ]}
            />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="start_date" label="开始日期" rules={[{ required: true, message: '请选择开始日期' }]}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="end_date" label="结束日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="计划说明" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
