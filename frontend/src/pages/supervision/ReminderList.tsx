import { useState } from 'react';
import { Table, Tag, InputNumber, Space, Button } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { supervisionApi } from '../../api/supervision';
import type { ReminderItem } from '../../types/supervision';
import type { ColumnsType } from 'antd/es/table';

interface ReminderListProps {
  onCreateLog: () => void;
}

export default function ReminderList({ onCreateLog }: ReminderListProps) {
  const [days, setDays] = useState(7);

  const { data, isLoading } = useQuery({
    queryKey: ['reminders', days],
    queryFn: () => supervisionApi.getReminders(days),
  });

  const columns: ColumnsType<ReminderItem> = [
    {
      title: '学员',
      dataIndex: 'student_name',
      width: 100,
    },
    {
      title: '上次联系',
      dataIndex: 'last_contact_date',
      width: 120,
      render: (v: string) => v || '从未联系',
    },
    {
      title: '未联系天数',
      dataIndex: 'days_since_contact',
      width: 120,
      render: (days: number) => {
        const color = days >= 14 ? 'red' : days >= 7 ? 'orange' : 'green';
        return <Tag color={color}>{days >= 999 ? '从未联系' : `${days} 天`}</Tag>;
      },
      sorter: (a, b) => b.days_since_contact - a.days_since_contact,
      defaultSortOrder: 'descend',
    },
    {
      title: '需要关注',
      dataIndex: 'need_attention',
      width: 100,
      render: (v: boolean) => v ? <Tag color="red">需关注</Tag> : <Tag color="default">正常</Tag>,
    },
    {
      title: '督学老师',
      dataIndex: 'supervisor_name',
      width: 100,
      render: (v: string) => v || '未���配',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: () => (
        <Button type="link" size="small" onClick={onCreateLog}>
          添加日志
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span>超过</span>
          <InputNumber min={1} max={90} value={days} onChange={(v) => setDays(v || 7)} />
          <span>天未联系的学员</span>
        </Space>
      </div>

      <Table<ReminderItem>
        columns={columns}
        dataSource={data?.items || []}
        rowKey="student_id"
        loading={isLoading}
        pagination={false}
        size="middle"
      />
    </div>
  );
}
