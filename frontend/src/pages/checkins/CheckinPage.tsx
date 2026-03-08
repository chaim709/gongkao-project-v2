import { useState } from 'react';
import { Card, Table, Tag, Select, Button, message, Modal, Input, Statistic, Row, Col } from 'antd';
import { CheckCircleOutlined, FireOutlined, TrophyOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { checkinApi } from '../../api/checkins';
import { studentApi } from '../../api/students';
import type { CheckinRankItem } from '../../types/checkin';
import type { ColumnsType } from 'antd/es/table';

export default function CheckinPage() {
  const queryClient = useQueryClient();
  const [checkinOpen, setCheckinOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [content, setContent] = useState('');
  const [searchValue, setSearchValue] = useState('');
  const [statsStudentId, setStatsStudentId] = useState<number | null>(null);

  const { data: students } = useQuery({
    queryKey: ['students-select', searchValue],
    queryFn: () => studentApi.list({ page: 1, page_size: 50, search: searchValue || undefined }),
  });

  const { data: rank, isLoading: rankLoading } = useQuery({
    queryKey: ['checkin-rank'],
    queryFn: () => checkinApi.getRank(20),
  });

  const { data: stats } = useQuery({
    queryKey: ['checkin-stats', statsStudentId],
    queryFn: () => checkinApi.getStats(statsStudentId!),
    enabled: !!statsStudentId,
  });

  const checkinMutation = useMutation({
    mutationFn: checkinApi.checkin,
    onSuccess: () => {
      message.success('打卡成功');
      setCheckinOpen(false);
      setSelectedStudent(null);
      setContent('');
      queryClient.invalidateQueries({ queryKey: ['checkin-rank'] });
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] });
    },
    onError: (err: any) => message.error(err?.message || '打卡失败'),
  });

  const handleCheckin = () => {
    if (!selectedStudent) { message.warning('请选择学员'); return; }
    checkinMutation.mutate({ student_id: selectedStudent, content: content || undefined });
  };

  const rankColumns: ColumnsType<CheckinRankItem> = [
    {
      title: '排名', key: 'rank', width: 60,
      render: (_, __, index) => {
        if (index === 0) return <TrophyOutlined style={{ color: '#faad14', fontSize: 18 }} />;
        if (index === 1) return <TrophyOutlined style={{ color: '#bfbfbf', fontSize: 16 }} />;
        if (index === 2) return <TrophyOutlined style={{ color: '#d48806', fontSize: 14 }} />;
        return index + 1;
      },
    },
    { title: '学员', dataIndex: 'student_name', ellipsis: true },
    {
      title: '累计', dataIndex: 'total_days', width: 80,
      render: (v: number) => <Tag color="blue">{v} 天</Tag>,
    },
    {
      title: '连续', dataIndex: 'consecutive_days', width: 80,
      render: (v: number) => v > 0 ? <Tag color="orange"><FireOutlined /> {v}</Tag> : <Tag>0</Tag>,
    },
    {
      title: '', key: 'action', width: 60,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => setStatsStudentId(record.student_id)}>详情</Button>
      ),
    },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="今日打卡人数"
              value={rank?.items?.filter((i: CheckinRankItem) => i.consecutive_days > 0).length || 0}
              prefix={<CheckCircleOutlined />}
              suffix="人"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总参与人数" value={rank?.items?.length || 0} suffix="人" />
          </Card>
        </Col>
        <Col span={8}>
          <Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <Button type="primary" size="large" icon={<CheckCircleOutlined />} onClick={() => setCheckinOpen(true)}>
              学员打卡
            </Button>
          </Card>
        </Col>
      </Row>

      <Card title="打卡排行榜">
        <Table<CheckinRankItem>
          columns={rankColumns}
          dataSource={rank?.items || []}
          rowKey="student_id"
          loading={rankLoading}
          pagination={false}
          size="middle"
        />
      </Card>

      {/* 打卡弹窗 */}
      <Modal title="学员打卡" open={checkinOpen} onOk={handleCheckin} onCancel={() => setCheckinOpen(false)} confirmLoading={checkinMutation.isPending}>
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label>选择学员</label>
            <Select
              showSearch
              placeholder="搜索学员"
              filterOption={false}
              onSearch={setSearchValue}
              onChange={setSelectedStudent}
              value={selectedStudent}
              style={{ width: '100%', marginTop: 4 }}
              options={(students?.items || []).map((s: any) => ({ value: s.id, label: `${s.name}${s.phone ? ` (${s.phone})` : ''}` }))}
            />
          </div>
          <div>
            <label>打卡内容（可选）</label>
            <Input.TextArea rows={3} value={content} onChange={(e) => setContent(e.target.value)} placeholder="记录今日学习内容" style={{ marginTop: 4 }} />
          </div>
        </div>
      </Modal>

      {/* 打卡统计详情 */}
      <Modal
        title={`${stats?.student_name || ''} 的打卡记录`}
        open={!!statsStudentId}
        onCancel={() => setStatsStudentId(null)}
        footer={null}
        width={500}
      >
        {stats && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Statistic title="累计打卡" value={stats.total_days} suffix="天" />
              </Col>
              <Col span={12}>
                <Statistic title="连续打卡" value={stats.consecutive_days} suffix="天" prefix={<FireOutlined />} />
              </Col>
            </Row>
            <div>
              <h4>打卡日期</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {stats.checkin_dates.slice(-30).map((d: string) => (
                  <Tag key={d} color="green">{d}</Tag>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
