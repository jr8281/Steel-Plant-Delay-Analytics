"""Initial PostgreSQL schema for steel plant delay analytics."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("shops", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("shop_code", sa.String(length=10), nullable=False), sa.Column("name", sa.String(length=80), nullable=False), sa.UniqueConstraint("shop_code"), sa.UniqueConstraint("name"))
    op.create_index("ix_shops_shop_code", "shops", ["shop_code"])
    op.create_table("equipment", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(length=100), nullable=False), sa.UniqueConstraint("name"))
    op.create_table("agencies", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(length=10), nullable=False), sa.Column("description", sa.String(length=200)), sa.UniqueConstraint("code"))
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(length=50), nullable=False), sa.Column("hashed_password", sa.String(length=255), nullable=False), sa.Column("role", sa.String(length=20), nullable=False), sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id"), nullable=True), sa.UniqueConstraint("username"))
    op.create_index("ix_users_username", "users", ["username"])
    op.create_table("delay_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("delay_date", sa.Date(), nullable=False), sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id"), nullable=False), sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("equipment.id"), nullable=True), sa.Column("agency_id", sa.Integer(), sa.ForeignKey("agencies.id"), nullable=False), sa.Column("sub_eqpt", sa.String(length=100)), sa.Column("from_time", sa.Float()), sa.Column("upto_time", sa.Float()), sa.Column("durn", sa.Float(), nullable=False), sa.Column("eff_durn", sa.Float(), nullable=False), sa.Column("cum_delay", sa.Float(), nullable=False, server_default="0"), sa.Column("freq", sa.Integer(), nullable=False, server_default="1"), sa.Column("descr", sa.String(length=500)), sa.Column("material", sa.String(length=100)), sa.Column("delay_code", sa.String(length=30)), sa.Column("contd", sa.String(length=5)), sa.Column("close_dt", sa.Date()), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_delay_events_delay_date", "delay_events", ["delay_date"])
    op.create_index("ix_delay_events_shop_id", "delay_events", ["shop_id"])
    op.create_index("ix_delay_events_equipment_id", "delay_events", ["equipment_id"])
    op.create_index("ix_delay_events_agency_id", "delay_events", ["agency_id"])


def downgrade() -> None:
    op.drop_table("delay_events")
    op.drop_table("users")
    op.drop_table("agencies")
    op.drop_table("equipment")
    op.drop_table("shops")
