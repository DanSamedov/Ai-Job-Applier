from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .logger import setup_logger


def db_safe(func):
    def wrapper(self, *args, **kwargs):
        with self.session() as db:
            try:
                return func(self, db, *args, **kwargs)
            except IntegrityError as e:
                db.rollback()
                self.logger.error(f"[IntegrityError] {func.__name__}: {e}")
                return {"status": "error", "error": "integrity"}
            except SQLAlchemyError as e:
                db.rollback()
                self.logger.error(f"[DatabaseError] {func.__name__}: {e}")
                return {"status": "error", "error": "db"}
            except Exception as e:
                db.rollback()
                self.logger.exception(f"[UnexpectedError] {func.__name__}: {e}")
                return {"status": "error", "error": "unexpected"}
    return wrapper
