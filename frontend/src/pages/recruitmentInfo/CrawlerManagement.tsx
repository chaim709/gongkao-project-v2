import { useState } from 'react';
import { Card, Table, Switch, Badge, Button, Modal, Form, InputNumber, Descriptions, Statistic, Row, Col, message, Space, Tag, Input, Alert, Divider } from 'antd';
import { ReloadOutlined, LoginOutlined, SettingOutlined, CheckCircleOutlined, CloseCircleOutlined, RobotOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recruitmentInfoApi } from '../../api/recruitmentInfo';
import type { CrawlerConfig, CrawlerStatus } from '../../types/recruitmentInfo';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

export default function CrawlerManagement() {
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [cookieOpen, setCookieOpen] = useState(false);
  const [cookieText, setCookieText] = useState('');
  const [editingConfig, setEditingConfig] = useState<CrawlerConfig | null>(null);
  const [form] = Form.useForm();

  // 获取采集器状态，每30秒刷新
  const { data, isLoading } = useQuery({
    queryKey: ['crawler-status'],
    queryFn: () => recruitmentInfoApi.getCrawlerStatus(),
    refetchInterval: 30000,
  });

  const crawlerStatus = data as unknown as CrawlerStatus | undefined;
  const configs = crawlerStatus?.configs || [];

  // 计算汇总数据
  const totalCrawled = configs.reduce((sum, c) => sum + (c.total_crawled || 0), 0);
  const lastCrawlAt = configs
    .filter(c => c.last_crawl_at)
    .sort((a, b) => (b.last_crawl_at || '').localeCompare(a.last_crawl_at || ''))[0]?.last_crawl_at;

  // 手动采集
  const crawlMutation = useMutation({
    mutationFn: () => recruitmentInfoApi.triggerCrawl(),
    onSuccess: () => {
      message.success('采集任务已触发');
      queryClient.invalidateQueries({ queryKey: ['crawler-status'] });
    },
    onError: () => {
      message.error('触发采集失败');
    },
  });

  // 导入 Cookie
  const loginMutation = useMutation({
    mutationFn: (cookies: string) => recruitmentInfoApi.triggerLogin(cookies),
    onSuccess: (res: any) => {
      if (res?.success) {
        message.success(res.message || 'Cookie 导入成功');
        setCookieOpen(false);
        setCookieText('');
      } else {
        message.error(res?.message || 'Cookie 导入失败');
      }
      queryClient.invalidateQueries({ queryKey: ['crawler-status'] });
    },
    onError: () => {
      message.error('Cookie 导入请求失败');
    },
  });

  // 更新采集器配置
  const updateConfigMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      recruitmentInfoApi.updateCrawlerConfig(id, data),
    onSuccess: () => {
      message.success('配置已更新');
      queryClient.invalidateQueries({ queryKey: ['crawler-status'] });
      setEditOpen(false);
      setEditingConfig(null);
    },
    onError: () => {
      message.error('更新配置失败');
    },
  });

  // 手动触发 AI 分析
  const aiAnalyzeMutation = useMutation({
    mutationFn: () => recruitmentInfoApi.triggerAiAnalyze(),
    onSuccess: (res: any) => {
      message.success(res?.message || 'AI 分析任务已触发');
    },
    onError: () => {
      message.error('触发 AI 分析失败');
    },
  });

  // 开关切换
  const handleActiveChange = (config: CrawlerConfig, checked: boolean) => {
    updateConfigMutation.mutate({
      id: config.id,
      data: { is_active: checked },
    });
  };

  // 打开编辑弹窗
  const handleEdit = (config: CrawlerConfig) => {
    setEditingConfig(config);
    form.setFieldsValue({
      interval_minutes: config.interval_minutes,
      is_active: config.is_active,
      ai_enabled: config.ai_enabled || false,
      ai_model: config.ai_model || '',
      ai_api_key: config.ai_api_key || '',
      ai_base_url: config.ai_base_url || '',
      ai_prompt: config.ai_prompt || '',
    });
    setEditOpen(true);
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingConfig) {
        updateConfigMutation.mutate({
          id: editingConfig.id,
          data: values,
        });
      }
    } catch {
      // 表单验证失败
    }
  };

  const columns: ColumnsType<CrawlerConfig> = [
    {
      title: '名称',
      dataIndex: 'name',
      width: 160,
    },
    {
      title: '目标地址',
      dataIndex: 'target_url',
      width: 240,
      ellipsis: true,
      render: (v: string) => (
        <a href={v} target="_blank" rel="noopener noreferrer">{v}</a>
      ),
    },
    {
      title: '采集间隔(分钟)',
      dataIndex: 'interval_minutes',
      width: 120,
      align: 'center',
    },
    {
      title: '启用状态',
      dataIndex: 'is_active',
      width: 100,
      align: 'center',
      render: (v: boolean, record: CrawlerConfig) => (
        <Switch
          checked={v}
          onChange={(checked) => handleActiveChange(record, checked)}
          loading={updateConfigMutation.isPending}
        />
      ),
    },
    {
      title: '会话状态',
      dataIndex: 'session_valid',
      width: 100,
      align: 'center',
      render: (v: boolean) => (
        <Badge
          status={v ? 'success' : 'error'}
          text={v ? '有效' : '已失效'}
        />
      ),
    },
    {
      title: '上次采集状态',
      dataIndex: 'last_crawl_status',
      width: 120,
      align: 'center',
      render: (v: string) => {
        if (!v) return '-';
        const color = v === 'success' ? 'green' : v === 'running' ? 'blue' : 'red';
        const text = v === 'success' ? '成功' : v === 'running' ? '运行中' : '失败';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '上次采集时间',
      dataIndex: 'last_crawl_at',
      width: 160,
      align: 'center',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '累计采集',
      dataIndex: 'total_crawled',
      width: 90,
      align: 'center',
      render: (v: number) => v || 0,
    },
    {
      title: '操作',
      width: 100,
      align: 'center',
      render: (_: unknown, record: CrawlerConfig) => (
        <Button
          type="link"
          size="small"
          icon={<SettingOutlined />}
          onClick={() => handleEdit(record)}
        >
          编辑
        </Button>
      ),
    },
  ];

  return (
    <div>
      {/* 状态概览 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card size="small">
            <Statistic
              title="采集器运行状态"
              value={crawlerStatus?.scheduler_running ? '运行中' : '已停止'}
              prefix={
                crawlerStatus?.scheduler_running
                  ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
              }
              valueStyle={{ color: crawlerStatus?.scheduler_running ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <Statistic
              title="上次采集时间"
              value={lastCrawlAt ? dayjs(lastCrawlAt).format('YYYY-MM-DD HH:mm') : '暂无'}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <Statistic
              title="累计采集数"
              value={totalCrawled}
              suffix="条"
            />
          </Card>
        </Col>
      </Row>

      {/* 操作按钮与采集器列表 */}
      <Card
        title="采集管理"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              loading={crawlMutation.isPending}
              onClick={() => crawlMutation.mutate()}
            >
              手动采集
            </Button>
            <Button
              icon={<LoginOutlined />}
              onClick={() => setCookieOpen(true)}
            >
              导入Cookie
            </Button>
            <Button
              icon={<RobotOutlined />}
              loading={aiAnalyzeMutation.isPending}
              onClick={() => aiAnalyzeMutation.mutate()}
            >
              AI分析
            </Button>
          </Space>
        }
      >
        <Table<CrawlerConfig>
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={isLoading}
          pagination={false}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* 错误日志 */}
      {configs.some(c => c.last_error) && (
        <Card title="最近错误日志" size="small" style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            {configs
              .filter(c => c.last_error)
              .map(c => (
                <Descriptions key={c.id} size="small" bordered column={1}>
                  <Descriptions.Item label={c.name}>
                    <span style={{ color: '#ff4d4f' }}>{c.last_error}</span>
                  </Descriptions.Item>
                </Descriptions>
              ))}
          </Space>
        </Card>
      )}

      {/* AI 分析日志 */}
      <AiAnalysisLogs />

      {/* 采集日志 */}
      <CrawlLogs />

      {/* 编辑配置弹窗 */}
      <Modal
        title={`编辑采集器 - ${editingConfig?.name || ''}`}
        open={editOpen}
        onOk={handleEditSubmit}
        onCancel={() => { setEditOpen(false); setEditingConfig(null); }}
        confirmLoading={updateConfigMutation.isPending}
        okText="保存"
        cancelText="取消"
        width={640}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="interval_minutes"
            label="采集间隔（分钟）"
            rules={[
              { required: true, message: '请输入采集间隔' },
              { type: 'number', min: 5, message: '最小间隔为5分钟' },
            ]}
          >
            <InputNumber min={5} max={1440} style={{ width: '100%' }} placeholder="请输入采集间隔" />
          </Form.Item>
          <Form.Item
            name="is_active"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>

          <Divider>AI 分析配置</Divider>

          <Form.Item
            name="ai_enabled"
            label="启用 AI 分析"
            valuePropName="checked"
          >
            <Switch checkedChildren="开" unCheckedChildren="关" />
          </Form.Item>
          <Form.Item
            name="ai_base_url"
            label="API 地址"
            tooltip="OpenAI 兼容接口，如 https://api.openai.com/v1 或 https://api.deepseek.com/v1"
          >
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item
            name="ai_model"
            label="模型名称"
          >
            <Input placeholder="如 gpt-4o-mini、deepseek-chat" />
          </Form.Item>
          <Form.Item
            name="ai_api_key"
            label="API Key"
          >
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item
            name="ai_prompt"
            label="分析提示词"
            tooltip="使用 {content} 作为公告内容占位符，留空则使用默认提示词"
          >
            <Input.TextArea
              rows={6}
              placeholder={"留空使用默认提示词。自定义示例：\n请分析以下招考公告，提取关键信息：\n{content}"}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Cookie 导入弹窗 */}
      <Modal
        title="导入 Cookie 登录态"
        open={cookieOpen}
        onOk={() => {
          if (!cookieText.trim()) {
            message.warning('请粘贴 Cookie 内容');
            return;
          }
          loginMutation.mutate(cookieText.trim());
        }}
        onCancel={() => { setCookieOpen(false); setCookieText(''); }}
        confirmLoading={loginMutation.isPending}
        okText="导入"
        cancelText="取消"
        width={640}
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="操作步骤"
          description={
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              <li>在浏览器中打开 <a href="https://gongkaoleida.com" target="_blank" rel="noopener noreferrer">gongkaoleida.com</a> 并登录</li>
              <li>按 F12 打开开发者工具 → Application → Cookies</li>
              <li>选中所有 Cookie，右键复制（或用 EditThisCookie 扩展导出）</li>
              <li>粘贴到下方输入框</li>
            </ol>
          }
        />
        <Input.TextArea
          rows={8}
          value={cookieText}
          onChange={e => setCookieText(e.target.value)}
          placeholder={'支持两种格式：\n1. name=value; name2=value2（从浏览器地址栏 document.cookie 复制）\n2. JSON 数组格式（从 EditThisCookie 等扩展导出）'}
        />
      </Modal>
    </div>
  );
}


