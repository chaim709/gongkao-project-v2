"""
PDF 选岗报告生成服务
"""
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.position import Position
from app.models.student import Student

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table as RLTable,
    TableStyle, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体（macOS 内置字体）
_FONT_REGISTERED = False


def _register_fonts():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    font_paths = [
        ('/System/Library/Fonts/PingFang.ttc', 'PingFang'),
        ('/System/Library/Fonts/STHeiti Medium.ttc', 'STHeiti'),
        ('/System/Library/Fonts/Supplemental/Songti.ttc', 'Songti'),
    ]
    for path, name in font_paths:
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
            _FONT_REGISTERED = True
            return
        except Exception:
            continue
    # fallback: 使用 Helvetica（不支持中文但不会崩溃）
    _FONT_REGISTERED = True


def _get_font():
    """获取已注册的中文字体名"""
    for name in ['PingFang', 'STHeiti', 'Songti']:
        if name in pdfmetrics.getRegisteredFontNames():
            return name
    return 'Helvetica'


class PDFReportService:
    """选岗���告 PDF 生成服务"""

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        student_id: int,
        position_ids: List[int],
        year: int,
        exam_type: str,
    ) -> BytesIO:
        """生成选岗报告 PDF"""
        _register_fonts()
        font_name = _get_font()

        # 获取数据
        student = (await db.execute(
            select(Student).where(Student.id == student_id)
        )).scalar_one_or_none()

        positions = []
        if position_ids:
            result = await db.execute(
                select(Position).where(Position.id.in_(position_ids))
            )
            positions = list(result.scalars().all())

        # 分析岗位
        from app.services.position_analysis_service import PositionAnalysisService
        analyses = [PositionAnalysisService.analyze_position(p) for p in positions]

        # 生成 PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )

        # 样式
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title_CN', parent=styles['Title'],
            fontName=font_name, fontSize=20, spaceAfter=6,
        )
        heading_style = ParagraphStyle(
            'Heading_CN', parent=styles['Heading2'],
            fontName=font_name, fontSize=14, spaceBefore=12, spaceAfter=6,
            textColor=colors.HexColor('#1a73e8'),
        )
        body_style = ParagraphStyle(
            'Body_CN', parent=styles['Normal'],
            fontName=font_name, fontSize=10, leading=16,
        )
        small_style = ParagraphStyle(
            'Small_CN', parent=styles['Normal'],
            fontName=font_name, fontSize=8, textColor=colors.grey,
        )

        story = []

        # ===== 标题 =====
        story.append(Paragraph('智能选岗分析报告', title_style))
        story.append(Paragraph(
            f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            small_style
        ))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#1a73e8')))
        story.append(Spacer(1, 12))

        # ===== 学员信息 =====
        story.append(Paragraph('一、学员基本信息', heading_style))
        if student:
            info_data = [
                ['姓名', student.name or '-', '学历', student.education or '-'],
                ['专业', student.major or '-', '政治面貌', student.political_status or '-'],
                ['基层年限', f'{student.work_years or 0}年', '性别', student.gender or '-'],
                ['目标年份', str(year), '考试类型', exam_type],
            ]
            info_table = RLTable(info_data, colWidths=[3 * cm, 5 * cm, 3 * cm, 5 * cm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333')),
                ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#333')),
                ('FONTNAME', (0, 0), (0, -1), font_name),
                ('FONTNAME', (2, 0), (2, -1), font_name),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(info_table)
        story.append(Spacer(1, 16))

        # ===== 推荐岗位 =====
        story.append(Paragraph(f'二、推荐岗位 ({len(positions)}个)', heading_style))

        if positions:
            # 分类
            sprint = [(p, a) for p, a in zip(positions, analyses) if a['competition']['score'] >= 70]
            stable = [(p, a) for p, a in zip(positions, analyses) if 40 <= a['competition']['score'] < 70]
            safe = [(p, a) for p, a in zip(positions, analyses) if a['competition']['score'] < 40]

            for category, label, items in [
                ('sprint', '冲刺岗位', sprint),
                ('stable', '稳妥岗位', stable),
                ('safe', '保底岗位', safe),
            ]:
                if not items:
                    continue

                story.append(Paragraph(f'【{label}】', ParagraphStyle(
                    f'{category}_style', parent=body_style,
                    fontSize=11, spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor(
                        '#ff4d4f' if category == 'sprint' else
                        '#52c41a' if category == 'stable' else '#1890ff'
                    ),
                )))

                # 岗位表格
                headers = ['单位', '岗位', '城市', '招录', '竞争比', '最低分', '性价比']
                rows = [headers]
                for pos, analysis in items:
                    rows.append([
                        (pos.department or '-')[:12],
                        (pos.title or '-')[:10],
                        pos.city or '-',
                        str(pos.recruitment_count or '-'),
                        f'{pos.competition_ratio:.0f}:1' if pos.competition_ratio else '-',
                        f'{pos.min_interview_score:.1f}' if pos.min_interview_score else '-',
                        f'{analysis["value"]["score"]:.0f}分',
                    ])

                pos_table = RLTable(
                    rows,
                    colWidths=[4.5 * cm, 3.5 * cm, 2 * cm, 1.5 * cm, 2 * cm, 2 * cm, 2 * cm],
                )
                pos_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(pos_table)
                story.append(Spacer(1, 8))

        else:
            story.append(Paragraph('暂无推荐岗位', body_style))

        story.append(Spacer(1, 16))

        # ===== 备注 =====
        story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            '说明: 本报告基于历年公考数据分析生成，仅供参考。'
            '竞争比和分数线数据来源于公开数据，实际情况以官方公布为准。',
            small_style
        ))
        story.append(Paragraph(
            f'报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            small_style
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer
