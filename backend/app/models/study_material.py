from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StudyMaterialTrace(Base):
    __tablename__ = "study_material_traces"

    study_material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("study_materials.id", ondelete="CASCADE"), primary_key=True
    )
    trace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("highlight_traces.id", ondelete="CASCADE"), primary_key=True
    )


class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    material_type: Mapped[str] = mapped_column(String(32), nullable=False)  # flashcard | quiz
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    items_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("UserAccount", back_populates="study_materials")
