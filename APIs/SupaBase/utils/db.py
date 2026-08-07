from psycopg import errors
from psycopg.rows import dict_row

from utils.banco import PendenciaDuplicadaError, conectar


def _unique_violation(err: Exception) -> bool:
    return isinstance(err, errors.UniqueViolation)


def listar_justificativas() -> list[dict]:
    with conectar() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                'SELECT "IdJustificativa", "DescJustificativa" '
                'FROM "dJustificativas" ORDER BY "IdJustificativa"'
            )
            return cur.fetchall()


def listar_areas() -> list[dict]:
    with conectar() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                'SELECT "IdAreaResponsavel", "NomeAreaResponsavel" '
                'FROM "dAreasResponsaveis" ORDER BY "IdAreaResponsavel"'
            )
            return cur.fetchall()


def inserir_registro(
    numero_pendencia: int,
    id_usuario: int,
    id_justificativa: int,
    id_area_responsavel: int,
) -> dict:
    try:
        with conectar() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    'INSERT INTO "fDados" '
                    '("NumeroPendencia", "IdUsuario", "IdJustificativa", "IdAreaResponsavel") '
                    "VALUES (%s, %s, %s, %s) RETURNING *",
                    (
                        numero_pendencia,
                        id_usuario,
                        id_justificativa,
                        id_area_responsavel,
                    ),
                )
                return cur.fetchone()
    except errors.UniqueViolation:
        raise PendenciaDuplicadaError(
            "Numero de pendencia ja registrado"
        ) from None


def inserir_registros_em_lote(registros: list[tuple]) -> int:
    """Bulk insert de [(numero_pendencia, id_usuario, id_justificativa,
    id_area_responsavel), ...]. Ignora pendências já existentes."""
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("SAVEPOINT antes_bulk")
            for numero, usuario, just, area in registros:
                try:
                    cur.execute(
                        'INSERT INTO "fDados" '
                        '("NumeroPendencia", "IdUsuario", "IdJustificativa", "IdAreaResponsavel") '
                        "VALUES (%s, %s, %s, %s)",
                        (numero, usuario, just, area),
                    )
                except errors.UniqueViolation:
                    cur.execute("ROLLBACK TO SAVEPOINT antes_bulk")
            return cur.rowcount


def listar_meus_registros(id_usuario: int) -> list[dict]:
    with conectar() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                'SELECT * FROM "fDados" WHERE "IdUsuario" = %s '
                'ORDER BY "DataHora" DESC',
                (id_usuario,),
            )
            return cur.fetchall()


def atualizar_registro(
    id_registro: int,
    id_usuario: int,
    numero_pendencia: int,
    id_justificativa: int,
    id_area_responsavel: int,
) -> None:
    try:
        with conectar() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE "fDados" SET "NumeroPendencia" = %s, '
                    '"IdJustificativa" = %s, "IdAreaResponsavel" = %s '
                    'WHERE "Id" = %s AND "IdUsuario" = %s',
                    (
                        numero_pendencia,
                        id_justificativa,
                        id_area_responsavel,
                        id_registro,
                        id_usuario,
                    ),
                )
    except errors.UniqueViolation:
        raise PendenciaDuplicadaError(
            "Numero de pendencia ja registrado"
        ) from None


def excluir_registro(id_registro: int, id_usuario: int) -> None:
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM "fDados" WHERE "Id" = %s AND "IdUsuario" = %s',
                (id_registro, id_usuario),
            )


def buscar_usuario_por_email(email: str) -> dict | None:
    with conectar() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                'SELECT * FROM "dUsuarios" WHERE "EmailUsuario" = %s',
                (email,),
            )
            return cur.fetchone()
