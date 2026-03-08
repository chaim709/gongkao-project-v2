import { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, Switch, Select, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { packageApi } from '../../api/packages';
import type { Package } from '../../types/package';

export default function PackageList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [editingPackage, setEditingPackage] = useState<Package | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['packages', params],
    queryFn: () => packageApi.listPackages(params),
  });

  const createMutation = useMutation({
    mutationFn: packageApi.createPackage,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['packages'] });
    },
    onError: () => message.error('创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Package> }) =>
      packageApi.updatePackage(id, data),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      setEditingPackage(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['packages'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: packageApi.deletePackage,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['packages'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleCreate = () => {
    setEditingPackage(null);
    form.resetFields();
    setFormOpen(true);
  };

  const handleEdit = (pkg: Package) => {
    setEditingPackage(pkg);
    form.setFieldsValue(pkg);
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingPackage) {
      updateMutation.mutate({ id: editingPackage.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个套餐吗？',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name', ellipsis: true },
    { title: '描述', dataIndex: 'description', ellipsis: true, render: (v: string) => v || '-' },
    { title: '价格', dataIndex: 'price', width: 100, render: (v: number) => `¥${v}` },
    { title: '原价', dataIndex: 'original_price', width: 100, render: (v: number) => v ? `¥${v}` : '-' },
    { title: '有效期(天)', dataIndex: 'validity_days', width: 100 },
    { title: '状态', dataIndex: 'is_active', width: 80, render: (v: boolean) => v ? '启用' : '禁用' },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Package) => (
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
          placeholder="状态筛选"
          allowClear
          style={{ width: 120 }}
          onChange={(v) => setParams((prev) => ({ ...prev, page: 1, is_active: v }))}
          options={[
            { value: true, label: '启用' },
            { value: false, label: '禁用' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建套餐
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
        title={editingPackage ? '编辑套餐' : '新建套餐'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setFormOpen(false);
          setEditingPackage(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="套餐名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="套餐描述" />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="price" label="价格" rules={[{ required: true, message: '请输入价格' }]}>
              <InputNumber min={0} step={0.01} placeholder="价格" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="original_price" label="原价">
              <InputNumber min={0} step={0.01} placeholder="原价" style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="validity_days" label="有效期(天)" initialValue={365}>
              <InputNumber min={1} placeholder="有效期" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="is_active" label="状态" valuePropName="checked" initialValue={true}>
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
