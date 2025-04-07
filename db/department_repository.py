# db/department_repository.py
import logging
from db.database import Database  # !!!
import db.queries as q

log = logging.getLogger(__name__)


class DepartmentRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all(self):
        log.debug(f"Вызван get_all")
        result = self.db.fetch_all(q.GET_DEPARTMENTS)  # !!!
        log.debug(f"get_departments вернул: {result}")
        return result

    def get_by_name(self, department_name):
        log.debug(
            f"Вызван get_department_by_name с department_name='{department_name}'")

        result = self.db.fetch_all(
            q.GET_DEPARTMENT_ID_BY_NAME, (department_name,))
        log.debug(f"get_department_by_name вернул: {result}")
        return result
