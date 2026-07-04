"""ORM models for the batch processing domain.

A ``Batch`` is a unit of work submitted by a client, made up of one or more
``BatchItem`` rows. The worker claims individual items (not whole batches)
so that partial progress and partial failure are both representable.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base


class BatchStatus(enum.StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class ItemStatus(enum.StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status", native_enum=True, validate_strings=True),
        nullable=False,
        default=BatchStatus.PENDING,
        index=True,
    )
    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    items: Mapped[list["BatchItem"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class BatchItem(Base):
    __tablename__ = "batch_items"
    __table_args__ = (
        # Powers the worker's poll query (WHERE status = 'PENDING' ...).
        Index("ix_batch_items_status", "status"),
        # Powers per-batch progress/count queries.
        Index("ix_batch_items_batch_id_status", "batch_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, name="item_status", native_enum=True, validate_strings=True),
        nullable=False,
        default=ItemStatus.PENDING,
    )
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    batch: Mapped["Batch"] = relationship(back_populates="items")
