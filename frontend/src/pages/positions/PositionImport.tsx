import { useState } from 'react';
import { Button, Upload, message, Card, Alert, Select, Row, Col, Table, Tag, Space } from 'antd';
import { UploadOutlined, DownloadOutlined, InboxOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd';
import client from '../../api/client';
import { positionApi } from '../../api/positions';

interface DetectedFile {
  filename: string;
  type: string;
  type_label: string;
  rows: number;
  columns: number;
}

interface ImportResult {
  detected_files: DetectedFile[];
  import_result: {
    total: number;
    inserted: number;
    updated: number;
    errors: string[];
  };
  merge_result?: {
    total: number;
    matched: number;
    unmatched_count: number;
    unmatched_details: Array<{ reason: string; data: any }>;
  };
}

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 6 }, (_, i) => CURRENT_YEAR - i);

export default function PositionImport() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [year, setYear] = useState<number>(CURRENT_YEAR);
  const [examType, setExamType] = useState<string>('省考');

  const handleDownloadTemplate = async () => {
    try {
      const blob = await client.get('/api/v1/positions/import-template', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'position_import_template.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
      message.success('模板下载成功');
    } catch {
      message.error('模板下载失败');
    }
  };

  const handleSmartImport = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const files = fileList.map(f => f.originFileObj as File);
      const response = await positionApi.smartImport(files, year, examType);
      setResult(response);
      message.success('导入完成');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '导入失败');
    } finally {
      setLoading(false);
    }
  };

  const fileTypeColor: Record<string, string> = {
    position: 'blue',
    application: 'green',
    score: 'orange',
    complete: 'purple',
    unknown: 'default',
  };

  return (
    <div style={{ padding: 24 }}>
      <Card title="智能岗位导入" extra={
        <Button icon={<DownloadOutlined />} onClick={handleDownloadTemplate}>下载模板</Button>
      }>
        {/* Step 1: 配置 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col>
            <Space>
              <span>年份:</span>
              <Select value={year} onChange={setYear} style={{ width: 100 }}
                options={YEAR_OPTIONS.map(y => ({ value: y, label: `${y}年` }))}
              />
            </Space>
          </Col>
          <Col>
            <Space>
              <span>考试类型:</span>
              <Select value={examType} onChange={setExamType} style={{ width: 120 }}
                options={[
                  { value: '省考', label: '省考' },
                  { value: '国考', label: '国考' },
                  { value: '事业单位', label: '事业单位' },
                ]}
              />
            </Space>
          </Col>
        </Row>

        {/* Step 2: 上传文件 */}
        <Upload.Dragger
          multiple
          accept=".xlsx,.xls"
          fileList={fileList}
          beforeUpload={() => false}
          onChange={({ fileList: fl }) => setFileList(fl)}
          style={{ marginBottom: 16 }}
        >
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">拖拽或点击上传 Excel 文件（支持多个）</p>
          <p className="ant-upload-hint">
            可同时上传：职位表 + 报名人数表 + 进面分数线表，系统自动识别类型并合并
          </p>
        </Upload.Dragger>

        <Button
          type="primary"
          icon={<UploadOutlined />}
          loading={loading}
          onClick={handleSmartImport}
          disabled={fileList.length === 0}
          size="large"
          style={{ marginBottom: 24 }}
        >
          开始智能导入 ({fileList.length} 个文件)
        </Button>

        {/* 导入结果 */}
        {result && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* 文件检测结果 */}
            <Card size="small" title="文件识别结果">
              <Space wrap>
                {result.detected_files.map((f, i) => (
                  <Tag key={i} color={fileTypeColor[f.type] || 'default'}>
                    {f.filename}: {f.type_label} ({f.rows}行)
                  </Tag>
                ))}
              </Space>
            </Card>

            {/* 导入统计 */}
            <Alert
              message="导入结果"
              description={
                <div>
                  <p>新增: <b>{result.import_result.inserted}</b> 条 | 更新: <b>{result.import_result.updated}</b> 条</p>
                  {result.import_result.errors.length > 0 && (
                    <div>
                      <p style={{ color: '#ff4d4f' }}>错误 ({result.import_result.errors.length}):</p>
                      <ul>{result.import_result.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
                    </div>
                  )}
                </div>
              }
              type={result.import_result.errors.length > 0 ? 'warning' : 'success'}
              showIcon
            />

            {/* 分数线合并结果 */}
            {result.merge_result && (
              <Alert
                message="进面分数线合并"
                description={
                  <div>
                    <p>
                      总记录: {result.merge_result.total} |
                      成功匹配: <b style={{ color: '#52c41a' }}>{result.merge_result.matched}</b> |
                      未匹配: <b style={{ color: result.merge_result.unmatched_count > 0 ? '#ff4d4f' : '#52c41a' }}>{result.merge_result.unmatched_count}</b>
                    </p>
                    <p>匹配率: <b>{(result.merge_result.matched * 100 / result.merge_result.total).toFixed(1)}%</b></p>
                    {result.merge_result.unmatched_details.length > 0 && (
                      <Table
                        size="small"
                        dataSource={result.merge_result.unmatched_details}
                        columns={[
                          { title: '原因', dataIndex: 'reason', key: 'reason' },
                        ]}
                        rowKey={(_, i) => String(i)}
                        pagination={false}
                        style={{ marginTop: 8 }}
                      />
                    )}
                  </div>
                }
                type={result.merge_result.unmatched_count === 0 ? 'success' : 'warning'}
                showIcon
              />
            )}
          </Space>
        )}
      </Card>
    </div>
  );
}
