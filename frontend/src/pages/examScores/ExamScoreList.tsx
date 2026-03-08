import { useState } from 'react';
import {
  Table, Select, Button, Space, Tag, Card, Row, Col, Statistic,
  Modal, Form, InputNumber, message,
} from 'antd';
import {
  PlusOutlined, TrophyOutlined, RiseOutlined,
  TeamOutlined, ReloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { examApi } from '../../api/exams';
import type { ColumnsType } from 'antd/es/table';

interface ScoreItem {
  id: number;
  student_id: number;
  student_name: string;
  paper_id: number;
  paper_title: string;
  subject: string;
  total_questions: number;
  correct_count: number;
  wrong_count: number;
  accuracy: number;
  time_used: number | null;
  rank_in_class: number | null;
  submitted_at: string;
}

const subjectColors: Record<string, string> = {
  '行测': 'blue', '申论': 'green', '公基': 'orange', '职测': 'purple',
};

export default function ExamScoreList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [paperId, setPaperId] = useState<number>();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['exam-scores', params, paperId],
    queryFn: () => examApi.listScores({ ...params, paper_id: paperId }),
  });

  // 试卷下拉
  const { data: papers } = useQuery({
    queryKey: ['exam-papers-select'],
    queryFn: () => examApi.listPapers({ page: 1, page_size: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: examApi.createScore,
    onSuccess: () => {
      message.success('成绩录入成功');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['exam-scores'] });
    },
    onError: (err: { detail?: string }) => message.error(err?.detail || '录入失败，可能已有记录'),
  });

  const items: ScoreItem[] = data?.items || [];
  const avgAccuracy = items.length
    ? (items.reduce((s, i) => s + i.accuracy, 0) / items.length).toFixed(1)
    : '0';

  const columns: ColumnsType<ScoreItem> = [
    { title: '学员', dataIndex: 'student_name', width: 100 },
    {
      title: '试卷', dataIndex: 'paper_title', width: 220, ellipsis: true,
    },
    {
      title: '科目', dataIndex: 'subject', width: 70, align: 'center',
      render: (v: string) => <Tag color={subjectColors[v] || 'default'}>{v}</Tag>,
    },
    {
      title: '正确', dataIndex: 'correct_count', width: 60, align: 'center',
      render: (v: number) => <span style={{ color: '#52c41a', fontWeight: 600 }}>{v}</span>,
    },
    {
      title: '错误', dataIndex: 'wrong_count', width: 60, align: 'center',
      render: (v: number) => <span style={{ color: v > 0 ? '#ff4d4f' : '#333', fontWeight: 600 }}>{v}</span>,
    },
    {
      title: '正确率', dataIndex: 'accuracy', width: 90, align: 'center',
      sorter: (a, b) => a.accuracy - b.accuracy,
      render: (v: number) => (
        <span style={{
          fontWeight: 700,
          color: v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f',
        }}>
          {v}%
        </span>
      ),
    },
    {
      title: '用时', dataIndex: 'time_used', width: 70, align: 'center',
      render: (v: number | null) => v ? `${v}分钟` : '-',
    },
    {
      title: '提交时间', dataIndex: 'submitted_at', width: 150,
      render: (v: string) => v ? new Date(v).toLocaleString('zh-CN') : '-',
    },
  ];

  return (
    <div>
      {/* 统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="成绩记录" value={data?.total || 0} prefix={<TrophyOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="平均正确率" value={avgAccuracy} suffix="%" prefix={<RiseOutlined />} valueStyle={{ color: '#1677ff' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="参与学员" value={new Set(items.map(i => i.student_id)).size} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="涉及试卷" value={new Set(items.map(i => i.paper_id)).size} prefix={<TrophyOutlined />} />
          </Card>
        </Col>
      </Row>

      {/* 筛选 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', gap: 8 }}>
        <Space>
          <Select
            placeholder="按试卷筛选"
            allowClear
            style={{ width: 280 }}
            showSearch
            optionFilterProp="label"
            onChange={(v) => { setPaperId(v); setParams(p => ({ ...p, page: 1 })); }}
            options={(papers?.items || []).map((p: { id: number; title: string }) => ({
              value: p.id, label: p.title,
            }))}
          />
          <Button icon={<ReloadOutlined />} onClick={() => { setPaperId(undefined); setParams({ page: 1, page_size: 20 }); }}>
            重置
          </Button>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          手动录入
        </Button>
      </div>

      {/* 表格 */}
      <Table<ScoreItem>
        columns={columns}
        dataSource={items}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: data?.total || 0,
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: (page, pageSize) => setParams({ page, page_size: pageSize }),
        }}
        size="middle"
      />

      {/* 手动录入成绩 */}
      <Modal
        title="手动录入模考成绩"
        open={createOpen}
        onOk={() => form.validateFields().then(v => createMutation.mutate(v))}
        onCancel={() => setCreateOpen(false)}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="paper_id" label="试卷" rules={[{ required: true, message: '请选择试卷' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="选择试卷"
              options={(papers?.items || []).map((p: { id: number; title: string; total_questions: number }) => ({
                value: p.id, label: `${p.title} (${p.total_questions}题)`,
              }))}
            />
          </Form.Item>
          <Form.Item name="student_id" label="学员ID" rules={[{ required: true, message: '请输入学员ID' }]}>
            <InputNumber min={1} style={{ width: '100%' }} placeholder="输入学员ID" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="correct_count" label="正确题数" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="wrong_count" label="错误题数" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="time_used" label="用时(分钟)">
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}
