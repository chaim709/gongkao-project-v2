"""
PDF 选岗报告生成服务
"""
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.models.student import Student

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table as RLTable,
    TableStyle,
)

# 注册中文字体（macOS 内置字体）
_FONT_REGISTERED = False


def _register_fonts():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    font_paths = [
        ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
        ("/System/Library/Fonts/STHeiti Medium.ttc", "STHeiti"),
        ("/System/Library/Fonts/Supplemental/Songti.ttc", "Songti"),
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
    for name in ["PingFang", "STHeiti", "Songti"]:
        if name in pdfmetrics.getRegisteredFontNames():
            return name
    return "Helvetica"


class PDFReportService:
    """选岗报告 PDF 生成服务"""

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        student_id: int,
        position_ids: List[int],
        year: int,
        exam_type: str,
        education: Optional[str] = None,
        major: Optional[str] = None,
        political_status: Optional[str] = None,
        work_years: int = 0,
        gender: Optional[str] = None,
        city: Optional[str] = None,
        location: Optional[str] = None,
        exam_category: Optional[str] = None,
        funding_source: Optional[str] = None,
        recruitment_target: Optional[str] = None,
        funding_sources: Optional[List[str]] = None,
        recruitment_targets: Optional[List[str]] = None,
        post_natures: Optional[List[str]] = None,
        recommendation_tiers: Optional[List[str]] = None,
        preferred_post_natures: Optional[List[str]] = None,
        excluded_risk_tags: Optional[List[str]] = None,
        recommendation_tier: Optional[str] = None,
        include_manual_review: bool = True,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> BytesIO:
        """生成选岗报告 PDF"""
        _register_fonts()
        font_name = _get_font()

        student = (
            await db.execute(select(Student).where(Student.id == student_id))
        ).scalar_one_or_none()

        positions: list[Position] = []
        if position_ids:
            result = await db.execute(select(Position).where(Position.id.in_(position_ids)))
            positions_by_id = {position.id: position for position in result.scalars().all()}
            positions = [positions_by_id[position_id] for position_id in position_ids if position_id in positions_by_id]

        effective_education = education or (student.education if student else "") or ""
        effective_major = major or (student.major if student else "") or ""
        effective_political_status = (
            political_status
            if political_status is not None
            else (student.political_status if student else None)
        )
        effective_work_years = work_years if work_years else (student.work_years or 0 if student else 0)
        effective_gender = gender if gender is not None else (student.gender if student else None)

        shiye_items: list[Dict[str, Any]] = []
        sort_basis: list[str] = []
        tier_counts = {"冲刺": 0, "稳妥": 0, "保底": 0}

        if exam_type == "事业单位" and positions:
            from app.services.selection.shiye_selection_service import ShiyeSelectionService

            selection_result = await ShiyeSelectionService.search(
                db=db,
                year=year,
                education=effective_education,
                major=effective_major,
                political_status=effective_political_status,
                work_years=effective_work_years,
                gender=effective_gender,
                city=city,
                location=location,
                exam_category=exam_category,
                funding_source=funding_source,
                recruitment_target=recruitment_target,
                funding_sources=funding_sources or [],
                recruitment_targets=recruitment_targets or [],
                post_natures=post_natures or [],
                preferred_post_natures=preferred_post_natures or [],
                excluded_risk_tags=excluded_risk_tags or [],
                recommendation_tiers=recommendation_tiers or [],
                recommendation_tier=recommendation_tier,
                include_manual_review=include_manual_review,
                page=1,
                page_size=50000,
                sort_by=sort_by,
                sort_order=sort_order,
            )
            summary = selection_result.get("summary", {})
            sort_basis = summary.get("sort_basis", [])
            tier_counts["冲刺"] = int(summary.get("sprint_count", 0) or 0)
            tier_counts["稳妥"] = int(summary.get("stable_count", 0) or 0)
            tier_counts["保底"] = int(summary.get("safe_count", 0) or 0)

            selection_map = {
                item["position"].id: item
                for item in selection_result.get("items", [])
            }
            for position in positions:
                selected_item = selection_map.get(position.id)
                if selected_item:
                    shiye_items.append(selected_item)
                    continue
                shiye_items.append(
                    {
                        "position": position,
                        "match_source": "条件匹配",
                        "sort_reasons": ["该岗位不在当前选岗结果页内，按已勾选岗位补充展示"],
                        "recommendation_tier": "稳妥",
                        "recommendation_reasons": ["当前缺少完整排序上下文，默认归入稳妥"],
                    }
                )

        grouped_shiye_items: dict[str, list[Dict[str, Any]]] = {
            "冲刺": [],
            "稳妥": [],
            "保底": [],
        }
        for item in shiye_items:
            tier = item.get("recommendation_tier") or "稳妥"
            if tier not in grouped_shiye_items:
                tier = "稳妥"
            grouped_shiye_items[tier].append(item)

        analyses = []
        if exam_type != "事业单位":
            from app.services.position_analysis_service import PositionAnalysisService

            analyses = [PositionAnalysisService.analyze_position(position) for position in positions]

        # 生成 PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title_CN",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=20,
            spaceAfter=6,
        )
        heading_style = ParagraphStyle(
            "Heading_CN",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#1a73e8"),
        )
        body_style = ParagraphStyle(
            "Body_CN",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=16,
        )
        small_style = ParagraphStyle(
            "Small_CN",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=8,
            textColor=colors.grey,
        )

        story = []

        # ===== 标题 =====
        story.append(Paragraph("智能选岗分析报告", title_style))
        story.append(Paragraph(f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}', small_style))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a73e8")))
        story.append(Spacer(1, 12))

        # ===== 学员信息 =====
        story.append(Paragraph("一、学员基本信息", heading_style))
        if student:
            info_data = [
                ["姓名", student.name or "-", "学历", student.education or "-"],
                ["专业", student.major or "-", "政治面貌", student.political_status or "-"],
                ["基层年限", f"{student.work_years or 0}年", "性别", student.gender or "-"],
                ["目标年份", str(year), "考试类型", exam_type],
            ]
            info_table = RLTable(info_data, colWidths=[3 * cm, 5 * cm, 3 * cm, 5 * cm])
            info_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f0f0f0")),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#333")),
                        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#333")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(info_table)
        story.append(Spacer(1, 16))

        if exam_type == "事业单位":
            # ===== 排序依据 =====
            story.append(Paragraph("二、排序依据", heading_style))
            if sort_basis:
                for idx, basis in enumerate(sort_basis, start=1):
                    story.append(Paragraph(f"{idx}. {basis}", body_style))
            else:
                story.append(Paragraph("暂无排序依据（请检查选岗条件是否完整）", body_style))
            story.append(Spacer(1, 12))

            # ===== 推荐岗位 =====
            story.append(Paragraph(f"三、推荐岗位 ({len(shiye_items)}个)", heading_style))
            story.append(
                Paragraph(
                    f'全量分层统计：冲刺 {tier_counts["冲刺"]}，稳妥 {tier_counts["稳妥"]}，保底 {tier_counts["保底"]}',
                    small_style,
                )
            )

            tier_colors = {
                "冲刺": "#ff4d4f",
                "稳妥": "#52c41a",
                "保底": "#1890ff",
            }
            for tier in ("冲刺", "稳妥", "保底"):
                tier_items = grouped_shiye_items[tier]
                if not tier_items:
                    continue

                story.append(
                    Paragraph(
                        f"【{tier}岗位】",
                        ParagraphStyle(
                            f"tier_{tier}",
                            parent=body_style,
                            fontSize=11,
                            spaceBefore=8,
                            spaceAfter=4,
                            textColor=colors.HexColor(tier_colors[tier]),
                        ),
                    )
                )

                headers = ["单位", "岗位", "地市", "招录", "竞争比", "最低分", "匹配来源"]
                rows = [headers]
                for item in tier_items:
                    position = item["position"]
                    rows.append(
                        [
                            (position.department or "-")[:12],
                            (position.title or "-")[:10],
                            position.city or "-",
                            str(position.recruitment_count or "-"),
                            f"{position.competition_ratio:.0f}:1" if position.competition_ratio else "-",
                            f"{position.min_interview_score:.1f}" if position.min_interview_score else "-",
                            item.get("match_source") or "-",
                        ]
                    )

                pos_table = RLTable(
                    rows,
                    colWidths=[4.2 * cm, 3.2 * cm, 2 * cm, 1.4 * cm, 1.8 * cm, 2 * cm, 2.4 * cm],
                )
                pos_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, -1), font_name),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("ALIGN", (3, 0), (-1, -1), "CENTER"),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd")),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(pos_table)

                for item in tier_items:
                    position = item["position"]
                    reason_segments = (item.get("sort_reasons") or [])[:2] + (item.get("recommendation_reasons") or [])[:2]
                    if reason_segments:
                        story.append(
                            Paragraph(
                                f'{position.title or "岗位"}：{"；".join(reason_segments)}',
                                small_style,
                            )
                        )
                story.append(Spacer(1, 8))
        else:
            # ===== 推荐岗位 =====
            story.append(Paragraph(f"二、推荐岗位 ({len(positions)}个)", heading_style))
            if positions:
                sprint = [(p, a) for p, a in zip(positions, analyses) if a["competition"]["score"] >= 70]
                stable = [(p, a) for p, a in zip(positions, analyses) if 40 <= a["competition"]["score"] < 70]
                safe = [(p, a) for p, a in zip(positions, analyses) if a["competition"]["score"] < 40]

                for category, label, items in [
                    ("sprint", "冲刺岗位", sprint),
                    ("stable", "稳妥岗位", stable),
                    ("safe", "保底岗位", safe),
                ]:
                    if not items:
                        continue

                    story.append(
                        Paragraph(
                            f"【{label}】",
                            ParagraphStyle(
                                f"{category}_style",
                                parent=body_style,
                                fontSize=11,
                                spaceBefore=8,
                                spaceAfter=4,
                                textColor=colors.HexColor(
                                    "#ff4d4f" if category == "sprint" else "#52c41a" if category == "stable" else "#1890ff"
                                ),
                            ),
                        )
                    )

                    headers = ["单位", "岗位", "城市", "招录", "竞争比", "最低分", "性价比"]
                    rows = [headers]
                    for pos, analysis in items:
                        rows.append(
                            [
                                (pos.department or "-")[:12],
                                (pos.title or "-")[:10],
                                pos.city or "-",
                                str(pos.recruitment_count or "-"),
                                f"{pos.competition_ratio:.0f}:1" if pos.competition_ratio else "-",
                                f"{pos.min_interview_score:.1f}" if pos.min_interview_score else "-",
                                f'{analysis["value"]["score"]:.0f}分',
                            ]
                        )

                    pos_table = RLTable(
                        rows,
                        colWidths=[4.5 * cm, 3.5 * cm, 2 * cm, 1.5 * cm, 2 * cm, 2 * cm, 2 * cm],
                    )
                    pos_table.setStyle(
                        TableStyle(
                            [
                                ("FONTNAME", (0, 0), (-1, -1), font_name),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("ALIGN", (3, 0), (-1, -1), "CENTER"),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd")),
                                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                                ("TOPPADDING", (0, 0), (-1, -1), 4),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ]
                        )
                    )
                    story.append(pos_table)
                    story.append(Spacer(1, 8))
            else:
                story.append(Paragraph("暂无推荐岗位", body_style))

        story.append(Spacer(1, 16))

        # ===== 备注 =====
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                "说明: 本报告基于历年公考数据分析生成，仅供参考。"
                "竞争比和分数线数据来源于公开数据，实际情况以官方公布为准。",
                small_style,
            )
        )
        story.append(
            Paragraph(
                f'报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                small_style,
            )
        )

        doc.build(story)
        buffer.seek(0)
        return buffer
