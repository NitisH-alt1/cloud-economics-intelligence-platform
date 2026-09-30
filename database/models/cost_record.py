import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class CostRecord(Base):
    __tablename__ = "cost_records"
    __table_args__ = (
        UniqueConstraint("project_id", "cloud_account_id", "service", "usage_date", name="uq_demo_cost_period"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    cloud_account_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cloud_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    service: Mapped[str] = mapped_column(String(80), nullable=False)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    usage_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="local-demo")
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="demo")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
