import { useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Divider,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Tag,
} from 'antd';
import {
  CloseOutlined,
  SearchOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';

import client from '../../api/client';
import type { MatchSummary } from '../../types/position';

export interface ShiyeSelectionConditions {
  education: string;
  major: string;
  political_status?: string;
  work_years?: number;
  gender?: string;
  student_id?: number;
  include_manual_review?: boolean;
}

interface Props {
  year: number;
  onYearChange: (year: number) => void;
  onMatch: (conditions: ShiyeSelectionConditions) => void;
  onClear: () => void;
  matchSummary?: MatchSummary;
  loading?: boolean;
  yearOptions?: number[];
}

const EDUCATION_OPTIONS = [
  { value: '大专', label: '大专' },
  { value: '本科', label: '本科' },
  { value: '研究生', label: '研究生' },
  { value: '博士', label: '博士' },
];

export default function ShiyeSelectionPanel({
  year,
  onYearChange,
  onMatch,
  onClear,
  matchSummary,
  loading,
  yearOptions = [],
}: Props) {
  const [studentId, setStudentId] = useState<number>();
  const [studentSearch, setStudentSearch] = useState('');
  const [inputMode, setInputMode] = useState<'student' | 'manual'>('manual');
  const [conditions, setConditions] = useState<ShiyeSelectionConditions>({
    education: '',
    major: '',
    include_manual_review: true,
  });

  const { data: studentList } = useQuery({
    queryKey: ['student-search', studentSearch],
    queryFn: () =>
      client.get('/students', {
        params: { search: studentSearch, page_size: 20 },
      }),
    enabled: inputMode === 'student' && studentSearch.length > 0,
  });

  const handleStudentSelect = async (id: number) => {
    setStudentId(id);
    try {
      const student = await client.get(`/students/${id}`);
      setConditions({
        education: student.education || '',
        major: student.major || '',
        political_status: student.political_status,
        work_years: student.work_years,
        gender: student.gender,
        include_manual_review: true,
      });
    } catch {
      // ignore
    }
  };

  const handleMatch = () => {
    if (!conditions.education || !conditions.major) {
      return;
    }
    onMatch({
      ...conditions,
      student_id: studentId,
    });
  };

  return (
    <Card
      size="small"
      title={
        <Space>
          <UserOutlined />
          <span>事业编选岗模式</span>
          <Button
            type="link"
            size="small"
            onClick={() =>
              setInputMode(inputMode === 'student' ? 'manual' : 'student')
            }
          >
            {inputMode === 'student' ? '手动输入' : '选择学员'}
          </Button>
        </Space>
      }
      extra={
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={onClear}
          size="small"
        >
          退出选岗
        </Button>
      }
      style={{
        marginBottom: 16,
        background: '#f6ffed',
        border: '1px solid #b7eb8f',
      }}
    >
      <Alert
        type="success"
        showIcon={false}
        style={{ marginBottom: 12 }}
        message="按 学历+专业 先召回，再用 岗位性质 / 招聘对象 / 经费来源 / 风险避雷 收缩结果。"
      />

      <Row gutter={8} style={{ marginBottom: 12 }}>
        <Col>
          <Select
            value={year}
            onChange={onYearChange}
            style={{ width: 110 }}
            options={yearOptions.map((item) => ({
              value: item,
              label: `${item}年`,
            }))}
            placeholder="年份"
          />
        </Col>
      </Row>

      {inputMode === 'student' ? (
        <Row gutter={8} style={{ marginBottom: 12 }}>
          <Col flex="auto">
            <Select
              showSearch
              placeholder="搜索学员姓名或手机号"
              value={studentId}
              onSearch={setStudentSearch}
              onChange={handleStudentSelect}
              style={{ width: '100%' }}
              filterOption={false}
              options={(studentList?.items || []).map((student: any) => ({
                value: student.id,
                label: `${student.name} (${student.phone || ''}) - ${
                  student.education || ''
                } ${student.major || ''}`,
              }))}
            />
          </Col>
        </Row>
      ) : null}

      <Row gutter={8} style={{ marginBottom: 12 }}>
        <Col>
          <Select
            value={conditions.education || undefined}
            onChange={(value) =>
              setConditions((current) => ({
                ...current,
                education: value,
              }))
            }
            style={{ width: 140 }}
            placeholder="学历层级 *"
            options={EDUCATION_OPTIONS}
          />
        </Col>
        <Col flex="auto">
          <Input
            value={conditions.major}
            onChange={(event) =>
              setConditions((current) => ({
                ...current,
                major: event.target.value,
              }))
            }
            placeholder="专业名称 *（如：财务管理、计算机科学与技术）"
          />
        </Col>
        <Col>
          <Select
            value={conditions.political_status || undefined}
            onChange={(value) =>
              setConditions((current) => ({
                ...current,
                political_status: value,
              }))
            }
            style={{ width: 120 }}
            placeholder="政治面貌"
            allowClear
            options={[
              { value: '中共党员', label: '中共党员' },
              { value: '中共预备党员', label: '预备党员' },
              { value: '共青团员', label: '共青团员' },
              { value: '群众', label: '群众' },
            ]}
          />
        </Col>
        <Col>
          <InputNumber
            value={conditions.work_years}
            onChange={(value) =>
              setConditions((current) => ({
                ...current,
                work_years: value ?? undefined,
              }))
            }
            placeholder="工作年限"
            min={0}
            max={40}
            style={{ width: 100 }}
          />
        </Col>
        <Col>
          <Select
            value={conditions.gender || undefined}
            onChange={(value) =>
              setConditions((current) => ({
                ...current,
                gender: value,
              }))
            }
            style={{ width: 90 }}
            placeholder="性别"
            allowClear
            options={[
              { value: '男', label: '男' },
              { value: '女', label: '女' },
            ]}
          />
        </Col>
        <Col>
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleMatch}
            loading={loading}
            disabled={!conditions.education || !conditions.major}
          >
            智能匹配
          </Button>
        </Col>
      </Row>

      <Row style={{ marginBottom: 8 }}>
        <Col>
          <Checkbox
            checked={conditions.include_manual_review}
            onChange={(event) =>
              setConditions((current) => ({
                ...current,
                include_manual_review: event.target.checked,
              }))
            }
          >
            包含需人工确认岗位
          </Checkbox>
        </Col>
      </Row>

      {matchSummary ? (
        <div>
          <Alert
            type="info"
            showIcon={false}
            message={
              <Space split={<Divider type="vertical" />} wrap>
                <span>
                  硬匹配:
                  <b style={{ color: '#52c41a', fontSize: 16 }}>
                    {' '}
                    {matchSummary.hard_pass || 0}
                  </b>
                </span>
                <Tag color="gold">
                  需人工确认 {matchSummary.manual_review_needed || 0}
                </Tag>
                <Tag color="default">已排除 {matchSummary.hard_fail || 0}</Tag>
                <Tag color="red">冲刺 {matchSummary.sprint_count || 0}</Tag>
                <Tag color="green">稳妥 {matchSummary.stable_count || 0}</Tag>
                <Tag color="blue">保底 {matchSummary.safe_count || 0}</Tag>
              </Space>
            }
            style={{ background: '#fff' }}
          />

          {matchSummary.sort_basis?.length ? (
            <div
              style={{
                marginTop: 10,
                padding: '10px 12px',
                background: '#fafafa',
                borderRadius: 8,
              }}
            >
              <div
                style={{
                  marginBottom: 8,
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#595959',
                }}
              >
                当前排序依据
              </div>
              <Space size={[0, 8]} wrap>
                {matchSummary.sort_basis.map((basis) => (
                  <Tag key={basis} color="blue">
                    {basis}
                  </Tag>
                ))}
              </Space>
            </div>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}
