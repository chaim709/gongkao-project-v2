import { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker, message, Image, InputNumber } from 'antd';
import { PlusOutlined, QrcodeOutlined, DownloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceApi } from '../../api/attendances';
import { exportApi } from '../../api/export';
import type { Attendance } from '../../types/attendance';
import dayjs from 'dayjs';
import client from '../../api/client';

export default function AttendanceList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [editingAttendance, setEditingAttendance] = useState<Attendance | null>(null);
  const [form] = Form.useForm();

  // 签到码相关
  const [checkinCodeOpen, setCheckinCodeOpen] = useState(false);
  const [checkinCode, setCheckinCode] = useState<{ token: string; title: string; qrcode_url: string; expires_at: string } | null>(null);
  const [codeForm] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['attendances', params],
    queryFn: () => attendanceApi.listAttendances(params),
  });

  const createMutation = useMutation({
    mutationFn: attendanceApi.createAttendance,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['attendances'] });
    },
    onError: () => message.error('创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Attendance> }) =>
      attendanceApi.updateAttendance(id, data),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      setEditingAttendance(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['attendances'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: attendanceApi.deleteAttendance,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['attendances'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleCreate = () => {
    setEditingAttendance(null);
    form.resetFields();
    setFormOpen(true);
  };

  const handleEdit = (attendance: Attendance) => {
    setEditingAttendance(attendance);
    form.setFieldsValue({
      ...attendance,
      attendance_date: dayjs(attendance.attendance_date),
    });
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    const submitData = {
      ...values,
      attendance_date: values.attendance_date.format('YYYY-MM-DD'),
    };
    if (editingAttendance) {
      updateMutation.mutate({ id: editingAttendance.id, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条考勤记录吗？',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '学员ID', dataIndex: 'student_id', width: 80 },
    { title: '课程ID', dataIndex: 'course_id', width: 80, render: (v: number) => v || '-' },
    { title: '日期', dataIndex: 'attendance_date', width: 120 },
    { title: '状态', dataIndex: 'status', width: 80 },
    { title: '备注', dataIndex: 'notes', ellipsis: true, render: (v: string) => v || '-' },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Attendance) => (
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
          onChange={(v) => setParams((prev) => ({ ...prev, page: 1, status: v }))}
          options={[
            { value: '出勤', label: '出勤' },
            { value: '缺勤', label: '缺勤' },
            { value: '请假', label: '请假' },
            { value: '迟到', label: '迟到' },
          ]}
        />
        <Space>
          <Button icon={<DownloadOutlined />} onClick={() => {
            exportApi.attendances().catch(() => message.error('导出失败'));
          }}>导出</Button>
          <Button icon={<QrcodeOutlined />} onClick={() => { codeForm.resetFields(); setCheckinCode(null); setCheckinCodeOpen(true); }}>
            生成签到码
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建考勤
          </Button>
        </Space>
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
        title={editingAttendance ? '编辑考勤' : '新建考勤'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setFormOpen(false);
          setEditingAttendance(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="student_id" label="学员ID" rules={[{ required: true, message: '请输入学员ID' }]}>
              <Input type="number" placeholder="学员ID" />
            </Form.Item>
            <Form.Item name="course_id" label="课程ID">
              <Input type="number" placeholder="课程ID" />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="attendance_date" label="日期" rules={[{ required: true, message: '请选择日期' }]}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
              <Select placeholder="选择状态" options={[
                { value: '出勤', label: '出勤' },
                { value: '缺勤', label: '缺勤' },
                { value: '请假', label: '请假' },
                { value: '迟到', label: '迟到' },
              ]} />
            </Form.Item>
          </div>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 生成签到码弹窗 */}
      <Modal
        title="生成签到码"
        open={checkinCodeOpen}
        onCancel={() => setCheckinCodeOpen(false)}
        footer={checkinCode ? [
          <Button key="print" type="primary" onClick={() => {
            const img = document.getElementById('checkin-qr-img') as HTMLImageElement;
            if (img) {
              const win = window.open('');
              if (win) {
                win.document.write(`<div style="text-align:center;padding:40px">
                  <h2>${checkinCode.title}</h2>
                  <p>扫码签到</p>
                  <img src="${img.src}" style="width:300px;height:300px" />
                  <p style="color:#999;margin-top:16px">有效期至 ${new Date(checkinCode.expires_at).toLocaleString('zh-CN')}</p>
                </div>`);
                win.document.close();
                setTimeout(() => win.print(), 300);
              }
            }
          }}>打印签到码</Button>,
        ] : [
          <Button key="generate" type="primary" onClick={async () => {
            const values = await codeForm.validateFields();
            try {
              const res: { token: string; title: string; qrcode_url: string; expires_at: string } = await client.post('/checkin-codes', values);
              setCheckinCode(res);
              message.success('签到码生成成功');
            } catch {
              message.error('生成失败');
            }
          }}>生成</Button>,
        ]}
      >
        {!checkinCode ? (
          <Form form={codeForm} layout="vertical" initialValues={{ title: '课堂签到', expire_minutes: 30 }}>
            <Form.Item name="title" label="签到标题" rules={[{ required: true }]}>
              <Input placeholder="如：第5次模考签到" />
            </Form.Item>
            <Form.Item name="expire_minutes" label="有效时长（分钟）">
              <InputNumber min={5} max={180} style={{ width: '100%' }} />
            </Form.Item>
          </Form>
        ) : (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <h3>{checkinCode.title}</h3>
            <Image
              id="checkin-qr-img"
              src={`/api/v1/checkin-codes/${checkinCode.token}/qrcode`}
              width={200}
              preview={false}
            />
            <p style={{ marginTop: 16, color: '#52c41a', fontWeight: 600 }}>签到码已生成</p>
            <p style={{ color: '#999', fontSize: 13 }}>
              有效期至 {new Date(checkinCode.expires_at).toLocaleString('zh-CN')}
            </p>
            <p style={{ color: '#666', fontSize: 13 }}>学生扫码后输入手机号即可完成签到</p>
          </div>
        )}
      </Modal>
    </div>
  );
}
