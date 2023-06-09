"""initial

Revision ID: 0001
Revises: 
Create Date: 2023-03-14 23:12:34.181919

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "project",
        sa.Column("id", sa.SMALLINT(), nullable=False),
        sa.Column("name", sa.String(length=25), nullable=True),
        sa.Column("created", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("modified", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "imports",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("project_id", sa.SMALLINT(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("created", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], name="project_id_fk", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "team",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("project_id", sa.SMALLINT(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("modified", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], name="project_id_fk", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "name", name="team_unique"),
    )
    op.create_table(
        "team_data",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("review_time", sa.Integer(), nullable=False),
        sa.Column("merge_time", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.SMALLINT(), nullable=False),
        sa.Column("created", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("modified", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], name="project_id_fk", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], name="team_id_fk", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "date", name="team_data_unique"),
    )
    op.create_table(
        "team_stats",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.SMALLINT(), nullable=False),
        sa.Column("created", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("modified", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], name="project_id_fk", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], name="team_id_fk", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id"),
    )
    op.execute("INSERT INTO project (name) VALUES('default');")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("team_stats")
    op.drop_table("team_data")
    op.drop_table("team")
    op.drop_table("imports")
    op.drop_table("project")
    # ### end Alembic commands ###
