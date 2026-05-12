"""完整初始建表（合并所有历史迁移）

合并了从 v1 到系统配置模块的所有表结构变更。
适用于全新部署时一条命令建完所有表。

Revision ID: 20260512_initial_schema
Revises:
Create Date: 2026-05-12 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import bcrypt
from sqlalchemy.dialects.mysql import JSON

revision: str = "20260512_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. 学院 ---
    op.create_table(
        "colleges",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- 2. 用户 ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("account", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("college_id", sa.Integer(), sa.ForeignKey("colleges.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("need_change_pwd", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("token_invalid_before", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_users_account", "users", ["account"])
    op.create_index("idx_users_role", "users", ["role"])

    # --- 3. 学生 ---
    op.create_table(
        "students",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("student_id", sa.CHAR(11), nullable=False, unique=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_students_student_id", "students", ["student_id"])

    # --- 4. 活动主体 ---
    op.create_table(
        "activity_owners",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("owner_type", sa.String(20), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("contact_name", sa.String(50), nullable=False),
        sa.Column("contact_student_id", sa.CHAR(11), nullable=False),
        sa.Column("contact_phone", sa.String(20), nullable=False),
        sa.Column("advisor_name", sa.String(50), nullable=True),
        sa.Column("advisor_contact", sa.String(50), nullable=True),
        sa.Column("pending_contact", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_owners_type", "activity_owners", ["owner_type"])

    # --- 5. 活动 ---
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("activity_type", sa.String(20), nullable=True),
        sa.Column("credit_type", sa.String(20), nullable=True),
        sa.Column("credit_value", sa.Numeric(3, 1), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("registration_deadline", sa.DateTime(), nullable=True),
        sa.Column("max_participants", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("reject_reason", sa.String(500), nullable=True),
        sa.Column("participant_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_activities_status", "activities", ["status"])
    op.create_index("idx_activities_owner", "activities", ["owner_id"])
    op.create_index("idx_activities_deadline", "activities", ["registration_deadline"])
    op.create_index("idx_activities_credit_type", "activities", ["credit_type"])
    op.create_index("idx_activities_activity_type", "activities", ["activity_type"])

    # --- 6. 活动图片 ---
    op.create_table(
        "activity_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_images_activity", "activity_images", ["activity_id"])

    # --- 7. 活动二维码 ---
    op.create_table(
        "activity_qrcodes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- 8. 参与记录 ---
    op.create_table(
        "participations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("credit_awarded", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("idx_participations_user", "participations", ["user_id"])
    op.create_index("idx_participations_activity", "participations", ["activity_id"])
    op.create_unique_constraint("uq_participations_user_activity", "participations", ["user_id", "activity_id"])

    # --- 9. 学分积累 ---
    op.create_table(
        "credit_accumulation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("participation_id", sa.Integer(), sa.ForeignKey("participations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("credit_type", sa.String(20), nullable=False),
        sa.Column("credit_value", sa.Numeric(3, 1), nullable=False),
        sa.Column("activity_title", sa.String(200), nullable=False),
        sa.Column("academic_year", sa.String(9), nullable=True, comment="学年，如 2025-2026"),
        sa.Column("earned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_credits_user", "credit_accumulation", ["user_id"])
    op.create_index("idx_credits_type", "credit_accumulation", ["credit_type"])

    # --- 10. 收藏 ---
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_favorites_user", "favorites", ["user_id"])
    op.create_unique_constraint("uq_favorites_user_activity", "favorites", ["user_id", "activity_id"])

    # --- 11. 评价 ---
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_reviews_activity", "reviews", ["activity_id"])
    op.create_unique_constraint("uq_reviews_user_activity", "reviews", ["user_id", "activity_id"])

    # --- 12. 通知 ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("link_type", sa.String(50), nullable=True),
        sa.Column("link_id", sa.Integer(), nullable=True),
        sa.Column("node_type", sa.String(10), nullable=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_notifications_user", "notifications", ["user_id", "is_read"])

    # --- 13. 公告 ---
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("publisher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # --- 14. 操作日志 ---
    op.create_table(
        "operation_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_logs_user", "operation_logs", ["user_id"])
    op.create_index("idx_logs_created", "operation_logs", ["created_at"])

    # --- 15. 调度器状态 ---
    op.create_table(
        "scheduler_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_name", sa.String(50), nullable=False, unique=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("extra_data", JSON(), nullable=True),
    )

    # --- 16. 轮播图 ---
    op.create_table(
        "banners",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("subtitle", sa.String(200), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── 种子数据 ─────────────────────────────────────

    # 1. 学院字典（12 个预设学院）
    colleges = [
        "基础医学院",
        "第一临床医学院",
        "第二临床医学院（全科医学院）",
        "医学技术学院",
        "护理学院",
        "药学院",
        "公共卫生学院",
        "妇儿医学院",
        "海洋与热带医学学院",
        "人文与管理学院",
        "生物医学工程学院(未来技术学院）",
        "外国语学院",
    ]
    for name in colleges:
        op.execute(f"INSERT IGNORE INTO colleges (name) VALUES ('{name}')")

    # 2. 测试用户（4 个）
    student_hash = bcrypt.hashpw(b"nr0oteK8", bcrypt.gensalt()).decode()
    owner_hash = bcrypt.hashpw(b"123456aa", bcrypt.gensalt()).decode()
    superadmin_hash = bcrypt.hashpw(b"super123", bcrypt.gensalt()).decode()
    admin_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()

    op.execute(f"""
        INSERT INTO users (account, password_hash, role, name, college_id, status, need_change_pwd, created_at, updated_at)
        VALUES
        ('12345678921', '{student_hash}', 'student', '测试学生', 1, 'active', FALSE, NOW(), NOW()),
        ('aaaa', '{owner_hash}', 'activity_owner', '测试社团', NULL, 'active', FALSE, NOW(), NOW()),
        ('superadmin', '{superadmin_hash}', 'super_admin', '超级管理员', NULL, 'active', FALSE, NOW(), NOW()),
        ('admin', '{admin_hash}', 'admin', '普通管理员', NULL, 'active', FALSE, NOW(), NOW())
        ON DUPLICATE KEY UPDATE account = account
    """)

    # 3. 学生扩展
    op.execute("""
        INSERT INTO students (user_id, student_id, name, phone, email, created_at, updated_at)
        SELECT u.id, u.account, u.name, '13800138000', 'student@example.com', NOW(), NOW()
        FROM users u WHERE u.account = '12345678921'
        AND NOT EXISTS (SELECT 1 FROM students s WHERE s.user_id = u.id)
    """)

    # 4. 活动主体扩展
    op.execute("""
        INSERT INTO activity_owners (user_id, owner_type, bio,
            contact_name, contact_student_id, contact_phone, advisor_name, advisor_contact,
            created_at, updated_at)
        SELECT u.id, '社团', '这是一个测试社团，用于演示活动发布、审核等完整流程。',
               '张三', '20230101005', '13800138001', '李老师', '13900139000',
               NOW(), NOW()
        FROM users u WHERE u.account = 'aaaa'
        AND NOT EXISTS (SELECT 1 FROM activity_owners o WHERE o.user_id = u.id)
    """)

    # 5. 示例活动
    op.execute("""
        INSERT INTO activities (owner_id, title, activity_type, credit_type, credit_value,
                                start_time, end_time, location, registration_deadline,
                                max_participants, description, status, participant_count,
                                created_at, updated_at)
        SELECT u.id, '志愿服务进社区', '志愿活动', '志愿公益', 0.5,
               DATE_ADD(NOW(), INTERVAL 21 DAY), DATE_ADD(NOW(), INTERVAL 21 DAY),
               '阳光社区党群服务中心', DATE_ADD(NOW(), INTERVAL 7 DAY),
               30, '组织同学前往阳光社区开展环境卫生整治、关爱空巢老人等志愿服务。',
               'active', 0, NOW(), NOW()
        FROM users u WHERE u.account = 'aaaa'
        AND NOT EXISTS (
            SELECT 1 FROM activities a
            WHERE a.title = '志愿服务进社区' AND a.owner_id = u.id
        )
    """)
    op.execute("""
        INSERT INTO activities (owner_id, title, activity_type, credit_type, credit_value,
                                start_time, end_time, location, registration_deadline,
                                max_participants, description, status, participant_count,
                                created_at, updated_at)
        SELECT u.id, '医学前沿讲座——AI在医疗中的应用', '讲座', '技能特长', 0.2,
               DATE_ADD(NOW(), INTERVAL 30 DAY), DATE_ADD(NOW(), INTERVAL 30 DAY),
               '学术报告厅', DATE_ADD(NOW(), INTERVAL 10 DAY),
               100, '邀请知名专家讲解人工智能技术在医疗诊断、药物研发等领域的最新进展。',
               'active', 0, NOW(), NOW()
        FROM users u WHERE u.account = 'aaaa'
        AND NOT EXISTS (
            SELECT 1 FROM activities a
            WHERE a.title LIKE '%医学前沿讲座%' AND a.owner_id = u.id
        )
    """)

    # 6. 示例轮播图
    op.execute("""
        INSERT INTO banners (title, subtitle, image_url, sort_order, is_active)
        SELECT '欢迎来到校园活动信息港', '探索丰富多彩的第二课堂活动', '', 0, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM banners WHERE title = '欢迎来到校园活动信息港')
    """)
    op.execute("""
        INSERT INTO banners (title, subtitle, image_url, sort_order, is_active)
        SELECT '发现你的兴趣', '参与社团活动，结识志同道合的朋友', '', 1, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM banners WHERE title = '发现你的兴趣')
    """)


def downgrade() -> None:
    # 删除种子数据（保留学院字典）
    op.execute("DELETE FROM announcements")
    op.execute("DELETE FROM notifications")
    op.execute("DELETE FROM operation_logs")
    op.execute("DELETE FROM credit_accumulation")
    op.execute("DELETE FROM participations")
    op.execute("DELETE FROM favorites")
    op.execute("DELETE FROM reviews")
    op.execute("DELETE FROM activity_qrcodes")
    op.execute("DELETE FROM activity_images")
    op.execute("DELETE FROM activities WHERE owner_id = (SELECT id FROM users WHERE account = 'aaaa')")
    op.execute("DELETE FROM activity_owners WHERE user_id = (SELECT id FROM users WHERE account = 'aaaa')")
    op.execute("DELETE FROM students WHERE user_id = (SELECT id FROM users WHERE account = '12345678921')")
    op.execute("DELETE FROM users WHERE account IN ('12345678921', 'aaaa', 'superadmin', 'admin')")
    op.execute("DELETE FROM banners WHERE title IN ('欢迎来到校园活动信息港', '发现你的兴趣')")
    op.drop_table("banners")
    op.drop_table("scheduler_state")
    op.drop_index("idx_logs_created", table_name="operation_logs")
    op.drop_index("idx_logs_user", table_name="operation_logs")
    op.drop_table("operation_logs")
    op.drop_table("announcements")
    op.drop_index("idx_notifications_user", table_name="notifications")
    op.drop_table("notifications")
    op.drop_constraint("uq_reviews_user_activity", "reviews", type_="unique")
    op.drop_index("idx_reviews_activity", table_name="reviews")
    op.drop_table("reviews")
    op.drop_constraint("uq_favorites_user_activity", "favorites", type_="unique")
    op.drop_index("idx_favorites_user", table_name="favorites")
    op.drop_table("favorites")
    op.drop_index("idx_credits_type", table_name="credit_accumulation")
    op.drop_index("idx_credits_user", table_name="credit_accumulation")
    op.drop_table("credit_accumulation")
    op.drop_constraint("uq_participations_user_activity", "participations", type_="unique")
    op.drop_index("idx_participations_activity", table_name="participations")
    op.drop_index("idx_participations_user", table_name="participations")
    op.drop_table("participations")
    op.drop_table("activity_qrcodes")
    op.drop_index("idx_images_activity", table_name="activity_images")
    op.drop_table("activity_images")
    op.drop_index("idx_activities_activity_type", table_name="activities")
    op.drop_index("idx_activities_credit_type", table_name="activities")
    op.drop_index("idx_activities_deadline", table_name="activities")
    op.drop_index("idx_activities_owner", table_name="activities")
    op.drop_index("idx_activities_status", table_name="activities")
    op.drop_table("activities")
    op.drop_index("idx_owners_type", table_name="activity_owners")
    op.drop_table("activity_owners")
    op.drop_index("idx_students_student_id", table_name="students")
    op.drop_table("students")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_index("idx_users_account", table_name="users")
    op.drop_table("users")
    op.drop_table("colleges")
