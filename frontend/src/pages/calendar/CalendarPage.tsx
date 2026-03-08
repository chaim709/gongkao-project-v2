import { useState } from 'react';
import { Card, Calendar, Badge, Button, Modal, Form, Input, DatePicker, Select, Space, message, Tabs, List, Tag } from 'antd';
import { PlusOutlined, ThunderboltOutlined, CalendarOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { calendarApi } from '../../api/calendar';
import dayjs, { Dayjs } from 'dayjs';
import type { BadgeProps } from 'antd';

const { TextArea } = Input;

const TYPE_MAP: Record<string, { text: string; color: BadgeProps['status'] }> = {
  exam: { text: '考试', color: 'error' },
  course: { text: '课程', color: 'processing' },
  mock: { text: '模考', color: 'success' },
  task: { text: '任务', color: 'warning' },
  custom: { text: '自定义', color: 'default' },
};

export default function CalendarPage() {
  const queryClient = useQueryClient();
  const [currentDate, setCurrentDate] = useState(dayjs());
  const [modalOpen, setModalOpen] = useState(false);
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [aiForm] = Form.useForm();

  const { data: events } = useQuery({
    queryKey: ['calendar-events', currentDate.year(), currentDate.month() + 1],
    queryFn: () => calendarApi.list({ year: currentDate.year(), month: currentDate.month() + 1 }),
  });

  const { data: upcoming } = useQuery({
    queryKey: ['calendar-upcoming'],
    queryFn: () => calendarApi.upcoming(90),
  });

  const createMutation = useMutation({
    mutationFn: calendarApi.create,
    onSuccess: () => {
      message.success('事件已创建');
      setModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
      queryClient.invalidateQueries({ queryKey: ['calendar-upcoming'] });
    },
  });

  const aiParseMutation = useMutation({
    mutationFn: (text: string) => calendarApi.aiParse(text),
  });

  const confirmAiMutation = useMutation({
    mutationFn: calendarApi.confirmAiEvents,
    onSuccess: () => {
      message.success('AI 事件已导入');
      setAiModalOpen(false);
      aiForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
      queryClient.invalidateQueries({ queryKey: ['calendar-upcoming'] });
    },
  });

  const dateCellRender = (value: Dayjs) => {
    const dateStr = value.format('YYYY-MM-DD');
    const dayEvents = (events?.items || []).filter((e: any) => e.start_date === dateStr);

    return (
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {dayEvents.map((e: any) => {
          const typeInfo = TYPE_MAP[e.event_type] || TYPE_MAP.custom;
          return (
            <li key={e.id} style={{ marginBottom: 2 }}>
              <Badge status={typeInfo.color} text={e.title} style={{ fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} />
            </li>
          );
        })}
      </ul>
    );
  };

  const handleCreate = (values: any) => {
    createMutation.mutate({
      ...values,
      start_date: values.start_date.format('YYYY-MM-DD'),
      end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : undefined,
    });
  };

  const handleAiParse = async () => {
    const text = aiForm.getFieldValue('text');
    if (!text) {
      message.warning('请输入公告文本');
      return;
    }
    try {
      const result = await aiParseMutation.mutateAsync(text);
      if (result.events?.length > 0) {
        Modal.confirm({
          title: `AI 解析到 ${result.events.length} 个事件`,
          content: (
            <List
              size="small"
              dataSource={result.events}
              renderItem={(e: any) => (
                <List.Item>
                  <span>{e.title}</span>
                  <Tag color={e.color}>{e.start_date}</Tag>
                </List.Item>
              )}
            />
          ),
          onOk: () => confirmAiMutation.mutate(result.events),
        });
      } else {
        message.warning('未解析到事件');
      }
    } catch (err) {
      message.error('AI 解析失败');
    }
  };

  return (
    <div>
      <Tabs
        items={[
          {
            key: 'calendar',
            label: <><CalendarOutlined /> 日历视图</>,
            children: (
              <Card
                title={`${currentDate.year()}年${currentDate.month() + 1}月`}
                extra={
                  <Space>
                    <Button icon={<ThunderboltOutlined />} onClick={() => setAiModalOpen(true)}>AI 解析</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>新建事件</Button>
                  </Space>
                }
              >
                <Calendar
                  value={currentDate}
                  onSelect={setCurrentDate}
                  cellRender={dateCellRender}
                />
              </Card>
            ),
          },
          {
            key: 'countdown',
            label: '考试倒计时',
            children: (
              <Card title="近期考试倒计时">
                <List
                  dataSource={upcoming?.items || []}
                  renderItem={(item: any) => (
                    <List.Item>
                      <List.Item.Meta
                        title={<><Tag color="red">{item.exam_category || '考试'}</Tag>{item.title}</>}
                        description={`${item.start_date} · ${item.province || '全国'}`}
                      />
                      <div style={{ fontSize: 24, fontWeight: 700, color: item.days_remaining <= 30 ? '#f5222d' : '#1890ff' }}>
                        还剩 {item.days_remaining} 天
                      </div>
                    </List.Item>
                  )}
                  locale={{ emptyText: '暂无近期考试' }}
                />
              </Card>
            ),
          },
        ]}
      />

      <Modal title="新建事件" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="event_type" label="类型" initialValue="exam">
            <Select options={[
              { label: '考试', value: 'exam' },
              { label: '课程', value: 'course' },
              { label: '模考', value: 'mock' },
              { label: '任务', value: 'task' },
            ]} />
          </Form.Item>
          <Form.Item name="exam_category" label="考试类别">
            <Select allowClear options={[
              { label: '国考', value: '国考' },
              { label: '省考', value: '省考' },
              { label: '事业单位', value: '事业单位' },
              { label: '选调生', value: '选调生' },
            ]} />
          </Form.Item>
          <Form.Item name="start_date" label="日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="AI 解析考试公告" open={aiModalOpen} onCancel={() => setAiModalOpen(false)} onOk={handleAiParse} confirmLoading={aiParseMutation.isPending}>
        <Form form={aiForm} layout="vertical">
          <Form.Item name="text" label="粘贴公告文本">
            <TextArea rows={10} placeholder="粘贴考试公告内容，AI 将自动提取考试时间节点..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
