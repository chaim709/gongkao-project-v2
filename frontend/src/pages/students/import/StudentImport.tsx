import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card, Steps, Upload, Button, Table, Alert, Space, message, Result,
} from 'antd';
import {
  UploadOutlined, DownloadOutlined, ArrowLeftOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { studentApi } from '../../../api/students';
import type { UploadFile } from 'antd';

export default function StudentImport() {
  const navigate = useNavigate();
  const [current, setCurrent] = useState(0);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [result, setResult] = useState<{
    success_count: number;
    failed_count: number;
    failed_rows: { row: number; name: string; reason: string }[];
  } | null>(null);

  const importMutation = useMutation({
    mutationFn: (file: File) => studentApi.batchImport(file),
    onSuccess: (data) => {
      setResult(data);
      setCurrent(2);
      if (data.failed_count === 0) {
        message.success(`成功导入 ${data.success_count} 名学员`);
      } else {
        message.warning(`成功 ${data.success_count} 条，失败 ${data.failed_count} 条`);
      }
    },
    onError: () => message.error('导入失败，请检查文件格式'),
  });

  const handleUpload = () => {
    if (fileList.length === 0) {
      message.error('请先选择文件');
      return;
    }
    const file = fileList[0].originFileObj as File;
    importMutation.mutate(file);
    setCurrent(1);
  };

  const downloadTemplate = () => {
    const headers = ['姓名*', '手机号', '微信', '性别', '学历', '专业', '报考类型'];
    const sample = ['张三', '13800138000', 'zhangsan', '男', '本科', '计算机', '省考'];

    const csv = [headers.join(','), sample.join(',')].join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '学员导入模板.csv';
    link.click();
  };

  const steps = [
    { title: '上传文件', icon: <UploadOutlined /> },
    { title: '导入中', icon: <UploadOutlined /> },
    { title: '完成', icon: <CheckCircleOutlined /> },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/students')}>
          返回学员列表
        </Button>
      </div>

      <Card title="批量导入学员">
        <Steps current={current} items={steps} style={{ marginBottom: 24 }} />

        {current === 0 && (
          <div>
            <Alert
              message="导入说明"
              description={
                <div>
                  <p>1. 下载模板文件，按照格式填写学员信息</p>
                  <p>2. 姓名为必填项，其他字段可选</p>
                  <p>3. 手机号重复的学员将跳过导入</p>
                  <p>4. 支持 .xlsx 和 .xls 格式</p>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Button icon={<DownloadOutlined />} onClick={downloadTemplate}>
                下载模板文件
              </Button>

              <Upload
                fileList={fileList}
                onChange={({ fileList: newFileList }) => setFileList(newFileList)}
                beforeUpload={() => false}
                maxCount={1}
                accept=".xlsx,.xls"
              >
                <Button icon={<UploadOutlined />}>选择文件</Button>
              </Upload>

              <Button
                type="primary"
                onClick={handleUpload}
                disabled={fileList.length === 0}
                loading={importMutation.isPending}
              >
                开始导入
              </Button>
            </Space>
          </div>
        )}

        {current === 1 && (
          <Result
            icon={<UploadOutlined spin />}
            title="正在导入..."
            subTitle="请稍候，正在处理文件"
          />
        )}

        {current === 2 && result && (
          <div>
            <Result
              status={result.failed_count === 0 ? 'success' : 'warning'}
              title={`导入完成`}
              subTitle={`成功 ${result.success_count} 条，失败 ${result.failed_count} 条`}
              extra={[
                <Button type="primary" key="back" onClick={() => navigate('/students')}>
                  返回学员列表
                </Button>,
                <Button key="retry" onClick={() => { setCurrent(0); setFileList([]); setResult(null); }}>
                  继续导入
                </Button>,
              ]}
            />

            {result.failed_count > 0 && (
              <Table
                size="small"
                dataSource={result.failed_rows}
                rowKey="row"
                pagination={false}
                columns={[
                  { title: '行号', dataIndex: 'row', width: 80 },
                  { title: '姓名', dataIndex: 'name', width: 120 },
                  { title: '失败原因', dataIndex: 'reason' },
                ]}
                style={{ marginTop: 24 }}
              />
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
