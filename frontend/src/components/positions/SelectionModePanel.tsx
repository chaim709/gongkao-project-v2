import { useState } from 'react';
import { Card, Select, Input, InputNumber, Button, Row, Col, Tag, Space, Alert, Divider } from 'antd';
import { SearchOutlined, UserOutlined, CloseOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import type { MatchSummary } from '../../types/position';
import client from '../../api/client';

interface StudentCondition {
  education: string;
  major: string;
  political_status?: string;
  work_years?: number;
  gender?: string;
  student_id?: number;
}

interface Props {
  year: number;
  examType: string;
  onYearChange: (year: number) => void;
  onExamTypeChange: (examType: string) => void;
  onMatch: (conditions: StudentCondition) => void;
  onClear: () => void;
  matchSummary?: MatchSummary;
  loading?: boolean;
  yearOptions?: number[];
  examTypeOptions?: string[];
}

export default function SelectionModePanel({
  year, examType, onYearChange, onExamTypeChange,
  onMatch, onClear, matchSummary, loading,
  yearOptions = [], examTypeOptions = [],
}: Props) {
  const [studentId, setStudentId] = useState<number>();
  const [conditions, setConditions] = useState<StudentCondition>({
    education: '', major: '',
  });
  const [inputMode, setInputMode] = useState<'student' | 'manual'>('manual');

  // 搜索学员
  const [studentSearch, setStudentSearch] = useState('');
  const { data: studentList } = useQuery({
    queryKey: ['student-search', studentSearch],
    queryFn: () => client.get('/students', { params: { search: studentSearch, page_size: 20 } }),
    enabled: inputMode === 'student' && studentSearch.length > 0,
  });

  // 选择学员后自动填充条件
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
      });
    } catch { /* ignore */ }
  };

  const handleMatch = () => {
    if (!conditions.education && !conditions.major) {
      return;
    }
    onMatch({ ...conditions, student_id: studentId });
  };

  return (
    <Card
      size="small"
      title={
        <Space>
          <UserOutlined />
          <span>选岗模式 - 输入学员条件</span>
          <Button type="link" size="small" onClick={() => setInputMode(inputMode === 'student' ? 'manual' : 'student')}>
            {inputMode === 'student' ? '手动输入' : '选择学员'}
          </Button>
        </Space>
      }
      extra={<Button type="text" icon={<CloseOutlined />} onClick={onClear} size="small">退出选岗</Button>}
      style={{ marginBottom: 16, background: '#f6ffed', border: '1px solid #b7eb8f' }}
    >
      {/* 年份和考试类型 */}
      <Row gutter={8} style={{ marginBottom: 12 }}>
        <Col>
          <Select value={year} onChange={onYearChange} style={{ width: 100 }}
            options={yearOptions.map(y => ({ value: y, label: `${y}年` }))}
            placeholder="年份"
          />
        </Col>
        <Col>
          <Select value={examType} onChange={onExamTypeChange} style={{ width: 120 }}
            options={examTypeOptions.map(t => ({ value: t, label: t === '省考' ? '江苏省考' : t }))}
            placeholder="考试类型"
          />
        </Col>
      </Row>

      {/* 学员选择模式 */}
      {inputMode === 'student' && (
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
              options={(studentList?.items || []).map((s: any) => ({
                value: s.id,
                label: `${s.name} (${s.phone || ''}) - ${s.education || ''} ${s.major || ''}`,
              }))}
            />
          </Col>
        </Row>
      )}

      {/* 条件输入 */}
      <Row gutter={8} style={{ marginBottom: 12 }}>
        <Col>
          <Select
            value={conditions.education || undefined}
            onChange={(v) => setConditions(c => ({ ...c, education: v }))}
            style={{ width: 130 }}
            placeholder="学历 *"
            options={[
              { value: '大专', label: '大专' },
              { value: '本科', label: '本科' },
              { value: '硕士', label: '硕士' },
              { value: '博士', label: '博士' },
            ]}
          />
        </Col>
        <Col flex="auto">
          <Input
            value={conditions.major}
            onChange={(e) => setConditions(c => ({ ...c, major: e.target.value }))}
            placeholder="专业 *（如：法学、计算机科学与技术）"
          />
        </Col>
        <Col>
          <Select
            value={conditions.political_status || undefined}
            onChange={(v) => setConditions(c => ({ ...c, political_status: v }))}
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
            onChange={(v) => setConditions(c => ({ ...c, work_years: v ?? undefined }))}
            placeholder="基层年限"
            min={0} max={30}
            style={{ width: 100 }}
          />
        </Col>
        <Col>
          <Select
            value={conditions.gender || undefined}
            onChange={(v) => setConditions(c => ({ ...c, gender: v }))}
            style={{ width: 80 }}
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
            disabled={!conditions.education && !conditions.major}
          >
            智能匹配
          </Button>
        </Col>
      </Row>

      {/* 匹配结果摘要 */}
      {matchSummary && (
        <Alert
          type="info"
          showIcon={false}
          message={
            <Space split={<Divider type="vertical" />} wrap>
              <span>
                符合条件: <b style={{ color: '#52c41a', fontSize: 16 }}>{matchSummary.matched}</b> / {matchSummary.total_positions} 个岗位
              </span>
              {matchSummary.education_excluded > 0 && (
                <Tag color="red">学历不符 {matchSummary.education_excluded}</Tag>
              )}
              {matchSummary.major_excluded > 0 && (
                <Tag color="orange">专业不符 {matchSummary.major_excluded}</Tag>
              )}
              {matchSummary.political_excluded > 0 && (
                <Tag color="blue">面貌不符 {matchSummary.political_excluded}</Tag>
              )}
              {matchSummary.work_experience_excluded > 0 && (
                <Tag color="purple">经历不符 {matchSummary.work_experience_excluded}</Tag>
              )}
              {matchSummary.gender_excluded > 0 && (
                <Tag color="default">性别不符 {matchSummary.gender_excluded}</Tag>
              )}
            </Space>
          }
          style={{ background: '#fff' }}
        />
      )}
    </Card>
  );
}
