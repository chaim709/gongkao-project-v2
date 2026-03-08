import { useState, useCallback, useRef, useEffect } from 'react';
import { Table, Input, Select, Button, Space, Tag, Popconfirm, message } from 'antd';
import { PlusOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { courseApi } from '../../api/courses';
import type { Course, CourseListParams } from '../../types/course';
import CourseForm from './CourseForm';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';

const statusMap: Record<string, { text: string; color: string }> = {
  active: { text: '进行中', color: 'green' },
  completed: { text: '已结束', color: 'blue' },
  cancelled: { text: '已取消', color: 'default' },
};

export default function CourseList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState<CourseListParams>({ page: 1, page_size: 20 });
  const [searchValue, setSearchValue] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const debounceTimer = useRef<ReturnType<typeof setTimeout>>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['courses', params],
    queryFn: () => courseApi.list(params),
  });

  const deleteMutation = useMutation({
    mutationFn: courseApi.delete,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['courses'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleSearchChange = useCallback((value: string) => {
    setSearchValue(value);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setParams((prev) => ({ ...prev, page: 1, search: value || undefined }));
    }, 300);
  }, []);

  useEffect(() => {
    return () => { if (debounceTimer.current) clearTimeout(debounceTimer.current); };
  }, []);

  const columns: ColumnsType<Course> = [
    { title: '课程名称', dataIndex: 'name', ellipsis: true },
    { title: '类型', dataIndex: 'course_type', width: 100, render: (v: string) => v || '-' },
    { title: '授课老师', dataIndex: 'teacher_name', width: 100, render: (v: string) => v || '-' },
    {
      title: '起止日期', key: 'dates', width: 200,
      render: (_, record) => {
        const start = record.start_date ? dayjs(record.start_date).format('MM-DD') : '?';
        const end = record.end_date ? dayjs(record.end_date).format('MM-DD') : '?';
        return record.start_date || record.end_date ? `${start} ~ ${end}` : '-';
      },
    },
    {
      title: '状态', dataIndex: 'status', width: 90,
      render: (v: string) => {
        const info = statusMap[v] || { text: v, color: 'default' };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '操作', key: 'action', width: 130, fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" onClick={() => { setEditingCourse(record); setFormOpen(true); }}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => deleteMutation.mutate(record.id)} okText="确认" cancelText="取消">
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <Space wrap>
          <Input
            placeholder="搜索课程名称"
            prefix={<SearchOutlined />}
            value={searchValue}
            onChange={(e) => handleSearchChange(e.target.value)}
            style={{ width: 220 }}
            allowClear
          />
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 120 }}
            value={params.status}
            onChange={(v) => setParams((prev) => ({ ...prev, page: 1, status: v }))}
            options={[
              { value: 'active', label: '进行中' },
              { value: 'completed', label: '已结束' },
              { value: 'cancelled', label: '已取消' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={() => { setSearchValue(''); setParams({ page: 1, page_size: 20 }); }}>重置</Button>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingCourse(null); setFormOpen(true); }}>新增课程</Button>
      </div>

      <Table<Course>
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
        scroll={{ x: 800 }}
        size="middle"
      />

      <CourseForm
        open={formOpen}
        course={editingCourse}
        onClose={() => setFormOpen(false)}
        onSuccess={() => { setFormOpen(false); queryClient.invalidateQueries({ queryKey: ['courses'] }); }}
      />
    </div>
  );
}
