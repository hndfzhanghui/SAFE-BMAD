"""Create initial database schema

Revision ID: 0001
Revises:
Create Date: 2025-10-21 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database tables."""

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create scenarios table
    op.create_table('scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.String(length=10), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('emergency_type', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenarios_created_at'), 'scenarios', ['created_at'], unique=False)
    op.create_index(op.f('ix_scenarios_priority'), 'scenarios', ['priority'], unique=False)
    op.create_index(op.f('ix_scenarios_status'), 'scenarios', ['status'], unique=False)

    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('last_activity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_name', sa.String(length=50), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_created_at'), 'agents', ['created_at'], unique=False)
    op.create_index(op.f('ix_agents_scenario_id'), 'agents', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_agents_status'), 'agents', ['status'], unique=False)
    op.create_index(op.f('ix_agents_type'), 'agents', ['type'], unique=False)

    # Create resources table
    op.create_table('resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('location', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('specifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('allocation_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('contact_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resources_created_at'), 'resources', ['created_at'], unique=False)
    op.create_index(op.f('ix_resources_scenario_id'), 'resources', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_resources_status'), 'resources', ['status'], unique=False)
    op.create_index(op.f('ix_resources_type'), 'resources', ['type'], unique=False)

    # Create analysis table
    op.create_table('analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('methodology', sa.String(length=100), nullable=True),
        sa.Column('processing_time', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_agent_id'), 'analysis', ['agent_id'], unique=False)
    op.create_index(op.f('ix_analysis_confidence_score'), 'analysis', ['confidence_score'], unique=False)
    op.create_index(op.f('ix_analysis_created_at'), 'analysis', ['created_at'], unique=False)
    op.create_index(op.f('ix_analysis_scenario_id'), 'analysis', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_analysis_type'), 'analysis', ['type'], unique=False)

    # Create decisions table
    op.create_table('decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('decision_type', sa.String(length=50), nullable=False),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendation', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('rationale', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_level', sa.String(length=20), nullable=True),
        sa.Column('implemented_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis.id'], ),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_created_at'), 'decisions', ['created_at'], unique=False)
    op.create_index(op.f('ix_decisions_scenario_id'), 'decisions', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_decisions_status'), 'decisions', ['status'], unique=False)
    op.create_index(op.f('ix_decisions_user_id'), 'decisions', ['user_id'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('receiver_id', sa.Integer(), nullable=True),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['receiver_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_messages_scenario_id'), 'messages', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_messages_sender_id'), 'messages', ['sender_id'], unique=False)
    op.create_index(op.f('ix_messages_status'), 'messages', ['status'], unique=False)

    # Create user_scenario association table
    op.create_table('user_scenarios',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'scenario_id')
    )
    op.create_index(op.f('ix_user_scenarios_is_active'), 'user_scenarios', ['is_active'], unique=False)
    op.create_index(op.f('ix_user_scenarios_scenario_id'), 'user_scenarios', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_user_scenarios_user_id'), 'user_scenarios', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('user_scenarios')
    op.drop_table('messages')
    op.drop_table('decisions')
    op.drop_table('analysis')
    op.drop_table('resources')
    op.drop_table('agents')
    op.drop_table('scenarios')
    op.drop_table('users')