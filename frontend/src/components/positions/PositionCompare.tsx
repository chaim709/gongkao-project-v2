import { Drawer, Table, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { positionApi } from '../../api/positions';

interface Props {
  open: boolean;
  onClose: () => void;
  positionIds: number[];
}

const COMPARE_FIELDS = [
  { key: 'department', label: '单位' },
  { key: 'city', label: '地区' },
  { key: 'education', label: '学历要求' },
  { key: 'major', label: '专业要求' },
  { key: 'exam_category', label: '考试类别' },
  { key: 'recruitment_count', label: '招录人数', numeric: true, higherBetter: true },
  { key: 'successful_applicants', label: '成功报名', numeric: true },
  { key: 'competition_ratio', label: '竞争比', numeric: true, lowerBetter: true, format: (v: number) => v ? `${v.toFixed(0)}:1` : '-' },
  { key: 'min_interview_score', label: '进面最低分', numeric: true, lowerBetter: true, format: (v: number) => v ? v.toFixed(1) : '-' },
  { key: 'max_interview_score', label: '进面最高分', numeric: true, format: (v: number) => v ? v.toFixed(1) : '-' },
  { key: 'other_requirements', label: '其他条件' },
];

export default function PositionCompare({ open, onClose, positionIds }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['position-compare', positionIds],
    queryFn: () => positionApi.compare(positionIds),
    enabled: open && positionIds.length >= 2,
  });

  if (!open) return null;

  const items = data?.items || [];

  // 构建对比表格数据
  const tableData = COMPARE_FIELDS.map(field => {
    const row: any = { key: field.key, field: field.label };

    items.forEach((item: any, idx: number) => {
      const value = item.position[field.key];
      row[`pos_${idx}`] = value;
    });

    // 数值型字���找最优/最差
    if (field.numeric) {
      const numericValues = items.map((item: any, idx: number) => ({
        idx,
        value: item.position[field.key] as number | null,
      })).filter((v: any) => v.value != null && v.value > 0);

      if (numericValues.length >= 2) {
        if (field.lowerBetter) {
          const best = numericValues.reduce((a: any, b: any) => a.value! < b.value! ? a : b);
          const worst = numericValues.reduce((a: any, b: any) => a.value! > b.value! ? a : b);
          row._best = best.idx;
          row._worst = worst.idx;
        } else if (field.higherBetter) {
          const best = numericValues.reduce((a: any, b: any) => a.value! > b.value! ? a : b);
          const worst = numericValues.reduce((a: any, b: any) => a.value! < b.value! ? a : b);
          row._best = best.idx;
          row._worst = worst.idx;
        }
      }
    }

    row._format = field.format;
    return row;
  });

  // 添加分析行
  if (items.length > 0) {
    tableData.push({
      key: 'difficulty',
      field: '竞争度评分',
      ...Object.fromEntries(items.map((item: any, idx: number) => [
        `pos_${idx}`,
        item.analysis?.competition?.score,
      ])),
      _format: (v: number) => v ? `${v.toFixed(0)}分` : '-',
      _best: items.reduce((bestIdx: number, item: any, idx: number) =>
        (item.analysis?.competition?.score || 100) < (items[bestIdx]?.analysis?.competition?.score || 100) ? idx : bestIdx, 0),
      _worst: items.reduce((worstIdx: number, item: any, idx: number) =>
        (item.analysis?.competition?.score || 0) > (items[worstIdx]?.analysis?.competition?.score || 0) ? idx : worstIdx, 0),
    });

    tableData.push({
      key: 'value',
      field: '性价比评分',
      ...Object.fromEntries(items.map((item: any, idx: number) => [
        `pos_${idx}`,
        item.analysis?.value?.score,
      ])),
      _format: (v: number) => v ? `${v.toFixed(0)}分` : '-',
      _best: items.reduce((bestIdx: number, item: any, idx: number) =>
        (item.analysis?.value?.score || 0) > (items[bestIdx]?.analysis?.value?.score || 0) ? idx : bestIdx, 0),
      _worst: items.reduce((worstIdx: number, item: any, idx: number) =>
        (item.analysis?.value?.score || 100) < (items[worstIdx]?.analysis?.value?.score || 100) ? idx : worstIdx, 0),
    });

    tableData.push({
      key: 'recommendation',
      field: '数据来源',
      ...Object.fromEntries(items.map((item: any, idx: number) => [
        `pos_${idx}`,
        item.analysis?.data_source === 'real' ? '真实数据' : '预测数据',
      ])),
    });
  }

  // 列定义
  const columns = [
    {
      title: '对比项',
      dataIndex: 'field',
      key: 'field',
      width: 120,
      fixed: 'left' as const,
      render: (v: string) => <b>{v}</b>,
    },
    ...items.map((item: any, idx: number) => ({
      title: (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 13, fontWeight: 600 }}>{item.position.title || item.position.department}</div>
          <div style={{ fontSize: 11, color: '#888' }}>{item.position.department}</div>
        </div>
      ),
      dataIndex: `pos_${idx}`,
      key: `pos_${idx}`,
      width: 180,
      render: (v: any, record: any) => {
        const formatted = record._format ? record._format(v) : (v ?? '-');
        const isBest = record._best === idx;
        const isWorst = record._worst === idx;

        return (
          <span style={{
            color: isBest ? '#52c41a' : isWorst ? '#ff4d4f' : undefined,
            fontWeight: (isBest || isWorst) ? 600 : undefined,
          }}>
            {formatted} {isBest ? ' ✓' : isWorst ? ' ✗' : ''}
          </span>
        );
      },
    })),
  ];

  return (
    <Drawer
      title={`岗位对比 (${positionIds.length}个)`}
      open={open}
      onClose={onClose}
      width={Math.min(180 * items.length + 160, window.innerWidth * 0.9)}
    >
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
      ) : (
        <Table
          columns={columns}
          dataSource={tableData}
          pagination={false}
          bordered
          size="small"
          scroll={{ x: 'max-content' }}
        />
      )}
    </Drawer>
  );
}
