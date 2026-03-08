import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, message } from 'antd';
import {
  UserOutlined,
  LockOutlined,
  BarChartOutlined,
  TeamOutlined,
  AimOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import { designTokens } from '../theme';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('登录成功');
      navigate('/dashboard');
    } catch (error: any) {
      message.error(error?.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: <BarChartOutlined style={{ fontSize: 20 }} />, title: '数据看板', desc: '实时掌控教学进度与学员动态' },
    { icon: <AimOutlined style={{ fontSize: 20 }} />, title: '智能选岗', desc: '精准匹配最优公考岗位' },
    { icon: <TeamOutlined style={{ fontSize: 20 }} />, title: '督学管理', desc: '完整记录学员学习轨迹' },
    { icon: <CheckCircleOutlined style={{ fontSize: 20 }} />, title: '模考分析', desc: '深度分析薄弱环节提升成绩' },
  ];

  return (
    <div className="login-page">
      {/* 左侧品牌区 */}
      <div className="login-brand">
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 460 }}>
          {/* Logo */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            marginBottom: 56,
          }}>
            <div style={{
              width: 44,
              height: 44,
              background: 'rgba(255, 255, 255, 0.15)',
              backdropFilter: 'blur(10px)',
              borderRadius: 14,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 20,
              fontWeight: 700,
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}>
              公
            </div>
            <span style={{
              fontSize: 20,
              fontWeight: 600,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}>
              公考管理系统
            </span>
          </div>

          {/* 标题 */}
          <h1 style={{
            fontSize: 40,
            fontWeight: 700,
            lineHeight: 1.25,
            margin: '0 0 16px 0',
            color: '#FFFFFF',
          }}>
            让培训管理
            <br />
            更高效、更智能
          </h1>

          <p style={{
            fontSize: 16,
            lineHeight: 1.7,
            color: 'rgba(255, 255, 255, 0.7)',
            margin: '0 0 56px 0',
          }}>
            全方位学员管理 · 智能督学跟进 · 数据驱动决策
          </p>

          {/* 特性网格 */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
          }}>
            {features.map((item) => (
              <div
                key={item.title}
                style={{
                  display: 'flex',
                  gap: 14,
                  padding: '18px 16px',
                  borderRadius: 14,
                  background: 'rgba(255, 255, 255, 0.08)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  transition: 'background 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)')}
              >
                <div style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: 'rgba(255, 255, 255, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  flexShrink: 0,
                }}>
                  {item.icon}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#FFFFFF', marginBottom: 4 }}>
                    {item.title}
                  </div>
                  <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.6)', lineHeight: 1.4 }}>
                    {item.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 底部版权 */}
        <div style={{
          position: 'absolute',
          bottom: 32,
          left: 60,
          fontSize: 12,
          color: 'rgba(255, 255, 255, 0.3)',
        }}>
          © 2026 公考管理系统 · 培训机构专用
        </div>
      </div>

      {/* 右侧登录表单 */}
      <div className="login-form-side">
        <div className="login-form-card">
          <div style={{ marginBottom: 44 }}>
            <h2 style={{
              fontSize: 26,
              fontWeight: 700,
              color: designTokens.colorText,
              margin: '0 0 8px 0',
            }}>
              欢迎回来
            </h2>
            <p style={{
              fontSize: 15,
              color: designTokens.colorTextTertiary,
              margin: 0,
            }}>
              请输入账号密码登录系统
            </p>
          </div>

          <Form onFinish={onFinish} autoComplete="off" layout="vertical" size="large">
            <Form.Item
              name="username"
              label={<span style={{ fontWeight: 500, color: designTokens.colorTextSecondary }}>用户名</span>}
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined style={{ color: designTokens.colorTextQuaternary }} />}
                placeholder="请输入用户名"
                style={{ height: 46, borderRadius: 12 }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span style={{ fontWeight: 500, color: designTokens.colorTextSecondary }}>密码</span>}
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: designTokens.colorTextQuaternary }} />}
                placeholder="请输入密码"
                style={{ height: 46, borderRadius: 12 }}
              />
            </Form.Item>

            <Form.Item style={{ marginTop: 36, marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  height: 48,
                  borderRadius: 12,
                  fontSize: 16,
                  fontWeight: 600,
                  boxShadow: '0 4px 16px rgba(59, 91, 219, 0.3)',
                }}
              >
                登 录
              </Button>
            </Form.Item>
          </Form>

          <div style={{
            marginTop: 36,
            textAlign: 'center',
            fontSize: 13,
            color: designTokens.colorTextQuaternary,
          }}>
            遇到问题？请联系管理员
          </div>
        </div>
      </div>
    </div>
  );
}
