import { Card, Row, Col, Statistic, Tag, Table, Empty, Spin, Progress } from 'antd';
import { WarningOutlined, RiseOutlined, BugOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend,
} from 'recharts';
import { examApi } from '../api/exams';
import { weaknessApi, type WeaknessRadarItem } from '../api/weakness';

interface CategoryItem {
  category: string;
  total: number;
  correct: number;
  wrong: number;
  accuracy: number;
}

interface ScoreItem {
  paper_title: string;
  correct: number;
  wrong: number;
  accuracy: number;
  date: string;
}

interface AnalysisData {
  student_id: number;
  categories: CategoryItem[];
  weakest: CategoryItem[];
  scores_trend: ScoreItem[];
  unmastered_mistakes: number;
}

export default function WeaknessAnalysis({ studentId }: { studentId: number }) {
  // 考试数据分析
  const { data, isLoading } = useQuery<AnalysisData>({
    queryKey: ['student-analysis', studentId],
    queryFn: () => examApi.getStudentAnalysis(studentId),
    enabled: !!studentId,
  });

  // 薄弱项标签雷达数据
  const { data: radarData, isLoading: radarLoading } = useQuery({
    queryKey: ['weakness-radar', studentId],
    queryFn: () => weaknessApi.getWeaknessRadar(studentId),
    enabled: !!studentId,
  });

  if (isLoading || radarLoading) {
    return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  }

  const hasExamData = data && (data.categories.length > 0 || data.scores_trend.length > 0);
  const hasWeaknessData = radarData && radarData.items.length > 0;

  if (!hasExamData && !hasWeaknessData) {
    return <Empty description="暂无答题数据，提交模考错题或添加薄弱项标签后将自动生成分析" />;
  }

  // 考试雷达图数据
  const examRadarData = data?.categories.slice(0, 8).map(c => ({
    name: c.category.length > 6 ? c.category.slice(0, 5) + '…' : c.category,
    fullName: c.category,
    accuracy: c.accuracy,
    total: c.total,
  })) || [];

  // 薄弱项标签雷达图数据
  const weaknessRadarChartData = radarData?.items.slice(0, 10).map((r: WeaknessRadarItem) => ({
    name: r.module.length > 6 ? r.module.slice(0, 5) + '…' : r.module,
    fullName: r.module,
    mastery: r.mastery,
    accuracy: r.accuracy,
  })) || [];

  const summary = radarData?.summary;

  return (
    <div>
      {/* 概览统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {hasExamData && (
          <>
            <Col span={hasWeaknessData ? 4 : 8}>
              <Card size="small">
                <Statistic
                  title="未掌握错题"
                  value={data!.unmastered_mistakes}
                  prefix={<BugOutlined />}
                  valueStyle={{ color: data!.unmastered_mistakes > 20 ? '#ff4d4f' : '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={hasWeaknessData ? 4 : 8}>
              <Card size="small">
                <Statistic
                  title="最近正确率"
                  value={data!.scores_trend.length ? data!.scores_trend[data!.scores_trend.length - 1].accuracy : 0}
                  suffix="%"
                  prefix={<RiseOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
          </>
        )}
        {hasWeaknessData && (
          <>
            <Col span={hasExamData ? 4 : 6}>
              <Card size="small">
                <Statistic
                  title="薄弱模块"
                  value={summary?.weak_modules || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                  suffix="个"
                />
              </Card>
            </Col>
            <Col span={hasExamData ? 4 : 6}>
              <Card size="small">
                <Statistic
                  title="一般模块"
                  value={summary?.medium_modules || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#faad14' }}
                  suffix="个"
                />
              </Card>
            </Col>
            <Col span={hasExamData ? 4 : 6}>
              <Card size="small">
                <Statistic
                  title="掌握模块"
                  value={summary?.strong_modules || 0}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                  suffix="个"
                />
              </Card>
            </Col>
            <Col span={hasExamData ? 4 : 6}>
              <Card size="small">
                <Statistic
                  title="知识点总数"
                  value={summary?.total_modules || 0}
                  suffix="个"
                />
              </Card>
            </Col>
          </>
        )}
      </Row>

      {/* 知识点掌握度雷达图（薄弱项标签数据） */}
      {hasWeaknessData && (
        <Card size="small" title="知识点掌握度分布" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={14}>
              {weaknessRadarChartData.length >= 3 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <RadarChart data={weaknessRadarChartData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                    <Radar name="掌握度" dataKey="mastery" stroke="#52c41a" fill="#52c41a" fillOpacity={0.3} />
                    <Radar name="正确率" dataKey="accuracy" stroke="#1677ff" fill="#1677ff" fillOpacity={0.15} />
                    <Legend />
                    <Tooltip
                      formatter={((value: number, name: string) => [`${value}%`, name]) as any}
                      labelFormatter={((_: string, payload: any[]) => payload?.[0]?.payload?.fullName || '') as any}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <Empty description="至少需要3个知识点模块才能生成雷达图" />
              )}
            </Col>
            <Col span={10}>
              <div style={{ padding: '8px 0' }}>
                {radarData!.items.map((item: WeaknessRadarItem) => (
                  <div key={item.module} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 13 }}>{item.module}</span>
                      <span>
                        <Tag color={item.mastery >= 70 ? 'green' : item.mastery >= 40 ? 'orange' : 'red'} style={{ marginRight: 0 }}>
                          {item.mastery}%
                        </Tag>
                      </span>
                    </div>
                    <Progress
                      percent={item.mastery}
                      showInfo={false}
                      size="small"
                      strokeColor={item.mastery >= 70 ? '#52c41a' : item.mastery >= 40 ? '#faad14' : '#ff4d4f'}
                    />
                  </div>
                ))}
              </div>
            </Col>
          </Row>
        </Card>
      )}

      <Row gutter={16}>
        {/* 考试正确率雷达图 */}
        {hasExamData && (
          <Col span={12}>
            <Card size="small" title="模考知识点正确率">
              {examRadarData.length >= 3 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={examRadarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                    <Radar name="正确率" dataKey="accuracy" stroke="#1677ff" fill="#1677ff" fillOpacity={0.3} />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <Empty description="至少需要3个知识点分类才能生成雷达图" />
              )}
            </Card>
          </Col>
        )}

        {/* 成绩趋势 */}
        {hasExamData && (
          <Col span={12}>
            <Card size="small" title="模考成绩趋势">
              {data!.scores_trend.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={data!.scores_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                    <Tooltip
                      formatter={((value: number) => [`${value}%`, '正确率']) as any}
                      labelFormatter={((label: string, payload: { payload?: ScoreItem }[]) =>
                        payload?.[0]?.payload?.paper_title || label
                      ) as any}
                    />
                    <Line type="monotone" dataKey="accuracy" stroke="#1677ff" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Empty description="暂无模考记录" />
              )}
            </Card>
          </Col>
        )}
      </Row>

      {/* 模块正确率明细表 */}
      {hasExamData && data!.categories.length > 0 && (
        <Card size="small" title="各模块正确率明细" style={{ marginTop: 16 }}>
          <Table<CategoryItem>
            columns={[
              {
                title: '知识模块', dataIndex: 'category', width: 180,
                render: (v: string, r: CategoryItem) => (
                  <span>
                    {r.accuracy < 50 && <Tag color="red">薄弱</Tag>}
                    {v}
                  </span>
                ),
              },
              { title: '做题数', dataIndex: 'total', width: 80, align: 'center' },
              { title: '正确', dataIndex: 'correct', width: 70, align: 'center' },
              {
                title: '错误', dataIndex: 'wrong', width: 70, align: 'center',
                render: (v: number) => <span style={{ color: v > 0 ? '#ff4d4f' : '#333' }}>{v}</span>,
              },
              {
                title: '正确率', dataIndex: 'accuracy', width: 100, align: 'center',
                sorter: (a, b) => a.accuracy - b.accuracy,
                defaultSortOrder: 'ascend',
                render: (v: number) => (
                  <span style={{
                    fontWeight: 600,
                    color: v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f',
                  }}>
                    {v}%
                  </span>
                ),
              },
            ]}
            dataSource={data!.categories}
            rowKey="category"
            pagination={false}
            size="small"
          />
        </Card>
      )}
    </div>
  );
}
