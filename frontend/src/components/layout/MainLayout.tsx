import { useState, useMemo } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Badge, Input, Tooltip } from 'antd';
import {
  TeamOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LogoutOutlined,
  UserOutlined,
  FileTextOutlined,
  BookOutlined,
  FormOutlined,
  CheckCircleOutlined,
  DashboardOutlined,
  AimOutlined,
  AuditOutlined,
  ProjectOutlined,
  VideoCameraOutlined,
  CalendarOutlined,
  FileExclamationOutlined,
  ReadOutlined,
  ContainerOutlined,
  GiftOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  RobotOutlined,
  BarChartOutlined,
  SettingOutlined,
  DollarOutlined,
  BellOutlined,
  RestOutlined,
  SearchOutlined,
  SunOutlined,
  MoonOutlined,
  NotificationOutlined,
  RadarChartOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useThemeStore } from '../../stores/themeStore';
import { useQuery } from '@tanstack/react-query';
import { notificationApi } from '../../api/notifications';
import { useGlobalShortcuts } from '../../hooks/useGlobalShortcuts';
import { getDesignTokens } from '../../theme';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = Layout;

type MenuItem = Required<MenuProps>['items'][number] & { roles?: string[] };

const allMenuItems: MenuItem[] = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '数据看板' },
  { key: '/calendar', icon: <CalendarOutlined />, label: '考试日历' },
  {
    key: 'student-group',
    icon: <TeamOutlined />,
    label: '学员管理',
    children: [
      { key: '/students', icon: <TeamOutlined />, label: '学员列表' },
      { key: '/supervision', icon: <FileTextOutlined />, label: '督学日志' },
      { key: '/study-plans', icon: <ProjectOutlined />, label: '学习计划' },
    ],
  },
  {
    key: 'course-group',
    icon: <BookOutlined />,
    label: '教学管理',
    children: [
      { key: '/courses', icon: <BookOutlined />, label: '课程管理' },
      { key: '/homework', icon: <FormOutlined />, label: '作业管理' },
      { key: '/class-batches', icon: <CalendarOutlined />, label: '班次管理' },
      { key: '/course-recordings', icon: <VideoCameraOutlined />, label: '课程录播' },
    ],
  },
  {
    key: 'exam-group',
    icon: <ReadOutlined />,
    label: '题库模考',
    children: [
      { key: '/exam-papers', icon: <ContainerOutlined />, label: '试卷管理' },
      { key: '/questions', icon: <ReadOutlined />, label: '题库管理' },
      { key: '/exam-scores', icon: <TrophyOutlined />, label: '模考成绩' },
      { key: '/mistakes', icon: <FileExclamationOutlined />, label: '错题本' },
      { key: '/workbooks', icon: <ContainerOutlined />, label: '作业本' },
      { key: '/ai-import', icon: <RobotOutlined />, label: 'AI导入' },
    ],
  },
  {
    key: 'recruitment-group',
    icon: <RadarChartOutlined />,
    label: '招考信息',
    children: [
      { key: '/recruitment-info', icon: <NotificationOutlined />, label: '招考公告' },
      { key: '/crawler-management', icon: <RadarChartOutlined />, label: '采集管理' },
    ],
  },
  {
    key: 'analysis-group',
    icon: <BarChartOutlined />,
    label: '数据分析',
    children: [
      { key: '/class-analysis', icon: <TeamOutlined />, label: '班级分析' },
      { key: '/positions', icon: <AimOutlined />, label: '省考选岗' },
      { key: '/guokao-positions', icon: <AimOutlined />, label: '国考选岗' },
      { key: '/shiye-positions', icon: <AimOutlined />, label: '事业编选岗' },
    ],
  },
  {
    key: 'daily-group',
    icon: <CheckCircleOutlined />,
    label: '日常管理',
    children: [
      { key: '/checkins', icon: <CheckCircleOutlined />, label: '打卡管理' },
      { key: '/attendances', icon: <ClockCircleOutlined />, label: '考勤管理' },
      { key: '/packages', icon: <GiftOutlined />, label: '套餐管理' },
      { key: '/finance', icon: <DollarOutlined />, label: '财务管理' },
    ],
  },
  {
    key: 'system-group',
    icon: <SettingOutlined />,
    label: '系统管理',
    roles: ['admin'],
    children: [
      { key: '/audit-logs', icon: <AuditOutlined />, label: '审计日志' },
      { key: '/users', icon: <TeamOutlined />, label: '用户管理' },
      { key: '/recycle-bin', icon: <RestOutlined />, label: '回收站' },
      { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
    ],
  },
];

