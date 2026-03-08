import type { ThemeConfig } from 'antd';
import { theme as antdTheme } from 'antd';

/**
 * 公考管理系统 - 现代 SaaS 风格主题配置
 *
 * 设计参考：FinPay + DealDeck + NeoPay 混合风格
 * 主色：靖蓝 #3B5BDB（专业、信任感）
 * 支持亮色/暗色主题切换
 * 卡片：大圆角 16px + 轻阴影
 */

// ========== 设计令牌 ==========
export const designTokens = {
  // 主色系
  colorPrimary: '#3B5BDB',
  colorPrimaryHover: '#4C6EF5',
  colorPrimaryActive: '#364FC7',
  colorPrimaryBg: '#EDF2FF',    // 主色浅底
  colorPrimaryBgHover: '#DBE4FF',

  // 功能色
  colorSuccess: '#12B886',
  colorWarning: '#F59F00',
  colorError: '#FA5252',
  colorInfo: '#4C6EF5',

  // 中性色
  colorBgLayout: '#F8FAFC',
  colorBgContainer: '#FFFFFF',
  colorBgElevated: '#FFFFFF',
  colorBgHover: '#F1F3F5',
  colorBorder: '#E9ECEF',
  colorBorderSecondary: '#F1F3F5',

  // 文字色
  colorText: '#212529',
  colorTextSecondary: '#495057',
  colorTextTertiary: '#868E96',
  colorTextQuaternary: '#ADB5BD',

  // 侧边栏（浅色主题）
  siderBg: '#FFFFFF',
  siderBorderColor: '#F1F3F5',
  siderMenuItemActive: '#EDF2FF',
  siderMenuItemHover: '#F8F9FA',
  siderMenuTextColor: '#495057',
  siderMenuTextActive: '#3B5BDB',
  siderMenuGroupTitle: '#ADB5BD',

  // 学员状态色
  statusColors: {
    lead:      { bg: '#F1F3F5', text: '#868E96', border: '#DEE2E6' },
    trial:     { bg: '#F3F0FF', text: '#7950F2', border: '#D0BFFF' },
    active:    { bg: '#E6FCF5', text: '#12B886', border: '#96F2D7' },
    inactive:  { bg: '#FFF9DB', text: '#F59F00', border: '#FFE066' },
    graduated: { bg: '#EDF2FF', text: '#3B5BDB', border: '#BAC8FF' },
    dropped:   { bg: '#FFF5F5', text: '#FA5252', border: '#FFC9C9' },
  },

  // 圆角
  borderRadius: 10,
  borderRadiusLG: 16,
  borderRadiusSM: 8,
  borderRadiusXS: 6,

  // 阴影
  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
  boxShadowSecondary: '0 4px 16px rgba(0, 0, 0, 0.06)',
  boxShadowTertiary: '0 8px 32px rgba(0, 0, 0, 0.08)',
  boxShadowCard: '0 1px 4px rgba(0, 0, 0, 0.04)',
  boxShadowCardHover: '0 8px 24px rgba(59, 91, 219, 0.08)',

  // 间距
  padding: 16,
  paddingLG: 24,
  paddingSM: 12,
  paddingXS: 8,

  // 内容区
  contentMaxWidth: 1440,
  headerHeight: 60,
  siderWidth: 240,
  siderCollapsedWidth: 72,
} as const;

