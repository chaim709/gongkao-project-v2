import { Card, Tabs, Form, Input, Button, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { useAuthStore } from '../../stores/authStore';
import client from '../../api/client';

const authApi = {
  changePassword: (data: { old_password: string; new_password: string }) =>
    client.put('/auth/change-password', data),
  updateProfile: (data: { real_name?: string; phone?: string; email?: string }) =>
    client.put('/auth/profile', data),
};

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [passwordForm] = Form.useForm();
  const [profileForm] = Form.useForm();

  const passwordMutation = useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => {
      message.success('密码已修改');
      passwordForm.resetFields();
    },
    onError: () => message.error('原密码错误'),
  });

  const profileMutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (data) => {
      message.success('个人信息已更新');
      setUser(data);
    },
  });

  return (
    <Card title="个人中心">
      <Tabs
        items={[
          {
            key: 'info',
            label: <><UserOutlined /> 个人信息</>,
            children: (
              <Form
                form={profileForm}
                layout="vertical"
                initialValues={{ real_name: user?.real_name, phone: user?.phone, email: user?.email }}
                onFinish={(values) => profileMutation.mutate(values)}
                style={{ maxWidth: 500 }}
              >
                <Form.Item label="用户名">
                  <Input value={user?.username} disabled />
                </Form.Item>
                <Form.Item name="real_name" label="真实姓名">
                  <Input />
                </Form.Item>
                <Form.Item name="phone" label="手机号">
                  <Input />
                </Form.Item>
                <Form.Item name="email" label="邮箱">
                  <Input />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={profileMutation.isPending}>保存</Button>
                </Form.Item>
              </Form>
            ),
          },
          {
            key: 'password',
            label: <><LockOutlined /> 修改密码</>,
            children: (
              <Form
                form={passwordForm}
                layout="vertical"
                onFinish={(values) => passwordMutation.mutate(values)}
                style={{ maxWidth: 500 }}
              >
                <Form.Item name="old_password" label="原密码" rules={[{ required: true }]}>
                  <Input.Password />
                </Form.Item>
                <Form.Item name="new_password" label="新密码" rules={[{ required: true, min: 6 }]}>
                  <Input.Password />
                </Form.Item>
                <Form.Item
                  name="confirm"
                  label="确认密码"
                  dependencies={['new_password']}
                  rules={[
                    { required: true },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('new_password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error('两次密码不一致'));
                      },
                    }),
                  ]}
                >
                  <Input.Password />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={passwordMutation.isPending}>修改密码</Button>
                </Form.Item>
              </Form>
            ),
          },
        ]}
      />
    </Card>
  );
}
