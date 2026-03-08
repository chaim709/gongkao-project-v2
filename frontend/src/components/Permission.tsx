import { useAuthStore } from '../stores/authStore';

interface PermissionProps {
  roles: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * 根据用户角色控制组件显示
 * <Permission roles={['admin']}>仅管理员可见</Permission>
 */
export default function Permission({ roles, children, fallback = null }: PermissionProps) {
  const user = useAuthStore((state) => state.user);
  if (!user || !roles.includes(user.role)) {
    return <>{fallback}</>;
  }
  return <>{children}</>;
}

/**
 * Hook: 检查当前用户是否有指定角色
 */
export function useHasRole(...roles: string[]): boolean {
  const user = useAuthStore((state) => state.user);
  return !!user && roles.includes(user.role);
}
