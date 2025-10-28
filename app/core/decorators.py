# app/core/decorators.py
from functools import wraps
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from .logger import setup_logger
from app.core.enums import APIError, APIStatus


def db_safe(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        db_instance = None 

        try:
            with self.session() as db:
                db_instance = db
                return func(self, db_instance, *args, **kwargs)

        except IntegrityError as e:
            if db_instance:
                db_instance.rollback()
            self.logger.error(f"[IntegrityError] {func.__name__}: {e}")
            return {"status": APIStatus.ERROR, "error": APIError.INTEGRITY}

        except SQLAlchemyError as e:
            if db_instance:
                db_instance.rollback()
            self.logger.error(f"[DatabaseError] {func.__name__}: {e}")
            return {"status": APIStatus.ERROR, "error": APIError.DB}

        except Exception as e:
            if db_instance:
                db_instance.rollback()
            self.logger.exception(f"[UnexpectedError] {func.__name__}: {e}")
            return {"status": APIStatus.ERROR, "error": APIError.UNEXPECTED}
    return wrapper
