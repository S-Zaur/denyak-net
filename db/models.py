import enum
from datetime import datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Time,
    func,
)

from db.database import Base


class TransactionType(enum.Enum):
    EXPENSE = "expense"  # приход
    INCOME = "income"  # расход


class UtilityLevel(enum.Enum):
    NEED = "need"  # Жизненно важное
    COMFORT = "comfort"  # Комфорт/Качество жизни
    WHIM = "whim"  # Прихоть/Слабость
    WASTE = "waste"  # Мусор/Слив денег


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String)

    setting: Mapped["UserSetting"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(back_populates="user")


class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    monthly_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    timezone: Mapped[Optional[str]] = mapped_column(String)
    notification_time: Mapped[time] = mapped_column(Time, default=time(8, 0))

    user: Mapped["User"] = relationship(back_populates="setting")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)

    user: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
    )

    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], back_populates="subcategories"
    )
    subcategories: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )
    user: Mapped[Optional["User"]] = relationship(back_populates="categories")
    transaction_items: Mapped[list["TransactionItem"]] = relationship(
        back_populates="category"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    comment: Mapped[Optional[str]] = mapped_column(String)
    operation_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_ignored: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped["Account"] = relationship(back_populates="transactions")
    items: Mapped[list["TransactionItem"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=1.000)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="RESTRICT")
    )
    utility_level: Mapped[UtilityLevel] = mapped_column(
        Enum(UtilityLevel), default=UtilityLevel.NEED
    )
    is_ignored: Mapped[bool] = mapped_column(Boolean, default=False)

    transaction: Mapped["Transaction"] = relationship(back_populates="items")
    category: Mapped["Category"] = relationship(back_populates="transaction_items")
