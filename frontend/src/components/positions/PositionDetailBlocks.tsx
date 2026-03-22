import type { ReactNode } from 'react';
import { Card, Col, Row, Space, Statistic, Tag } from 'antd';

interface DetailFieldItem {
  key: string;
  label: string;
  value?: ReactNode;
}

interface DetailStatItem {
  key: string;
  title: string;
  value: string | number;
  span?: number;
}

interface LevelMetric {
  score: number;
  level: string;
  level_text: string;
}

interface PositionAnalysisData {
  competition: LevelMetric;
  value: LevelMetric;
  recommendation: string;
}

interface PositionDetailInfoCardProps {
  title: ReactNode;
  items: DetailFieldItem[];
}

interface PositionDetailStatsCardProps {
  title: ReactNode;
  items: DetailStatItem[];
}

interface PositionDetailTextCardProps {
  title: ReactNode;
  content?: string | null;
  emptyText?: string;
}

interface PositionDetailTagListCardProps {
  title: ReactNode;
  items?: string[];
  tagColor?: string;
}

interface PositionAnalysisCardProps {
  analysis: PositionAnalysisData;
}

export function PositionDetailInfoCard({
  title,
  items,
}: PositionDetailInfoCardProps) {
  return (
    <Card size="small" title={title}>
      {items.map((item) => (
        <p key={item.key}>
          <b>{item.label}：</b>
          {item.value ?? '-'}
        </p>
      ))}
    </Card>
  );
}

export function PositionDetailStatsCard({
  title,
  items,
}: PositionDetailStatsCardProps) {
  const defaultSpan = Math.floor(24 / items.length) || 8;

  return (
    <Card size="small" title={title}>
      <Row gutter={16}>
        {items.map((item) => (
          <Col key={item.key} span={item.span ?? defaultSpan}>
            <Statistic title={item.title} value={item.value} />
          </Col>
        ))}
      </Row>
    </Card>
  );
}

export function PositionDetailTextCard({
  title,
  content,
  emptyText = '暂无内容',
}: PositionDetailTextCardProps) {
  return (
    <Card size="small" title={title}>
      <p>{content || emptyText}</p>
    </Card>
  );
}

export function PositionDetailTagListCard({
  title,
  items,
  tagColor,
}: PositionDetailTagListCardProps) {
  if (!items?.length) {
    return null;
  }

  return (
    <Card size="small" title={title}>
      <Space size={[0, 8]} wrap>
        {items.map((item) => (
          <Tag key={item} color={tagColor}>
            {item}
          </Tag>
        ))}
      </Space>
    </Card>
  );
}

export function PositionAnalysisCard({
  analysis,
}: PositionAnalysisCardProps) {
  return (
    <Card size="small" title="智能分析">
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Statistic
            title="竞争度"
            value={analysis.competition.score}
            suffix={
              <Tag
                color={
                  analysis.competition.level === 'high'
                    ? 'red'
                    : analysis.competition.level === 'medium'
                      ? 'orange'
                      : 'green'
                }
              >
                {analysis.competition.level_text}
              </Tag>
            }
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="性价比"
            value={analysis.value.score}
            suffix={
              <Tag
                color={
                  analysis.value.level === 'high'
                    ? 'green'
                    : analysis.value.level === 'medium'
                      ? 'orange'
                      : 'red'
                }
              >
                {analysis.value.level_text}
              </Tag>
            }
          />
        </Col>
      </Row>
      <p style={{ color: '#666', fontSize: 14 }}>{analysis.recommendation}</p>
    </Card>
  );
}
