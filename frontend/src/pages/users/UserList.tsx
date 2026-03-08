import { useState } from 'react';
import {
  Table, Button, Space, Tag, Modal, Form, Input, Select, Switch,
  message, Popconfirm,
} from 'antd';
import { PlusOutlined, ReloadOutlined, KeyOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../../api/users';
import type { UserItem } from '../../api/users';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const roleMap: Record<string, { text: string; color: string }> = {
  admin: { text: '管理员', color: 'red' },
  supervisor: { text: '督学', color: 'blue' },
  teacher: { text: '教师', color: 'green' },
};

export default function UserList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
  const [resetPwdOpen, setResetPwdOpen] = useState(false);
  const [resetUserId, setResetUserId] = useState<number>(0);
  const [form] = Form.useForm();
  const [pwdForm] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['users', params],
    queryFn: () => userApi.list(params),
  });

  const createMutation = useMutation({
    mutationFn: (values: Parameters<typeof userApi.create>[0]) => userApi.create(values),
    onSuccess: () => {
      message.success('用户创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: () => message.error('创建失败，用户名可能已存在'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data: d }: { id: number; data: Parameters<typeof userApi.update>[1] }) =>
      userApi.update(id, d),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      form.resetFields();
      setEditingUser(null);
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: userApi.delete,
    onSuccess: () => {
      message.success('已删除');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: () => message.error('删除失败'),
  });

  const resetPwdMutation = useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) =>
      userApi.resetPassword(id, password),
    onSuccess: () => {
      message.success('密码已重置');
      setResetPwdOpen(false);
      pwdForm.resetFields();
    },
    onError: () => message.error('重置失败'),
  });

  const handleSubmit = () => {
    form.validateFields().then(values => {
      if (editingUser) {
        const { username, password, ...rest } = values;
        updateMutation.mutate({ id: editingUser.id, data: rest });
      } else {
        createMutation.mutate(values);
      }
    });
  };

  const openCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setFormOpen(true);
  };

  const openEdit = (user: UserItem) => {
    setEditingUser(user);
    form.setFieldsValue(user);
    setFormOpen(true);
  };

  const columns: ColumnsType<UserItem> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用户名', dataIndex: 'username', width: 120 },
    { title: '姓名', dataIndex: 'real_name', width: 100, render: (v: string) => v || '-' },
    {
      title: '角色', dataIndex: 'role', width: 90,
      render: (v: string) => {
        const info = roleMap[v] || { text: v, color: 'default' };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    { title: '手机', dataIndex: 'phone', width: 130, render: (v: string) => v || '-' },
    { title: '邮箱', dataIndex: 'email', width: 160, render: (v: string) => v || '-' },
    {
      title: '状态', dataIndex: 'is_active', width: 80, align: 'center',
      render: (v: boolean) => v
        ? <Tag color="green">启用</Tag>
        : <Tag color="red">禁用</Tag>,
    },
    {
      title: '创建时间', dataIndex: 'created_at', width: 120,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-',
    },
    {
      title: '操作', key: 'action', width: 180, align: 'center',
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" onClick={() => openEdit(record)}>编辑</Button>
          <Button type="link" size="small" icon={<KeyOutlined />}
            onClick={() => { setResetUserId(record.id); pwdForm.resetFields(); setResetPwdOpen(true); }}>
            重置密码
          </Button>
          <Popconfirm title="确认删除该用户？" onConfirm={() => deleteMutation.mutate(record.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Select
            placeholder="角色筛选" allowClear style={{ width: 120 }}
            onChange={v => setParams(p => ({ ...p, page: 1, role: v }))}
            options={[
              { value: 'admin', label: '管理员' },
              { value: 'supervisor', label: '督学' },
              { value: 'teacher', label: '教师' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={() => setParams({ page: 1, page_size: 20 })}>
            重置
          </Button>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新增用户
        </Button>
      </div>

      <Table<UserItem>
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: data?.total || 0,
          showTotal: total => `共 ${total} 条`,
          onChange: (page, pageSize) => setParams({ page, page_size: pageSize }),
        }}
        size="middle"
      />

      {/* 新增/编辑用户 */}
      <Modal
        title={editingUser ? '编辑用户' : '新增用户'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => { setFormOpen(false); setEditingUser(null); }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: !editingUser, message: '请输入用户名' }]}>
            <Input disabled={!!editingUser} placeholder="登录用户名" />
          </Form.Item>
          {!editingUser && (
            <Form.Item name="password" label="初始密码" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password placeholder="初始密码" />
            </Form.Item>
          )}
          <Form.Item name="real_name" label="姓名">
            <Input placeholder="真实姓名" />
          </Form.Item>
          <Form.Item name="role" label="角色" initialValue="supervisor">
            <Select options={[
              { value: 'admin', label: '管理员' },
              { value: 'supervisor', label: '督学' },
              { value: 'teacher', label: '教师' },
            ]} />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input placeholder="手机号" />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input placeholder="邮箱" />
          </Form.Item>
          {editingUser && (
            <Form.Item name="is_active" label="状态" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 重置密码 */}
      <Modal
        title="重置密码"
        open={resetPwdOpen}
        onOk={() => {
          pwdForm.validateFields().then(values => {
            resetPwdMutation.mutate({ id: resetUserId, password: values.new_password });
          });
        }}
        onCancel={() => setResetPwdOpen(false)}
        confirmLoading={resetPwdMutation.isPending}
      >
        <Form form={pwdForm} layout="vertical">
          <Form.Item name="new_password" label="新密码" rules={[{ required: true, min: 6, message: '密码至少6位' }]}>
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
