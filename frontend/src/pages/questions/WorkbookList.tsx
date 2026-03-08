import { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { questionApi } from '../../api/questions';
import type { Workbook } from '../../types/question';

export default function WorkbookList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [editingWorkbook, setEditingWorkbook] = useState<Workbook | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['workbooks', params],
    queryFn: () => questionApi.listWorkbooks(params),
  });

  const createMutation = useMutation({
    mutationFn: questionApi.createWorkbook,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['workbooks'] });
    },
    onError: () => message.error('创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Workbook> }) =>
      questionApi.updateWorkbook(id, data),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      setEditingWorkbook(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['workbooks'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: questionApi.deleteWorkbook,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['workbooks'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleCreate = () => {
    setEditingWorkbook(null);
    form.resetFields();
    setFormOpen(true);
  };

  const handleEdit = (workbook: Workbook) => {
    setEditingWorkbook(workbook);
    form.setFieldsValue(workbook);
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingWorkbook) {
      updateMutation.mutate({ id: editingWorkbook.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个作业本吗？',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name', ellipsis: true },
    { title: '描述', dataIndex: 'description', ellipsis: true, render: (v: string) => v || '-' },
    { title: '题目数', dataIndex: 'question_count', width: 80 },
    { title: '总分', dataIndex: 'total_score', width: 80 },
    { title: '时限(分钟)', dataIndex: 'time_limit', width: 100, render: (v: number) => v || '-' },
    { title: '创建人', dataIndex: 'creator_name', width: 100, render: (v: string) => v || '-' },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Workbook) => (
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
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建作业本
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
        title={editingWorkbook ? '编辑作业本' : '新建作业本'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setFormOpen(false);
          setEditingWorkbook(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="作业本名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="作业本描述" />
          </Form.Item>
          <Form.Item name="time_limit" label="时限(分钟)">
            <InputNumber min={1} placeholder="考试时限" style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
