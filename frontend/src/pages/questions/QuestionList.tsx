import { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { questionApi } from '../../api/questions';
import type { Question } from '../../types/question';

export default function QuestionList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [formOpen, setFormOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['questions', params],
    queryFn: () => questionApi.listQuestions(params),
  });

  const createMutation = useMutation({
    mutationFn: questionApi.createQuestion,
    onSuccess: () => {
      message.success('创建成功');
      setFormOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
    onError: () => message.error('创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Question> }) =>
      questionApi.updateQuestion(id, data),
    onSuccess: () => {
      message.success('更新成功');
      setFormOpen(false);
      setEditingQuestion(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
    onError: () => message.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: questionApi.deleteQuestion,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
    onError: () => message.error('删除失败'),
  });

  const handleCreate = () => {
    setEditingQuestion(null);
    form.resetFields();
    setFormOpen(true);
  };

  const handleEdit = (question: Question) => {
    setEditingQuestion(question);
    form.setFieldsValue(question);
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingQuestion) {
      updateMutation.mutate({ id: editingQuestion.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这道题目吗？',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '题干', dataIndex: 'stem', ellipsis: true },
    { title: '答案', dataIndex: 'answer', width: 60 },
    { title: '类别', dataIndex: 'category', width: 100, render: (v: string) => v || '-' },
    { title: '难度', dataIndex: 'difficulty', width: 80, render: (v: string) => v || '-' },
    { title: '知识点', dataIndex: 'knowledge_point', width: 120, render: (v: string) => v || '-' },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Question) => (
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
        <Space>
          <Select
            placeholder="类别筛选"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => setParams((prev) => ({ ...prev, page: 1, category: v }))}
            options={[
              { value: '行测', label: '行测' },
              { value: '申论', label: '申论' },
            ]}
          />
          <Select
            placeholder="难度筛选"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => setParams((prev) => ({ ...prev, page: 1, difficulty: v }))}
            options={[
              { value: '简单', label: '简单' },
              { value: '中等', label: '中等' },
              { value: '困难', label: '困难' },
            ]}
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建题目
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
        title={editingQuestion ? '编辑题目' : '新建题目'}
        open={formOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setFormOpen(false);
          setEditingQuestion(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
        width={800}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="stem" label="题干" rules={[{ required: true, message: '请输入题干' }]}>
            <Input.TextArea rows={4} placeholder="题目内容" />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="option_a" label="选项A">
              <Input placeholder="选项A内容" />
            </Form.Item>
            <Form.Item name="option_b" label="选项B">
              <Input placeholder="选项B内容" />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="option_c" label="选项C">
              <Input placeholder="选项C内容" />
            </Form.Item>
            <Form.Item name="option_d" label="选项D">
              <Input placeholder="选项D内容" />
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <Form.Item name="answer" label="答案" rules={[{ required: true, message: '请输入答案' }]}>
              <Input placeholder="如：A" />
            </Form.Item>
            <Form.Item name="category" label="类别">
              <Select placeholder="选择类别" options={[{ value: '行测', label: '行测' }, { value: '申论', label: '申论' }]} />
            </Form.Item>
            <Form.Item name="difficulty" label="难度">
              <Select placeholder="选择难度" options={[{ value: '简单', label: '简单' }, { value: '中等', label: '中等' }, { value: '困难', label: '困难' }]} />
            </Form.Item>
          </div>
          <Form.Item name="knowledge_point" label="知识点">
            <Input placeholder="如：数量关系" />
          </Form.Item>
          <Form.Item name="analysis" label="解析">
            <Input.TextArea rows={3} placeholder="题目解析" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
