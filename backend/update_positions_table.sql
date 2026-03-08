-- 手动更新positions表，添加选岗系统需要的字段

-- 添加新字段
ALTER TABLE positions ADD COLUMN IF NOT EXISTS city VARCHAR(50);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS position_code VARCHAR(50);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS exam_category VARCHAR(20);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS apply_count INTEGER;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS competition_ratio FLOAT;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS estimated_competition_ratio FLOAT;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS difficulty_level VARCHAR(20);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_position_city_year ON positions(city, year);
CREATE INDEX IF NOT EXISTS ix_positions_estimated_competition_ratio ON positions(estimated_competition_ratio);

-- 更新现有字段长度
ALTER TABLE positions ALTER COLUMN education TYPE VARCHAR(100);
ALTER TABLE positions ALTER COLUMN exam_type TYPE VARCHAR(50);
