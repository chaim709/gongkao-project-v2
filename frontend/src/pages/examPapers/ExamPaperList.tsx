import { useState } from 'react';
import {
  Table, Input, Select, Button, Space, Tag, Card, Row, Col, Statistic,
  Modal, Form, InputNumber, message, Image, Drawer, Descriptions,
} from 'antd';
import {
  PlusOutlined, SearchOutlined, QrcodeOutlined, FileTextOutlined,
  BookOutlined, ReloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { examApi } from '../../api/exams';
import type { ColumnsType } from 'antd/es/table';

interface ExamPaper {
  id: number;
  title: string;
  exam_type: string;
  subject: string;
  total_questions: number;
  time_limit: number;
  year: number;
  source: string;
  qr_code_token: string;
  description: string;
  created_at: string;
}

const subjectColors: Record<string, string> = {
  '行测': 'blue', '申论': 'green', '公基': 'orange', '职测': 'purple',
};

export default function ExamPaperList() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState<string>();
  const [createOpen, setCreateOpen] = useState(false);
  const [qrOpen, setQrOpen] = useState(false);
  const [selectedPaper, setSelectedPaper] = useState<ExamPaper | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['exam-papers', params, search, subject],
    queryFn: () => examApi.listPapers({ ...params, search: search || undefined, subject }),
  });

  const createMutation = useMutation({
    mutationFn: examApi.createPaper,
    onSuccess: () => {
      message.success('试卷创建成功，二维码已自动生��');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['exam-papers'] });
    },
    onError: () => message.error('创建失败'),
  });

  const handleCreate = () => {
    form.validateFields().then((values) => {
      createMutation.mutate(values);
    });
  };

  const showQrCode = (paper: ExamPaper) => {
    setSelectedPaper(paper);
    setQrOpen(true);
  };

  const columns: ColumnsType<ExamPaper> = [
    {
      title: '试卷名称', dataIndex: 'title', ellipsis: true,
      render: (v: string, r: ExamPaper) => (
        <a onClick={() => { setSelectedPaper(r); setDetailOpen(true); }}>{v}</a>
      ),
    },
    {
      title: '科目', dataIndex: 'subject', width: 80, align: 'center',
      render: (v: string) => <Tag color={subjectColors[v] || 'default'}>{v}</Tag>,
    },
    { title: '考试类型', dataIndex: 'exam_type', width: 100 },
    { title: '题数', dataIndex: 'total_questions', width: 60, align: 'center' },
    {
      title: '时限', dataIndex: 'time_limit', width: 80, align: 'center',
      render: (v: number) => v ? `${v}分钟` : '-',
    },
    { title: '年份', dataIndex: 'year', width: 60 },
    {
      title: '来源', dataIndex: 'source', width: 80,
      render: (v: string) => v || '-',
    },
    {
      title: '操作', key: 'action', width: 120, align: 'center',
      render: (_, record: ExamPaper) => (
        <Space>
          <Button type="link" size="small" icon={<QrcodeOutlined />} onClick={() => showQrCode(record)}>
            二维码
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="试卷总数" value={data?.total || 0} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="行测" value={(data?.items || []).filter((p: ExamPaper) => p.subject === '行测').length} prefix={<BookOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="申论" value={(data?.items || []).filter((p: ExamPaper) => p.subject === '申论').length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="公基/职测" value={(data?.items || []).filter((p: ExamPaper) => p.subject === '公基' || p.subject === '职测').length} />
          </Card>
        </Col>
      </Row>

      {/* 筛选 + 操作 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', gap: 8 }}>
        <Space>
          <Input
            placeholder="搜索试卷名称"
            prefix={<SearchOutlined />}
            style={{ width: 220 }}
            allowClear
            onChange={(e) => { setSearch(e.target.value); setParams(p => ({ ...p, page: 1 })); }}
          />
          <Select
            placeholder="科目"
            allowClear
            style={{ width: 100 }}
            onChange={(v) => { setSubject(v); setParams(p => ({ ...p, page: 1 })); }}
            options={[
              { value: '行测', label: '行测' },
              { value: '申论', label: '申论' },
              { value: '公基', label: '公基' },
              { value: '职测', label: '职测' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={() => { setSearch(''); setSubject(undefined); setParams({ page: 1, page_size: 20 }); }}>
            重置
          </Button>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          新建试卷
        </Button>
      </div>

      {/* 表格 */}
      <Table<ExamPaper>
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: data?.total || 0,
          showTotal: (total) => `共 ${total} 套试卷`,
          onChange: (page, pageSize) => setParams({ page, page_size: pageSize }),
        }}
        size="middle"
      />

      {/* 新建试卷 */}
      <Modal
        title="新建试卷"
        open={createOpen}
        onOk={handleCreate}
        onCancel={() => setCreateOpen(false)}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="试卷名称" rules={[{ required: true }]}>
            <Input placeholder="如：2025年江苏省考行测模拟卷（第3期）" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="subject" label="科目" rules={[{ required: true }]}>
                <Select options={[
                  { value: '行测', label: '行测' },
                  { value: '申论', label: '申论' },
                  { value: '公基', label: '公基' },
                  { value: '职测', label: '职测' },
                ]} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="total_questions" label="总题数" rules={[{ required: true }]}>
                <InputNumber min={1} max={300} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="time_limit" label="时限(分钟)">
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="exam_type" label="考试类型">
                <Select allowClear options={[
                  { value: '国考', label: '国考' },
                  { value: '省考', label: '省考' },
                  { value: '事业单位', label: '事业单位' },
                ]} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="year" label="年份">
                <InputNumber min={2020} max={2030} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="source" label="来源">
                <Select allowClear options={[
                  { value: '真题', label: '真题' },
                  { value: '模拟', label: '模拟' },
                  { value: '自编', label: '自编' },
                ]} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 二维码弹窗 */}
      <Modal
        title={`${selectedPaper?.title} - 错题提交二维码`}
        open={qrOpen}
        onCancel={() => setQrOpen(false)}
        footer={[
          <Button key="print" type="primary" onClick={() => {
            const img = document.getElementById('qr-img') as HTMLImageElement;
            if (img) {
              const win = window.open('');
              if (win) {
                win.document.write(`<div style="text-align:center;padding:40px">
                  <h2>${selectedPaper?.title}</h2>
                  <p>扫码提交错题</p>
                  <img src="${img.src}" style="width:300px;height:300px" />
                  <p style="color:#999;margin-top:16px">共${selectedPaper?.total_questions}题 · ${selectedPaper?.subject}</p>
                </div>`);
                win.document.close();
                setTimeout(() => win.print(), 300);
              }
            }
          }}>
            打印二维码
          </Button>,
        ]}
      >
        {selectedPaper && (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Image
              id="qr-img"
              src={`/api/v1/exams/papers/${selectedPaper.id}/qrcode`}
              width={200}
              preview={false}
            />
            <p style={{ marginTop: 16, color: '#666' }}>
              学生扫码后输入手机号和错题题号即可提交
            </p>
            <p style={{ color: '#999', fontSize: 12 }}>
              {selectedPaper.subject} · {selectedPaper.total_questions}题
              {selectedPaper.time_limit ? ` · ${selectedPaper.time_limit}分钟` : ''}
            </p>
          </div>
        )}
      </Modal>

      {/* 试卷详情 */}
      <Drawer
        title={selectedPaper?.title || '试卷详情'}
        open={detailOpen}
        onClose={() => { setDetailOpen(false); setSelectedPaper(null); }}
        width={480}
      >
        {selectedPaper && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="科目"><Tag color={subjectColors[selectedPaper.subject]}>{selectedPaper.subject}</Tag></Descriptions.Item>
              <Descriptions.Item label="考试类型">{selectedPaper.exam_type || '-'}</Descriptions.Item>
              <Descriptions.Item label="总题数">{selectedPaper.total_questions}</Descriptions.Item>
              <Descriptions.Item label="时限">{selectedPaper.time_limit ? `${selectedPaper.time_limit}分钟` : '-'}</Descriptions.Item>
              <Descriptions.Item label="年份">{selectedPaper.year || '-'}</Descriptions.Item>
              <Descriptions.Item label="来源">{selectedPaper.source || '-'}</Descriptions.Item>
            </Descriptions>
            <Button block icon={<QrcodeOutlined />} onClick={() => { setDetailOpen(false); showQrCode(selectedPaper); }}>
              查看二维码
            </Button>
          </Space>
        )}
      </Drawer>
    </div>
  );
}
