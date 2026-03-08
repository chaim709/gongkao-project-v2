import { useParams, useNavigate } from 'react-router-dom';
import { Button, Spin, Empty, Descriptions, Tag, Progress, Card, Table } from 'antd';
import { ArrowLeftOutlined, PrinterOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { studentApi } from '../../api/students';

const statusMap: Record<string, { text: string; color: string }> = {
  lead: { text: '线索', color: 'default' },
  trial: { text: '试听', color: 'purple' },
  active: { text: '在读', color: 'green' },
  inactive: { text: '休学', color: 'orange' },
  graduated: { text: '结业', color: 'blue' },
  dropped: { text: '退出', color: 'red' },
};

export default function StudentReport() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const studentId = Number(id);

  const { data: report, isLoading } = useQuery({
    queryKey: ['student-report', studentId],
    queryFn: () => studentApi.getReport(studentId),
    enabled: !!studentId,
  });

  if (isLoading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  if (!report) {
    return <Empty description="报告数据不存在" />;
  }

  const { student, attendance, supervision, generated_at } = report;
  const statusInfo = statusMap[student.status] || { text: student.status, color: 'default' };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div>
      {/* 操作按钮 - 打印时隐藏 */}
      <div className="no-print" style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/students/${studentId}`)}>
          返回详情
        </Button>
        <Button type="primary" icon={<PrinterOutlined />} onClick={handlePrint}>
          打印报告
        </Button>
      </div>

      {/* 报告正文 */}
      <div id="report-content" style={{ background: '#fff', padding: 32, maxWidth: 800, margin: '0 auto' }}>
        {/* 报告标题 */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>学员学习报告</h1>
          <p style={{ color: '#999' }}>报告生成日期: {generated_at}</p>
        </div>

        {/* 基本信息 */}
        <Card title="一、基本信息" size="small" style={{ marginBottom: 24 }}>
          <Descriptions column={2} size="small">
            <Descriptions.Item label="姓名">{student.name}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusInfo.color}>{statusInfo.text}</Tag></Descriptions.Item>
            <Descriptions.Item label="手机号">{student.phone || '-'}</Descriptions.Item>
            <Descriptions.Item label="学历">{student.education || '-'}</Descriptions.Item>
            <Descriptions.Item label="专业">{student.major || '-'}</Descriptions.Item>
            <Descriptions.Item label="报考类型">{student.exam_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="入学日期">{student.enrollment_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="最近联系">{student.last_contact_date || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 考勤统计 */}
        <Card title="二、考勤情况" size="small" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', gap: 48, alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={attendance.rate}
                size={120}
                strokeColor={attendance.rate >= 80 ? '#52c41a' : attendance.rate >= 60 ? '#faad14' : '#ff4d4f'}
                format={(p) => `${p}%`}
              />
              <p style={{ marginTop: 8, color: '#666' }}>出勤率</p>
            </div>
            <div style={{ flex: 1 }}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="总考勤次数">{attendance.total} 次</Descriptions.Item>
                <Descriptions.Item label="出勤次数">{attendance.present} 次</Descriptions.Item>
                <Descriptions.Item label="缺勤次数">{attendance.total - attendance.present} 次</Descriptions.Item>
                <Descriptions.Item label="评价">
                  <Tag color={attendance.rate >= 80 ? 'green' : attendance.rate >= 60 ? 'orange' : 'red'}>
                    {attendance.rate >= 80 ? '优秀' : attendance.rate >= 60 ? '良好' : '需改善'}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </div>
          </div>
        </Card>

        {/* 督学跟进 */}
        <Card title="三、督学跟进记录" size="small" style={{ marginBottom: 24 }}>
          <p style={{ marginBottom: 16 }}>共 {supervision.log_count} 条督学日志，最近 5 条记录如下：</p>
          {supervision.recent_logs.length > 0 ? (
            <Table
              size="small"
              dataSource={supervision.recent_logs}
              rowKey="date"
              pagination={false}
              columns={[
                { title: '日期', dataIndex: 'date', width: 110 },
                { title: '心情', dataIndex: 'mood', width: 80, render: (v: string) => v || '-' },
                { title: '学习状态', dataIndex: 'study_status', width: 100, render: (v: string) => v || '-' },
                { title: '内容', dataIndex: 'content', ellipsis: true, render: (v: string) => v || '-' },
              ]}
            />
          ) : (
            <p style={{ color: '#999', textAlign: 'center' }}>暂无督学记录</p>
          )}
        </Card>

        {/* 建议 */}
        <Card title="四、学习建议" size="small" style={{ marginBottom: 24 }}>
          <ul style={{ paddingLeft: 20, lineHeight: 2 }}>
            {attendance.rate < 80 && (
              <li>出勤率偏低（{attendance.rate}%），建议加强出勤管理，保持规律学习节奏。</li>
            )}
            {attendance.rate >= 80 && (
              <li>出勤表现优秀（{attendance.rate}%），继续保持良好的学习习惯。</li>
            )}
            {supervision.log_count < 5 && (
              <li>督学跟进次数较少，建议增加沟通频次，及时了解学习进度。</li>
            )}
            {supervision.log_count >= 5 && (
              <li>督学跟进积极，建议继续保持定期沟通。</li>
            )}
            <li>建议制定阶段性学习目标，定期进行模考评估。</li>
            <li>关注薄弱知识点，有针对性地进行专项练习。</li>
          </ul>
        </Card>

        {/* 页脚 */}
        <div style={{ textAlign: 'center', color: '#999', fontSize: 12, marginTop: 32, borderTop: '1px solid #eee', paddingTop: 16 }}>
          <p>本报告由公考培训管理系统自动生成 | {generated_at}</p>
        </div>
      </div>

      {/* 打印样式 */}
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: #fff; }
          #report-content { box-shadow: none; max-width: 100%; padding: 0; }
        }
      `}</style>
    </div>
  );
}
