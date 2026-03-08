import { useState } from 'react';
import { Table, Select, Tag } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { auditLogApi } from '../../api/auditLogs';
import type { AuditLog, AuditLogListParams } from '../../api/auditLogs';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const ACTION_MAP: Record<string, { label: string; color: string }> = {
  CREATE_STUDENT: { label: '创建学员', color: 'green' },
  UPDATE_STUDENT: { label: '更新学员', color: 'blue' },
  DELETE_STUDENT: { label: '删除学员', color: 'red' },
  CREATE_COURSE: { label: '创建课程', color: 'green' },
  UPDATE_COURSE: { label: '更新课程', color: 'blue' },
  DELETE_COURSE: { label: '删除课程', color: 'red' },
  CREATE_LOG: { label: '创建督学日志', color: 'green' },
  UPDATE_LOG: { label: '更新督学日志', color: 'blue' },
  DELETE_LOG: { label: '删除督学日志', color: 'red' },
  CREATE_HOMEWORK: { label: '发布作业', color: 'green' },
  DELETE_HOMEWORK: { label: '删除作业', color: 'red' },
};

export default function AuditLogList() {
  const [params, setParams] = useState<AuditLogListParams>({ page: 1, page_size: 20 });

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => auditLogApi.list(params),
  });

  const columns: ColumnsType<AuditLog> = [
    {
      title: '时间', dataIndex: 'created_at', width: 160,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作人', dataIndex: 'user_name', width: 100,
      render: (v: string) => v || '-',
    },
    {
      title: '操作', dataIndex: 'action', width: 120,
      render: (v: string) => {
        const info = ACTION_MAP[v] || { label: v, color: 'default' };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    { title: '资源类型', dataIndex: 'resource_type', width: 100 },
    { title: '资源ID', dataIndex: 'resource_id', width: 80 },
    { title: 'IP', dataIndex: 'ip_address', width: 120, render: (v: string) => v || '-' },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <Select
          placeholder="操作类型"
          allowClear
          style={{ width: 160 }}
          onChange={(v) => setParams((p) => ({ ...p, page: 1, action: v }))}
          options={Object.entries(ACTION_MAP).map(([value, { label }]) => ({ value, label }))}
        />
        <Select
          placeholder="资源类型"
          allowClear
          style={{ width: 120 }}
          onChange={(v) => setParams((p) => ({ ...p, page: 1, resource_type: v }))}
          options={[
            { value: 'student', label: '学员' },
            { value: 'course', label: '课程' },
            { value: 'supervision_log', label: '督学日志' },
            { value: 'homework', label: '作业' },
          ]}
        />
      </div>

      <Table<AuditLog>
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: data?.total || 0,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => setParams((p) => ({ ...p, page, page_size: pageSize })),
        }}
        size="middle"
      />
    </div>
  );
}
