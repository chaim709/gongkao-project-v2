import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Row, Col, Statistic, Tag, Table, Select, Button, Space, Descriptions,
  Segmented, Empty, Spin, Alert, message, Tooltip, Progress,
} from 'antd';
import {
  ArrowLeftOutlined, UserOutlined, TrophyOutlined, SafetyOutlined,
  ThunderboltOutlined, AimOutlined, StarOutlined, StarFilled,
  DownloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentApi } from '../../api/students';
import { positionApi } from '../../api/positions';
import type { ColumnsType } from 'antd/es/table';
import WeaknessAnalysis from '../../components/WeaknessAnalysis';

interface RecommendPosition {
  position: {
    id: number;
    title: string;
    department: string;
    city: string;
    education: string;
    major: string;
    recruitment_count: number;
    year: number;
    exam_type: string;
  };
  recommend_score: number;
  competition: { score: number; level: string; level_text: string };
  value: { score: number; level: string; level_text: string };
}

interface CityRating {
  city: string;
  positions: number;
  recruitment: number;
  avg_competition_ratio: number;
  rating: number;
}

const levelColors: Record<string, string> = {
  high: 'red', medium: 'orange', easy: 'green', low: 'red',
};

export default function StudentRecommend() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const studentId = Number(id);

  const [year, setYear] = useState<number>(2025);
  const [examType, setExamType] = useState<string>('事业单位');
  const [strategy, setStrategy] = useState<string>('balanced');
  const [activeTab, setActiveTab] = useState<string>('stable');

  const queryClient = useQueryClient();

  // 获取学员信息
  const { data: student, isLoading: studentLoading } = useQuery({
    queryKey: ['student', studentId],
    queryFn: () => studentApi.getById(studentId),
    enabled: !!studentId,
  });

  // 获取可选年���和考试类型
  const { data: filterOptions } = useQuery({
    queryKey: ['position-filters-recommend'],
    queryFn: () => positionApi.filterOptions(),
  });

  // 获取推荐结果
  const { data: recommend, isLoading: recommendLoading } = useQuery({
    queryKey: ['position-recommend', studentId, year, examType, strategy],
    queryFn: () => positionApi.recommend(studentId, {
      year,
      exam_type: examType,
      limit: 30,
      strategy,
    }),
    enabled: !!studentId,
  });

  const recommendData = recommend?.success ? recommend.data : null;

  // 收藏列表
  const { data: favorites } = useQuery({
    queryKey: ['position-favorites', studentId],
    queryFn: () => positionApi.getFavorites(studentId),
    enabled: !!studentId,
  });

  const favoriteIds = new Set((favorites?.items || []).map((f: { position: { id: number } }) => f.position.id));

  const addFavMutation = useMutation({
    mutationFn: positionApi.addFavorite,
    onSuccess: () => { message.success('已收藏'); queryClient.invalidateQueries({ queryKey: ['position-favorites'] }); },
    onError: () => message.warning('已收藏过该岗位'),
  });

  const removeFavMutation = useMutation({
    mutationFn: positionApi.removeFavorite,
    onSuccess: () => { message.success('已取消收藏'); queryClient.invalidateQueries({ queryKey: ['position-favorites'] }); },
  });

  const toggleFavorite = (positionId: number) => {
    const existing = (favorites?.items || []).find((f: { position: { id: number }; id: number }) => f.position.id === positionId);
    if (existing) {
      removeFavMutation.mutate(existing.id);
    } else {
      addFavMutation.mutate({ student_id: studentId, position_id: positionId, category: activeTab });
    }
  };

  // 城市评级
  const { data: cityRatings } = useQuery({
    queryKey: ['city-ratings', year, examType],
    queryFn: () => positionApi.cityRatings({ year, exam_type: examType }),
  });

  // 导出选岗报告（浏览器打印为PDF）
  const handleExportReport = () => {
    if (!recommendData || !student) return;
    const allPositions = [
      ...(recommendData.sprint || []).map((r: RecommendPosition) => ({ ...r, category: '冲刺' })),
      ...(recommendData.stable || []).map((r: RecommendPosition) => ({ ...r, category: '稳妥' })),
      ...(recommendData.safe || []).map((r: RecommendPosition) => ({ ...r, category: '保底' })),
    ];
    const strategyText = strategyLabels[strategy] || strategy;
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${student.name} 选岗报告</title>
<style>
  body { font-family: -apple-system, "Microsoft YaHei", sans-serif; padding: 40px; color: #333; }
  h1 { text-align: center; color: #1677ff; border-bottom: 2px solid #1677ff; padding-bottom: 12px; }
  .info { display: flex; gap: 40px; margin: 20px 0; padding: 16px; background: #f5f5f5; border-radius: 8px; }
  .info span { font-size: 14px; }
  .summary { display: flex; gap: 24px; margin: 16px 0; }
  .summary .card { flex: 1; padding: 16px; border-radius: 8px; text-align: center; color: #fff; }
  .card.sprint { background: #ff4d4f; } .card.stable { background: #faad14; } .card.safe { background: #52c41a; }
  .card .num { font-size: 28px; font-weight: bold; }
  table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }
  th { background: #1677ff; color: #fff; padding: 8px; text-align: left; }
  td { padding: 6px 8px; border-bottom: 1px solid #eee; }
  tr:nth-child(even) { background: #fafafa; }
  .category { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; color: #fff; }
  .cat-冲刺 { background: #ff4d4f; } .cat-稳妥 { background: #faad14; } .cat-保底 { background: #52c41a; }
  .footer { text-align: center; color: #999; margin-top: 30px; font-size: 12px; }
  @media print { body { padding: 20px; } }
</style></head><body>
<h1>${student.name} - 智能选岗报告</h1>
<div class="info">
  <span><b>学员：</b>${student.name}</span>
  <span><b>学历：</b>${student.education || '未填写'}</span>
  <span><b>专业：</b>${student.major || '未填写'}</span>
  <span><b>年份：</b>${year}年</span>
  <span><b>考试类型：</b>${examType}</span>
  <span><b>策略：</b>${strategyText}</span>
</div>
<div class="summary">
  <div class="card sprint"><div class="num">${recommendData.summary?.sprint_count || 0}</div><div>冲刺岗位</div></div>
  <div class="card stable"><div class="num">${recommendData.summary?.stable_count || 0}</div><div>稳妥岗位</div></div>
  <div class="card safe"><div class="num">${recommendData.summary?.safe_count || 0}</div><div>保底岗位</div></div>
</div>
<p>共匹配 <b>${recommendData.total_matched || 0}</b> 个符合条件的岗位</p>
<table>
  <thead><tr><th>分类</th><th>岗位</th><th>单位</th><th>地区</th><th>学历</th><th>招录</th><th>推荐分</th><th>竞争度</th><th>性价比</th></tr></thead>
  <tbody>${allPositions.map((r: RecommendPosition & { category: string }) => `<tr>
    <td><span class="category cat-${r.category}">${r.category}</span></td>
    <td>${r.position.title || r.position.department || '-'}</td>
    <td>${r.position.department || '-'}</td>
    <td>${r.position.city || '-'}</td>
    <td>${r.position.education || '-'}</td>
    <td>${r.position.recruitment_count || '-'}</td>
    <td>${r.recommend_score}</td>
    <td>${r.competition.level_text}</td>
    <td>${r.value.level_text}</td>
  </tr>`).join('')}</tbody>
</table>
<div class="footer">报告生成时间：${new Date().toLocaleString('zh-CN')} | 智能选岗系统</div>
</body></html>`;
    const win = window.open('', '_blank');
    if (win) {
      win.document.write(html);
      win.document.close();
      setTimeout(() => win.print(), 500);
    }
    message.success('报告已生成，请在新窗口中打印/保存为PDF');
  };

  // 推荐表格列
  const columns: ColumnsType<RecommendPosition> = [
    {
      title: '岗位', dataIndex: ['position', 'title'], width: 150, ellipsis: true,
      render: (_: unknown, r: RecommendPosition) => r.position.title || r.position.department || '-',
    },
    {
      title: '单位', dataIndex: ['position', 'department'], width: 180, ellipsis: true,
    },
    {
      title: '地区', dataIndex: ['position', 'city'], width: 80,
    },
    {
      title: '学历', dataIndex: ['position', 'education'], width: 100, ellipsis: true,
    },
    {
      title: '招录', dataIndex: ['position', 'recruitment_count'], width: 60, align: 'center',
    },
    {
      title: '推荐分', dataIndex: 'recommend_score', width: 80, align: 'center',
      sorter: (a, b) => a.recommend_score - b.recommend_score,
      render: (v: number) => <span style={{ fontWeight: 600, color: v >= 70 ? '#52c41a' : v >= 50 ? '#faad14' : '#ff4d4f' }}>{v}</span>,
    },
    {
      title: '竞争度', key: 'competition', width: 100, align: 'center',
      render: (_: unknown, r: RecommendPosition) => (
        <Tag color={levelColors[r.competition.level]}>{r.competition.level_text}</Tag>
      ),
    },
    {
      title: '性价比', key: 'value', width: 100, align: 'center',
      render: (_: unknown, r: RecommendPosition) => (
        <Tag color={r.value.level === 'high' ? 'green' : r.value.level === 'medium' ? 'orange' : 'red'}>
          {r.value.level_text}
        </Tag>
      ),
    },
    {
      title: '收藏', key: 'favorite', width: 50, align: 'center',
      render: (_: unknown, r: RecommendPosition) => (
        <Tooltip title={favoriteIds.has(r.position.id) ? '取消收藏' : '收藏'}>
          <Button
            type="text"
            size="small"
            icon={favoriteIds.has(r.position.id)
              ? <StarFilled style={{ color: '#faad14' }} />
              : <StarOutlined style={{ color: '#999' }} />
            }
            onClick={() => toggleFavorite(r.position.id)}
          />
        </Tooltip>
      ),
    },
  ];

  const strategyLabels: Record<string, string> = {
    aggressive: '激进策略 - 多冲刺',
    balanced: '平衡策略 - 推荐',
    conservative: '保守策略 - 求稳',
  };

  const tabItems = [
    { label: `冲刺 (${recommendData?.summary?.sprint_count || 0})`, value: 'sprint', icon: <ThunderboltOutlined /> },
    { label: `稳妥 (${recommendData?.summary?.stable_count || 0})`, value: 'stable', icon: <AimOutlined /> },
    { label: `保底 (${recommendData?.summary?.safe_count || 0})`, value: 'safe', icon: <SafetyOutlined /> },
  ];

  const currentList: RecommendPosition[] = recommendData?.[activeTab] || [];

  if (studentLoading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      {/* 顶部导航 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/students')}>返回学员列表</Button>
          <span style={{ fontSize: 18, fontWeight: 600 }}>
            <UserOutlined /> {student?.name} - 智能选岗
          </span>
        </Space>
      </div>

      {/* 学员信息 + 筛选条件 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card size="small" title="学员信息">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="姓名">{student?.name}</Descriptions.Item>
              <Descriptions.Item label="学历">{student?.education || <Tag color="red">未填写</Tag>}</Descriptions.Item>
              <Descriptions.Item label="专业">{student?.major || <Tag color="red">未填写</Tag>}</Descriptions.Item>
              <Descriptions.Item label="报考类型">{student?.exam_type || '-'}</Descriptions.Item>
            </Descriptions>
            {!student?.education && (
              <Alert
                type="warning" showIcon
                message="请先完善学员的学历和专业信息，以获得更精准的推荐"
                style={{ marginTop: 8 }}
              />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small" title="推荐设置">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div style={{ display: 'flex', gap: 8 }}>
                <Select
                  value={year}
                  style={{ width: 120 }}
                  onChange={setYear}
                  options={(filterOptions?.years || [2025, 2024]).map((y: number) => ({ value: y, label: `${y}年` }))}
                />
                <Select
                  value={examType}
                  style={{ width: 130 }}
                  onChange={setExamType}
                  options={(filterOptions?.exam_types || ['事业单位', '国考', '省考']).map((t: string) => ({ value: t, label: t }))}
                />
                <Select
                  value={strategy}
                  style={{ flex: 1 }}
                  onChange={setStrategy}
                  options={[
                    { value: 'aggressive', label: '激进策略 - 多冲刺岗位' },
                    { value: 'balanced', label: '平衡策略 - 推荐' },
                    { value: 'conservative', label: '保守策略 - 求稳上岸' },
                  ]}
                />
              </div>
              <div style={{ color: '#666', fontSize: 13 }}>
                {strategyLabels[strategy]}：
                {strategy === 'aggressive' && '30%冲刺 + 40%稳妥 + 30%保底'}
                {strategy === 'balanced' && '20%冲刺 + 50%稳妥 + 30%保底'}
                {strategy === 'conservative' && '10%冲刺 + 40%稳妥 + 50%保底'}
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 匹配概览 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="符合条件岗位"
              value={recommendData?.total_matched || 0}
              prefix={<TrophyOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="冲刺岗位"
              value={recommendData?.summary?.sprint_count || 0}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="稳妥岗位"
              value={recommendData?.summary?.stable_count || 0}
              valueStyle={{ color: '#faad14' }}
              prefix={<AimOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="保底岗位"
              value={recommendData?.summary?.safe_count || 0}
              valueStyle={{ color: '#52c41a' }}
              prefix={<SafetyOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 推荐岗位列表 */}
      <Card
        size="small"
        title={
          <Segmented
            options={tabItems.map(t => ({ label: <Space>{t.icon}{t.label}</Space>, value: t.value }))}
            value={activeTab}
            onChange={(v) => setActiveTab(v as string)}
          />
        }
        extra={
          <Space>
            <span style={{ color: '#999' }}>{year}年 · {examType}</span>
            <Tooltip title="导出选岗报告">
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => handleExportReport()}
                disabled={!recommendData}
              >
                导出报告
              </Button>
            </Tooltip>
          </Space>
        }
      >
        {recommendLoading ? (
          <Spin style={{ display: 'block', margin: '40px auto' }} />
        ) : currentList.length > 0 ? (
          <Table<RecommendPosition>
            columns={columns}
            dataSource={currentList}
            rowKey={(r) => r.position.id}
            pagination={false}
            scroll={{ x: 900 }}
            size="small"
          />
        ) : (
          <Empty description={`暂无${activeTab === 'sprint' ? '冲刺' : activeTab === 'stable' ? '稳妥' : '保底'}岗位`} />
        )}
      </Card>

      {/* 城市竞争热力图 */}
      {Array.isArray(cityRatings) && cityRatings.length > 0 && (
        <Card size="small" title="城市竞争概览" style={{ marginTop: 16 }}>
          <Table<CityRating>
            columns={[
              { title: '城市', dataIndex: 'city', width: 100 },
              {
                title: '评级', dataIndex: 'rating', width: 80, align: 'center',
                render: (v: number) => {
                  const stars = Math.max(1, Math.min(5, 6 - v));
                  return <span style={{ color: '#faad14' }}>{'★'.repeat(stars)}{'☆'.repeat(5 - stars)}</span>;
                },
                sorter: (a, b) => a.rating - b.rating,
              },
              { title: '岗位数', dataIndex: 'positions', width: 80, align: 'center', sorter: (a, b) => a.positions - b.positions },
              { title: '招录人数', dataIndex: 'recruitment', width: 90, align: 'center', sorter: (a, b) => a.recruitment - b.recruitment },
              {
                title: '平均竞争比', dataIndex: 'avg_competition_ratio', width: 120,
                render: (v: number) => (
                  <Space>
                    <Progress
                      percent={Math.min(100, v * 2)}
                      size="small"
                      strokeColor={v > 30 ? '#ff4d4f' : v > 15 ? '#faad14' : '#52c41a'}
                      showInfo={false}
                      style={{ width: 60 }}
                    />
                    <span>{v}:1</span>
                  </Space>
                ),
                sorter: (a, b) => a.avg_competition_ratio - b.avg_competition_ratio,
              },
            ]}
            dataSource={cityRatings}
            rowKey="city"
            pagination={false}
            size="small"
          />
        </Card>
      )}

      {/* 弱项分析 */}
      <Card size="small" title="📊 模考弱项分析" style={{ marginTop: 16 }}>
        <WeaknessAnalysis studentId={studentId} />
      </Card>
    </div>
  );
}
