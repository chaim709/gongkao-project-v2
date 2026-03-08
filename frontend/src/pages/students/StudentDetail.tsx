import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Tabs, Descriptions, Tag, Button, Space, Table, Spin, Timeline, Empty,
} from 'antd';
import {
  ArrowLeftOutlined, AimOutlined, UserOutlined, FileTextOutlined,
  ClockCircleOutlined, TrophyOutlined, BugOutlined, PrinterOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { studentApi } from '../../api/students';
import { supervisionApi } from '../../api/supervision';
import { attendanceApi } from '../../api/attendances';
import { examApi } from '../../api/exams';
import WeaknessAnalysis from '../../components/WeaknessAnalysis';
import dayjs from 'dayjs';

const statusMap: Record<string, { text: string; color: string }> = {
  lead: { text: '线索', color: 'default' },
  trial: { text: '试听', color: 'purple' },
  active: { text: '在读', color: 'green' },
  inactive: { text: '休学', color: 'orange' },
  graduated: { text: '结业', color: 'blue' },
  dropped: { text: '退出', color: 'red' },
};

export default function StudentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const studentId = Number(id);
  const [activeTab, setActiveTab] = useState('info');

  const { data: student, isLoading } = useQuery({
    queryKey: ['student', studentId],
    queryFn: () => studentApi.getById(studentId),
    enabled: !!studentId,
  });

  const { data: logs } = useQuery({
    queryKey: ['supervision-logs', studentId],
    queryFn: () => supervisionApi.list({ student_id: studentId, page: 1, page_size: 50 }),
    enabled: activeTab === 'supervision',
  });

  const { data: attendances } = useQuery({
    queryKey: ['attendances', studentId],
    queryFn: () => attendanceApi.listAttendances({ student_id: studentId, page: 1, page_size: 50 }),
    enabled: activeTab === 'attendance',
  });

  const { data: scores } = useQuery({
    queryKey: ['exam-scores', studentId],
    queryFn: () => examApi.listScores({ student_id: studentId, page: 1, page_size: 50 }),
    enabled: activeTab === 'exams',
  });

  if (isLoading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  if (!student) {
    return <Empty description="学员不存在" />;
  }

  const statusInfo = statusMap[student.status] || { text: student.status, color: 'default' };

  const tabItems = [
    {
      key: 'info',
      label: <><UserOutlined /> 基本信息</>,
      children: (
        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="姓名">{student.name}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={statusInfo.color}>{statusInfo.text}</Tag></Descriptions.Item>
          <Descriptions.Item label="手机号">{student.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="微信">{student.wechat || '-'}</Descriptions.Item>
          <Descriptions.Item label="性别">{student.gender || '-'}</Descriptions.Item>
          <Descriptions.Item label="学历">{student.education || '-'}</Descriptions.Item>
          <Descriptions.Item label="专业">{student.major || '-'}</Descriptions.Item>
          <Descriptions.Item label="报考类型">{student.exam_type || '-'}</Descriptions.Item>
          <Descriptions.Item label="入学日期">{student.enrollment_date || '-'}</Descriptions.Item>
          <Descriptions.Item label="最近联系">{student.last_contact_date || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{student.created_at ? dayjs(student.created_at).format('YYYY-MM-DD HH:mm') : '-'}</Descriptions.Item>
          <Descriptions.Item label="需要关注">{student.need_attention ? <Tag color="red">是</Tag> : '否'}</Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'supervision',
      label: <><FileTextOutlined /> 督学日志</>,
      children: (
        <div>
          {(logs?.items?.length ?? 0) > 0 ? (
            <Timeline
              items={(logs?.items || []).map((log: {
                id: number;
                log_date: string;
                contact_method?: string;
                mood?: string;
                study_status?: string;
                content?: string;
                next_followup_date?: string;
              }) => ({
                key: log.id,
                children: (
                  <div>
                    <div style={{ fontWeight: 500, marginBottom: 4 }}>
                      {log.log_date}
                      {log.contact_method && <Tag style={{ marginLeft: 8 }}>{log.contact_method}</Tag>}
                      {log.mood && <Tag color="blue">{log.mood}</Tag>}
                    </div>
                    {log.study_status && <div style={{ color: '#666', marginBottom: 2 }}>学习状态: {log.study_status}</div>}
                    <div>{log.content}</div>
                    {log.next_followup_date && (
                      <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                        下次跟进: {log.next_followup_date}
                      </div>
                    )}
                  </div>
                ),
              }))}
            />
          ) : (
            <Empty description="暂无督学日志" />
          )}
        </div>
      ),
    },
    {
      key: 'attendance',
      label: <><ClockCircleOutlined /> 考勤记录</>,
      children: (
        <Table
          size="small"
          dataSource={attendances?.items || []}
          rowKey="id"
          pagination={false}
          columns={[
            { title: '日期', dataIndex: 'attendance_date', width: 120 },
            {
              title: '状态', dataIndex: 'status', width: 80,
              render: (v: string) => {
                const m: Record<string, { text: string; color: string }> = {
                  present: { text: '出勤', color: 'green' },
                  absent: { text: '缺勤', color: 'red' },
                  late: { text: '迟到', color: 'orange' },
                  leave: { text: '请假', color: 'blue' },
                };
                const info = m[v] || { text: v, color: 'default' };
                return <Tag color={info.color}>{info.text}</Tag>;
              },
            },
            { title: '备注', dataIndex: 'notes', render: (v: string) => v || '-' },
          ]}
        />
      ),
    },
    {
      key: 'exams',
      label: <><TrophyOutlined /> 考试成绩</>,
      children: (
        <Table
          size="small"
          dataSource={scores?.items || []}
          rowKey="id"
          pagination={false}
          columns={[
            { title: '试卷', dataIndex: 'paper_title', ellipsis: true },
            { title: '正确数', dataIndex: 'correct_count', width: 80, align: 'center' as const },
            { title: '总题数', dataIndex: 'total_questions', width: 80, align: 'center' as const },
            {
              title: '正确率', key: 'accuracy', width: 100, align: 'center' as const,
              render: (_: unknown, r: { correct_count: number; total_questions: number }) => {
                const acc = r.total_questions > 0 ? (r.correct_count / r.total_questions * 100) : 0;
                return (
                  <span style={{ fontWeight: 700, color: acc >= 70 ? '#52c41a' : acc >= 50 ? '#faad14' : '#ff4d4f' }}>
                    {acc.toFixed(1)}%
                  </span>
                );
              },
            },
            {
              title: '时间', dataIndex: 'created_at', width: 120,
              render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-',
            },
          ]}
        />
      ),
    },
    {
      key: 'weakness',
      label: <><BugOutlined /> 薄弱分析</>,
      children: <WeaknessAnalysis studentId={studentId} />,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/students')}>返回列表</Button>
          <span style={{ fontSize: 18, fontWeight: 600 }}>{student.name}</span>
          <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
        </Space>
        <Space>
          <Button icon={<PrinterOutlined />} onClick={() => navigate(`/students/${studentId}/report`)}>
            生成报告
          </Button>
          <Button type="primary" icon={<AimOutlined />} onClick={() => navigate(`/students/${studentId}/recommend`)}>
            智能选岗
          </Button>
        </Space>
      </div>

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  );
}
