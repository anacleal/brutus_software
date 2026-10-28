import re
from collections.abc import Mapping
from typing import Any

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SENHA_MIN_LEN = 8

CAMPOS_OBRIGATORIOS = [
    "nome",
    "sobrenome",
    "email",
    "usuario",
    "senha",
    "confirmacao_senha",
    "modalidade_preferida",
]


def validar_dados_cadastro(dados: Mapping[str, Any]) -> list[str]:
    if not isinstance(dados, Mapping):
        return ["Corpo da requisição inválido."]

    erros = []

    for campo in CAMPOS_OBRIGATORIOS:
        valor = dados.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            erros.append(f"O campo '{campo}' é obrigatório.")

    if erros:
        return erros

    campos_texto = (
        "nome",
        "sobrenome",
        "email",
        "usuario",
        "senha",
        "confirmacao_senha",
    )
    for campo in campos_texto:
        if not isinstance(dados[campo], str):
            erros.append(f"O campo '{campo}' deve ser um texto.")

    if erros:
        return erros

    limites = {
        "nome": 100,
        "sobrenome": 100,
        "email": 255,
        "usuario": 100,
    }
    for campo, limite in limites.items():
        if len(dados[campo]) > limite:
            erros.append(
                f"O campo '{campo}' deve ter no máximo {limite} caracteres."
            )

    if not EMAIL_REGEX.fullmatch(dados["email"]):
        erros.append("E-mail em formato inválido.")

    senha = dados["senha"]
    confirmacao = dados["confirmacao_senha"]

    if senha != confirmacao:
        erros.append("A senha e a confirmação de senha não são iguais.")

    if len(senha) < SENHA_MIN_LEN:
        erros.append(f"A senha deve ter pelo menos {SENHA_MIN_LEN} caracteres.")

    modalidade = dados["modalidade_preferida"]
    if isinstance(modalidade, int) and not isinstance(modalidade, bool):
        modalidade_id = modalidade
    elif (
        isinstance(modalidade, str)
        and modalidade.isdecimal()
        and len(modalidade) <= 19
    ):
        modalidade_id = int(modalidade)
    else:
        modalidade_id = 0

    if not 0 < modalidade_id <= 9223372036854775807:
        erros.append(
            "O campo 'modalidade_preferida' deve ser o id (número) da modalidade."
        )

    return erros


def foto_e_imagem_valida(foto) -> bool:
    inicio = foto.read(12)
    foto.seek(0)
    return (
        inicio.startswith(b"\xff\xd8\xff")
        or inicio.startswith(b"\x89PNG")
        or (inicio.startswith(b"RIFF") and inicio[8:12] == b"WEBP")
    )
