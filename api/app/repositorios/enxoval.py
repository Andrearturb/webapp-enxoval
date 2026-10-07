"""Repositório de Enxoval: encapsula o acesso ao banco para a entidade Enxoval.

O padrão Repository isola a lógica de persistência da lógica de negócio,
tornando os serviços independentes do ORM e facilitando testes com mocks.

Responsabilidades exclusivas deste módulo:
- Buscar enxovais por ID.
- Persistir novas instâncias de Enxoval.
- Atualizar campos de um Enxoval existente.
- Apagar enxovais (com cascata nas linhas).
- Buscar, criar e atualizar EnxovalLinha.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.familia import Enxoval, EnxovalLinha
from app.erros import EnxovalNaoEncontrado


class EnxovalRepository:
    """Acesso a dados para a entidade Enxoval e suas linhas.

    Todos os métodos operam dentro da sessão injetada e fazem ``flush``
    ao final para materializar as mudanças sem commitar a transação —
    o commit é responsabilidade do chamador (a camada de rota).

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

        Chaves que não existem na lista calculada são aceitas para preservar
        marcações de famílias que mudaram de respostas.

        Args:
            enxoval: Enxoval dono da linha.
            chave: Chave da linha no formato ``<slug>:<tamanho>:<variante>``.

        Returns:
            Instância ORM de EnxovalLinha (existente ou recém-criada).
        """
        for linha in enxoval.linhas:
            if linha.chave == chave:
                return linha
        # qtd_* ficam None em memória até o flush aplicar o default da coluna —
        # completar_linha soma essas quantidades antes de qualquer flush.
        linha = EnxovalLinha(chave=chave, qtd_comprada=0, qtd_ganhada=0, qtd_ja_tinha=0)
        enxoval.linhas.append(linha)
        return linha

    def salvar_linha(self, linha: EnxovalLinha) -> EnxovalLinha:
        """Faz flush na sessão para persistir alterações numa linha.

        Args:
            linha: Instância ORM com os campos já modificados.

        Returns:
            A mesma instância após o flush.
        """
        self._sessao.flush()
        return linha
