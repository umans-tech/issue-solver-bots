import os

CURR_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_PATH = os.path.join(CURR_PATH, "..")
ALEMBIC_INI_LOCATION = os.path.join(PROJECT_ROOT_PATH, "alembic.ini")
MIGRATIONS_PATH = os.path.join(
    PROJECT_ROOT_PATH, "src/issue_solver/database/migrations"
)
