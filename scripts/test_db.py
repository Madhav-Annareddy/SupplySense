from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5432/supplysense"

engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    result = connection.execute(text("SELECT COUNT(*) FROM sales"))
    print("Sales rows:", result.scalar())
    print("Database connection OK")
