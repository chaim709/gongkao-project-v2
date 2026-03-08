import { useState } from 'react';
import { Table, Button, Space, Tag, Modal, Form, Input, Select, DatePicker, InputNumber, message, Checkbox } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mistakeApi } from '../../api/mistakes';
import type { Mistake } from '../../types/mistake';
import { studentApi } from '../../api/students';
import dayjs from 'dayjs';

export default function MistakeList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [editingMistake, setEditingMistake] = useState<Mistake | null>(null);
  const [reviewingMistake, setReviewingMistake] = useState<Mistake | null>(null);
  const [form] = Form.useForm();
  const [reviewForm] = Form.useForm();

  const { data: students } = useQuery({
    queryKey: ['students-select'],
    queryFn: () => studentApi.list({ page: 1, page_size: 100 }),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['mistakes', params],
    queryFn: () => mistakeApi.list(params),
  });

  const createMutation = useMutation({
    mutationFn: mistakeApi.create,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['mistakes'] });
    },
    onError: () => message.error('创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Mistake> }) =>
      mistakeApi.update(id, data),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      setEditingMistake(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['mistakes'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: mistakeApi.delete,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['mistakes'] });
    },
    onError: () => message.error('删除失败'),
  });

  const reviewMutation = useMutation({
    mutationFn: ({ mistakeId, data }: { mistakeId: number; data: any }) =>
      mistakeApi.createReview(mistakeId, data),
    onSuccess: () => {
      message.success('复习记录已保存');
      setReviewOpen(false);
      setReviewingMistake(null);
      reviewForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['mistakes'] });
    },
    onError: () => message.error('保存失败'),
  });

  const handleCreate = () => {
    setEditingMistake(null);
    form.resetFields();
    setFormOpen(true);
  };

  const handleEdit = (mistake: Mistake) => {
    setEditingMistake(mistake);
    form.setFieldsValue(mistake);
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingMistake) {
      updateMutation.mutate({ id: editingMistake.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条错题记录吗？',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const handleReview = (mistake: Mistake) => {
    setReviewingMistake(mistake);
    reviewForm.setFieldsValue({
      review_date: dayjs(),
      student_id: mistake.student_id,
    });
    setReviewOpen(true);
  };

  const handleSubmitReview = async () => {
    const values = await reviewForm.validateFields();
    values.review_date = values.review_date.format('YYYY-MM-DD');
    reviewMutation.mutate({ mistakeId: reviewingMistake!.id, data: values });
  };

  const columns = [
    { title: '学员', dataIndex: 'student_name', width: 100, render: (v: string) => v || '-' },
    { title: '题目ID', dataIndex: 'question_id', width: 80, render: (v: number) => v || '-' },
    { title: '作业本ID', dataIndex: 'workbook_id', width: 100, render: (v: number) => v || '-' },
    { title: '题号', dataIndex: 'question_order', width: 60, render: (v: number) => v || '-' },
    { title: '错误答案', dataIndex: 'wrong_answer', width: 80, render: (v: string) => v || '-' },
    { title: '复习次数', dataIndex: 'review_count', width: 80 },
    {
      title: '最后复习',
      dataIndex: 'last_review_at',
      width: 110,
      render: (v: string) => (v ? dayjs(v).format('YYYY-MM-DD') : '-'),
    },
    {
      title: '掌握状态',
      dataIndex: 'mastered',
      width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'orange'}>{v ? '已掌握' : '未掌握'}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: Mistake) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleReview(record)}>
            复习
          </Button>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button type="link" size="small" danger onClick={() => handleDelete(record.id)}>
            删除
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
            placeholder="掌握状态"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => setParams((prev) => ({ ...prev, page: 1, mastered: v }))}
            options={[
              { value: true, label: '已掌握' },
              { value: false, label: '未掌握' },
            ]}
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          添加错题
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
        scroll={{ x: 1000 }}
      />

      <Modal
        title={editingMistake ? '编辑错题' : '添加错题'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setFormOpen(false);
          setEditingMistake(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="student_id" label="学员" rules={[{ required: true, message: '请选择学员' }]}>
            <Select
              placeholder="选择学员"
              options={(students?.items || []).map((s: any) => ({ value: s.id, label: s.name }))}
            />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="question_id" label="题目ID">
              <InputNumber placeholder="题目ID" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="workbook_id" label="作业本ID">
              <InputNumber placeholder="作业本ID" style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="question_order" label="题号">
              <InputNumber placeholder="题号" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="wrong_answer" label="错误答案">
              <Input placeholder="如：A" />
            </Form.Item>
          </div>
          {editingMistake && (
            <Form.Item name="mastered" valuePropName="checked">
              <Checkbox>已掌握</Checkbox>
            </Form.Item>
          )}
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="错题说明" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="记录复习"
        open={reviewOpen}
        onOk={handleSubmitReview}
        onCancel={() => {
          setReviewOpen(false);
          setReviewingMistake(null);
          reviewForm.resetFields();
        }}
        confirmLoading={reviewMutation.isPending}
        destroyOnClose
      >
        <Form form={reviewForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="review_date" label="复习日期" rules={[{ required: true, message: '请选择日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_correct" valuePropName="checked">
            <Checkbox>本次答对</Checkbox>
          </Form.Item>
          <Form.Item name="time_spent" label="用时(秒)">
            <InputNumber min={1} placeholder="答题用时" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="复习说明" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
