from sqlalchemy import CheckConstraint, Column, Integer, String, text

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'support_agent', 'admin')",
            name="ck_users_role_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", server_default=text("'user'"), nullable=False)
