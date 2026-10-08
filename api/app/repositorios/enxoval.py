"""Repositório de Enxoval: encapsula o acesso ao banco para a entidade Enxoval.

O padrão Repository isola a lógica de persistência da lógica de negócio,
tornando os serviços independentes do ORM e facilitando testes com mocks.

Responsabilidades exclusivas deste módulo:
- Buscar enxovais por ID.
- Persistir novas instâncias de Enxoval.
- Atualizar campos de um Enxoval existente.
- Apagar enxovais (com cascata nas linhas).
- Buscar, criar e atualizar EnxovalLinha com proteção contra corrida de dados.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.familia import Enxoval, EnxovalLinha
from app.erros import EnxovalNaoEncontrado


class EnxovalRepository:
    """Acesso a dados para a entidade Enxoval e suas linhas.

    Todos os métodos operam dentro da sessão injetada. O commit é
    responsabilidade do chamador (a camada de rota).

    Args:
        sessao: Sessão SQLAlchemy ativa.
    """

    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def buscar_por_id(self, enxoval_id: uuid.UUID) -> Enxoval:
        """Busca um Enxoval pelo UUID, carregando suas linhas em eager loading.

        Args:
            enxoval_id: UUID do enxoval.

        Returns:
            Instância ORM de Enxoval com ``linhas`` já carregadas.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir no banco.
        """
        enxoval = self._sessao.scalars(
            select(Enxoval)
            .where(Enxoval.id == enxoval_id)
            .options(selectinload(Enxoval.linhas))
        ).one_or_none()
        if enxoval is None:
            raise EnxovalNaoEncontrado()
        return enxoval

    def buscar_por_id_e_dono(self, enxoval_id: uuid.UUID, dono_id: str | None) -> Enxoval:
        """Busca um Enxoval pelo UUID verificando o proprietário.

        Quando ``dono_id`` é ``None`` (modo dev sem autenticação), apenas
        confirma que o enxoval existe — sem filtrar por proprietário.

        Args:
            enxoval_id: UUID do enxoval.
            dono_id: ``sub`` do token JWT do usuário logado, ou ``None`` em dev.

        Returns:
            Instância ORM de Enxoval com ``linhas`` já carregadas.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir.
            EnxovalNaoEncontrado: Se o enxoval existir mas pertencer a outro dono
                (retorna 404 propositalmente para não vazar existência do recurso).
        """
        enxoval = self.buscar_por_id(enxoval_id)
        if dono_id is not None and enxoval.dono_id != dono_id:
            # Retorna 404 (não 403) para não confirmar ao atacante que o recurso existe
            raise EnxovalNaoEncontrado()
        return enxoval

    def listar_por_dono(self, dono_id: str | None) -> list[Enxoval]:
        """Retorna todos os enxovais de um usuário, sem carregar as linhas.

        Em modo dev (``dono_id=None``), retorna todos os enxovais do banco.

        Args:
            dono_id: ``sub`` do token JWT ou ``None`` em dev.

        Returns:
            Lista de ``Enxoval`` ordenada do mais recente para o mais antigo.
        """
        query = select(Enxoval).order_by(Enxoval.criado_em.desc())
        if dono_id is not None:
            query = query.where(Enxoval.dono_id == dono_id)
        return list(self._sessao.scalars(query).all())

    # ------------------------------------------------------------------
    # Escrita — Enxoval
    # ------------------------------------------------------------------

    def criar(self, enxoval: Enxoval) -> Enxoval:
        """Adiciona um novo Enxoval à sessão e faz flush para obter o ID.

        Args:
            enxoval: Instância ORM ainda não persistida.

        Returns:
            A mesma instância após o flush (ID preenchido).
        """
        self._sessao.add(enxoval)
        self._sessao.flush()
        return enxoval

    def apagar(self, enxoval: Enxoval) -> None:
        """Remove o Enxoval e suas linhas (cascata ON DELETE CASCADE).

        Args:
            enxoval: Instância ORM a ser removida.
        """
        self._sessao.delete(enxoval)
        self._sessao.flush()

    # ------------------------------------------------------------------
    # Escrita — EnxovalLinha
    # ------------------------------------------------------------------

    def buscar_ou_criar_linha(self, enxoval: Enxoval, chave: str) -> EnxovalLinha:
        """Retorna a linha existente ou cria uma nova com quantidades zeradas.

        Protegido contra corrida de dados (race condition): se duas requisições
        simultâneas tentarem criar a mesma linha nova, a que perder a corrida
        receberá um ``IntegrityError`` na chave primária. Nesse caso, a sessão
        é revertida ao savepoint anterior e a linha já criada pela outra
        requisição é retornada via ``refresh``.

        Args:
            enxoval: Enxoval dono da linha.
            chave: Chave da linha no formato ``<slug>:<tamanho>:<variante>``.

        Returns:
            Instância ORM de EnxovalLinha (existente ou recém-criada).
        """
        # Linha já está em memória na sessão atual?
        for linha in enxoval.linhas:
            if linha.chave == chave:
                return linha

        # Cria nova linha e tenta persistir
        nova = EnxovalLinha(chave=chave, qtd_comprada=0, qtd_ganhada=0, qtd_ja_tinha=0)
        enxoval.linhas.append(nova)

        # Usa savepoint para poder reverter só este INSERT em caso de corrida
        savepoint = self._sessao.begin_nested()
        try:
            self._sessao.flush()
            savepoint.commit()
            return nova
        except IntegrityError:
            # Outra requisição ganhou a corrida — descarta a linha local
            savepoint.rollback()
            enxoval.linhas.remove(nova)
            self._sessao.expire(enxoval)
            # Recarrega as linhas do banco e retorna a que foi criada pela outra req
            self._sessao.refresh(enxoval)
            for linha in enxoval.linhas:
                if linha.chave == chave:
                    return linha
            raise  # nunca deve chegar aqui

    def salvar_linha(self, linha: EnxovalLinha) -> EnxovalLinha:
        """Faz flush na sessão para persistir alterações numa linha.

        Args:
            linha: Instância ORM com os campos já modificados.

        Returns:
            A mesma instância após o flush.
        """
        self._sessao.flush()
        return linha
