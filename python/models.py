from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    emailVerified = Column(Boolean)
    image = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    twoFactorEnabled = Column(Boolean)
    role = Column(String)
    banned = Column(Boolean)
    banReason = Column(String)
    banExpires = Column(DateTime)
    finishedOnboarding = Column(Boolean)

    members = relationship("Member", back_populates="user")


class Organization(Base):
    __tablename__ = "organization"

    id = Column(String, primary_key=True)
    name = Column(String)
    slug = Column(String, unique=True)
    logo = Column(String)
    createdAt = Column(DateTime)
    # metadata = Column(String)

    members = relationship("Member", back_populates="organization")


class Member(Base):
    __tablename__ = "member"

    id = Column(String, primary_key=True)
    organizationId = Column(String, ForeignKey("organization.id"))
    userId = Column(String, ForeignKey("user.id"))
    role = Column(String)
    createdAt = Column(DateTime)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="members")


class ApiKey(Base):
    __tablename__ = "api_key"

    id = Column(String, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)
    keyString = Column(String, default="*********")
    organizationId = Column(String, ForeignKey("organization.id"))
    userId = Column(String, ForeignKey("user.id"))
    createdAt = Column(DateTime)
    isHashed = Column(Boolean, default=True)
    lastUsed = Column(DateTime, nullable=True)
    expiresAt = Column(DateTime, nullable=True)

    organization = relationship("Organization", backref="api_keys")
    user = relationship("User", backref="api_keys")

    def __repr__(self):
        return f"<ApiKey(id={self.id}, key={self.key}, name={self.name}, organizationId={self.organizationId})>"
