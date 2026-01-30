from sqlalchemy import Column, String, DateTime, UniqueConstraint, UUID
from sqlalchemy.sql import func
from app.core.database import Base # Assuming your Base is defined in database.py
import uuid

class IngestionSource(Base):
    __tablename__ = "ingestion_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True) 
    source_id = Column(String, nullable=False) # video_id or filename
    source_type = Column(String, nullable=False) # 'video' or 'pdf'
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure a user can't have duplicate source_ids
    __table_args__ = (
        UniqueConstraint('user_id', 'source_id', name='_user_source_uc'),
    )