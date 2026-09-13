-- CodeSense Supabase PostgreSQL Schema

-- 1. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Analysis Runs Table
CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'queued', -- queued, analyzing, scoring, done, failed
    overall_score NUMERIC(5, 2),
    total_loc INTEGER DEFAULT 0,
    total_complexity NUMERIC(8, 2) DEFAULT 0,
    bug_probability NUMERIC(4, 3) DEFAULT 0,
    tech_debt_minutes INTEGER DEFAULT 0,
    error_message TEXT,
    summary JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 3. File Metrics Table
CREATE TABLE IF NOT EXISTS file_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    loc INTEGER NOT NULL,
    cyclomatic_complexity NUMERIC(6, 2) NOT NULL,
    maintainability_index NUMERIC(5, 2) NOT NULL,
    duplication_pct NUMERIC(5, 2) NOT NULL DEFAULT 0,
    cbo INTEGER NOT NULL DEFAULT 0,
    lcom INTEGER NOT NULL DEFAULT 0,
    dit INTEGER NOT NULL DEFAULT 0,
    noc INTEGER NOT NULL DEFAULT 0,
    comment_density NUMERIC(5, 2) NOT NULL DEFAULT 0,
    bug_probability NUMERIC(4, 3) NOT NULL DEFAULT 0,
    smells_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Defects Table
CREATE TABLE IF NOT EXISTS defects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    rule_id VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL, -- info, warning, error, critical
    tool VARCHAR(50) NOT NULL, -- radon, pylint, bandit, eslint
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    suggested_fix TEXT,
    file_path TEXT,
    impact VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_project_id ON analysis_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_file_metrics_run_id ON file_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_defects_run_id ON defects(run_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_run_id ON recommendations(run_id);
