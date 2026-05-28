from db import dao


class Repository:
    def __init__(self, session):
        self.session = session
        self.user = dao.UserDAO(session)
        self.location = dao.AccountDAO(session)
        self.setting = dao.CategoryDAO(session)
        self.transaction = dao.TransactionDAO(session)
