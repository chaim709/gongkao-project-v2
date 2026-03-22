"""Parse and evaluate Jiangsu事业编 free-text constraint signals."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def _normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", "", text).strip()


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _is_meaningful(value: str | None) -> bool:
    normalized = _normalize_text(value)
    return normalized not in {"", "无", "无要求", "不限", "nan", "none"}


def _parse_chinese_year_token(token: str) -> int | None:
    normalized = _normalize_text(token)
    if normalized.isdigit():
        return int(normalized)

    digits = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if normalized in digits:
        return digits[normalized]
    if normalized == "十一":
        return 11
    if normalized == "十二":
        return 12
    return None


@dataclass(frozen=True)
class ConstraintEvaluationResult:
    political_status_pass: bool = True
    work_experience_pass: bool = True
    gender_pass: bool = True
    status: str = "hard_pass"
    political_requirement: str | None = None
    minimum_work_years: int | None = None
    gender_requirement: str | None = None
    degree_required: bool = False
    recruitment_tags: tuple[str, ...] = ()
    display_tags: tuple[str, ...] = ()
    manual_review_tags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "political_status_pass": self.political_status_pass,
            "work_experience_pass": self.work_experience_pass,
            "gender_pass": self.gender_pass,
            "status": self.status,
            "political_requirement": self.political_requirement,
            "minimum_work_years": self.minimum_work_years,
            "gender_requirement": self.gender_requirement,
            "degree_required": self.degree_required,
            "recruitment_tags": list(self.recruitment_tags),
            "display_tags": list(self.display_tags),
            "manual_review_tags": list(self.manual_review_tags),
        }


class ConstraintRules:
    """Structured parser for `其他条件` and `招聘对象`."""

    PARTY_PASS_VALUES = {"中共党员", "中共预备党员", "预备党员", "党员"}
    MALE_HARD_KEYWORDS = ("限男性", "仅限男性", "性别为男")
    FEMALE_HARD_KEYWORDS = ("限女性", "仅限女性", "性别为女")
    MALE_SOFT_KEYWORDS = ("适合男性",)
    FEMALE_SOFT_KEYWORDS = ("适合女性",)
    WORK_YEAR_PATTERNS = (
        r"([一二两三四五六七八九十\d]+)年(?:及以上|以上).{0,12}(?:工作经历|工作经验|相应专业工作经历|本专业工作经历|教学工作经历|法律职业经历|实习)",
        r"具有([一二两三四五六七八九十\d]+)年(?:及以上|以上).{0,12}(?:工作经历|工作经验|相应专业工作经历|本专业工作经历|教学工作经历|法律职业经历|实习)",
    )

    @classmethod
    def evaluate(
        cls,
        student_political_status: str | None = None,
        student_work_years: int = 0,
        student_gender: str | None = None,
        other_requirements: str | None = None,
        recruitment_target: str | None = None,
        position_political_status: str | None = None,
        degree_requirement: str | None = None,
        evaluate_gender: bool = True,
    ) -> ConstraintEvaluationResult:
        constraint_text = "；".join(
            part for part in [position_political_status, other_requirements] if _is_meaningful(part)
        )
        target_text = recruitment_target or ""

        recruitment_tags = cls._parse_recruitment_tags(constraint_text, target_text)
        display_tags = list(recruitment_tags)
        manual_review_tags: list[str] = []

        political_requirement = cls._parse_political_requirement(constraint_text)
        if political_requirement:
            display_tags.append(political_requirement)
        political_status_pass = cls._evaluate_political_status(
            student_political_status,
            political_requirement,
        )

        work_years = cls._parse_minimum_work_years(constraint_text)
        work_experience_pass = True
        if work_years["minimum_work_years"] is not None:
            minimum_work_years = work_years["minimum_work_years"]
            display_tags.append(f"{minimum_work_years}年工作经历")
            work_experience_pass = (student_work_years or 0) >= minimum_work_years
        else:
            minimum_work_years = None
        manual_review_tags.extend(work_years["manual_review_tags"])

        gender_parse = cls._parse_gender_requirement(constraint_text)
        gender_requirement = gender_parse["gender_requirement"]
        if gender_requirement:
            display_tags.append(f"{gender_requirement}性岗位")
        if gender_parse["gender_hint"]:
            display_tags.append(gender_parse["gender_hint"])
        manual_review_tags.extend(gender_parse["manual_review_tags"])
        if evaluate_gender:
            gender_pass = cls._evaluate_gender(student_gender, gender_requirement)
        else:
            gender_pass = True

        degree_required = cls._parse_degree_required(constraint_text, degree_requirement)
        if degree_required:
            display_tags.append("需相应学位")

        certificate_tags = cls._parse_certificate_tags(constraint_text)
        display_tags.extend(certificate_tags)
        manual_review_tags.extend(certificate_tags)

        display_tags = _dedupe(display_tags)
        manual_review_tags = _dedupe(manual_review_tags)

        hard_pass = political_status_pass and work_experience_pass and gender_pass
        status = "hard_pass"
        if not hard_pass:
            status = "hard_fail"
        elif manual_review_tags:
            status = "manual_review_needed"

        return ConstraintEvaluationResult(
            political_status_pass=political_status_pass,
            work_experience_pass=work_experience_pass,
            gender_pass=gender_pass,
            status=status,
            political_requirement=political_requirement,
            minimum_work_years=minimum_work_years,
            gender_requirement=gender_requirement,
            degree_required=degree_required,
            recruitment_tags=tuple(recruitment_tags),
            display_tags=tuple(display_tags),
            manual_review_tags=tuple(manual_review_tags),
        )

    @classmethod
    def _parse_political_requirement(cls, text: str) -> str | None:
        normalized = _normalize_text(text)
        if "中共党员" in normalized or "党员" in normalized:
            return "中共党员"
        if "共青团员" in normalized:
            return "共青团员"
        return None

    @classmethod
    def _evaluate_political_status(
        cls,
        student_political_status: str | None,
        political_requirement: str | None,
    ) -> bool:
        if not political_requirement:
            return True
        if political_requirement == "中共党员":
            return (student_political_status or "") in cls.PARTY_PASS_VALUES
        return (student_political_status or "") == political_requirement

    @classmethod
    def _parse_minimum_work_years(cls, text: str) -> dict:
        normalized = _normalize_text(text)
        values: list[int] = []
        for pattern in cls.WORK_YEAR_PATTERNS:
            for match in re.findall(pattern, normalized):
                parsed = _parse_chinese_year_token(match)
                if parsed is not None:
                    values.append(parsed)
        unique_values = sorted(set(values))

        if len(unique_values) > 1:
            return {
                "minimum_work_years": None,
                "manual_review_tags": ["复杂工作年限要求"],
            }
        if len(unique_values) == 1:
            return {
                "minimum_work_years": unique_values[0],
                "manual_review_tags": [],
            }
        return {
            "minimum_work_years": None,
            "manual_review_tags": [],
        }

    @classmethod
    def _parse_gender_requirement(cls, text: str) -> dict:
        normalized = _normalize_text(text)
        has_male = any(keyword in normalized for keyword in cls.MALE_HARD_KEYWORDS)
        has_female = any(keyword in normalized for keyword in cls.FEMALE_HARD_KEYWORDS)
        gender_hint = None
        manual_review_tags: list[str] = []

        if "适合男性" in normalized:
            gender_hint = "适合男性"
        if "适合女性" in normalized:
            gender_hint = "适合女性"

        if has_male and not has_female:
            return {
                "gender_requirement": "男",
                "gender_hint": gender_hint,
                "manual_review_tags": manual_review_tags,
            }
        if has_female and not has_male:
            return {
                "gender_requirement": "女",
                "gender_hint": gender_hint,
                "manual_review_tags": manual_review_tags,
            }
        if has_male and has_female:
            manual_review_tags.append("复杂性别要求")
        return {
            "gender_requirement": None,
            "gender_hint": gender_hint,
            "manual_review_tags": manual_review_tags,
        }

    @classmethod
    def _evaluate_gender(
        cls,
        student_gender: str | None,
        gender_requirement: str | None,
    ) -> bool:
        if not gender_requirement:
            return True
        return (student_gender or "") == gender_requirement

    @classmethod
    def _parse_recruitment_tags(
        cls,
        constraint_text: str,
        recruitment_target: str,
    ) -> list[str]:
        combined = f"{constraint_text}；{recruitment_target}"
        normalized = _normalize_text(combined)
        tags: list[str] = []

        year_graduate_matches = re.findall(r"(\d{4})年毕业生", normalized)
        for year in year_graduate_matches:
            tags.append(f"{year}年毕业生")

        if "应届毕业生" in normalized or "普通高校应届毕业生" in normalized:
            tags.append("应届毕业生")
        if "社会人员" in normalized:
            tags.append("社会人员")
        if "退役大学生士兵" in normalized:
            tags.append("退役大学生士兵")
        if "高校毕业生退役士兵" in normalized:
            tags.append("高校毕业生退役士兵")
        if "退役军人" in normalized:
            tags.append("退役军人")
        if "残疾人" in normalized:
            tags.append("残疾人岗位")

        return _dedupe(tags)

    @classmethod
    def _parse_degree_required(
        cls,
        constraint_text: str,
        degree_requirement: str | None,
    ) -> bool:
        return _is_meaningful(degree_requirement) or "学位" in _normalize_text(constraint_text)

    @classmethod
    def _parse_certificate_tags(cls, text: str) -> list[str]:
        normalized = _normalize_text(text)
        tags: list[str] = []
        if "教师资格" in normalized:
            tags.append("教师资格证要求")
        if "法律职业资格" in normalized or "法考" in normalized:
            tags.append("法律职业资格要求")
        if "职称" in normalized:
            tags.append("职称要求")
        return tags
