import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Table, Space, Tag, Modal, Form, Input, DatePicker, Select, InputNumber, message, Spin } from 'antd';
import { PlusOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studyPlanApi } from '../../api/studyPlans';
import type { PlanTask } from '../../types/studyPlan';
import dayjs from 'dayjs';

export default function StudyPlanDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [taskFormOpen, setTaskFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<PlanTask | null>(null);
  const [form] = Form.useForm();

  const { data: plan, isLoading: planLoading } = useQuery({
    queryKey: ['study-plan', id],
    queryFn: () => studyPlanApi.get(Number(id)),
  });

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['study-plan-tasks', id],
    queryFn: () => studyPlanApi.listTasks(Number(id)),
  });

  const createTaskMutation = useMutation({
    mutationFn: (data: any) => studyPlanApi.createTask(Number(id), data),
    onSuccess: () => {
      message.success('任务创建成功');
      setTaskFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['study-plan-tasks', id] });
    },
    onError: () => message.error('任务创建失败'),
  });

  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: any }) =>
      studyPlanApi.updateTask(taskId, data),
    onSuccess: () => {
      message.success('任务更新成功');
      setTaskFormOpen(false);
      setEditingTask(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['study-plan-tasks', id] });
    },
    onError: () => message.error('任务更新失败'),
  });

  const deleteTaskMutation = useMutation({
    mutationFn: studyPlanApi.deleteTask,
    onSuccess: () => {
      message.success('任务删除成功');
      queryClient.invalidateQueries({ queryKey: ['study-plan-tasks', id] });
    },
    onError: () => message.error('任务删除失败'),
  });

  const handleCreateTask = () => {
    setEditingTask(null);
    form.resetFields();
    setTaskFormOpen(true);
  };

  const handleEditTask = (task: PlanTask) => {
    setEditingTask(task);
    form.setFieldsValue({
      ...task,
      due_date: task.due_date ? dayjs(task.due_date) : null,
    });
    setTaskFormOpen(true);
  };

  const handleSubmitTask = async () => {
    const values = await form.validateFields();
    if (values.due_date) {
      values.due_date = values.due_date.format('YYYY-MM-DD');
    }

    if (editingTask) {
      updateTaskMutation.mutate({ taskId: editingTask.id, data: values });
    } else {
      createTaskMutation.mutate(values);
    }
  };

  const handleDeleteTask = (taskId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个任务吗？',
      onOk: () => deleteTaskMutation.mutate(taskId),
    });
  };

  const handleStatusChange = (task: PlanTask, newStatus: string) => {
    updateTaskMutation.mutate({
      taskId: task.id,
      data: { status: newStatus },
    });
  };

  if (planLoading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!plan) return <div>计划不存在</div>;

  const statusColorMap: Record<string, string> = {
    active: 'green',
    completed: 'blue',
    cancelled: 'default',
  };

  const taskColumns = [
    { title: '任务标题', dataIndex: 'title', ellipsis: true },
    { title: '类型', dataIndex: 'task_type', width: 100, render: (v: string) => v || '-' },
    {
      title: '目标/完成',
      key: 'progress',
      width: 120,
      render: (_: any, record: PlanTask) => (
        <span>
          {record.actual_value} / {record.target_value || '-'}
        </span>
      ),
    },
    {
      title: '截止日期',
      dataIndex: 'due_date',
      width: 110,
      render: (v: string) => (v ? dayjs(v).format('YYYY-MM-DD') : '-'),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 80,
      render: (v: number) => v || 0,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: string, record: PlanTask) => (
        <Select
          value={status}
          size="small"
          style={{ width: 90 }}
          onChange={(v) => handleStatusChange(record, v)}
          options={[
            { value: 'pending', label: '待开始' },
            { value: 'in_progress', label: '进行中' },
            { value: 'completed', label: '已完成' },
            { value: 'cancelled', label: '已取消' },
          ]}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: PlanTask) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEditTask(record)}>
            编辑
          </Button>
          <Button type="link" size="small" danger onClick={() => handleDeleteTask(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/study-plans')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card title="学习计划详情" style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="计划名称">{plan.name}</Descriptions.Item>
          <Descriptions.Item label="学员">{plan.student_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="阶段">{plan.phase || '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColorMap[plan.status]}>{plan.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="开始日期">{dayjs(plan.start_date).format('YYYY-MM-DD')}</Descriptions.Item>
          <Descriptions.Item label="结束日期">
            {plan.end_date ? dayjs(plan.end_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="任务进度" span={2}>
            {plan.completed_task_count} / {plan.task_count}
          </Descriptions.Item>
          {plan.ai_suggestion && (
            <Descriptions.Item label="AI建议" span={2}>
              {plan.ai_suggestion}
            </Descriptions.Item>
          )}
          {plan.notes && (
            <Descriptions.Item label="备注" span={2}>
              {plan.notes}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Card
        title="任务列表"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateTask}>
            新建任务
          </Button>
        }
      >
        <Table
          columns={taskColumns}
          dataSource={tasks || []}
          rowKey="id"
          loading={tasksLoading}
          pagination={false}
          scroll={{ x: 900 }}
        />
      </Card>

      <Modal
        title={editingTask ? '编辑任务' : '新建任务'}
        open={taskFormOpen}
        onOk={handleSubmitTask}
        onCancel={() => {
          setTaskFormOpen(false);
          setEditingTask(null);
          form.resetFields();
        }}
        confirmLoading={createTaskMutation.isPending || updateTaskMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="title" label="任务标题" rules={[{ required: true, message: '请输入任务标题' }]}>
            <Input placeholder="如：完成行测真题10套" />
          </Form.Item>
          <Form.Item name="description" label="任务描述">
            <Input.TextArea rows={3} placeholder="详细说明" />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="task_type" label="任务类型">
              <Select
                placeholder="选择类型"
                allowClear
                options={[
                  { value: '刷题', label: '刷题' },
                  { value: '背诵', label: '背诵' },
                  { value: '复习', label: '复习' },
                  { value: '模考', label: '模考' },
                ]}
              />
            </Form.Item>
            <Form.Item name="priority" label="优先级">
              <InputNumber min={0} max={10} placeholder="0-10" style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="target_value" label="目标值">
              <InputNumber min={1} placeholder="如：10套题" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="actual_value" label="完成值">
              <InputNumber min={0} placeholder="已完成" style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <Form.Item name="due_date" label="截止日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          {editingTask && (
            <Form.Item name="status" label="状态">
              <Select
                options={[
                  { value: 'pending', label: '待开始' },
                  { value: 'in_progress', label: '进行中' },
                  { value: 'completed', label: '已完成' },
                  { value: 'cancelled', label: '已取消' },
                ]}
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
