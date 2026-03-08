import { useEffect } from 'react';
import { Modal, Form, Input, Select, DatePicker, message } from 'antd';
import { useMutation } from '@tanstack/react-query';
import { studentApi } from '../../api/students';
import type { Student, StudentUpdate } from '../../types/student';
import dayjs from 'dayjs';

interface ApiError {
  message?: string;
  detail?: string;
}

interface StudentFormProps {
  open: boolean;
  student: Student | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function StudentForm({ open, student, onClose, onSuccess }: StudentFormProps) {
  const [form] = Form.useForm();
  const isEdit = !!student;

  useEffect(() => {
    if (open) {
      if (student) {
        form.setFieldsValue({
          ...student,
          enrollment_date: student.enrollment_date ? dayjs(student.enrollment_date) : undefined,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, student, form]);

  const createMutation = useMutation({
    mutationFn: studentApi.create,
    onSuccess: () => {
      message.success('创建成功');
      onSuccess();
    },
    onError: (err: ApiError) => message.error(err?.message || '创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: StudentUpdate }) => studentApi.update(id, data),
    onSuccess: () => {
      message.success('更新成功');
      onSuccess();
    },
    onError: (err: ApiError) => message.error(err?.message || '更新失败'),
  });

  const loading = createMutation.isPending || updateMutation.isPending;

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (values.enrollment_date) {
      values.enrollment_date = values.enrollment_date.format('YYYY-MM-DD');
    }
    if (isEdit) {
      updateMutation.mutate({ id: student.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  return (
    <Modal
      title={isEdit ? '编辑学员' : '新增学员'}
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnClose
      width={600}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item name="name" label="姓名" rules={[{ required: true, message: '请输入姓名' }]}>
          <Input placeholder="请输入姓名" />
        </Form.Item>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Form.Item name="phone" label="手机号" rules={[{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }]}>
            <Input placeholder="请输入手机号" />
          </Form.Item>

          <Form.Item name="wechat" label="微信号">
            <Input placeholder="请输入微信号" />
          </Form.Item>

          <Form.Item name="parent_phone" label="家长电话" rules={[{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }]}>
            <Input placeholder="请输入家长电话" />
          </Form.Item>

          <Form.Item name="class_name" label="班级名称">
            <Input placeholder="如：国考冲刺班" />
          </Form.Item>

          <Form.Item name="gender" label="性别">
            <Select placeholder="请选择" allowClear options={[{ value: '男', label: '男' }, { value: '女', label: '女' }]} />
          </Form.Item>

          <Form.Item name="education" label="学历">
            <Select
              placeholder="请选择"
              allowClear
              options={['高中', '大专', '本科', '硕士', '博士'].map((v) => ({ value: v, label: v }))}
            />
          </Form.Item>

          <Form.Item name="major" label="专业">
            <Input placeholder="请输入专业" />
          </Form.Item>

          <Form.Item name="exam_type" label="报考类型">
            <Input placeholder="如：国考、省考、事业编" />
          </Form.Item>

          <Form.Item name="enrollment_date" label="报名日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          {isEdit && (
            <Form.Item name="status" label="状态">
              <Select
                options={[
                  { value: 'active', label: '在读' },
                  { value: 'inactive', label: '休学' },
                  { value: 'graduated', label: '结业' },
                ]}
              />
            </Form.Item>
          )}
        </div>

        <Form.Item name="notes" label="备注">
          <Input.TextArea rows={3} placeholder="请输入备注信息" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