// ========== Ant Design 主题 ==========
export const antTheme: ThemeConfig = {
  token: {
    colorPrimary: designTokens.colorPrimary,
    colorSuccess: designTokens.colorSuccess,
    colorWarning: designTokens.colorWarning,
    colorError: designTokens.colorError,
    colorInfo: designTokens.colorInfo,

    colorBgLayout: designTokens.colorBgLayout,
    colorBgContainer: designTokens.colorBgContainer,
    colorBgElevated: designTokens.colorBgElevated,

    colorText: designTokens.colorText,
    colorTextSecondary: designTokens.colorTextSecondary,
    colorTextTertiary: designTokens.colorTextTertiary,
    colorTextQuaternary: designTokens.colorTextQuaternary,

    colorBorder: designTokens.colorBorder,
    colorBorderSecondary: designTokens.colorBorderSecondary,

    borderRadius: designTokens.borderRadius,
    borderRadiusLG: designTokens.borderRadiusLG,
    borderRadiusSM: designTokens.borderRadiusSM,

    boxShadow: designTokens.boxShadow,
    boxShadowSecondary: designTokens.boxShadowSecondary,
    boxShadowTertiary: designTokens.boxShadowTertiary,

    fontFamily:
      '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
    fontSize: 14,

    controlHeight: 38,
    padding: designTokens.padding,
    paddingLG: designTokens.paddingLG,
    paddingSM: designTokens.paddingSM,
    paddingXS: designTokens.paddingXS,
  },

  components: {
    // 按钮
    Button: {
      borderRadius: 10,
      controlHeight: 38,
      paddingInline: 20,
      primaryShadow: '0 2px 8px rgba(59, 91, 219, 0.25)',
    },

    // 卡片
    Card: {
      borderRadiusLG: 16,
      paddingLG: 24,
      boxShadow: designTokens.boxShadowCard,
    } as Record<string, unknown>,

    // 表格
    Table: {
      headerBg: '#FAFBFD',
      headerColor: designTokens.colorTextSecondary,
      rowHoverBg: '#F8F9FF',
      borderColor: designTokens.colorBorderSecondary,
      headerBorderRadius: 12,
      cellPaddingBlock: 14,
      cellPaddingInline: 16,
    },

    // 输入框
    Input: {
      controlHeight: 38,
      borderRadius: 10,
      activeBorderColor: designTokens.colorPrimary,
      hoverBorderColor: designTokens.colorPrimaryHover,
    },

    // 选择器
    Select: {
      controlHeight: 38,
      borderRadius: 10,
    },

    // 标签
    Tag: {
      borderRadiusSM: 6,
    },

    // 菜单（浅色主题）
    Menu: {
      itemBg: 'transparent',
      subMenuItemBg: 'transparent',
      itemSelectedBg: designTokens.siderMenuItemActive,
      itemHoverBg: designTokens.siderMenuItemHover,
      itemColor: designTokens.siderMenuTextColor,
      itemSelectedColor: designTokens.siderMenuTextActive,
      itemBorderRadius: 10,
      itemMarginInline: 12,
      itemMarginBlock: 2,
      itemHeight: 42,
      iconSize: 18,
      groupTitleColor: designTokens.siderMenuGroupTitle,
      groupTitleFontSize: 11,
    },

    // 布局
    Layout: {
      siderBg: designTokens.siderBg,
      headerBg: designTokens.colorBgContainer,
      bodyBg: designTokens.colorBgLayout,
    },

    // 统计数值
    Statistic: {
      contentFontSize: 30,
      titleFontSize: 13,
    },

    // 徽章
    Badge: {
      dotSize: 8,
    },

    // 分页
    Pagination: {
      borderRadius: 8,
      itemActiveBg: designTokens.colorPrimary,
    },

    // 模态框
    Modal: {
      borderRadiusLG: 16,
    },

    // 消息
    Message: {
      borderRadiusLG: 10,
    },

    // 抽屉
    Drawer: {
      borderRadiusLG: 16,
    },
  },
};

// ========== 图表配色 ==========
export const chartColors = {
  primary: '#3B5BDB',
  secondary: '#12B886',
  tertiary: '#F59F00',
  quaternary: '#7950F2',
  quinary: '#4C6EF5',
  senary: '#FA5252',

  // 有序调色板（更柔和的配色）
  palette: ['#3B5BDB', '#12B886', '#F59F00', '#7950F2', '#4C6EF5', '#FA5252', '#20C997', '#845EF7'],

  // 学员状态
  statusPalette: {
    lead: '#ADB5BD',
    trial: '#7950F2',
    active: '#12B886',
    inactive: '#F59F00',
    graduated: '#3B5BDB',
    dropped: '#FA5252',
  },

  // 渐变色（用于面积图）
  gradients: {
    primary: { start: 'rgba(59, 91, 219, 0.2)', end: 'rgba(59, 91, 219, 0.01)' },
    success: { start: 'rgba(18, 184, 134, 0.2)', end: 'rgba(18, 184, 134, 0.01)' },
  },
};

// ========== 暗色设计令牌 ==========
export const darkDesignTokens = {
  ...designTokens,

  // 中性色（暗色）
  colorBgLayout: '#0F1117',
  colorBgContainer: '#1A1D27',
  colorBgElevated: '#222633',
  colorBgHover: '#2A2E3B',
  colorBorder: '#2E3345',
  colorBorderSecondary: '#252938',

  // 文字色（暗色）
  colorText: '#E9ECEF',
  colorTextSecondary: '#ADB5BD',
  colorTextTertiary: '#6C757D',
  colorTextQuaternary: '#495057',

  // 侧边栏（暗色）
  siderBg: '#141720',
  siderBorderColor: '#252938',
  siderMenuItemActive: 'rgba(59, 91, 219, 0.2)',
  siderMenuItemHover: 'rgba(255, 255, 255, 0.05)',
  siderMenuTextColor: '#ADB5BD',
  siderMenuTextActive: '#748FFC',
  siderMenuGroupTitle: '#495057',

  // 阴影（暗色下更深）
  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2), 0 1px 2px rgba(0, 0, 0, 0.12)',
  boxShadowSecondary: '0 4px 16px rgba(0, 0, 0, 0.25)',
  boxShadowTertiary: '0 8px 32px rgba(0, 0, 0, 0.3)',
  boxShadowCard: '0 1px 4px rgba(0, 0, 0, 0.15)',
  boxShadowCardHover: '0 8px 24px rgba(0, 0, 0, 0.2)',
} as const;

