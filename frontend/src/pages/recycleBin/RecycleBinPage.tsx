import { useState } from 'react';
import { Card, Table, Button, Select, message, Tag, Statistic, Row, Col } from 'antd';
import { RestOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recycleBinApi } from '../../api/recycleBin';

export default function RecycleBinPage() {
  const queryClient = useQueryClient();
  const [modelType, setModelType] = useState('student');
  const [page, setPage] = useState(1);

  const { data: summary } = useQuery({
    queryKey: ['recycle-summary'],
    queryFn: recycleBinApi.summary,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['recycle-bin', modelType, page],
    queryFn: () => recycleBinApi.list({ model: modelType, page, page_size: 20 }),
  });

  const restoreMutation = useMutation({
    mutationFn: ({ model, id }: { model: string; id: number }) => recycleBinApi.restore(model, id),
    onSuccess: () => {
      message.success('数据已恢复');
      queryClient.invalidateQueries({ queryKey: ['recycle-bin'] });
      queryClient.invalidateQueries({ queryKey: ['recycle-summary'] });
    },
  });

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {summary && Object.entries(summary).map(([key, val]: [string, any]) => (
          <Col span={6} key={key}>
            <Card>
              <Statistic title={val.label} value={val.count} prefix={<RestOutlined />} />
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        title="数据回收站"
        extra={
          <Select value={modelType} onChange={(v) => { setModelType(v); setPage(1); }} style={{ width: 150 }}>
            <Select.Option value="student">学员</Select.Option>
            <Select.Option value="finance">财务记录</Select.Option>
            <Select.Option value="supervision_log">督学日志</Select.Option>
            <Select.Option value="calendar_event">日历事件</Select.Option>
          </Select>
        }
      >
        <Table
          loading={isLoading}
          dataSource={data?.items || []}
          rowKey="id"
          pagination={{
            current: page,
            total: data?.total || 0,
            pageSize: 20,
            onChange: setPage,
          }}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 80 },
            { title: '名称', dataIndex: 'name' },
            { title: '类型', dataIndex: 'model_label', width: 120, render: (v) => <Tag>{v}</Tag> },
            { title: '删除时间', dataIndex: 'deleted_at', width: 180 },
            {
              title: '操作',
              width: 100,
              render: (_, record: any) => (
                <Button
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={() => restoreMutation.mutate({ model: record.model, id: record.id })}
                  loading={restoreMutation.isPending}
                >
                  恢复
                </Button>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
