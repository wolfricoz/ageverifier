import os
from datetime import datetime
from typing import List, Optional

import pymysql
from dotenv import load_dotenv
from sqlalchemy import Integer, create_engine, DateTime, ForeignKey, String, BigInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func
from sqlalchemy_utils import database_exists, create_database

pymysql.install_as_MySQLdb()
load_dotenv('.env')
DB = os.getenv('DB')
db_string = f"{DB}/rmrbotnew?charset=utf8mb4"
engine = create_engine(db_string, poolclass=NullPool, echo=False, isolation_level="READ COMMITTED")
if not database_exists(engine.url):
    create_database(engine.url)

conn = engine.connect()


class Base(DeclarativeBase):
    pass

class Staff(Base) :
	__tablename__ = "staff"
	id: Mapped[int] = mapped_column(primary_key=True)
	uid: Mapped[int] = mapped_column(BigInteger)
	role: Mapped[str] = mapped_column(String(128))

	def __int__(self) :
		return self.id

# noinspection PyTypeChecker, PydanticTypeChecker
class Users(Base):
    __tablename__ = "users"
    uid: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    entry: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(10))
    server: Mapped[Optional[str]] = mapped_column(String(255))
    warnings: Mapped[List["Warnings"]] = relationship(cascade="save-update, merge, delete, delete-orphan")
    id_verification: Mapped[Optional["IdVerification"]] = relationship(back_populates="user", cascade="save-update, merge, delete, delete-orphan", uselist=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)


# noinspection PyTypeChecker, PydanticTypeChecker
class Warnings(Base):
    __tablename__ = "warnings"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(4096))
    type: Mapped[str] = mapped_column(String(20))
    entry: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# noinspection PyTypeChecker, PydanticTypeChecker

class Servers(Base):
    __tablename__ = "servers"
    guild: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False)


# noinspection PyTypeChecker, PydanticTypeChecker

class Config(Base):
    # Reminder to self you can add multiple keys in this database
    __tablename__ = "config"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(512))
    value: Mapped[str] = mapped_column(String(10000))


# noinspection PyTypeChecker, PydanticTypeChecker

# noinspection PyTypeChecker, PydanticTypeChecker
class IdVerification(Base):
    __tablename__ = "verification"
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    reason: Mapped[Optional[str]] = mapped_column(String(1024))
    idcheck: Mapped[bool] = mapped_column(Boolean, default=False)
    idverified: Mapped[bool] = mapped_column(Boolean, default=False)
    verifieddob: Mapped[Optional[datetime]]
    server: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user: Mapped["Users"] = relationship(back_populates="id_verification")


class Timers(Base):
    __tablename__ = "timers"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"))
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    role: Mapped[Optional[int]] = mapped_column(BigInteger)
    reason: Mapped[Optional[str]] = mapped_column(String(1024))  # Reason for timer
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    removal: Mapped[int]  # In hours


class AgeRole(Base):
    __tablename__ = "age_roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20))
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(BigInteger)
    minimum_age: Mapped[int] = mapped_column(Integer, default=18, nullable=True)
    maximum_age: Mapped[int] = mapped_column(Integer, default=200, nullable=True)


class database:
    @staticmethod
    def create():
        Base.metadata.create_all(engine)
        print("Database built")

    @staticmethod
    def restart():
        global engine
        engine.dispose()

        engine = create_engine(db_string, poolclass=NullPool, echo=False, isolation_level="READ COMMITTED",)