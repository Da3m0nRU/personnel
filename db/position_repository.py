# db/position_repository.py
import logging
from db.database import Database
import db.queries as q

log = logging.getLogger(__name__)


class PositionRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all(self):
        log.debug("Вызов get_all")
        result = self.db.fetch_all(q.GET_ALL_POSITIONS)
        log.debug(f"get_all вернул: {result}")
        return result

    def get_by_id(self, position_id):
        """
        Возвращает ID должности по названию.
        """
        log.debug(f"Вызван get_position_id с position_id={position_id}")
        result = self.db.fetch_one(
            q.GET_POSITION_ID, (position_id,))  # !!! self.db
        log.debug(f"get_position_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_by_name(self, name):
        return self.get_by_id(name)

    def get_departments_for_position(self, position_id):
        log.debug(
            f"Вызов get_departments_for_position с position_id={position_id}")
        result = self.db.fetch_all(
            q.GET_DEPARTMENTS_FOR_POSITION, (position_id,))  # !!!
        log.debug(f"get_departments_for_position вернул: {result}")
        return result

    def get_positions(self):
        log.debug("Вызов get_positions")
        result = self.db.fetch_all(q.GET_POSITIONS)  # !!!
        log.debug(f"get_positions вернул: {result}")
        return result
