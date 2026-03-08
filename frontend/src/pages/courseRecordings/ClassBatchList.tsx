import { useState } from 'react';
import { Table, Button, Space, Tag, Modal, Form, Input, DatePicker, Select, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { courseRecordingApi } from '../../api/courseRecordings';
import type { ClassBatch } from '../../types/courseRecording';
import dayjs from 'dayjs';

export default function ClassBatchList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [editingBatch, setEditingBatch] = useState<ClassBatch | null>(null);
  const [form] = Form.useForm();

  const { data: teachers } = useQuery({
    queryKey: ['teachers-select'],
    queryFn: () => courseRecordingApi.listTeachers({ page: 1, page_size: 100 }),
  });

  const { data: classTypes } = useQuery({
    queryKey: ['class-types'],
    queryFn: () => courseRecordingApi.listClassTypes(),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['class-batches', params],
    queryFn: () => courseRecordingApi.listClassBatches(params),
  });

  const createMutation = useMutation({
    mutationFn: courseRecordingApi.createClassBatch,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['class-batches'] });
    },
    onError: () => message.error('创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ClassBatch> }) =>
      courseRecordingApi.updateClassBatch(id, data),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      setEditingBatch(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['class-batches'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: courseRecordingApi.deleteClassBatch,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['class-batches'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleCreate = () => {
    setEditingBatch(null);
    form.resetFields();
    setFormOpen(true);
  };

  const handleEdit = (batch: ClassBatch) => {
    setEditingBatch(batch);
    form.setFieldsValue({
      ...batch,
      start_date: batch.start_date ? dayjs(batch.start_date) : null,
      end_date: batch.end_date ? dayjs(batch.end_date) : null,
    });
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (values.start_date) values.start_date = values.start_date.format('YYYY-MM-DD');
    if (values.end_date) values.end_date = values.end_date.format('YYYY-MM-DD');

    if (editingBatch) {
      updateMutation.mutate({ id: editingBatch.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个班次吗？',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const columns = [
    { title: '班次名称', dataIndex: 'name', ellipsis: true },
    { title: '班型', dataIndex: 'class_type_name', width: 120, render: (v: string) => v || '-' },
    { title: '主讲教师', dataIndex: 'teacher_name', width: 100, render: (v: string) => v || '-' },
    {
      title: '开始日期',
      dataIndex: 'start_date',
      width: 110,
      render: (v: string) => (v ? dayjs(v).format('YYYY-MM-DD') : '-'),
    },
    {
      title: '结束日期',
      dataIndex: 'end_date',
      width: 110,
      render: (v: string) => (v ? dayjs(v).format('YYYY-MM-DD') : '-'),
    },
    { title: '学员数', dataIndex: 'student_count', width: 80 },
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
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: ClassBatch) => (
        <Space>
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
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建班次
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
        title={editingBatch ? '编辑班次' : '新建班次'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setFormOpen(false);
          setEditingBatch(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="班次名称" rules={[{ required: true, message: '请输入班次名称' }]}>
            <Input placeholder="如：2024国考冲刺班" />
          </Form.Item>
          <Form.Item name="class_type_id" label="班型">
            <Select
              placeholder="选择班型"
              allowClear
              options={(classTypes || []).map((ct: any) => ({ value: ct.id, label: ct.name }))}
            />
          </Form.Item>
          <Form.Item name="teacher_id" label="主讲教师">
            <Select
              placeholder="选择教师"
              allowClear
              options={(teachers?.items || []).map((t: any) => ({ value: t.id, label: t.name }))}
            />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="start_date" label="开始日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="end_date" label="结束日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </div>
          {editingBatch && (
            <Form.Item name="status" label="状态">
              <Select
                options={[
                  { value: 'active', label: '进行中' },
                  { value: 'completed', label: '已完成' },
                  { value: 'cancelled', label: '已取消' },
                ]}
              />
            </Form.Item>
          )}
          <Form.Item name="description" label="班次说明">
            <Input.TextArea rows={3} placeholder="班次描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