// ========== Ant Design 暗色主题 ==========
export const antDarkTheme: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: '#4C6EF5',
    colorSuccess: '#20C997',
    colorWarning: '#FCC419',
    colorError: '#FF6B6B',
    colorInfo: '#748FFC',

    colorBgLayout: darkDesignTokens.colorBgLayout,
    colorBgContainer: darkDesignTokens.colorBgContainer,
    colorBgElevated: darkDesignTokens.colorBgElevated,

    colorText: darkDesignTokens.colorText,
    colorTextSecondary: darkDesignTokens.colorTextSecondary,
    colorTextTertiary: darkDesignTokens.colorTextTertiary,
    colorTextQuaternary: darkDesignTokens.colorTextQuaternary,

    colorBorder: darkDesignTokens.colorBorder,
    colorBorderSecondary: darkDesignTokens.colorBorderSecondary,

    borderRadius: designTokens.borderRadius,
    borderRadiusLG: designTokens.borderRadiusLG,
    borderRadiusSM: designTokens.borderRadiusSM,

    boxShadow: darkDesignTokens.boxShadow,
    boxShadowSecondary: darkDesignTokens.boxShadowSecondary,
    boxShadowTertiary: darkDesignTokens.boxShadowTertiary,

    fontFamily: designTokens.siderBg ? // reuse same font
      '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif'
      : undefined,
    fontSize: 14,

    controlHeight: 38,
    padding: designTokens.padding,
    paddingLG: designTokens.paddingLG,
    paddingSM: designTokens.paddingSM,
    paddingXS: designTokens.paddingXS,
  },

  components: {
    Button: {
      borderRadius: 10,
      controlHeight: 38,
      paddingInline: 20,
      primaryShadow: '0 2px 8px rgba(76, 110, 245, 0.35)',
    },

    Card: {
      borderRadiusLG: 16,
      paddingLG: 24,
      boxShadow: darkDesignTokens.boxShadowCard,
    } as Record<string, unknown>,

    Table: {
      headerBg: '#1E2230',
      headerColor: darkDesignTokens.colorTextSecondary,
      rowHoverBg: '#252938',
      borderColor: darkDesignTokens.colorBorderSecondary,
      headerBorderRadius: 12,
      cellPaddingBlock: 14,
      cellPaddingInline: 16,
    },

    Input: {
      controlHeight: 38,
      borderRadius: 10,
      activeBorderColor: '#4C6EF5',
      hoverBorderColor: '#5C7CFA',
    },

    Select: {
      controlHeight: 38,
      borderRadius: 10,
    },

    Tag: {
      borderRadiusSM: 6,
    },

    Menu: {
      itemBg: 'transparent',
      subMenuItemBg: 'transparent',
      itemSelectedBg: darkDesignTokens.siderMenuItemActive,
      itemHoverBg: darkDesignTokens.siderMenuItemHover,
      itemColor: darkDesignTokens.siderMenuTextColor,
      itemSelectedColor: darkDesignTokens.siderMenuTextActive,
      itemBorderRadius: 10,
      itemMarginInline: 12,
      itemMarginBlock: 2,
      itemHeight: 42,
      iconSize: 18,
      groupTitleColor: darkDesignTokens.siderMenuGroupTitle,
      groupTitleFontSize: 11,
    },

    Layout: {
      siderBg: darkDesignTokens.siderBg,
      headerBg: darkDesignTokens.colorBgContainer,
      bodyBg: darkDesignTokens.colorBgLayout,
    },

    Statistic: {
      contentFontSize: 30,
      titleFontSize: 13,
    },

    Badge: {
      dotSize: 8,
    },

    Pagination: {
      borderRadius: 8,
      itemActiveBg: '#4C6EF5',
    },

    Modal: {
      borderRadiusLG: 16,
    },

    Message: {
      borderRadiusLG: 10,
    },

    Drawer: {
      borderRadiusLG: 16,
    },
  },
};

/** 根据模式获取对应的设计令牌 */
export function getDesignTokens(mode: 'light' | 'dark') {
  return mode === 'dark' ? darkDesignTokens : designTokens;
}

/** 根据模式获取对应的 Ant Design 主题 */
export function getAntTheme(mode: 'light' | 'dark') {
  return mode === 'dark' ? antDarkTheme : antTheme;
}
