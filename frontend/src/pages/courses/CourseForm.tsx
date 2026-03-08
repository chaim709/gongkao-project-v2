import { useEffect } from 'react';
import { Modal, Form, Input, Select, DatePicker, message } from 'antd';
import { useMutation } from '@tanstack/react-query';
import { courseApi } from '../../api/courses';
import type { Course, CourseUpdate } from '../../types/course';
import dayjs from 'dayjs';

interface CourseFormProps {
  open: boolean;
  course: Course | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CourseForm({ open, course, onClose, onSuccess }: CourseFormProps) {
  const [form] = Form.useForm();
  const isEdit = !!course;

  useEffect(() => {
    if (open) {
      if (course) {
        form.setFieldsValue({
          ...course,
          start_date: course.start_date ? dayjs(course.start_date) : undefined,
          end_date: course.end_date ? dayjs(course.end_date) : undefined,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, course, form]);

  const createMutation = useMutation({
    mutationFn: courseApi.create,
    onSuccess: () => { message.success('创建成功'); onSuccess(); },
    onError: (err: any) => message.error(err?.message || '创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CourseUpdate }) => courseApi.update(id, data),
    onSuccess: () => { message.success('更新成功'); onSuccess(); },
    onError: (err: any) => message.error(err?.message || '更新失败'),
  });

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (values.start_date) values.start_date = values.start_date.format('YYYY-MM-DD');
    if (values.end_date) values.end_date = values.end_date.format('YYYY-MM-DD');
    if (isEdit) {
      updateMutation.mutate({ id: course.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  return (
    <Modal
      title={isEdit ? '编辑课程' : '新增课程'}
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      destroyOnClose
      width={600}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item name="name" label="课程名称" rules={[{ required: true, message: '请输入课程名称' }]}>
          <Input placeholder="请输入课程名称" />
        </Form.Item>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Form.Item name="course_type" label="课程类型">
            <Input placeholder="如：行测、申论、面试" />
          </Form.Item>

          <Form.Item name="start_date" label="开始日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="end_date" label="结束日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          {isEdit && (
            <Form.Item name="status" label="状态">
              <Select options={[
                { value: 'active', label: '进行中' },
                { value: 'completed', label: '已结束' },
                { value: 'cancelled', label: '已取消' },
              ]} />
            </Form.Item>
          )}
        </div>

        <Form.Item name="description" label="课程描述">
          <Input.TextArea rows={3} placeholder="请输入课程描述" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
