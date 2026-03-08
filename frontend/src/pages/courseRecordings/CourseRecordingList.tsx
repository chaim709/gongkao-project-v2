import { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, DatePicker, Select, InputNumber, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { courseRecordingApi } from '../../api/courseRecordings';
import type { CourseRecording } from '../../types/courseRecording';
import dayjs from 'dayjs';

export default function CourseRecordingList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [editingRecording, setEditingRecording] = useState<CourseRecording | null>(null);
  const [form] = Form.useForm();

  const { data: batches } = useQuery({
    queryKey: ['class-batches-select'],
    queryFn: () => courseRecordingApi.listClassBatches({ page: 1, page_size: 100 }),
  });

  const { data: teachers } = useQuery({
    queryKey: ['teachers-select'],
    queryFn: () => courseRecordingApi.listTeachers({ page: 1, page_size: 100 }),
  });

  const { data: subjects } = useQuery({
    queryKey: ['subjects'],
    queryFn: () => courseRecordingApi.listSubjects(),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['course-recordings', params],
    queryFn: () => courseRecordingApi.listCourseRecordings(params),
  });

  const createMutation = useMutation({
    mutationFn: courseRecordingApi.createCourseRecording,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['course-recordings'] });
    },
    onError: () => message.error('创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CourseRecording> }) =>
      courseRecordingApi.updateCourseRecording(id, data),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      setEditingRecording(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['course-recordings'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: courseRecordingApi.deleteCourseRecording,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['course-recordings'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleCreate = () => {
    setEditingRecording(null);
    form.resetFields();
    setFormOpen(true);
  };

  const handleEdit = (recording: CourseRecording) => {
    setEditingRecording(recording);
    form.setFieldsValue({
      ...recording,
      recording_date: recording.recording_date ? dayjs(recording.recording_date) : null,
    });
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (values.recording_date) {
      values.recording_date = values.recording_date.format('YYYY-MM-DD');
    }

    if (editingRecording) {
      updateMutation.mutate({ id: editingRecording.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个课程录播吗？',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const columns = [
    { title: '课程标题', dataIndex: 'title', ellipsis: true },
    { title: '班次', dataIndex: 'batch_name', width: 120, render: (v: string) => v || '-' },
    { title: '科目', dataIndex: 'subject_name', width: 100, render: (v: string) => v || '-' },
    { title: '教师', dataIndex: 'teacher_name', width: 100, render: (v: string) => v || '-' },
    {
      title: '录播日期',
      dataIndex: 'recording_date',
      width: 110,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD'),
    },
    { title: '时段', dataIndex: 'period', width: 80, render: (v: string) => v || '-' },
    { title: '时长(分钟)', dataIndex: 'duration_minutes', width: 100, render: (v: number) => v || '-' },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: CourseRecording) => (
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
          placeholder="按班次筛选"
          allowClear
          style={{ width: 200 }}
          onChange={(v) => setParams((prev) => ({ ...prev, page: 1, batch_id: v }))}
          options={(batches?.items || []).map((b: any) => ({ value: b.id, label: b.name }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建录播
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
        title={editingRecording ? '编辑课程录播' : '新建课程录播'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setFormOpen(false);
          setEditingRecording(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="title" label="课程标题" rules={[{ required: true, message: '请输入课程标题' }]}>
            <Input placeholder="如：行测数量关系专项训练" />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="batch_id" label="所属班次">
              <Select
                placeholder="选择班次"
                allowClear
                options={(batches?.items || []).map((b: any) => ({ value: b.id, label: b.name }))}
              />
            </Form.Item>
            <Form.Item name="subject_id" label="科目">
              <Select
                placeholder="选择科目"
                allowClear
                options={(subjects || []).map((s: any) => ({ value: s.id, label: s.name }))}
              />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="recording_date" label="录播日期" rules={[{ required: true, message: '请选择日期' }]}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="period" label="时段">
              <Select
                placeholder="选择时段"
                allowClear
                options={[
                  { value: '上午', label: '上午' },
                  { value: '下午', label: '下午' },
                  { value: '晚上', label: '晚上' },
                ]}
              />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="teacher_id" label="授课教师">
              <Select
                placeholder="选择教师"
                allowClear
                options={(teachers?.items || []).map((t: any) => ({ value: t.id, label: t.name }))}
              />
            </Form.Item>
            <Form.Item name="duration_minutes" label="时长(分钟)">
              <InputNumber min={1} placeholder="课程时长" style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <Form.Item name="recording_url" label="录播链接">
            <Input placeholder="视频链接地址" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} placeholder="课程说明" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
