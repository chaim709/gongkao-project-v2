import { TreeSelect, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { weaknessApi, type ModuleTreeNode } from '../api/weakness';

interface Props {
  value?: string;
  onChange?: (value: string, label?: string, extra?: { subModule?: string }) => void;
  examType?: string;
  placeholder?: string;
  style?: React.CSSProperties;
}

export default function KnowledgeTreeSelect({ value, onChange, examType, placeholder, style }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['module-tree', examType],
    queryFn: () => weaknessApi.getModuleTree(examType),
  });

  const handleChange = (val: string) => {
    // val 格式: "言语理解" 或 "言语理解/片段阅读"
    const parts = val.split('/');
    const moduleName = parts[0];
    const subModule = parts.length > 1 ? parts[1] : undefined;
    onChange?.(moduleName, moduleName, { subModule });
  };

  // 递归转为 Ant Design TreeSelect 的 treeData 格式
  const toTreeData = (nodes: ModuleTreeNode[]): any[] =>
    nodes.map(node => ({
      title: node.title,
      value: node.value,
      selectable: node.selectable !== false,
      children: node.children?.length ? toTreeData(node.children) : undefined,
    }));

  const treeData = data?.tree ? toTreeData(data.tree) : [];

  if (isLoading) {
    return <Spin size="small" />;
  }

  return (
    <TreeSelect
      value={value}
      onChange={handleChange}
      treeData={treeData}
      placeholder={placeholder || '选择知识点模块'}
      showSearch
      treeDefaultExpandAll={false}
      treeExpandAction="click"
      filterTreeNode={(input, node) =>
        String(node?.title ?? '').toLowerCase().includes(input.toLowerCase())
      }
      style={{ width: '100%', ...style }}
      dropdownStyle={{ maxHeight: 400, overflow: 'auto' }}
      allowClear
    />
  );
}
