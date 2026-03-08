import { useState } from 'react';
import {
  Card, Row, Col, Statistic, Select, Table, Tag, Space, Empty, Spin,
} from 'antd';
import {
  TrophyOutlined, TeamOutlined, WarningOutlined, RiseOutlined,
  CrownOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import { examApi } from '../../api/exams';
import type { ColumnsType } from 'antd/es/table';

interface RankingItem {
  rank: number;
  student_id: number;
  student_name: string;
  exam_count: number;
  avg_accuracy: number;
  best_accuracy: number;
}

interface WeaknessItem {
  category: string;
  total: number;
  correct: number;
  wrong: number;
  accuracy: number;
}

interface ClassData {
  rankings: RankingItem[];
  class_weaknesses: WeaknessItem[];
  summary: {
    total_students: number;
    avg_accuracy: number;
    total_exams: number;
    weakest_area: string;
  };
}

export default function ClassAnalysisPage() {
  const [paperId, setPaperId] = useState<number>();

  const { data: papers } = useQuery({
    queryKey: ['exam-papers-select'],
    queryFn: () => examApi.listPapers({ page: 1, page_size: 100 }),
  });

  const { data, isLoading } = useQuery<ClassData>({
    queryKey: ['class-analysis', paperId],
    queryFn: () => examApi.getClassAnalysis(paperId),
  });

  const rankColumns: ColumnsType<RankingItem> = [
    {
      title: '排名', dataIndex: 'rank', width: 70, align: 'center',
      render: (v: number) => {
        if (v <= 3) return <CrownOutlined style={{ color: v === 1 ? '#faad14' : v === 2 ? '#bfbfbf' : '#d48806', fontSize: 18 }} />;
        return v;
      },
    },
    { title: '学员', dataIndex: 'student_name', width: 120 },
    { title: '参加模考', dataIndex: 'exam_count', width: 90, align: 'center' },
    {
      title: '平均正确率', dataIndex: 'avg_accuracy', width: 120, align: 'center',
      sorter: (a, b) => a.avg_accuracy - b.avg_accuracy,
      defaultSortOrder: 'descend',
      render: (v: number) => (
        <span style={{
          fontWeight: 700,
          color: v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f',
        }}>
          {v}%
        </span>
      ),
    },
    {
      title: '最高正确率', dataIndex: 'best_accuracy', width: 120, align: 'center',
      render: (v: number) => <span style={{ color: '#1677ff', fontWeight: 600 }}>{v}%</span>,
    },
    {
      title: '水平', key: 'level', width: 90, align: 'center',
      render: (_: unknown, r: RankingItem) => {
        if (r.avg_accuracy >= 80) return <Tag color="green">优秀</Tag>;
        if (r.avg_accuracy >= 65) return <Tag color="blue">良好</Tag>;
        if (r.avg_accuracy >= 50) return <Tag color="orange">待提升</Tag>;
        return <Tag color="red">需关注</Tag>;
      },
    },
  ];

  const radarData = (data?.class_weaknesses || []).slice(0, 8).map(w => ({
    name: w.category.length > 6 ? w.category.slice(0, 5) + '…' : w.category,
    accuracy: w.accuracy,
  }));

  if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      {/* 筛选 */}
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span style={{ fontWeight: 600 }}>按试卷筛选：</span>
          <Select
            value={paperId}
            onChange={setPaperId}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 320 }}
            placeholder="全部试卷"
            options={(papers?.items || []).map((p: { id: number; title: string }) => ({
              value: p.id, label: p.title,
            }))}
          />
        </Space>
      </div>

      {/* 概览 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="参与学员" value={data?.summary?.total_students || 0} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="班级平均正确率"
              value={data?.summary?.avg_accuracy || 0}
              suffix="%"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="模考总次数" value={data?.summary?.total_exams || 0} prefix={<TrophyOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="最薄弱模块"
              value={data?.summary?.weakest_area || '暂无'}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#ff4d4f', fontSize: 18 }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        {/* 学员排名 */}
        <Col span={14}>
          <Card size="small" title="学员成绩排名">
            {(data?.rankings?.length || 0) > 0 ? (
              <Table<RankingItem>
                columns={rankColumns}
                dataSource={data?.rankings || []}
                rowKey="student_id"
                pagination={false}
                size="small"
                scroll={{ y: 400 }}
              />
            ) : (
              <Empty description="暂无模考数据" />
            )}
          </Card>
        </Col>

        {/* 班级弱项雷达图 */}
        <Col span={10}>
          <Card size="small" title="班级知识点正确率">
            {radarData.length >= 3 ? (
              <ResponsiveContainer width="100%" height={360}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                  <Radar name="正确率" dataKey="accuracy" stroke="#ff4d4f" fill="#ff4d4f" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="至少需要3个知识分类" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 薄弱模块柱状图 */}
      {(data?.class_weaknesses?.length || 0) > 0 && (
        <Card size="small" title="班级各模块正确率（从低到高）">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data!.class_weaknesses} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis type="category" dataKey="category" width={110} tick={{ fontSize: 12 }} />
              <Tooltip formatter={((v: number) => [`${v}%`, '正确率']) as any} />
              <Bar
                dataKey="accuracy"
                fill="#1677ff"
                name="正确率"
                label={{ position: 'right', formatter: ((v: number) => `${v}%`) as any, fontSize: 11 }}
              />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}
