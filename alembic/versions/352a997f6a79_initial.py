"""initial

Revision ID: 352a997f6a79
Revises: 
Create Date: 2025-08-09 11:58:05.460647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = '352a997f6a79'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Create enums first using raw SQL with proper error handling
    op.execute("""
    DO $$
    BEGIN
        -- Create country_code enum if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'country_code') THEN
            CREATE TYPE country_code AS ENUM ('KE');
        END IF;
        
        -- Create game_verdict enum if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'game_verdict') THEN
            CREATE TYPE game_verdict AS ENUM ('0', '1', '2', '3', '4');
        END IF;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Error creating enums: %', SQLERRM;
    END
    $$;
    """)
    
    # Create the enum objects for SQLAlchemy (but don't auto-create them)
    country_code_enum = ENUM('KE', name='country_code', create_type=False)
    game_verdict_enum = ENUM('0', '1', '2', '3', '4', name='game_verdict', create_type=False)
    
    # Create native_chess_profile table
    op.create_table(
        'native_chess_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('foreign_chess_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), server_default='0', nullable=False),
        sa.Column('wins', sa.Integer(), server_default='0', nullable=False),
        sa.Column('loses', sa.Integer(), server_default='0', nullable=False),
        sa.Column('country', country_code_enum, server_default='KE', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['foreign_chess_id'], ['chess_profile_table.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create native_games table
    op.create_table(
        'native_games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('native_chess_profile_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('played_as', sa.String(), nullable=False),
        sa.Column('opponent', sa.String(), nullable=False),
        sa.Column('verdict', game_verdict_enum, nullable=False),
        sa.Column('date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('start_time', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['native_chess_profile_id'], ['native_chess_profile.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables if they exist
    op.drop_table('native_games')
    op.drop_table('native_chess_profile')
    
    # Drop enums with error handling
    op.execute("""
    DO $$
    BEGIN
        DROP TYPE IF EXISTS game_verdict;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Error dropping game_verdict: %', SQLERRM;
    END;
    
    BEGIN
        DROP TYPE IF EXISTS country_code;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Error dropping country_code: %', SQLERRM;
    END;
    $$;
    """)