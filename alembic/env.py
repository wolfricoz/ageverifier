from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from databases.current import Base, db_string

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Take the database from the same place the bot's engine does, rather than from alembic.ini.
# The ini value is committed to the repository, so it could only ever name one machine's
# database - running `alembic upgrade head` against production would have migrated whatever
# was on localhost instead. Reading db_string means the CLI, the /dev migrate_database command
# and the bot itself can never disagree about which database is being migrated.
# Only fills in a url that nothing else supplied, so a caller that deliberately points at
# another database (a throwaway one for testing a revision, say) still wins.
# The '%' escape is for ConfigParser, which treats a bare '%' in a value as interpolation
# (passwords are url-encoded, so a real one can contain them).
if not config.get_main_option("sqlalchemy.url", None) :
    config.set_main_option("sqlalchemy.url", db_string.replace("%", "%%"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
	            connection=connection, target_metadata=target_metadata,
	        compare_type = True,  # detect column type changes
	        compare_server_default = True,  # detect changes in default values
	        render_as_batch = True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
