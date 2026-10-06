from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import obter_configuracoes
from app.db import modelos  # noqa: F401  (registra as tabelas)
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    # disable_existing_loggers=False: por padrão o fileConfig desabilitaria qualquer
    # logger já criado no processo (ex.: ao rodar as migrações dentro da suíte de testes,
    # no mesmo processo que importou os loggers da aplicação).
    fileConfig(config.config_file_name, disable_existing_loggers=False)

if not config.get_main_option("sqlalchemy.url"):
    # O configparser interpreta "%"; por isso o escape.
    config.set_main_option(
        "sqlalchemy.url", obter_configuracoes().database_url.replace("%", "%%")
    )

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conectavel = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conectavel.connect() as conexao:
        context.configure(
            connection=conexao, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
