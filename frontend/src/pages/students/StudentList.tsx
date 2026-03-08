import { useState, useCallback, useRef, useEffect } from 'react';
import { Table, Input, Select, Button, Space, Tag, Popconfirm, message, Dropdown, Modal, Form } from 'antd';
import { PlusOutlined, SearchOutlined, ReloadOutlined, DeleteOutlined, AimOutlined, DownloadOutlined, SwapOutlined, UploadOutlined, TeamOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentApi } from '../../api/students';
import { exportApi } from '../../api/export';
import type { Student, StudentListParams } from '../../types/student';
import StudentForm from './StudentForm';
import WeaknessTagPanel from './WeaknessTagPanel';
import { useHasRole } from '../../components/Permission';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import { getDesignTokens } from '../../theme';
import { useThemeStore } from '../../stores/themeStore';

interface ApiError {
  message?: string;
  detail?: string;
}

const statusMap: Record<string, { text: string; color: string }> = {
  lead: { text: '线索', color: 'default' },
  trial: { text: '试听', color: 'purple' },
  active: { text: '在读', color: 'green' },
  inactive: { text: '休学', color: 'orange' },
  graduated: { text: '结业', color: 'blue' },
  dropped: { text: '退出', color: 'red' },
};

export default function StudentList() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const isAdmin = useHasRole('admin');
  const themeMode = useThemeStore((s) => s.mode);
  const tokens = getDesignTokens(themeMode);
  const [params, setParams] = useState<StudentListParams>({ page: 1, page_size: 20 });
  const [searchValue, setSearchValue] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [batchType, setBatchType] = useState<'supervisor' | 'status'>('supervisor');
  const [batchForm] = Form.useForm();
  const debounceTimer = useRef<ReturnType<typeof setTimeout>>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['students', params],
    queryFn: () => studentApi.list(params),
  });

  const deleteMutation = useMutation({
    mutationFn: studentApi.delete,
    onSuccess: () => {
      message.success('删除成功');
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
    onError: (err: ApiError) => message.error(err?.message || '删除失败，请稍后重试'),
  });

  const handleSearchChange = useCallback((value: string) => {
    setSearchValue(value);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setParams((prev) => ({ ...prev, page: 1, search: value || undefined }));
    }, 300);
  }, []);

  useEffect(() => {
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, []);

  const handleStatusFilter = (value: string | undefined) => {
    setParams((prev) => ({ ...prev, page: 1, status: value }));
  };

  const handleReset = () => {
    setSearchValue('');
    setSelectedRowKeys([]);
    setParams({ page: 1, page_size: 20 });
  };

  const openCreate = () => {
    setEditingStudent(null);
    setFormOpen(true);
  };

  const openEdit = (student: Student) => {
    setEditingStudent(student);
    setFormOpen(true);
  };

  const handleBatchDelete = () => {
    selectedRowKeys.forEach((id) => deleteMutation.mutate(id));
  };

  const validTransitions: Record<string, string[]> = {
    lead: ['trial', 'active', 'dropped'],
    trial: ['active', 'dropped'],
    active: ['inactive', 'graduated', 'dropped'],
    inactive: ['active', 'dropped'],
    dropped: ['lead'],
  };

  const statusChangeMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      studentApi.changeStatus(id, status),
    onSuccess: () => {
      message.success('状态更新成功');
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
    onError: (err: ApiError) => message.error(err?.detail || err?.message || '状态更新失败'),
  });

  const batchAssignMutation = useMutation({
    mutationFn: ({ student_ids, supervisor_id }: { student_ids: number[]; supervisor_id: number }) =>
      studentApi.batchAssignSupervisor(student_ids, supervisor_id),
    onSuccess: () => {
      message.success('批量分配成功');
      setBatchModalOpen(false);
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
    onError: () => message.error('批量分配失败'),
  });

  const batchStatusMutation = useMutation({
    mutationFn: ({ student_ids, status }: { student_ids: number[]; status: string }) =>
      studentApi.batchUpdateStatus(student_ids, status),
    onSuccess: () => {
      message.success('批量更新成功');
      setBatchModalOpen(false);
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
    onError: () => message.error('批量更新失败'),
  });

  const columns: ColumnsType<Student> = [
    {
      title: '姓名',
      dataIndex: 'name',
      ellipsis: true,
      render: (v: string, r: Student) => (
        <Button type="link" size="small" style={{ padding: 0, fontWeight: 600 }} onClick={() => navigate(`/students/${r.id}`)}>
          {v}
        </Button>
      ),
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      width: 130,
      render: (v: string) => v || '-',
    },
    {
      title: '微信',
      dataIndex: 'wechat',
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '性别',
      dataIndex: 'gender',
      width: 70,
      render: (v: string) => v || '-',
    },
    {
      title: '学历',
      dataIndex: 'education',
      width: 80,
      render: (v: string) => v || '-',
    },
    {
      title: '报考类型',
      dataIndex: 'exam_type',
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (status: string) => {
        const info = statusMap[status] || { text: status, color: 'default' };
        return <Tag color={info.color} style={{ borderRadius: 6 }}>{info.text}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 120,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      fixed: 'right',
      render: (_, record) => {
        const transitions = validTransitions[record.status] || [];
        const statusItems = transitions.map(s => ({
          key: s,
          label: statusMap[s]?.text || s,
          onClick: () => statusChangeMutation.mutate({ id: record.id, status: s }),
        }));
        return (
          <Space>
            <Button type="link" size="small" icon={<AimOutlined />} onClick={() => navigate(`/students/${record.id}/recommend`)}>
              选岗
            </Button>
            <Button type="link" size="small" onClick={() => openEdit(record)}>
              编辑
            </Button>
            {statusItems.length > 0 && (
              <Dropdown menu={{ items: statusItems }} trigger={['click']}>
                <Button type="link" size="small" icon={<SwapOutlined />}>转态</Button>
              </Dropdown>
            )}
            {isAdmin && (
              <Popconfirm
                title="确认删除该学员？"
                description="删除后数据可恢复"
                onConfirm={() => deleteMutation.mutate(record.id)}
                okText="确认"
                cancelText="取消"
              >
                <Button type="link" size="small" danger>
                  删除
                </Button>
              </Popconfirm>
            )}
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 4px 0', color: tokens.colorText }}>
          学员管理
        </h2>
        <p style={{ fontSize: 13, color: tokens.colorTextTertiary, margin: 0 }}>
          管理所有学员信息，支持搜索、筛选和批量操作
        </p>
      </div>

      {/* 搜索栏 - 卡片式 */}
      <div style={{
        marginBottom: 20,
        padding: '16px 24px',
        background: tokens.colorBgContainer,
        borderRadius: tokens.borderRadiusLG,
        border: `1px solid ${tokens.colorBorderSecondary}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 12,
        boxShadow: tokens.boxShadow,
      }}>
        <Space wrap>
          <Input
            placeholder="搜索姓名/手机号"
            prefix={<SearchOutlined style={{ color: tokens.colorTextQuaternary }} />}
            value={searchValue}
            onChange={(e) => handleSearchChange(e.target.value)}
            style={{ width: 240, borderRadius: 10 }}
            allowClear
          />
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 120 }}
            value={params.status}
            onChange={handleStatusFilter}
            options={[
              { value: 'lead', label: '线索' },
              { value: 'trial', label: '试听' },
              { value: 'active', label: '在读' },
              { value: 'inactive', label: '休学' },
              { value: 'graduated', label: '结业' },
              { value: 'dropped', label: '退出' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={handleReset} style={{ borderRadius: 10 }}>重置</Button>
          {selectedRowKeys.length > 0 && (
            <>
              <Button icon={<TeamOutlined />} onClick={() => { setBatchType('supervisor'); setBatchModalOpen(true); }} style={{ borderRadius: 10 }}>
                批量分配督学 ({selectedRowKeys.length})
              </Button>
              <Button icon={<SwapOutlined />} onClick={() => { setBatchType('status'); setBatchModalOpen(true); }} style={{ borderRadius: 10 }}>
                批量修改状态 ({selectedRowKeys.length})
              </Button>
            </>
          )}
          {isAdmin && selectedRowKeys.length > 0 && (
            <Popconfirm
              title={`确认删除选中的 ${selectedRowKeys.length} 名学员？`}
              onConfirm={handleBatchDelete}
              okText="确认"
              cancelText="取消"
            >
              <Button danger icon={<DeleteOutlined />} style={{ borderRadius: 10 }}>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </Space>
        <Space>
          <Button icon={<UploadOutlined />} onClick={() => navigate('/students/import')} style={{ borderRadius: 10 }}>
            批量导入
          </Button>
          <Button icon={<DownloadOutlined />} onClick={() => {
            exportApi.students({ status: params.status }).catch(() => message.error('导出失败'));
          }} style={{ borderRadius: 10 }}>导出</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ borderRadius: 10 }}>
            新增学员
          </Button>
        </Space>
      </div>

      {/* 表格 - 卡片式包裹 */}
      <div className="gk-table-wrapper">
        <Table<Student>
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: '8px 0' }}>
                <WeaknessTagPanel studentId={record.id} />
              </div>
            ),
          }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
          pagination={{
            current: params.page,
            pageSize: params.page_size,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => setParams((prev) => ({ ...prev, page, page_size: pageSize })),
          }}
          scroll={{ x: 900 }}
          size="middle"
        />
      </div>

      <StudentForm
        open={formOpen}
        student={editingStudent}
        onClose={() => setFormOpen(false)}
        onSuccess={() => {
          setFormOpen(false);
          queryClient.invalidateQueries({ queryKey: ['students'] });
        }}
      />

      {/* 批量操作 Modal */}
      <Modal
        title={batchType === 'supervisor' ? '批量分配督学' : '批量修改状态'}
        open={batchModalOpen}
        onOk={() => {
          batchForm.validateFields().then(values => {
            if (batchType === 'supervisor') {
              batchAssignMutation.mutate({ student_ids: selectedRowKeys, supervisor_id: values.supervisor_id });
            } else {
              batchStatusMutation.mutate({ student_ids: selectedRowKeys, status: values.status });
            }
          });
        }}
        onCancel={() => setBatchModalOpen(false)}
        confirmLoading={batchAssignMutation.isPending || batchStatusMutation.isPending}
      >
        <Form form={batchForm} layout="vertical">
          {batchType === 'supervisor' ? (
            <Form.Item name="supervisor_id" label="督学老师" rules={[{ required: true, message: '请选择督学老师' }]}>
              <Select placeholder="选择督学老师">
                <Select.Option value={1}>督学老师A</Select.Option>
                <Select.Option value={2}>督学老师B</Select.Option>
              </Select>
            </Form.Item>
          ) : (
            <Form.Item name="status" label="学员状态" rules={[{ required: true, message: '请选择状态' }]}>
              <Select placeholder="选择状态">
                <Select.Option value="lead">线索</Select.Option>
                <Select.Option value="trial">试听</Select.Option>
                <Select.Option value="active">在读</Select.Option>
                <Select.Option value="inactive">休学</Select.Option>
                <Select.Option value="graduated">结业</Select.Option>
                <Select.Option value="dropped">退出</Select.Option>
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
