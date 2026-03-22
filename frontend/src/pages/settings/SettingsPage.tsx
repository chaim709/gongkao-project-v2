import {
  Card, Form, InputNumber, Button, message, Tabs,
  Descriptions, Tag, Space, Divider,
} from 'antd';
import { SaveOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { studentApi } from '../../api/students';
import { settingsApi } from '../../api/settings';
import type { ShiyeTierThresholdSettings } from '../../types/settings';

export default function SettingsPage() {
  const [tierForm] = Form.useForm<ShiyeTierThresholdSettings>();
  const [savingTierThresholds, setSavingTierThresholds] = useState(false);

  const { data: lifecycleStats } = useQuery({
    queryKey: ['lifecycle-stats'],
    queryFn: () => studentApi.getLifecycleStats(),
  });

  const {
    data: shiyeTierThresholds,
    refetch: refetchShiyeTierThresholds,
    isLoading: shiyeTierThresholdLoading,
  } = useQuery({
    queryKey: ['shiye-tier-thresholds'],
    queryFn: () => settingsApi.getShiyeTierThresholds(),
  });

  useEffect(() => {
    if (shiyeTierThresholds) {
      tierForm.setFieldsValue(shiyeTierThresholds);
    }
  }, [shiyeTierThresholds, tierForm]);

  const handleSaveShiyeTierThresholds = async () => {
    const values = await tierForm.validateFields();
    setSavingTierThresholds(true);
    try {
      await settingsApi.updateShiyeTierThresholds(values);
      message.success('事业编分层阈值已保存');
      await refetchShiyeTierThresholds();
    } finally {
      setSavingTierThresholds(false);
    }
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
      label: <><SaveOutlined /> 参数配置</>,
      forceRender: true,
      children: (
        <div>
          <Card
            title="事业编分层阈值"
            size="small"
            loading={shiyeTierThresholdLoading}
            extra={(
              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={savingTierThresholds}
                onClick={handleSaveShiyeTierThresholds}
              >
                保存阈值
              </Button>
            )}
          >
            <Form form={tierForm} layout="vertical" style={{ maxWidth: 600 }}>
              <Form.Item
                label="竞争比中位分位值"
                name="competition_low_percentile"
                tooltip="命中该分位值以上时，按中位竞争强度处理"
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                label="竞争比高位分位值"
                name="competition_high_percentile"
                tooltip="命中该分位值以上时，按高竞争处理"
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                label="分数线中位分位值"
                name="score_low_percentile"
                tooltip="命中该分位值以上时，按中位分数线处理"
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                label="分数线高位分位值"
                name="score_high_percentile"
                tooltip="命中该分位值以上时，按高分线处理"
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                label="稳妥分界线"
                name="stable_min_score"
                tooltip="综合难度分达到该值后进入稳妥层"
              >
                <InputNumber min={0} max={100} step={1} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                label="冲刺分界线"
                name="sprint_min_score"
                tooltip="综合难度分达到该值后进入冲刺层"
              >
                <InputNumber min={0} max={100} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Form>
          </Card>
        </div>
      ),
    },
  ];

  return (
    <Card>
      <Tabs items={tabItems} />
    </Card>
  );
}
