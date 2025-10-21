-- Initial Database Schema for S3DA2 SAFE-BMAD System
-- Migration 001: Core tables for agents, plans, and tasks
-- Created: 2025-10-21

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================
-- AGENT MANAGEMENT TABLES
-- =====================================

-- Agent status table (supports AutoGen multi-agent framework)
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('s', 'a', 'f', 'e', 'r')),
    status VARCHAR(20) NOT NULL DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'busy', 'error')),
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Agent execution logs
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    execution_id VARCHAR(255) NOT NULL,
    level VARCHAR(10) NOT NULL CHECK (level IN ('debug', 'info', 'warning', 'error')),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- WORKFLOW AND PLAN MANAGEMENT TABLES
-- =====================================

-- Plan instances table (supports SOP workflow)
CREATE TABLE IF NOT EXISTS plan_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_template_source VARCHAR(255),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'running', 'completed', 'failed', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Task information table (Plan Tool Model)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    plan_id UUID REFERENCES plan_instances(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    assignee VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    estimated_hours INTEGER,
    actual_hours INTEGER,
    result_summary TEXT,
    result_details JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Task dependencies table
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) DEFAULT 'finish_to_start' CHECK (dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, depends_on_task_id)
);

-- =====================================
-- WORKFLOW EXECUTION TABLES
-- =====================================

-- Workflow execution tracking
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES plan_instances(id) ON DELETE CASCADE,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT,
    execution_context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow step executions
CREATE TABLE IF NOT EXISTS workflow_step_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(20),
    agent_id UUID REFERENCES agents(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- SYSTEM CONFIGURATION TABLES
-- =====================================

-- System configuration
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- AUDIT AND LOGGING TABLES
-- =====================================

-- Audit log
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    action VARCHAR(50) NOT NULL,
    old_values JSONB DEFAULT '{}',
    new_values JSONB DEFAULT '{}',
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- INDEXES FOR PERFORMANCE
-- =====================================

-- Agent indexes
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);

-- Plan instances indexes
CREATE INDEX IF NOT EXISTS idx_plan_instances_status ON plan_instances(status);
CREATE INDEX IF NOT EXISTS idx_plan_instances_created_at ON plan_instances(created_at);
CREATE INDEX IF NOT EXISTS idx_plan_instances_priority ON plan_instances(priority);

-- Tasks indexes
CREATE INDEX IF NOT EXISTS idx_tasks_plan_id ON tasks(plan_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);

-- Workflow execution indexes
CREATE INDEX IF NOT EXISTS idx_workflow_executions_plan_id ON workflow_executions(plan_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_execution_id ON workflow_executions(execution_id);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

-- =====================================
-- TRIGGERS AND FUNCTIONS
-- =====================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plan_instances_updated_at BEFORE UPDATE ON plan_instances FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON workflow_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_step_executions_updated_at BEFORE UPDATE ON workflow_step_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================
-- INSERT DEFAULT DATA
-- =====================================

-- Default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('system.name', '"S3DA2 SAFE-BMAD"', 'System display name'),
('system.version', '"1.0.0"', 'System version'),
('system.environment', '"development"', 'Current environment'),
('workflow.max_parallel_tasks', '5', 'Maximum number of parallel tasks'),
('workflow.default_timeout_minutes', '60', 'Default workflow timeout in minutes'),
('agent.max_retries', '3', 'Maximum retry attempts for agents'),
('logging.level', '"INFO"', 'Default logging level')
ON CONFLICT (config_key) DO NOTHING;

-- Default agent types and configurations
INSERT INTO agents (name, type, status, configuration, capabilities) VALUES
('StrategyAgent', 's', 'active',
 '{"model": "deepseek-chat", "temperature": 0.7, "max_tokens": 2000}',
 '["strategic_planning", "analysis", "decision_support"]'
),
('AnalysisAgent', 'a', 'active',
 '{"model": "deepseek-chat", "temperature": 0.3, "max_tokens": 1500}',
 '["data_analysis", "situational_awareness", "risk_assessment"]'
),
('FocusAgent', 'f', 'active',
 '{"model": "deepseek-chat", "temperature": 0.5, "max_tokens": 1800}',
 '["expert_analysis", "domain_knowledge", "specialized_insights"]'
),
('ExecutionAgent', 'e', 'active',
 '{"model": "deepseek-chat", "temperature": 0.2, "max_tokens": 2500}',
 '["task_execution", "implementation", "coordination"]'
),
('EvaluationAgent', 'r', 'active',
 '{"model": "deepseek-chat", "temperature": 0.4, "max_tokens": 1200}',
 '["evaluation", "quality_assessment", "feedback_generation"]'
)
ON CONFLICT (name) DO NOTHING;

COMMIT;