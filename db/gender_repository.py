# db/gender_repository.py
import logging
from db.database import Database  # Database
import db.queries as q


log = logging.getLogger(__name__)


class GenderRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all(self):
        log.debug(f"Вызван get_all")
        result = self.db.fetch_all(q.GET_GENDERS)  # Используем self.db
        log.debug(f"get_all вернул: {result}")
        return result

    def get_by_id(self, gender_id):
        log.debug(f"Вызван get_gender_id с gender_id={gender_id}")
        result = self.db.fetch_one(
            q.GET_GENDER_ID, (gender_id,))  # Используем self.db
        log.debug(f"get_gender_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_by_name(self, name):
        return self.get_by_id(name)
