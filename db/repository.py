from db import dao


class Repository:
    def __init__(self, session):
        self.session = session
        self.user = dao.UserDAO(session)
        self.location = dao.AccountDAO(session)
        self.category = dao.CategoryDAO(session)
        self.transaction = dao.TransactionDAO(session)

    async def commit(self):
        await self.session.commit()
