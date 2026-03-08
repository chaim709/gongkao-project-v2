import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * 全局键盘快捷键
 * Alt+D: 看板  Alt+S: 学员  Alt+N: 通知
 */
export function useGlobalShortcuts() {
  const navigate = useNavigate();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!e.altKey || e.ctrlKey || e.metaKey) return;
      // 忽略输入框内的快捷键
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      switch (e.key.toLowerCase()) {
        case 'd':
          e.preventDefault();
          navigate('/dashboard');
          break;
        case 's':
          e.preventDefault();
          navigate('/students');
          break;
        case 'n':
          e.preventDefault();
          navigate('/notifications');
          break;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navigate]);
}
