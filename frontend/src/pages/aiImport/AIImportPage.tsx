import { useState } from 'react';
import {
  Card, Button, Upload, Select, Steps, Table, Tag, Space,
  message, Alert, Descriptions, Statistic, Row, Col, Input,
  Modal,
} from 'antd';
import {
  UploadOutlined, RobotOutlined, CheckCircleOutlined,
  FileTextOutlined, DatabaseOutlined, EditOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { examApi } from '../../api/exams';
import type { ColumnsType } from 'antd/es/table';

interface ParsedQuestion {
  question_number: number;
  question_type: string;
  stem: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  answer: string;
  analysis?: string;
  category?: string;
  subcategory?: string;
  knowledge_point?: string;
  difficulty?: string;
  key_technique?: string;
  common_mistake?: string;
  is_image_question: boolean;
  ai_confidence?: number;
}

interface ParseResult {
  subject: string;
  total_questions: number;
  questions: ParsedQuestion[];
  summary: Record<string, number>;
}

type StepKey = 'upload' | 'preview' | 'import';

const difficultyColors: Record<string, string> = {
  easy: 'green', medium: 'orange', hard: 'red',
};
const difficultyLabels: Record<string, string> = {
  easy: '简单', medium: '中等', hard: '困难',
};

export default function AIImportPage() {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [subject, setSubject] = useState<string>('行测');
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<number[]>([]);
  const [paperId, setPaperId] = useState<number>();
  const [editingQuestion, setEditingQuestion] = useState<ParsedQuestion | null>(null);
  const [editOpen, setEditOpen] = useState(false);

  const stepKey: StepKey = currentStep === 0 ? 'upload' : currentStep === 1 ? 'preview' : 'import';

  // 试卷列表
  const { data: papers } = useQuery({
    queryKey: ['exam-papers-select'],
    queryFn: () => examApi.listPapers({ page: 1, page_size: 100 }),
  });

  // AI 解析
  const parseMutation = useMutation({
    mutationFn: () => examApi.aiParse(file!, subject),
    onSuccess: (data: ParseResult) => {
      setParseResult(data);
      setSelectedKeys(data.questions.map(q => q.question_number));
      setCurrentStep(1);
      message.success(`成功解析 ${data.total_questions} 道题目`);
    },
    onError: (err: { detail?: string }) => {
      message.error(err?.detail || 'AI 解析失败，请检查文件格式');
    },
  });

  // 批量入库
  const importMutation = useMutation({
    mutationFn: (questions: Record<string, unknown>[]) => examApi.batchCreateQuestions(questions),
    onSuccess: (data: { count: number }) => {
      message.success(`成功导入 ${data.count} 道题目`);
      setCurrentStep(2);
      queryClient.invalidateQueries({ queryKey: ['exam-questions'] });
    },
    onError: () => message.error('导入失败'),
  });

  const handleImport = () => {
    if (!parseResult) return;
    const selected = parseResult.questions
      .filter(q => selectedKeys.includes(q.question_number))
      .map(q => ({
        ...q,
        paper_id: paperId || undefined,
        source: 'ai_import',
      }));
    importMutation.mutate(selected);
  };

  // 编辑单题
  const handleEditSave = () => {
    if (!editingQuestion || !parseResult) return;
    setParseResult({
      ...parseResult,
      questions: parseResult.questions.map(q =>
        q.question_number === editingQuestion.question_number ? editingQuestion : q
      ),
    });
    setEditOpen(false);
    message.success('已更新');
  };

  const columns: ColumnsType<ParsedQuestion> = [
    { title: '题号', dataIndex: 'question_number', width: 60, align: 'center' },
    {
      title: '题干', dataIndex: 'stem', ellipsis: true,
      render: (v: string) => v ? (v.length > 60 ? v.slice(0, 60) + '...' : v) : <Tag color="orange">图形题</Tag>,
    },
    { title: '答案', dataIndex: 'answer', width: 60, align: 'center' },
    {
      title: '分类', dataIndex: 'subcategory', width: 120,
      render: (v: string) => v || '-',
    },
    {
      title: '难度', dataIndex: 'difficulty', width: 70, align: 'center',
      render: (v: string) => v ? <Tag color={difficultyColors[v]}>{difficultyLabels[v] || v}</Tag> : '-',
    },
    {
      title: '置信度', dataIndex: 'ai_confidence', width: 80, align: 'center',
      render: (v: number) => v ? (
        <span style={{ color: v >= 0.9 ? '#52c41a' : v >= 0.7 ? '#faad14' : '#ff4d4f' }}>
          {(v * 100).toFixed(0)}%
        </span>
      ) : '-',
    },
    {
      title: '操作', key: 'action', width: 60, align: 'center',
      render: (_, r: ParsedQuestion) => (
        <Button type="link" size="small" icon={<EditOutlined />} onClick={() => {
          setEditingQuestion({ ...r });
          setEditOpen(true);
        }}>
          编辑
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Steps
        current={currentStep}
        style={{ marginBottom: 24 }}
        items={[
          { title: '上传文档', icon: <UploadOutlined /> },
          { title: 'AI 解析预览', icon: <RobotOutlined /> },
          { title: '确认入库', icon: <CheckCircleOutlined /> },
        ]}
      />

      {/* Step 1: 上传 */}
      {stepKey === 'upload' && (
        <Card>
          <Alert
            message="支持 txt/md 格式的题目文档，AI 将自动识别题目结构、分类和难度"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>科目</label>
              <Select
                value={subject}
                onChange={setSubject}
                style={{ width: 200 }}
                options={[
                  { value: '行测', label: '行测' },
                  { value: '申论', label: '申论' },
                  { value: '公基', label: '公基' },
                  { value: '职测', label: '职测' },
                ]}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>关联试卷（可选）</label>
              <Select
                value={paperId}
                onChange={setPaperId}
                allowClear
                showSearch
                optionFilterProp="label"
                style={{ width: 400 }}
                placeholder="选择要关联的试卷"
                options={(papers?.items || []).map((p: { id: number; title: string }) => ({
                  value: p.id, label: p.title,
                }))}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>上传文档</label>
              <Upload
                beforeUpload={(f) => { setFile(f); return false; }}
                maxCount={1}
                accept=".txt,.md"
                onRemove={() => setFile(null)}
              >
                <Button icon={<UploadOutlined />}>选择文件</Button>
              </Upload>
            </div>
            <Button
              type="primary"
              size="large"
              icon={<RobotOutlined />}
              onClick={() => parseMutation.mutate()}
              loading={parseMutation.isPending}
              disabled={!file}
              style={{ marginTop: 16 }}
            >
              {parseMutation.isPending ? 'AI 正在解析中...' : '开始 AI 解析'}
            </Button>
            {parseMutation.isPending && (
              <Alert
                message="AI 正在分析文档，通常需要 10-30 秒，请耐心等待..."
                type="warning"
                showIcon
              />
            )}
          </Space>
        </Card>
      )}

      {/* Step 2: 预览 */}
      {stepKey === 'preview' && parseResult && (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <Statistic title="解析题目" value={parseResult.total_questions} prefix={<FileTextOutlined />} />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic title="已选择" value={selectedKeys.length} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#1677ff' }} />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic title="科目" value={parseResult.subject} prefix={<FileTextOutlined />} />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Descriptions size="small" column={1}>
                  {Object.entries(parseResult.summary).slice(0, 3).map(([k, v]) => (
                    <Descriptions.Item key={k} label={k}>{v}题</Descriptions.Item>
                  ))}
                </Descriptions>
              </Card>
            </Col>
          </Row>

          <Card
            title="解析结果预览"
            extra={
              <Space>
                <Button onClick={() => { setCurrentStep(0); setParseResult(null); }}>重新上传</Button>
                <Button
                  type="primary"
                  icon={<DatabaseOutlined />}
                  onClick={handleImport}
                  loading={importMutation.isPending}
                  disabled={selectedKeys.length === 0}
                >
                  导入选中 ({selectedKeys.length}) 题
                </Button>
              </Space>
            }
          >
            <Table<ParsedQuestion>
              columns={columns}
              dataSource={parseResult.questions}
              rowKey="question_number"
              size="small"
              pagination={false}
              scroll={{ y: 500 }}
              rowSelection={{
                selectedRowKeys: selectedKeys,
                onChange: (keys) => setSelectedKeys(keys as number[]),
              }}
            />
          </Card>
        </>
      )}

      {/* Step 3: 完成 */}
      {stepKey === 'import' && (
        <Card style={{ textAlign: 'center', padding: '60px 0' }}>
          <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 24 }} />
          <h2>导入完成</h2>
          <p style={{ color: '#999' }}>
            已成功导入 {selectedKeys.length} 道题目到题库
            {paperId && '，已关联到指定试卷'}
          </p>
          <Space style={{ marginTop: 24 }}>
            <Button onClick={() => { setCurrentStep(0); setParseResult(null); setFile(null); setSelectedKeys([]); }}>
              继续导入
            </Button>
            <Button type="primary" onClick={() => window.location.href = '/questions'}>
              查看题库
            </Button>
          </Space>
        </Card>
      )}

      {/* 编辑题目弹窗 */}
      <Modal
        title={`编辑第 ${editingQuestion?.question_number} 题`}
        open={editOpen}
        onOk={handleEditSave}
        onCancel={() => setEditOpen(false)}
        width={700}
      >
        {editingQuestion && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div>
              <label>题干</label>
              <Input.TextArea
                value={editingQuestion.stem}
                onChange={e => setEditingQuestion({ ...editingQuestion, stem: e.target.value })}
                rows={3}
              />
            </div>
            <Row gutter={16}>
              <Col span={12}>
                <label>选项A</label>
                <Input value={editingQuestion.option_a} onChange={e => setEditingQuestion({ ...editingQuestion, option_a: e.target.value })} />
              </Col>
              <Col span={12}>
                <label>选项B</label>
                <Input value={editingQuestion.option_b} onChange={e => setEditingQuestion({ ...editingQuestion, option_b: e.target.value })} />
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <label>选项C</label>
                <Input value={editingQuestion.option_c} onChange={e => setEditingQuestion({ ...editingQuestion, option_c: e.target.value })} />
              </Col>
              <Col span={12}>
                <label>选项D</label>
                <Input value={editingQuestion.option_d} onChange={e => setEditingQuestion({ ...editingQuestion, option_d: e.target.value })} />
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={6}>
                <label>答案</label>
                <Select
                  value={editingQuestion.answer}
                  onChange={v => setEditingQuestion({ ...editingQuestion, answer: v })}
                  style={{ width: '100%' }}
                  options={['A', 'B', 'C', 'D'].map(v => ({ value: v, label: v }))}
                />
              </Col>
              <Col span={6}>
                <label>难度</label>
                <Select
                  value={editingQuestion.difficulty}
                  onChange={v => setEditingQuestion({ ...editingQuestion, difficulty: v })}
                  style={{ width: '100%' }}
                  options={[
                    { value: 'easy', label: '简单' },
                    { value: 'medium', label: '中等' },
                    { value: 'hard', label: '困难' },
                  ]}
                />
              </Col>
              <Col span={12}>
                <label>二级分类</label>
                <Input
                  value={editingQuestion.subcategory}
                  onChange={e => setEditingQuestion({ ...editingQuestion, subcategory: e.target.value })}
                />
              </Col>
            </Row>
            <div>
              <label>解析</label>
              <Input.TextArea
                value={editingQuestion.analysis || ''}
                onChange={e => setEditingQuestion({ ...editingQuestion, analysis: e.target.value })}
                rows={2}
              />
            </div>
          </Space>
        )}
      </Modal>
    </div>
  );
}
