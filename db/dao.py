from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Transaction, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, TypeVar, Generic, Type

from sqlalchemy.orm import selectinload

from db.models import (
    Account,
    Category,
    TransactionItem,
    TransactionType,
    User,
    UserSetting,
    UtilityLevel,
)

ModelType = TypeVar("ModelType")


class BaseDAO(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> ModelType:
        result = await self.session.get(self.model, id)
        return result


class UserDAO(BaseDAO[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_or_create(self, tg_id: int, username: Optional[str] = None) -> User:
        query = select(User).where(User.id == tg_id).options(selectinload(User.setting))
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            if username and user.username != username:
                user.username = username
        else:
            user = User(id=tg_id, username=username)
            self.session.add(user)

            user_setting = UserSetting(user_id=tg_id, timezone="UTC")
            self.session.add(user_setting)

            await self.session.flush()
        return user

    async def get_user_with_settings(self, tg_id) -> Optional[User]:
        query = select(User).where(User.id == tg_id).options(selectinload(User.setting))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_user_settings(
        self,
        tg_id: int,
        monthly_limit: Optional[float] = None,
        timezone: Optional[str] = None,
        notification_time: Optional[time] = None,
    ):
        query = select(UserSetting).where(UserSetting.user_id == tg_id)
        result = await self.session.execute(query)
        setting = result.scalar_one_or_none()

        if not setting:
            return
        if monthly_limit:
            setting.monthly_limit = monthly_limit
        if timezone:
            setting.timezone = timezone
        if notification_time:
            setting.notification_time = notification_time
        return setting


class AccountDAO(BaseDAO[Account]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Account)

    async def create_account(
        self, user_id: int, name: str, intial_balance: Decimal = Decimal("0.00")
    ) -> Account:
        account = Account(user_id=user_id, name=name, balance=intial_balance)
        self.session.add(account)
        await self.session.flush()
        return account

    async def get_user_accounts(self, user_id: int) -> list[Account]:
        query = select(Account).where(Account.user_id == user_id).order_by(Account.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_balance(self, account_id: int, amount: Decimal) -> None:
        query = (
            update(Account)
            .where(Account.id == account_id)
            .values(balance=Account.balance + amount)
        )
        await self.session.execute(query)


class CategoryDAO(BaseDAO[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)

    async def create_category(
        self,
        name: str,
        type: TransactionType,
        user_id: Optional[int] = None,
        parent_id: Optional[int] = None,
    ) -> Category:
        category = Category(name=name, type=type, user_id=user_id, parent_id=parent_id)
        self.session.add(category)
        await self.session.flush()
        return category

    async def get_root_categories(
        self, user_id: int, type: TransactionType
    ) -> list[Category]:
        query = (
            select(Category)
            .where(
                Category.parent_id.is_(None),
                Category.type == type,
                or_(Category.user_id.is_(None), Category.user_id == user_id),
            )
            .order_by(Category.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_subcategories(self, parent_id: int, user_id: int) -> list[Category]:
        query = (
            select(Category)
            .where(
                Category.parent_id == parent_id,
                or_(Category.user_id.is_(None), Category.user_id == user_id),
            )
            .order_by(Category.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: int, user_id: int) -> Optional[Category]:
        query = select(Category).where(
            Category.id == category_id,
            or_(Category.user_id.is_(None), Category.user_id == user_id),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class TransactionDAO(BaseDAO[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Transaction)

    async def create_simple_transaction(
        self,
        account_id: int,
        amount: Decimal,
        category_id: int,
        comment: str,
        operation_date: Optional[datetime] = None,
        is_ignored: bool = False,
        utility_level: UtilityLevel = UtilityLevel.NEED,
    ) -> Transaction:
        if not operation_date:
            operation_date = datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        transaction = Transaction(
            account_id=account_id,
            amount=amount,
            comment=comment,
            operation_date=operation_date,
            is_ignored=is_ignored,
        )
        self.session.add(transaction)

        transaction_item = TransactionItem(
            name=comment,
            price=amount,
            quantity=Decimal("1.000"),
            amount=amount,
            category_id=category_id,
            utility_level=utility_level,
            is_ignored=is_ignored,
        )
        transaction.items.append(transaction_item)

        acc_dao = AccountDAO(self.session)
        await acc_dao.update_balance(account_id, amount)
        await self.session.flush()
        return transaction

    async def get_user_transactions(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> list[Transaction]:
        query = (
            select(Transaction)
            .join(Account)
            .where(Account.user_id == user_id)
            .order_by(desc(Transaction.operation_date))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self, transaction_id: int, user_id: int
    ) -> Optional[Transaction]:
        query = (
            select(Transaction)
            .join(Account)
            .where(Transaction.id == transaction_id, Account.user_id == user_id)
            .options(selectinload(Transaction.items).selectinload(Transaction.category))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
