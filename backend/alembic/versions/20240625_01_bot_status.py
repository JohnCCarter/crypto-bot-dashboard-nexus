from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240625_01_bot_status'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'bot_status',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('running', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('start_time', sa.Float),
        sa.Column('last_update', sa.DateTime),
        sa.Column('cycle_count', sa.Integer, server_default='0'),
        sa.Column('last_cycle_time', sa.DateTime),
        sa.Column('error', sa.String(length=255)),
    )


def downgrade():
    op.drop_table('bot_status')