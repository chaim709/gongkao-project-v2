import { Card, Col, Row, Select, Spin, Alert, Badge, List, Tag, Tour } from 'antd';
import {
  TeamOutlined, CheckCircleOutlined, AlertOutlined,
  CalendarOutlined, BellOutlined, ProjectOutlined,
  FileTextOutlined, UploadOutlined,
  ArrowUpOutlined, ArrowDownOutlined,
  DollarOutlined, TrophyOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../../api/analytics';
import { examApi } from '../../api/exams';
import { studentApi } from '../../api/students';
import { calendarApi } from '../../api/calendar';
import { useState, useMemo, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import { useAuthStore } from '../../stores/authStore';
import { useThemeStore } from '../../stores/themeStore';
import { chartColors, getDesignTokens } from '../../theme';

const STATUS_LABELS: Record<string, string> = {
  lead: '线索', trial: '试听', active: '在读',
  inactive: '休学', graduated: '结业', dropped: '退出',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const themeMode = useThemeStore((s) => s.mode);
  const designTokens = getDesignTokens(themeMode);
  const isAdmin = user?.role === 'admin';
  const [trendDays, setTrendDays] = useState(7);

  // 新手引导
  const overviewRef = useRef<HTMLDivElement>(null);
  const trendRef = useRef<HTMLDivElement>(null);
  const [tourOpen, setTourOpen] = useState(false);

  useEffect(() => {
    const toured = localStorage.getItem('dashboard_toured');
    if (!toured) {
      const timer = setTimeout(() => setTourOpen(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const tourSteps = [
    {
      title: '数据概览',
      description: '核心指标一目了然：学员总数、打卡情况、待跟进、学习计划。',
      target: () => overviewRef.current!,
    },
    {
      title: '数据趋势',
      description: '查看打卡和新增学员的趋势变化，支持 7/14/30 天切换。',
      target: () => trendRef.current!,
    },
  ];

  // === 数据请求 ===
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: analyticsApi.overview,
  });

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics-trends', trendDays],
    queryFn: () => analyticsApi.trends(trendDays),
  });

  const { data: reminders } = useQuery({
    queryKey: ['follow-up-reminders'],
    queryFn: () => studentApi.getReminders(7),
  });

  const { data: upcomingExams } = useQuery({
    queryKey: ['calendar-upcoming-dashboard'],
    queryFn: () => calendarApi.upcoming(90),
  });

  const { data: financeTrend } = useQuery({
    queryKey: ['finance-trend'],
    queryFn: () => analyticsApi.financeTrend(6),
    enabled: isAdmin,
  });

  const { data: classAnalysis } = useQuery({
    queryKey: ['class-analysis-dashboard'],
    queryFn: () => examApi.getClassAnalysis(),
  });

  // 合并趋势数据
  const trendData = useMemo(() => {
    if (!trends) return [];
    return (trends.checkins || []).map((item: { date: string; count: number }, i: number) => ({
      date: item.date,
      checkins: item.count,
      students: trends.students?.[i]?.count || 0,
    }));
  }, [trends]);

  // 学员状态分布
  const statusData = useMemo(() => {
    if (!overview?.students?.by_status) return [];
    return Object.entries(overview.students.by_status).map(([key, value]) => ({
      name: STATUS_LABELS[key] || key,
      value,
      key,
    }));
  }, [overview]);

  if (overviewLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (overviewError) {
    return <Alert message="数据加载失败" description="请检查网络连接或稍后重试" type="error" showIcon />;
  }

  const totalStudents = overview?.students?.total || 0;
  const activeStudents = overview?.students?.active || 0;
  const todayCheckins = overview?.checkins?.today || 0;
  const needsFollowup = reminders?.count || 0;
  const checkinRate = activeStudents ? Math.round((todayCheckins / activeStudents) * 100) : 0;

  // KPI 卡片数据
  const kpiCards = [
    {
      title: '学员总数',
      value: activeStudents,
      suffix: <span style={{ fontSize: 14, fontWeight: 400, color: designTokens.colorTextTertiary }}>/ {totalStudents}</span>,
      subText: '在读 / 总数',
      icon: <TeamOutlined style={{ fontSize: 22 }} />,
      iconBg: 'gk-metric-icon--primary',
      delay: '0s',
    },
    {
      title: '今日打卡',
      value: todayCheckins,
      trend: { value: `${checkinRate}%`, up: checkinRate >= 80 },
      subText: '打卡率',
      icon: <CheckCircleOutlined style={{ fontSize: 22 }} />,
      iconBg: 'gk-metric-icon--success',
      delay: '0.06s',
    },
    {
      title: '待跟进',
      value: needsFollowup,
      suffix: <span style={{ fontSize: 14, fontWeight: 400 }}> 人</span>,
      subText: '超过 7 天未联系',
      icon: <AlertOutlined style={{ fontSize: 22 }} />,
      iconBg: 'gk-metric-icon--warning',
      valueColor: needsFollowup > 0 ? designTokens.colorWarning : undefined,
      delay: '0.12s',
    },
    {
      title: '督学日志',
      value: overview?.supervision?.logs_this_month || 0,
      subText: '本月记录数',
      icon: <ProjectOutlined style={{ fontSize: 22 }} />,
      iconBg: 'gk-metric-icon--info',
      delay: '0.18s',
    },
  ];

  return (
    <div>
      {/* ===== 欢迎 Banner ===== */}
      <div className="gk-welcome-banner gk-animate-in">
        <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 6px 0', color: '#FFFFFF' }}>
              {getGreeting()}，{user?.real_name || user?.username || '老师'}
            </h2>
            <p style={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.7)', margin: 0 }}>
              今天是 {new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}，祝工作顺利
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            {[
              { label: '录入打卡', path: '/checkins', icon: <CheckCircleOutlined /> },
              { label: '添加日志', path: '/supervision', icon: <FileTextOutlined /> },
            ].map((a) => (
              <div
                key={a.label}
                onClick={() => navigate(a.path)}
                style={{
                  padding: '8px 18px',
                  borderRadius: 10,
                  background: 'rgba(255, 255, 255, 0.15)',
                  color: '#FFFFFF',
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 500,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  transition: 'background 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.25)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)')}
              >
                {a.icon}
                {a.label}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ===== KPI 卡片 ===== */}
      <div ref={overviewRef} className="dashboard-section">
        <Row gutter={20}>
          {kpiCards.map((card) => (
            <Col span={6} key={card.title}>
              <div
                className="gk-metric-card gk-animate-in"
                style={{ animationDelay: card.delay }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, color: designTokens.colorTextTertiary, marginBottom: 12, fontWeight: 500 }}>
                      {card.title}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                      <span style={{
                        fontSize: 32,
                        fontWeight: 700,
                        color: card.valueColor || designTokens.colorText,
                        lineHeight: 1,
                      }}>
                        {card.value}
                      </span>
                      {card.suffix}
                      {card.trend && (
                        <span className={`gk-trend-tag ${card.trend.up ? 'gk-trend-tag--up' : 'gk-trend-tag--down'}`}>
                          {card.trend.up ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                          {card.trend.value}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 12, color: designTokens.colorTextTertiary, marginTop: 10 }}>
                      {card.subText}
                    </div>
                  </div>
                  <div className={`gk-metric-icon ${card.iconBg}`}>
                    {card.icon}
                  </div>
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </div>

      {/* ===== 趋势 + 状态分布 ===== */}
      <div ref={trendRef} className="dashboard-section">
        <Row gutter={20}>
          {/* 左侧趋势图 - 改为面积图 */}
          <Col span={16}>
            <Card
              title={<span style={{ fontSize: 15, fontWeight: 600 }}>数据趋势</span>}
              extra={
                <Select value={trendDays} onChange={setTrendDays} style={{ width: 100 }} size="small">
                  <Select.Option value={7}>近 7 天</Select.Option>
                  <Select.Option value={14}>近 14 天</Select.Option>
                  <Select.Option value={30}>近 30 天</Select.Option>
                </Select>
              }
              styles={{ body: { padding: '12px 20px 20px' } }}
            >
              {trendsLoading ? (
                <div style={{ textAlign: 'center', padding: 60 }}><Spin /></div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={trendData}>
                    <defs>
                      <linearGradient id="colorCheckins" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={chartColors.primary} stopOpacity={0.15} />
                        <stop offset="100%" stopColor={chartColors.primary} stopOpacity={0.01} />
                      </linearGradient>
                      <linearGradient id="colorStudents" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={chartColors.secondary} stopOpacity={0.15} />
                        <stop offset="100%" stopColor={chartColors.secondary} stopOpacity={0.01} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F3F5" vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(v: string) => v.slice(5)}
                      axisLine={{ stroke: '#E9ECEF' }}
                      tickLine={false}
                      tick={{ fontSize: 12, fill: '#868E96' }}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 12, fill: '#868E96' }}
                    />
                    <Tooltip
                      labelFormatter={(v) => String(v)}
                      contentStyle={{
                        borderRadius: 12,
                        border: '1px solid #E9ECEF',
                        boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
                        padding: '10px 14px',
                      }}
                    />
                    <Area
                      type="monotone" dataKey="checkins" stroke={chartColors.primary}
                      name="打卡" strokeWidth={2.5}
                      fill="url(#colorCheckins)"
                      dot={false}
                      activeDot={{ r: 5, strokeWidth: 2, fill: '#FFFFFF', stroke: chartColors.primary }}
                    />
                    <Area
                      type="monotone" dataKey="students" stroke={chartColors.secondary}
                      name="新增学员" strokeWidth={2.5}
                      fill="url(#colorStudents)"
                      dot={false}
                      activeDot={{ r: 5, strokeWidth: 2, fill: '#FFFFFF', stroke: chartColors.secondary }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </Card>
          </Col>

          {/* 右侧状态分布 */}
          <Col span={8}>
            <Card
              title={<span style={{ fontSize: 15, fontWeight: 600 }}>学员状态</span>}
              styles={{ body: { padding: '16px 20px 20px' } }}
            >
              {statusData.length > 0 ? (
                <div>
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie
                        data={statusData}
                        cx="50%" cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        dataKey="value"
                        paddingAngle={3}
                        strokeWidth={0}
                      >
                        {statusData.map((entry) => (
                          <Cell
                            key={entry.key}
                            fill={chartColors.statusPalette[entry.key as keyof typeof chartColors.statusPalette] || '#ADB5BD'}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  {/* 图例列表 */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8, justifyContent: 'center' }}>
                    {statusData.map((item) => (
                      <div key={item.key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: designTokens.colorTextSecondary }}>
                        <div style={{
                          width: 8, height: 8, borderRadius: '50%',
                          background: chartColors.statusPalette[item.key as keyof typeof chartColors.statusPalette] || '#ADB5BD',
                        }} />
                        {item.name} {item.value as number}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 80, color: designTokens.colorTextTertiary }}>
                  暂无数据
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </div>

      {/* ===== 考试倒计时 + 待办 ===== */}
      <div className="dashboard-section">
        <Row gutter={20}>
          {/* 考试倒计时 */}
          <Col span={12}>
            <Card
              title={
                <span style={{ fontSize: 15, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <CalendarOutlined style={{ color: designTokens.colorPrimary }} />
                  考试倒计时
                </span>
              }
              extra={
                <a onClick={() => navigate('/calendar')} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}>
                  查看日历 <RightOutlined style={{ fontSize: 10 }} />
                </a>
              }
              styles={{ body: { padding: 20 } }}
            >
              {(upcomingExams?.items?.length ?? 0) > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {(upcomingExams!.items as { id: number; title: string; exam_category?: string; days_remaining: number; start_date: string }[])
                    .slice(0, 5)
                    .map((e) => {
                      const urgent = e.days_remaining <= 3;
                      const warning = e.days_remaining <= 7;
                      const near = e.days_remaining <= 30;
                      const color = urgent ? designTokens.colorError
                        : warning ? designTokens.colorWarning
                          : near ? '#F59F00'
                            : designTokens.colorPrimary;

                      return (
                        <div key={e.id} style={{
                          display: 'flex', alignItems: 'center', gap: 16,
                          padding: '14px 16px',
                          borderRadius: 12,
                          border: `1px solid ${urgent ? 'rgba(250, 82, 82, 0.15)' : designTokens.colorBorderSecondary}`,
                          background: urgent ? 'rgba(250, 82, 82, 0.03)' : designTokens.colorBgLayout,
                          transition: 'all 0.2s',
                        }}>
                          <div style={{ minWidth: 52, textAlign: 'center' }}>
                            <div style={{ fontSize: 26, fontWeight: 700, color, lineHeight: 1 }}>
                              {e.days_remaining}
                            </div>
                            <div style={{ fontSize: 11, color: designTokens.colorTextTertiary, marginTop: 2 }}>天</div>
                          </div>
                          <div style={{ flex: 1, overflow: 'hidden' }}>
                            <div style={{
                              fontSize: 14, fontWeight: 500,
                              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                            }}>
                              {e.title}
                            </div>
                            <div style={{ fontSize: 12, color: designTokens.colorTextTertiary, marginTop: 3 }}>
                              {e.start_date}
                            </div>
                          </div>
                          {urgent && <Tag color="red" style={{ borderRadius: 6 }}>紧急</Tag>}
                          {!urgent && warning && <Tag color="orange" style={{ borderRadius: 6 }}>临近</Tag>}
                        </div>
                      );
                    })}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 48, color: designTokens.colorTextTertiary }}>
                  暂无近期考试
                </div>
              )}
            </Card>
          </Col>

          {/* 待办 + 快捷操作 */}
          <Col span={12}>
            <Card
              title={
                <span style={{ fontSize: 15, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <BellOutlined style={{ color: designTokens.colorWarning }} />
                  待跟进学员
                  {needsFollowup > 0 && <Badge count={needsFollowup} style={{ marginLeft: 4 }} />}
                </span>
              }
              styles={{ body: { padding: 20 } }}
            >
              {/* 待跟进列表 */}
              {(reminders?.students?.length ?? 0) > 0 ? (
                <List
                  size="small"
                  dataSource={(reminders!.students || []).slice(0, 4)}
                  renderItem={(s: { id: number; name: string; phone?: string; last_contact_date?: string }) => (
                    <List.Item style={{ padding: '12px 0', borderBottom: `1px solid ${designTokens.colorBorderSecondary}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                        <div>
                          <span style={{ fontWeight: 600, marginRight: 8 }}>{s.name}</span>
                          <span style={{ fontSize: 12, color: designTokens.colorTextTertiary }}>{s.phone || ''}</span>
                        </div>
                        <Tag
                          color={s.last_contact_date ? 'orange' : 'red'}
                          style={{ fontSize: 11, borderRadius: 6 }}
                        >
                          {s.last_contact_date ? `${s.last_contact_date}` : '从未联系'}
                        </Tag>
                      </div>
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: 24, color: designTokens.colorTextTertiary, fontSize: 13 }}>
                  暂无待跟进学员
                </div>
              )}

              {/* 快捷操作 */}
              <div style={{ marginTop: 20, paddingTop: 20, borderTop: `1px solid ${designTokens.colorBorderSecondary}` }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: designTokens.colorTextSecondary }}>
                  快捷操作
                </div>
                <Row gutter={[12, 12]}>
                  {[
                    { icon: <CheckCircleOutlined />, label: '录入打卡', path: '/checkins' },
                    { icon: <FileTextOutlined />, label: '添加日志', path: '/supervision' },
                    { icon: <ProjectOutlined />, label: '新建计划', path: '/study-plans' },
                    { icon: <UploadOutlined />, label: '导入成绩', path: '/exam-scores' },
                  ].map((item) => (
                    <Col span={12} key={item.label}>
                      <div className="gk-quick-action" onClick={() => navigate(item.path)}>
                        {item.icon}
                        <span>{item.label}</span>
                      </div>
                    </Col>
                  ))}
                </Row>
              </div>
            </Card>
          </Col>
        </Row>
      </div>

      {/* ===== 管理员：财务 + 考试统计 ===== */}
      {isAdmin && (
        <div className="dashboard-section">
          <Row gutter={20}>
            <Col span={12}>
              <Card
                title={
                  <span style={{ fontSize: 15, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <DollarOutlined style={{ color: designTokens.colorSuccess }} />
                    本月财务摘要
                  </span>
                }
                styles={{ body: { padding: 24 } }}
              >
                {(financeTrend as { month: string; income: number; expense: number; profit: number }[] | undefined)?.length ? (
                  (() => {
                    const ft = financeTrend as { month: string; income: number; expense: number; profit: number }[];
                    const latest = ft[ft.length - 1];
                    const prev = ft.length > 1 ? ft[ft.length - 2] : null;
                    const incomeChange = prev ? ((latest.income - prev.income) / (prev.income || 1)) * 100 : 0;

                    return (
                      <Row gutter={24}>
                        <Col span={8}>
                          <div style={{ fontSize: 13, color: designTokens.colorTextTertiary, marginBottom: 8 }}>收入</div>
                          <div style={{ fontSize: 24, fontWeight: 700, color: designTokens.colorSuccess }}>
                            ¥{latest.income.toLocaleString()}
                          </div>
                          {prev && (
                            <div style={{ fontSize: 12, marginTop: 6 }}>
                              <span className={`gk-trend-tag ${incomeChange >= 0 ? 'gk-trend-tag--up' : 'gk-trend-tag--down'}`}>
                                {incomeChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                                {Math.abs(incomeChange).toFixed(1)}%
                              </span>
                              <span style={{ color: designTokens.colorTextTertiary, marginLeft: 6, fontSize: 11 }}>环比</span>
                            </div>
                          )}
                        </Col>
                        <Col span={8}>
                          <div style={{ fontSize: 13, color: designTokens.colorTextTertiary, marginBottom: 8 }}>支出</div>
                          <div style={{ fontSize: 24, fontWeight: 700, color: designTokens.colorError }}>
                            ¥{latest.expense.toLocaleString()}
                          </div>
                        </Col>
                        <Col span={8}>
                          <div style={{ fontSize: 13, color: designTokens.colorTextTertiary, marginBottom: 8 }}>净利润</div>
                          <div style={{ fontSize: 24, fontWeight: 700, color: latest.profit >= 0 ? designTokens.colorPrimary : designTokens.colorError }}>
                            ¥{latest.profit.toLocaleString()}
                          </div>
                        </Col>
                      </Row>
                    );
                  })()
                ) : (
                  <div style={{ textAlign: 'center', padding: 48, color: designTokens.colorTextTertiary }}>暂无财务数据</div>
                )}
              </Card>
            </Col>

            <Col span={12}>
              <Card
                title={
                  <span style={{ fontSize: 15, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <TrophyOutlined style={{ color: designTokens.colorPrimary }} />
                    考试统计摘要
                  </span>
                }
                styles={{ body: { padding: 24 } }}
              >
                <Row gutter={24}>
                  <Col span={8}>
                    <div style={{ fontSize: 13, color: designTokens.colorTextTertiary, marginBottom: 8 }}>模考总次数</div>
                    <div style={{ fontSize: 24, fontWeight: 700, color: designTokens.colorText }}>
                      {classAnalysis?.summary?.total_exams || 0}
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ fontSize: 13, color: designTokens.colorTextTertiary, marginBottom: 8 }}>平均正确率</div>
                    <div style={{ fontSize: 24, fontWeight: 700, color: designTokens.colorPrimary }}>
                      {classAnalysis?.summary?.avg_accuracy || 0}%
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ fontSize: 13, color: designTokens.colorTextTertiary, marginBottom: 8 }}>最薄弱模块</div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: designTokens.colorError, marginTop: 4 }}>
                      {classAnalysis?.summary?.weakest_area || '暂无'}
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </div>
      )}

      <Tour
        open={tourOpen}
        onClose={() => {
          setTourOpen(false);
          localStorage.setItem('dashboard_toured', '1');
        }}
        steps={tourSteps}
      />
    </div>
  );
}

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 6) return '夜深了';
  if (h < 12) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
}
