from pydantic import BaseModel, Field, model_validator


class ShiyeTierThresholdSettings(BaseModel):
    competition_low_percentile: float = Field(0.35, ge=0, le=1)
    competition_high_percentile: float = Field(0.70, ge=0, le=1)
    score_low_percentile: float = Field(0.35, ge=0, le=1)
    score_high_percentile: float = Field(0.70, ge=0, le=1)
    stable_min_score: float = Field(32.0, ge=0, le=100)
    sprint_min_score: float = Field(60.0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_threshold_relationships(self):
        if self.competition_high_percentile <= self.competition_low_percentile:
            raise ValueError("竞争比高位分位值必须大于中位分位值")
        if self.score_high_percentile <= self.score_low_percentile:
            raise ValueError("分数线高位分位值必须大于中位分位值")
        if self.sprint_min_score <= self.stable_min_score:
            raise ValueError("冲刺分界线必须大于稳妥分界线")
        return self
