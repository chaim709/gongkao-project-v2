import type { ReactNode } from 'react';
import {
  AimOutlined,
  FilePdfOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Checkbox,
  Col,
  Drawer,
  Modal,
  Row,
  Space,
  Statistic,
  Switch,
  Table,
  Tag,
} from 'antd';
import type { DrawerProps } from 'antd';
import type { ColumnsType, TableProps } from 'antd/es/table';

import type { Position } from '../../types/position';
import PositionCompare from './PositionCompare';

interface ColumnOption {
  key: string;
  label: string;
}

interface StatsCard {
  key: string;
  title: string;
  value: number | string;
  prefix?: ReactNode;
  suffix?: ReactNode;
  span?: number;
}

interface PositionPageFrameProps {
  selectionMode: boolean;
  onSelectionModeChange: (checked: boolean) => void;
  selectionPanel?: ReactNode;
  selectionTagText?: string;
  stats?: StatsCard[];
  filters: ReactNode;
  columns: ColumnsType<Position>;
  dataSource: Position[];
  loading: boolean;
  rowSelection?: TableProps<Position>['rowSelection'];
  onTableChange?: TableProps<Position>['onChange'];
  pagination: TableProps<Position>['pagination'];
  tableScroll?: TableProps<Position>['scroll'];
  tableSize?: TableProps<Position>['size'];
  tableLayout?: TableProps<Position>['tableLayout'];
  detailTitle: ReactNode;
  detailOpen: boolean;
  onDetailClose: () => void;
  detailDrawerSize?: DrawerProps['size'];
  detailContent?: ReactNode;
  selectedPositionIds?: number[];
  compareOpen: boolean;
  onCloseCompare: () => void;
  onOpenCompare: () => void;
  onClearSelected: () => void;
  onGenerateReport: () => void;
  reportLoading?: boolean;
  columnSettingOpen: boolean;
  onSaveColumnSetting: () => void;
  onCloseColumnSetting: () => void;
  allColumns: ColumnOption[];
  visibleColumns: string[];
  onVisibleColumnsChange: (values: string[]) => void;
}

const DEFAULT_SELECTION_TEXT = '选岗模式已开启 - 输入学员条件后自动匹配可报岗位';

export default function PositionPageFrame({
  selectionMode,
  onSelectionModeChange,
  selectionPanel,
  selectionTagText = DEFAULT_SELECTION_TEXT,
  stats = [],
  filters,
  columns,
  dataSource,
  loading,
  rowSelection,
  onTableChange,
  pagination,
  tableScroll = { x: 1000 },
  tableSize = 'middle',
  tableLayout,
  detailTitle,
  detailOpen,
  onDetailClose,
  detailDrawerSize = 'large',
  detailContent,
  selectedPositionIds = [],
  compareOpen,
  onCloseCompare,
  onOpenCompare,
  onClearSelected,
  onGenerateReport,
  reportLoading = false,
  columnSettingOpen,
  onSaveColumnSetting,
  onCloseColumnSetting,
  allColumns,
  visibleColumns,
  onVisibleColumnsChange,
}: PositionPageFrameProps) {
  const selectedCount = selectedPositionIds.length;

  return (
    <div>
      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Space>
          <AimOutlined style={{ color: selectionMode ? '#52c41a' : '#999' }} />
          <Switch
            checked={selectionMode}
            onChange={onSelectionModeChange}
            checkedChildren="选岗模式"
            unCheckedChildren="浏览模式"
          />
          {selectionMode ? <Tag color="green">{selectionTagText}</Tag> : null}
        </Space>
      </div>

      {selectionMode ? selectionPanel : null}

      {!selectionMode && stats.length > 0 ? (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          {stats.map((item) => (
            <Col key={item.key} span={item.span ?? Math.floor(24 / stats.length)}>
              <Card size="small">
                <Statistic
                  title={item.title}
                  value={item.value}
                  prefix={item.prefix}
                  suffix={item.suffix}
                />
              </Card>
            </Col>
          ))}
        </Row>
      ) : null}

      <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {filters}
      </div>

      <Table<Position>
        columns={columns}
        dataSource={dataSource}
        rowKey="id"
        loading={loading}
        rowSelection={rowSelection}
        onChange={onTableChange}
        pagination={pagination}
        scroll={tableScroll}
        size={tableSize}
        tableLayout={tableLayout}
      />

      <Drawer
        title={detailTitle}
        open={detailOpen}
        onClose={onDetailClose}
        size={detailDrawerSize}
      >
        {detailContent}
      </Drawer>

      {selectionMode && selectedCount > 0 ? (
        <div
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#fff',
            borderTop: '2px solid #1890ff',
            padding: '12px 24px',
            zIndex: 100,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <Space>
            <Tag color="blue">已选 {selectedCount} 个岗位</Tag>
            <Button size="small" onClick={onClearSelected}>
              清空选择
            </Button>
          </Space>
          <Space>
            <Button
              type="primary"
              icon={<SwapOutlined />}
              disabled={selectedCount < 2}
              onClick={onOpenCompare}
            >
              对比岗位
            </Button>
            <Button
              icon={<FilePdfOutlined />}
              loading={reportLoading}
              onClick={onGenerateReport}
            >
              生成报告
            </Button>
          </Space>
        </div>
      ) : null}

      <PositionCompare
        open={compareOpen}
        onClose={onCloseCompare}
        positionIds={selectedPositionIds}
      />

      <Modal
        title="列设置"
        open={columnSettingOpen}
        onOk={onSaveColumnSetting}
        onCancel={onCloseColumnSetting}
        width={500}
      >
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          <Checkbox.Group
            value={visibleColumns}
            onChange={(values) => onVisibleColumnsChange(values as string[])}
            style={{ width: '100%' }}
          >
            <Row gutter={[16, 16]}>
              {allColumns.map((column) => (
                <Col span={12} key={column.key}>
                  <Checkbox value={column.key}>{column.label}</Checkbox>
                </Col>
              ))}
            </Row>
          </Checkbox.Group>
        </div>
      </Modal>
    </div>
  );
}