function getOpenKeys(pathname: string): string[] {
  for (const item of allMenuItems) {
    if ('children' in item && item.children) {
      for (const child of item.children as { key: string }[]) {
        if (pathname.startsWith(child.key as string)) {
          return [item.key as string];
        }
      }
    }
  }
  return [];
}

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { mode, toggle } = useThemeStore();
  const tokens = getDesignTokens(mode);
  useGlobalShortcuts();

  const [collapsed, setCollapsed] = useState(false);
  const [openKeys, setOpenKeys] = useState<string[]>(() => getOpenKeys(location.pathname));

  const { data: unreadData } = useQuery({
    queryKey: ['unread-count'],
    queryFn: notificationApi.unreadCount,
    refetchInterval: 60000,
  });

  const menuItems = useMemo(() => {
    return allMenuItems.filter((item) => {
      if (!item.roles) return true;
      return user?.role && item.roles.includes(user.role);
    });
  }, [user?.role]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const dropdownItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
      danger: true,
    },
  ];

  const selectedKeys = useMemo(() => {
    const path = location.pathname;
    for (const item of allMenuItems) {
      if ('children' in item && item.children) {
        for (const child of item.children as { key: string }[]) {
          if (path === child.key || path.startsWith(child.key + '/')) {
            return [child.key];
          }
        }
      }
      if (path === item.key) return [item.key as string];
    }
    return [path];
  }, [location.pathname]);

  const unreadCount = unreadData?.count || 0;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={tokens.siderWidth}
        collapsedWidth={tokens.siderCollapsedWidth}
        style={{
          background: tokens.siderBg,
          borderRight: `1px solid ${tokens.siderBorderColor}`,
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
        }}
      >
        {/* 品牌 Logo */}
        <div className="gk-sider-logo">
          <div className="logo-icon">公</div>
          {!collapsed && <h1>公考管理</h1>}
        </div>

        {/* 菜单 - 浅色 */}
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          openKeys={collapsed ? [] : openKeys}
          onOpenChange={(keys) => setOpenKeys(keys)}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{
            background: 'transparent',
            border: 'none',
            padding: '4px 0',
          }}
        />
      </Sider>

      {/* 右侧内容 */}
      <Layout style={{
        marginLeft: collapsed ? tokens.siderCollapsedWidth : tokens.siderWidth,
        transition: 'margin-left 0.2s ease',
      }}>
        {/* 头部 */}
        <Header className="gk-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: 16,
                width: 38,
                height: 38,
                borderRadius: 10,
                color: tokens.colorTextSecondary,
              }}
            />
            <Input
              placeholder="搜索..."
              prefix={<SearchOutlined style={{ color: tokens.colorTextQuaternary }} />}
              style={{
                width: 240,
                borderRadius: 10,
                background: tokens.colorBgLayout,
                border: 'none',
              }}
              variant="filled"
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* 主题切换 */}
            <Tooltip title={mode === 'light' ? '切换暗色模式' : '切换亮色模式'}>
              <Button
                type="text"
                icon={mode === 'light' ? <MoonOutlined style={{ fontSize: 17 }} /> : <SunOutlined style={{ fontSize: 17 }} />}
                onClick={toggle}
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  color: tokens.colorTextSecondary,
                }}
              />
            </Tooltip>

            {/* 通知 */}
            <Badge count={unreadCount} size="small" offset={[-4, 4]}>
              <Button
                type="text"
                icon={<BellOutlined style={{ fontSize: 18 }} />}
                onClick={() => navigate('/notifications')}
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  color: tokens.colorTextSecondary,
                }}
              />
            </Badge>

            {/* 分割线 */}
            <div style={{
              width: 1,
              height: 24,
              background: tokens.colorBorderSecondary,
              margin: '0 4px',
            }} />

            {/* 用户信息 */}
            <Dropdown menu={{ items: dropdownItems }} placement="bottomRight" trigger={['click']}>
              <div style={{
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 12px 6px 6px',
                borderRadius: 12,
                transition: 'background 0.2s',
              }}
                onMouseEnter={(e) => (e.currentTarget.style.background = tokens.colorBgHover)}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <Avatar
                  size={34}
                  icon={<UserOutlined />}
                  style={{
                    background: `linear-gradient(135deg, ${tokens.colorPrimary}, #5C7CFA)`,
                  }}
                />
                <div>
                  <div style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: tokens.colorText,
                    lineHeight: 1.3,
                  }}>
                    {user?.real_name || user?.username || '用户'}
                  </div>
                  <div style={{
                    fontSize: 11,
                    color: tokens.colorTextTertiary,
                    lineHeight: 1.2,
                  }}>
                    {user?.role === 'admin' ? '管理员' : '督学老师'}
                  </div>
                </div>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区 - 不再包裹在白色卡片里，让每个页面自己控制 */}
        <Content style={{
          padding: 24,
          minHeight: 280,
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
