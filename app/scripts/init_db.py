from app.database import engine, Base
import app.models


def init_db():
    models.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
