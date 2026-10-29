"""initial schema — countries/states/zones/sectors/routes/pitches/sources/
source_observations/crawl_runs (spec Phase 2)

Revision ID: 0001
Revises:
Create Date: 2026-10-25

Design rules (spec):
- UUID primary keys, generated server-side with gen_random_uuid()
- timestamps on every table (created_at/updated_at, tz-aware)
- parent links are NOT NULL and never cascade-delete (NFR-006: never destroy
  historical information)
- PostGIS geometry(Point, 4326) columns are added with raw SQL (no
  geoalchemy2 dependency; shapely is the geometry library in the stack) and
  covered by GIST indexes (NFR-007)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = sa.DateTime(timezone=True)
_NOW = sa.text("now()")
_UUID = sa.Uuid()

_STATUS_CHECK = "status IN ('active', 'closed', 'removed', 'unknown')"
_CRAWL_CHECK = "status IN ('pending', 'running', 'completed', 'failed', 'partial')"


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("updated_at", _TS, nullable=False, server_default=_NOW),
        sa.UniqueConstraint("code", name="uq_countries_code"),
    )

    op.create_table(
        "states",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("country_id", sa.Uuid(), sa.ForeignKey("countries.id"), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("updated_at", _TS, nullable=False, server_default=_NOW),
        sa.UniqueConstraint("country_id", "code", name="uq_states_country_code"),
    )
    op.create_index("ix_states_country_id", "states", ["country_id"])

    op.create_table(
        "zones",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("state_id", sa.Uuid(), sa.ForeignKey("states.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("updated_at", _TS, nullable=False, server_default=_NOW),
        sa.UniqueConstraint("state_id", "slug", name="uq_zones_state_slug"),
    )
    op.create_index("ix_zones_state_id", "zones", ["state_id"])

    op.create_table(
        "sectors",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("zone_id", sa.Uuid(), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("updated_at", _TS, nullable=False, server_default=_NOW),
        sa.UniqueConstraint("zone_id", "slug", name="uq_sectors_zone_slug"),
    )
    op.create_index("ix_sectors_zone_id", "sectors", ["zone_id"])

    op.create_table(
        "routes",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("sector_id", sa.Uuid(), sa.ForeignKey("sectors.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("discipline", sa.Text(), server_default="sport"),
        sa.Column("is_multipitch", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text()),
        sa.Column("length_m", sa.Numeric(6, 1)),
        # Canonical grade (spec: {value, system, normalized} — original always kept)
        sa.Column("grade_value", sa.Text()),
        sa.Column("grade_system", sa.Text()),
        sa.Column("grade_normalized", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("alternative_names", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.Column("created_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("updated_at", _TS, nullable=False, server_default=_NOW),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_routes_status"),
        sa.UniqueConstraint("sector_id", "slug", name="uq_routes_sector_slug"),
    )
    op.create_index("ix_routes_sector_id", "routes", ["sector_id"])
    op.create_index("ix_routes_status", "routes", ["status"])
    op.create_index("ix_routes_name", "routes", ["name"])

    op.create_table(
        "pitches",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("route_id", sa.Uuid(), sa.ForeignKey("routes.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text()),
        sa.Column("grade_value", sa.Text()),
        sa.Column("grade_system", sa.Text()),
        sa.Column("length_m", sa.Numeric(6, 1)),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("updated_at", _TS, nullable=False, server_default=_NOW),
        sa.CheckConstraint("number > 0", name="ck_pitches_number_positive"),
        sa.UniqueConstraint("route_id", "number", name="uq_pitches_route_number"),
    )
    op.create_index("ix_pitches_route_id", "pitches", ["route_id"])

    op.create_table(
        "sources",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("updated_at", _TS, nullable=False, server_default=_NOW),
        sa.UniqueConstraint("name", name="uq_sources_name"),
    )

    op.create_table(
        "source_observations",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), nullable=False),
        # Nullable: an observation exists before entity resolution assigns a
        # canonical route (Phase 6/10).
        sa.Column("route_id", sa.Uuid(), sa.ForeignKey("routes.id")),
        sa.Column("source_entity_id", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("observed_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("source_updated_at", _TS),
        sa.Column("source_name", sa.Text()),
        sa.Column("source_grade", sa.Text()),
        sa.Column("source_length", sa.Text()),
        sa.Column("source_status", sa.Text()),
        sa.Column("normalized_data", postgresql.JSONB()),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("raw_object_key", sa.Text()),
        # Idempotency (spec §28): re-crawling unchanged content inserts nothing.
        sa.UniqueConstraint(
            "source_id", "source_entity_id", "content_hash", name="uq_obs_source_entity_hash"
        ),
    )
    op.create_index("ix_source_observations_route_id", "source_observations", ["route_id"])
    op.create_index("ix_source_observations_source_id", "source_observations", ["source_id"])
    op.create_index("ix_source_observations_observed_at", "source_observations", ["observed_at"])

    op.create_table(
        "crawl_runs",
        sa.Column("id", _UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("geographic_scope", sa.Text(), nullable=False),
        sa.Column("started_at", _TS, nullable=False, server_default=_NOW),
        sa.Column("finished_at", _TS),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("pages_processed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("routes_found", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("routes_changed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("routes_new", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("errors", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("logs", sa.Text()),
        sa.CheckConstraint(_CRAWL_CHECK, name="ck_crawl_runs_status"),
    )
    op.create_index("ix_crawl_runs_source_id", "crawl_runs", ["source_id"])

    # --- PostGIS columns (raw SQL: no geoalchemy2 in the stack, spec §38) ---
    op.execute("ALTER TABLE zones ADD COLUMN location geometry(Point, 4326)")
    op.execute("ALTER TABLE sectors ADD COLUMN location geometry(Point, 4326)")
    op.execute("ALTER TABLE routes ADD COLUMN location geometry(Point, 4326)")
    op.execute(
        "ALTER TABLE source_observations ADD COLUMN source_coordinates geometry(Point, 4326)"
    )

    # Spatial indexes (NFR-007)
    op.execute("CREATE INDEX ix_zones_location_gist ON zones USING GIST (location)")
    op.execute("CREATE INDEX ix_sectors_location_gist ON sectors USING GIST (location)")
    op.execute("CREATE INDEX ix_routes_location_gist ON routes USING GIST (location)")
    op.execute(
        "CREATE INDEX ix_source_observations_coords_gist "
        "ON source_observations USING GIST (source_coordinates)"
    )


def downgrade() -> None:
    op.drop_table("crawl_runs")
    op.drop_table("source_observations")
    op.drop_table("sources")
    op.drop_table("pitches")
    op.drop_table("routes")
    op.drop_table("sectors")
    op.drop_table("zones")
    op.drop_table("states")
    op.drop_table("countries")
