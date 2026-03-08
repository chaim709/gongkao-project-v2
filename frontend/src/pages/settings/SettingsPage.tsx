import {
  Card, Form, Input, InputNumber, Switch, Button, message, Tabs,
  Descriptions, Tag, Space, Divider,
} from 'antd';
import { SaveOutlined, InfoCircleOutlined, ToolOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { studentApi } from '../../api/students';

export default function SettingsPage() {
  const [form] = Form.useForm();

  const { data: lifecycleStats } = useQuery({
    queryKey: ['lifecycle-stats'],
    queryFn: () => studentApi.getLifecycleStats(),
  });

  const handleSave = () => {
    form.validateFields().then(() => {
      message.success('设置已保存（本地）');
    });
  };

  const statusLabels: Record<string, string> = {
    lead: '线索',
    trial: '试听',
    active: '在读',
    inactive: '休学',
    graduated: '结业',
    dropped: '退出',
  };

  const statusColors: Record<string, string> = {
    lead: 'default',
    trial: 'purple',
    active: 'green',
    inactive: 'orange',
    graduated: 'blue',
    dropped: 'red',
  };

  const tabItems = [
    {
      key: 'overview',
      label: <><InfoCircleOutlined /> 系统概况</>,
      children: (
        <div>
          <Descriptions bordered column={2} size="small" title="系统信息">
            <Descriptions.Item label="系统名称">公考培训管理系统 V2</Descriptions.Item>
            <Descriptions.Item label="技术栈">FastAPI + React + PostgreSQL</Descriptions.Item>
            <Descriptions.Item label="前端框架">React 18 + TypeScript + Ant Design</Descriptions.Item>
            <Descriptions.Item label="后端框架">FastAPI + SQLAlchemy 2.0</Descriptions.Item>
            <Descriptions.Item label="API 文档">
              <a href="/docs" target="_blank" rel="noopener noreferrer">/docs (Swagger)</a>
            </Descriptions.Item>
            <Descriptions.Item label="健康检查">
              <a href="/health" target="_blank" rel="noopener noreferrer">/health</a>
            </Descriptions.Item>
          </Descriptions>

          <Divider />

          <Card title="学员生命周期统计" size="small">
            <Space wrap>
              {Object.entries(lifecycleStats?.by_status || {}).map(([status, count]) => (
                <Tag key={status} color={statusColors[status] || 'default'} style={{ fontSize: 14, padding: '4px 12px' }}>
                  {statusLabels[status] || status}: {count as number}
                </Tag>
              ))}
              <Tag color="geekblue" style={{ fontSize: 14, padding: '4px 12px', fontWeight: 600 }}>
                总计: {lifecycleStats?.total || 0}
              </Tag>
            </Space>
          </Card>

          <Divider />

          <Card title="功能模块" size="small">
            <Descriptions column={3} size="small">
              <Descriptions.Item label="学员管理"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="督学日志"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="课程管理"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="作业管理"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="打卡管理"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="考勤管理"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="智能选岗"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="题库模考"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="AI导入"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="财务管理"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="数据导出"><Tag color="green">已启用</Tag></Descriptions.Item>
              <Descriptions.Item label="审计日志"><Tag color="green">已启用</Tag></Descriptions.Item>
            </Descriptions>
          </Card>
        </div>
      ),
    },
    {
      key: 'params',
      label: <><ToolOutlined /> 参数配置</>,
      children: (
        <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
          <Form.Item label="跟进提醒天数" name="follow_up_days" initialValue={7}>
            <InputNumber min={1} max={30} addonAfter="天" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="每页默认显示条数" name="page_size" initialValue={20}>
            <InputNumber min={10} max={100} addonAfter="条" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="默认密码" name="default_password" initialValue="123456">
            <Input.Password />
          </Form.Item>
          <Form.Item label="机构名称" name="org_name" initialValue="公考培训机构">
            <Input />
          </Form.Item>
          <Form.Item label="启用 AI 智能导入" name="ai_enabled" valuePropName="checked" initialValue={true}>
            <Switch checkedChildren="开" unCheckedChildren="关" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
              保存设置
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <Card>
      <Tabs items={tabItems} />
    </Card>
  );
}
