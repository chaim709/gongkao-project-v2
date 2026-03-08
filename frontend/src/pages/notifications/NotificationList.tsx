import { useState } from 'react';
import { Card, List, Tag, Button, Space, Empty, Badge, Tabs } from 'antd';
import { CheckOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationApi } from '../../api/notifications';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const typeMap: Record<string, { text: string; color: string }> = {
  system: { text: '系统', color: 'blue' },
  reminder: { text: '提醒', color: 'orange' },
  alert: { text: '预警', color: 'red' },
  exam_reminder: { text: '考试提醒', color: 'volcano' },
};

export default function NotificationList() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<string>('all');
  const [page, setPage] = useState(1);

  const isReadParam = filter === 'unread' ? false : filter === 'read' ? true : undefined;

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', page, filter],
    queryFn: () => notificationApi.list({ page, page_size: 20, is_read: isReadParam }),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: number) => notificationApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });

  const markAllMutation = useMutation({
    mutationFn: () => notificationApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });

  return (
    <Card
      title="通知中心"
      extra={
        <Button
          icon={<CheckCircleOutlined />}
          onClick={() => markAllMutation.mutate()}
          loading={markAllMutation.isPending}
        >
          全部已读
        </Button>
      }
    >
      <Tabs
        activeKey={filter}
        onChange={(k) => { setFilter(k); setPage(1); }}
        items={[
          { key: 'all', label: '全部' },
          { key: 'unread', label: '未读' },
          { key: 'read', label: '已读' },
        ]}
        style={{ marginBottom: 16 }}
      />

      <List
        loading={isLoading}
        dataSource={data?.items || []}
        locale={{ emptyText: <Empty description="暂无通知" /> }}
        pagination={{
          current: page,
          total: data?.total || 0,
          pageSize: 20,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 条`,
        }}
        renderItem={(item: {
          id: number;
          title: string;
          content?: string;
          type: string;
          is_read: boolean;
          created_at?: string;
        }) => {
          const typeInfo = typeMap[item.type] || { text: item.type, color: 'default' };
          return (
            <List.Item
              style={{
                background: item.is_read ? undefined : '#f0f5ff',
                padding: '12px 16px',
                borderRadius: 6,
                marginBottom: 8,
              }}
              actions={
                !item.is_read
                  ? [
                      <Button
                        key="read"
                        size="small"
                        type="link"
                        icon={<CheckOutlined />}
                        onClick={() => markReadMutation.mutate(item.id)}
                      >
                        标记已读
                      </Button>,
                    ]
                  : undefined
              }
            >
              <List.Item.Meta
                title={
                  <Space>
                    {!item.is_read && <Badge status="processing" />}
                    <Tag color={typeInfo.color}>{typeInfo.text}</Tag>
                    <span>{item.title}</span>
                  </Space>
                }
                description={
                  <div>
                    {item.content && <p style={{ margin: '4px 0', color: '#666' }}>{item.content}</p>}
                    <span style={{ color: '#999', fontSize: 12 }}>
                      {item.created_at ? dayjs(item.created_at).fromNow() : ''}
                    </span>
                  </div>
                }
              />
            </List.Item>
          );
        }}
      />
    </Card>
  );
}
