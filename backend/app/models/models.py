from datetime import datetime
from decimal import Decimal as PyDecimal

from sqlalchemy import Boolean, CHAR, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    users: Mapped[list["User"]] = relationship(back_populates="college")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_account", "account"),
        Index("idx_users_role", "role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    college_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("colleges.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    need_change_pwd: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_invalid_before: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    college: Mapped["College | None"] = relationship(back_populates="users")
    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    activity_owner: Mapped["ActivityOwner | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    owned_activities: Mapped[list["Activity"]] = relationship(back_populates="owner")
    participations: Mapped[list["Participation"]] = relationship(back_populates="user")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    credit_records: Mapped[list["CreditAccumulation"]] = relationship(back_populates="user")
    published_announcements: Mapped[list["Announcement"]] = relationship(back_populates="publisher")
    operation_logs: Mapped[list["OperationLog"]] = relationship(back_populates="user")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        Index("idx_students_student_id", "student_id"),
    )

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    student_id: Mapped[str] = mapped_column(CHAR(11), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    user: Mapped["User"] = relationship(back_populates="student")


class ActivityOwner(Base):
    __tablename__ = "activity_owners"
    __table_args__ = (
        Index("idx_owners_type", "owner_type"),
    )

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    owner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_name: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_student_id: Mapped[str] = mapped_column(CHAR(11), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    advisor_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    advisor_contact: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pending_contact: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    user: Mapped["User"] = relationship(back_populates="activity_owner")


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        Index("idx_activities_status", "status"),
        Index("idx_activities_owner", "owner_id"),
        Index("idx_activities_deadline", "registration_deadline"),
        Index("idx_activities_credit_type", "credit_type"),
        Index("idx_activities_activity_type", "activity_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    activity_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    credit_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    credit_value: Mapped[PyDecimal | None] = mapped_column(Numeric(3, 1), nullable=True, default=None)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    owner: Mapped["User"] = relationship(back_populates="owned_activities")
    images: Mapped[list["ActivityImage"]] = relationship(back_populates="activity", cascade="all, delete-orphan")
    qrcode: Mapped["ActivityQrcode | None"] = relationship(back_populates="activity", uselist=False, cascade="all, delete-orphan")
    participations: Mapped[list["Participation"]] = relationship(back_populates="activity")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="activity")
    reviews: Mapped[list["Review"]] = relationship(back_populates="activity")


class ActivityImage(Base):
    __tablename__ = "activity_images"
    __table_args__ = (
        Index("idx_images_activity", "activity_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_cover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    activity: Mapped["Activity"] = relationship(back_populates="images")


class ActivityQrcode(Base):
    __tablename__ = "activity_qrcodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    activity: Mapped["Activity"] = relationship(back_populates="qrcode")


class Participation(Base):
    __tablename__ = "participations"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_id"),
        Index("idx_participations_user", "user_id"),
        Index("idx_participations_activity", "activity_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    credit_awarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="participations")
    activity: Mapped["Activity"] = relationship(back_populates="participations")
    credit_records: Mapped[list["CreditAccumulation"]] = relationship(back_populates="participation")


class CreditAccumulation(Base):
    __tablename__ = "credit_accumulation"
    __table_args__ = (
        Index("idx_credits_user", "user_id"),
        Index("idx_credits_type", "credit_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    participation_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("participations.id", ondelete="SET NULL"), nullable=True)
    credit_type: Mapped[str] = mapped_column(String(20), nullable=False)
    credit_value: Mapped[PyDecimal] = mapped_column(Numeric(3, 1), nullable=False)
    activity_title: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_year: Mapped[str | None] = mapped_column(String(9), nullable=True, comment="学年，如 2025-2026")
    earned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="credit_records")
    participation: Mapped["Participation | None"] = relationship(back_populates="credit_records")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_id"),
        Index("idx_favorites_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="favorites")
    activity: Mapped["Activity"] = relationship(back_populates="favorites")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_id"),
        Index("idx_reviews_activity", "activity_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="reviews")
    activity: Mapped["Activity"] = relationship(back_populates="reviews")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user", "user_id", "is_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    link_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    link_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    node_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="notifications")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    publisher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    publisher: Mapped["User"] = relationship(back_populates="published_announcements")


class OperationLog(Base):
    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("idx_logs_user", "user_id"),
        Index("idx_logs_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    user: Mapped["User | None"] = relationship(back_populates="operation_logs")



class SchedulerState(Base):
    __tablename__ = "scheduler_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Banner(Base):
    __tablename__ = "banners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