function AiAnalysisLogs() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ['ai-logs', page],
    queryFn: () => recruitmentInfoApi.getAiLogs(page, 10),
    refetchInterval: 10000,
  });

  const logs = (data as any)?.items || [];
  const total = (data as any)?.total || 0;

  if (total === 0 && !isLoading) return null;

  const columns: ColumnsType<any> = [
    {
      title: '公告',
      dataIndex: 'title',
      ellipsis: true,
      width: 280,
    },
    {
      title: '模型',
      dataIndex: 'model',
      width: 130,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      align: 'center',
      render: (v: string) => (
        <Tag color={v === 'success' ? 'green' : 'red'}>
          {v === 'success' ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '输入/输出',
      width: 120,
      align: 'center',
      render: (_: unknown, r: any) => `${r.input_length || 0} / ${r.output_length || 0}`,
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      width: 80,
      align: 'center',
      render: (v: number) => v ? `${(v / 1000).toFixed(1)}s` : '-',
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      ellipsis: true,
      render: (v: string) => v ? <span style={{ color: '#ff4d4f' }}>{v}</span> : '-',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 160,
      render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm:ss') : '-',
    },
  ];

  return (
    <Card title="AI 分析日志" size="small" style={{ marginTop: 16 }}>
      <Table
        columns={columns}
        dataSource={logs}
        rowKey="id"
        loading={isLoading}
        size="small"
        pagination={{
          current: page,
          pageSize: 10,
          total,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 条`,
          size: 'small',
        }}
      />
    </Card>
  );
}


function CrawlLogs() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ['crawl-logs', page],
    queryFn: () => recruitmentInfoApi.getCrawlLogs(page, 10),
    refetchInterval: 30000,
  });

  const logs = (data as any)?.items || [];
  const total = (data as any)?.total || 0;

  if (total === 0 && !isLoading) return null;

  const columns: ColumnsType<any> = [
    {
      title: '目标地址',
      dataIndex: 'target_url',
      ellipsis: true,
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      align: 'center',
      render: (v: string) => (
        <Tag color={v === 'success' ? 'green' : v === 'partial' ? 'orange' : 'red'}>
          {v === 'success' ? '成功' : v === 'partial' ? '部分' : '失败'}
        </Tag>
      ),
    },
    {
      title: '总数',
      dataIndex: 'total',
      width: 60,
      align: 'center',
    },
    {
      title: '新增',
      dataIndex: 'new_count',
      width: 60,
      align: 'center',
      render: (v: number) => <span style={{ color: v > 0 ? '#52c41a' : undefined }}>{v}</span>,
    },
    {
      title: '跳过',
      dataIndex: 'skipped',
      width: 60,
      align: 'center',
    },
    {
      title: '失败',
      dataIndex: 'failed',
      width: 60,
      align: 'center',
      render: (v: number) => v > 0 ? <span style={{ color: '#ff4d4f' }}>{v}</span> : 0,
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      width: 80,
      align: 'center',
      render: (v: number) => v ? `${(v / 1000).toFixed(1)}s` : '-',
    },
    {
      title: '错误',
      dataIndex: 'error_message',
      ellipsis: true,
      render: (v: string) => v ? <span style={{ color: '#ff4d4f' }}>{v}</span> : '-',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 160,
      render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm:ss') : '-',
    },
  ];

  return (
    <Card title="采集日志" size="small" style={{ marginTop: 16 }}>
      <Table
        columns={columns}
        dataSource={logs}
        rowKey="id"
        loading={isLoading}
        size="small"
        pagination={{
          current: page,
          pageSize: 10,
          total,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 条`,
          size: 'small',
        }}
      />
    </Card>
  );
}
