# db/state_repository.py
import logging
from db.database import Database  # !!!
import db.queries as q

log = logging.getLogger(__name__)


class StateRepository:  # !!!
    def __init__(self, db: Database):  # !!!
        self.db = db

    def get_all(self):
        log.debug(f"Вызван get_all")
        result = self.db.fetch_all(q.GET_STATES)
        log.debug(f"get_all вернул: {result}")
        return result

    def get_by_id(self, state_id):
        log.debug(f"Вызван get_by_id с state_id={state_id}")
        result = self.db.fetch_one(q.GET_STATE_ID, (state_id,))
        log.debug(f"get_state_id вернул: {result[0] if result else None}")
        return result[0] if result else None

    def get_by_name(self, name):
        return self.get_by_id(name)
