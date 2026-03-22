import { useCallback, useEffect, useState } from 'react';
import type { TableProps } from 'antd';

interface PaginationParams {
  page: number;
  page_size: number;
}

interface UsePositionPageStateOptions {
  columnStorageKey: string;
  defaultVisibleColumns: string[];
  defaultParams?: PaginationParams;
}

const DEFAULT_PARAMS: PaginationParams = {
  page: 1,
  page_size: 20,
};

export default function usePositionPageState<TPosition>({
  columnStorageKey,
  defaultVisibleColumns,
  defaultParams = DEFAULT_PARAMS,
}: UsePositionPageStateOptions) {
  type TableChangeParams = Parameters<NonNullable<TableProps<TPosition>['onChange']>>;

  const [params, setParams] = useState<PaginationParams>(defaultParams);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<TPosition | null>(null);
  const [sortBy, setSortBy] = useState<string>();
  const [sortOrder, setSortOrder] = useState<string>();
  const [columnSettingOpen, setColumnSettingOpen] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<string[]>(defaultVisibleColumns);
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);

  useEffect(() => {
    const savedColumns = localStorage.getItem(columnStorageKey);

    if (!savedColumns) {
      return;
    }

    try {
      const parsedColumns = JSON.parse(savedColumns);

      if (Array.isArray(parsedColumns)) {
        setVisibleColumns(parsedColumns);
      }
    } catch {
      setVisibleColumns(defaultVisibleColumns);
    }
  }, [columnStorageKey]);

  const resetToFirstPage = useCallback(() => {
    setParams((current) => ({
      ...current,
      page: 1,
    }));
  }, []);

  const openPositionDetail = useCallback((position: TPosition) => {
    setSelectedPosition(position);
    setDetailOpen(true);
  }, []);

  const closePositionDetail = useCallback(() => {
    setDetailOpen(false);
    setSelectedPosition(null);
  }, []);

  const openColumnSetting = useCallback(() => {
    setColumnSettingOpen(true);
  }, []);

  const closeColumnSetting = useCallback(() => {
    setColumnSettingOpen(false);
  }, []);

  const saveColumnConfig = useCallback(() => {
    localStorage.setItem(columnStorageKey, JSON.stringify(visibleColumns));
    setColumnSettingOpen(false);
  }, [columnStorageKey, visibleColumns]);

  const handleTableChange: TableProps<TPosition>['onChange'] = useCallback(
    (
      _pagination: TableChangeParams[0],
      _filters: TableChangeParams[1],
      sorter: TableChangeParams[2],
    ) => {
      if (Array.isArray(sorter) || !sorter.field) {
        return;
      }

      const field = String(sorter.field);

      if (sorter.order) {
        setSortBy(field);
        setSortOrder(sorter.order === 'ascend' ? 'asc' : 'desc');
        return;
      }

      setSortBy(undefined);
      setSortOrder(undefined);
    },
    [],
  );

  const openCompare = useCallback(() => {
    setCompareOpen(true);
  }, []);

  const closeCompare = useCallback(() => {
    setCompareOpen(false);
  }, []);

  const clearSelectedRowKeys = useCallback(() => {
    setSelectedRowKeys([]);
  }, []);

  const buildPagination = useCallback(
    (total: number) => ({
      current: params.page,
      pageSize: params.page_size,
      total,
      showTotal: (count: number) => `共 ${count} 个岗位`,
      showSizeChanger: true,
      pageSizeOptions: ['20', '50', '100'],
      onChange: (page: number, pageSize: number) =>
        setParams((current) => ({
          ...current,
          page,
          page_size: pageSize,
        })),
    }),
    [params.page, params.page_size],
  );

  return {
    params,
    setParams,
    resetToFirstPage,
    detailOpen,
    selectedPosition,
    openPositionDetail,
    closePositionDetail,
    sortBy,
    sortOrder,
    handleTableChange,
    columnSettingOpen,
    openColumnSetting,
    closeColumnSetting,
    visibleColumns,
    setVisibleColumns,
    saveColumnConfig,
    selectedRowKeys,
    setSelectedRowKeys,
    compareOpen,
    openCompare,
    closeCompare,
    clearSelectedRowKeys,
    buildPagination,
  };
}
