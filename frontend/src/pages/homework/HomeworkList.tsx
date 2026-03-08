import { useState } from 'react';
import { Table, Button, Space, Tag, Popconfirm, message, Modal, Form, Input, Select, DatePicker, InputNumber } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { homeworkApi } from '../../api/homework';
import { courseApi } from '../../api/courses';
import type { Homework, HomeworkListParams, Submission } from '../../types/homework';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';

export default function HomeworkList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState<HomeworkListParams>({ page: 1, page_size: 20 });
  const [createOpen, setCreateOpen] = useState(false);
  const [submissionsHwId, setSubmissionsHwId] = useState<number | null>(null);
  const [reviewingSub, setReviewingSub] = useState<Submission | null>(null);
  const [form] = Form.useForm();
  const [reviewForm] = Form.useForm();

  const { data: courses } = useQuery({
    queryKey: ['courses-select'],
    queryFn: () => courseApi.list({ page: 1, page_size: 100 }),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['homework', params],
    queryFn: () => homeworkApi.list(params),
  });

  const { data: submissions, isLoading: subsLoading } = useQuery({
    queryKey: ['submissions', submissionsHwId],
    queryFn: () => homeworkApi.listSubmissions(submissionsHwId!),
    enabled: !!submissionsHwId,
  });

  const createMutation = useMutation({
    mutationFn: homeworkApi.create,
    onSuccess: () => { message.success('发布成功'); setCreateOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['homework'] }); },
    onError: () => message.error('发布失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: homeworkApi.delete,
    onSuccess: () => { message.success('删除成功'); queryClient.invalidateQueries({ queryKey: ['homework'] }); },
  });

  const reviewMutation = useMutation({
    mutationFn: ({ subId, data }: { subId: number; data: { score: number; feedback?: string } }) => homeworkApi.review(subId, data),
    onSuccess: () => {
      message.success('批改完成');
      setReviewingSub(null);
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      queryClient.invalidateQueries({ queryKey: ['homework'] });
    },
  });

  const handleCreate = async () => {
    const values = await form.validateFields();
    if (values.due_date) values.due_date = values.due_date.toISOString();
    createMutation.mutate(values);
  };

  const handleReview = async () => {
    const values = await reviewForm.validateFields();
    reviewMutation.mutate({ subId: reviewingSub!.id, data: values });
  };

  const columns: ColumnsType<Homework> = [
    { title: '标题', dataIndex: 'title', ellipsis: true },
    { title: '课程', dataIndex: 'course_name', width: 120, render: (v: string) => v || '-' },
    {
      title: '截止时间', dataIndex: 'due_date', width: 140,
      render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm') : '无',
    },
    {
      title: '提交/批改', key: 'stats', width: 110,
      render: (_, r) => <span>{r.submission_count} / <Tag color={r.reviewed_count >= r.submission_count && r.submission_count > 0 ? 'green' : 'default'}>{r.reviewed_count}</Tag></span>,
    },
    {
      title: '操作', key: 'action', width: 160, fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" onClick={() => setSubmissionsHwId(record.id)}>查看提交</Button>
          <Popconfirm title="确认删除？" onConfirm={() => deleteMutation.mutate(record.id)} okText="确认" cancelText="取消">
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const subColumns: ColumnsType<Submission> = [
    { title: '学员', dataIndex: 'student_name', width: 100 },
    { title: '内容', dataIndex: 'content', ellipsis: true, render: (v: string) => v || '-' },
    { title: '提交时间', dataIndex: 'submitted_at', width: 140, render: (v: string) => dayjs(v).format('MM-DD HH:mm') },
    {
      title: '成绩', dataIndex: 'score', width: 80,
      render: (v: number | null) => v !== null && v !== undefined ? <Tag color={v >= 60 ? 'green' : 'red'}>{v}分</Tag> : <Tag>未批改</Tag>,
    },
    { title: '反馈', dataIndex: 'feedback', ellipsis: true, render: (v: string) => v || '-' },
    {
      title: '操作', key: 'action', width: 80,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => { setReviewingSub(record); reviewForm.setFieldsValue({ score: record.score, feedback: record.feedback }); }}>
          {record.score !== null && record.score !== undefined ? '重评' : '批改'}
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Select
          placeholder="按课程筛选"
          allowClear
          style={{ width: 200 }}
          onChange={(v) => setParams((prev) => ({ ...prev, page: 1, course_id: v }))}
          options={(courses?.items || []).map((c: any) => ({ value: c.id, label: c.name }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>发布作业</Button>
      </div>

      <Table<Homework>
        columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading}
        pagination={{
          current: params.page, pageSize: params.page_size, total: data?.total || 0,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => setParams((prev) => ({ ...prev, page, page_size: pageSize })),
        }}
        scroll={{ x: 700 }} size="middle"
      />

      {/* 发布作业 */}
      <Modal title="发布作业" open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)} confirmLoading={createMutation.isPending} destroyOnClose>
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="course_id" label="课程" rules={[{ required: true, message: '请选择课程' }]}>
            <Select placeholder="选择课程" options={(courses?.items || []).map((c: any) => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="作业标题" />
          </Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={3} /></Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="question_count" label="题量"><InputNumber min={1} placeholder="题目数量" style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="module" label="知识模块"><Input placeholder="如：数量关系" /></Form.Item>
          </div>
          <Form.Item name="due_date" label="截止时间"><DatePicker showTime style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>

      {/* 提交列表 */}
      <Modal title="提交记录" open={!!submissionsHwId} onCancel={() => setSubmissionsHwId(null)} footer={null} width={800}>
        <Table<Submission> columns={subColumns} dataSource={submissions || []} rowKey="id" loading={subsLoading} pagination={false} size="small" />
      </Modal>

      {/* 批改 */}
      <Modal title="批改作业" open={!!reviewingSub} onOk={handleReview} onCancel={() => setReviewingSub(null)} confirmLoading={reviewMutation.isPending}>
        <Form form={reviewForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="score" label="分数" rules={[{ required: true, message: '请输入分数' }]}>
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="feedback" label="反馈"><Input.TextArea rows={3} placeholder="输入批改反馈" /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
