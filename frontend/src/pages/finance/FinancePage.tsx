import { useState } from 'react';
import {
  Table, Button, Space, Tag, Card, Row, Col, Statistic, Select,
  Modal, Form, Input, InputNumber, DatePicker, message,
} from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined,
  DollarOutlined, ReloadOutlined, DownloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { financeApi } from '../../api/finance';
import { exportApi } from '../../api/export';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

interface FinanceItem {
  id: number;
  record_type: string;
  category: string;
  amount: number;
  record_date: string;
  description: string | null;
  payment_method: string | null;
  receipt_no: string | null;
  created_at: string;
}

const INCOME_CATEGORIES = ['学费', '教材费', '模考费', '其他收入'];
const EXPENSE_CATEGORIES = ['场地租金', '教师工资', '教材成本', '广告营销', '办公用品', '水电费', '其他支出'];
const COLORS = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'];

export default function FinancePage() {
  const queryClient = useQueryClient();
  const [params, setParams] = useState({ page: 1, page_size: 20 });
  const [recordType, setRecordType] = useState<string>();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();
  const [formType, setFormType] = useState<string>('income');

  const now = dayjs();

  const { data, isLoading } = useQuery({
    queryKey: ['finance', params, recordType],
    queryFn: () => financeApi.list({ ...params, record_type: recordType }),
  });

  const { data: summary } = useQuery({
    queryKey: ['finance-summary', now.year(), now.month() + 1],
    queryFn: () => financeApi.summary(now.year(), now.month() + 1),
  });

  const createMutation = useMutation({
    mutationFn: financeApi.create,
    onSuccess: () => {
      message.success('记录创建成功');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['finance'] });
      queryClient.invalidateQueries({ queryKey: ['finance-summary'] });
    },
    onError: () => message.error('创建失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: financeApi.delete,
    onSuccess: () => {
      message.success('已删除');
      queryClient.invalidateQueries({ queryKey: ['finance'] });
      queryClient.invalidateQueries({ queryKey: ['finance-summary'] });
    },
  });

  const handleCreate = () => {
    form.validateFields().then(values => {
      createMutation.mutate({
        ...values,
        record_type: formType,
        record_date: values.record_date.format('YYYY-MM-DD'),
      });
    });
  };

  // 饼图数据
  const incomePie = (summary?.by_category || [])
    .filter((c: { type: string }) => c.type === 'income')
    .map((c: { category: string; total: number }) => ({ name: c.category, value: c.total }));
  const expensePie = (summary?.by_category || [])
    .filter((c: { type: string }) => c.type === 'expense')
    .map((c: { category: string; total: number }) => ({ name: c.category, value: c.total }));

  const columns: ColumnsType<FinanceItem> = [
    {
      title: '类型', dataIndex: 'record_type', width: 70, align: 'center',
      render: (v: string) => v === 'income'
        ? <Tag color="green">收入</Tag>
        : <Tag color="red">支出</Tag>,
    },
    { title: '分类', dataIndex: 'category', width: 100 },
    {
      title: '金额', dataIndex: 'amount', width: 110, align: 'right',
      render: (v: number, r: FinanceItem) => (
        <span style={{ fontWeight: 700, color: r.record_type === 'income' ? '#52c41a' : '#ff4d4f' }}>
          {r.record_type === 'income' ? '+' : '-'}¥{v.toLocaleString()}
        </span>
      ),
    },
    { title: '日期', dataIndex: 'record_date', width: 110 },
    { title: '说明', dataIndex: 'description', ellipsis: true, render: (v: string) => v || '-' },
    {
      title: '支付方式', dataIndex: 'payment_method', width: 90,
      render: (v: string) => v || '-',
    },
    {
      title: '操作', key: 'action', width: 60, align: 'center',
      render: (_, r: FinanceItem) => (
        <Button type="link" size="small" danger onClick={() => {
          Modal.confirm({
            title: '确认删除',
            content: `确定删除这条${r.record_type === 'income' ? '收入' : '支出'}记录？`,
            onOk: () => deleteMutation.mutate(r.id),
          });
        }}>删除</Button>
      ),
    },
  ];

  return (
    <div>
      {/* 汇总统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title={`${now.month() + 1}月收入`}
              value={summary?.income_total || 0}
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: '#52c41a' }}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title={`${now.month() + 1}月支出`}
              value={summary?.expense_total || 0}
              prefix={<ArrowDownOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="本月利润"
              value={summary?.profit || 0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: (summary?.profit || 0) >= 0 ? '#1677ff' : '#ff4d4f' }}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="记录总数"
              value={data?.total || 0}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 分类饼图 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card size="small" title="收入分布">
            {incomePie.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={incomePie} cx="50%" cy="50%" outerRadius={70} dataKey="value"
                    label={(({ name, percent }: { name: string; percent: number }) => `${name} ${(percent * 100).toFixed(0)}%`) as any}
                  >
                    {incomePie.map((_: unknown, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={((v: number) => `¥${v.toLocaleString()}`) as any} />
                </PieChart>
              </ResponsiveContainer>
            ) : <p style={{ textAlign: 'center', color: '#999', padding: 40 }}>本月暂无收入记录</p>}
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small" title="支出分布">
            {expensePie.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={expensePie} cx="50%" cy="50%" outerRadius={70} dataKey="value"
                    label={(({ name, percent }: { name: string; percent: number }) => `${name} ${(percent * 100).toFixed(0)}%`) as any}
                  >
                    {expensePie.map((_: unknown, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={((v: number) => `¥${v.toLocaleString()}`) as any} />
                </PieChart>
              </ResponsiveContainer>
            ) : <p style={{ textAlign: 'center', color: '#999', padding: 40 }}>本月暂无支出记录</p>}
          </Card>
        </Col>
      </Row>

      {/* 筛选 + 操作 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Select
            placeholder="类型" allowClear style={{ width: 100 }}
            onChange={v => { setRecordType(v); setParams(p => ({ ...p, page: 1 })); }}
            options={[{ value: 'income', label: '收入' }, { value: 'expense', label: '支出' }]}
          />
          <Button icon={<ReloadOutlined />} onClick={() => { setRecordType(undefined); setParams({ page: 1, page_size: 20 }); }}>
            重置
          </Button>
        </Space>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={() => {
            const now2 = dayjs();
            exportApi.finance({ record_type: recordType, year: now2.year(), month: now2.month() + 1 })
              .catch(() => message.error('导出失败'));
          }}>导出</Button>
          <Button icon={<ArrowUpOutlined />} style={{ color: '#52c41a', borderColor: '#52c41a' }}
            onClick={() => { setFormType('income'); form.resetFields(); setCreateOpen(true); }}>
            记录收入
          </Button>
          <Button icon={<ArrowDownOutlined />} style={{ color: '#ff4d4f', borderColor: '#ff4d4f' }}
            onClick={() => { setFormType('expense'); form.resetFields(); setCreateOpen(true); }}>
            记录支出
          </Button>
        </Space>
      </div>

      {/* 表格 */}
      <Table<FinanceItem>
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total: data?.total || 0,
          showTotal: total => `共 ${total} 条`,
          onChange: (page, pageSize) => setParams({ page, page_size: pageSize }),
        }}
        size="middle"
      />

      {/* 新增记录 */}
      <Modal
        title={formType === 'income' ? '记录收入' : '记录支出'}
        open={createOpen}
        onOk={handleCreate}
        onCancel={() => setCreateOpen(false)}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="category" label="分类" rules={[{ required: true }]}>
                <Select
                  options={(formType === 'income' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES)
                    .map(c => ({ value: c, label: c }))}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="amount" label="金额" rules={[{ required: true }]}>
                <InputNumber min={0.01} step={0.01} style={{ width: '100%' }} prefix="¥" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="record_date" label="日期" rules={[{ required: true }]} initialValue={dayjs()}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="payment_method" label="支付方式">
                <Select allowClear options={[
                  { value: '微信', label: '微信' },
                  { value: '支付宝', label: '支付宝' },
                  { value: '银行转账', label: '银行转账' },
                  { value: '现金', label: '现金' },
                ]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="说明">
            <Input.TextArea rows={2} placeholder="备注说明" />
          </Form.Item>
          <Form.Item name="receipt_no" label="收据/发票号">
            <Input placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
