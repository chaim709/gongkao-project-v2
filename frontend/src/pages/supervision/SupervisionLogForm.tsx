import { useEffect, useState } from 'react';
import { Modal, Form, Input, Select, DatePicker, message, Tag, InputNumber } from 'antd';
import { useMutation, useQuery } from '@tanstack/react-query';
import { supervisionApi } from '../../api/supervision';
import { studentApi } from '../../api/students';
import dayjs from 'dayjs';

interface SupervisionLogFormProps {
  open: boolean;
  studentId?: number;
  onClose: () => void;
  onSuccess: () => void;
}

export default function SupervisionLogForm({ open, studentId, onClose, onSuccess }: SupervisionLogFormProps) {
  const [form] = Form.useForm();
  const [searchValue, setSearchValue] = useState('');

  const { data: studentsData } = useQuery({
    queryKey: ['students-select', searchValue],
    queryFn: () => studentApi.list({ page: 1, page_size: 50, search: searchValue || undefined }),
    enabled: open,
  });

  useEffect(() => {
    if (open) {
      form.resetFields();
      form.setFieldsValue({
        log_date: dayjs(),
        student_id: studentId,
      });
    }
  }, [open, studentId, form]);

  const createMutation = useMutation({
    mutationFn: supervisionApi.create,
    onSuccess: () => {
      message.success('日志创建成功');
      onSuccess();
    },
    onError: (err: any) => message.error(err?.message || '创建失败'),
  });

  const handleSubmit = async () => {
    const values = await form.validateFields();
    values.log_date = values.log_date.format('YYYY-MM-DD');
    if (values.next_followup_date) {
      values.next_followup_date = values.next_followup_date.format('YYYY-MM-DD');
    }
    createMutation.mutate(values);
  };

  const QUICK_PHRASES = [
    '学员状态良好，按计划复习中',
    '布置了专项练习，下次检查完成情况',
    '做了心理疏导，缓解考前焦虑',
    '检查模拟卷成绩，分析错题',
    '沟通学习进度，调整复习计划',
    '提醒注意作息，保持良好状态',
  ];

  const insertPhrase = (phrase: string) => {
    const current = form.getFieldValue('content') || '';
    form.setFieldsValue({ content: current ? `${current}\n${phrase}` : phrase });
  };

  const studentOptions = (studentsData?.items || []).map((s: any) => ({
    value: s.id,
    label: `${s.name}${s.phone ? ` (${s.phone})` : ''}`,
  }));

  return (
    <Modal
      title="新增督学日志"
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={createMutation.isPending}
      destroyOnClose
      width={600}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item name="student_id" label="学员" rules={[{ required: true, message: '请选择学员' }]}>
          <Select
            showSearch
            placeholder="搜索并选择学员"
            filterOption={false}
            onSearch={setSearchValue}
            options={studentOptions}
          />
        </Form.Item>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Form.Item name="log_date" label="日期" rules={[{ required: true, message: '请选择日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="contact_method" label="联系方式">
            <Select
              placeholder="请选择"
              allowClear
              options={[
                { value: 'phone', label: '电话' },
                { value: 'wechat', label: '微信' },
                { value: 'meeting', label: '面谈' },
              ]}
            />
          </Form.Item>

          <Form.Item name="contact_duration" label="联系时长（分钟）">
            <InputNumber min={1} placeholder="沟通时长" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="mood" label="心情状态">
            <Select
              placeholder="请选择"
              allowClear
              options={[
                { value: 'positive', label: '积极' },
                { value: 'stable', label: '稳定' },
                { value: 'anxious', label: '焦虑' },
                { value: 'down', label: '低落' },
              ]}
            />
          </Form.Item>

          <Form.Item name="study_status" label="学习状态">
            <Select
              placeholder="请选择"
              allowClear
              options={[
                { value: 'excellent', label: '优秀' },
                { value: 'good', label: '良好' },
                { value: 'average', label: '一般' },
                { value: 'poor', label: '较差' },
              ]}
            />
          </Form.Item>
        </div>

        <Form.Item name="content" label="督学内容" rules={[{ required: true, message: '请输入督学内容' }]}>
          <Input.TextArea rows={4} placeholder="记录今天的督学内容" />
        </Form.Item>
        <div style={{ marginBottom: 16 }}>
          <span style={{ fontSize: 12, color: '#999', marginRight: 8 }}>常用短语：</span>
          {QUICK_PHRASES.map((p) => (
            <Tag key={p} style={{ cursor: 'pointer', marginBottom: 4 }} onClick={() => insertPhrase(p)}>{p}</Tag>
          ))}
        </div>

        <Form.Item name="next_followup_date" label="下次跟进日期">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
