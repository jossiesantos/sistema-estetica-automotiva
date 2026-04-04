import pyodbc
from decimal import Decimal
from functools import wraps
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "sistema_estetica_automotiva_chave_secreta_123"

# ==========================================
# CONFIGURAÇÃO DO SQL SERVER
# ==========================================
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=EsteticaAutomotiva;"
    "UID=sa;"
    "PWD=123;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

# =========================
# FUNÇÕES DE BANCO
# =========================
def get_connection():
    return pyodbc.connect(CONN_STR)


def normalizar_valor_banco(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def fetch_all(sql, params=()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        colunas = [col[0] for col in cursor.description]
        resultados = []
        for row in cursor.fetchall():
            item = {}
            for i, col in enumerate(colunas):
                item[col] = normalizar_valor_banco(row[i])
            resultados.append(item)
        return resultados


def fetch_one(sql, params=()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if not row:
            return None
        colunas = [col[0] for col in cursor.description]
        item = {}
        for i, col in enumerate(colunas):
            item[col] = normalizar_valor_banco(row[i])
        return item


def execute_query(sql, params=()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()


def execute_insert(sql, params=()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        cursor.execute("SELECT SCOPE_IDENTITY()")
        novo_id = cursor.fetchone()[0]
        conn.commit()
        return int(novo_id)


# =========================
# FUNÇÕES GENÉRICAS
# =========================
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario_logado" not in session:
            flash("Faça login para acessar o sistema.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def usuario_autenticado(usuario, senha):
    sql = """
        SELECT id, usuario, senha
        FROM usuarios
        WHERE usuario = ? AND senha = ?
    """
    return fetch_one(sql, (usuario, senha))


def converter_valor_para_float(valor):
    try:
        if valor is None:
            return 0.0

        # Se já for número
        if isinstance(valor, (int, float)):
            return float(valor)

        valor_limpo = str(valor).strip().replace("R$", "").replace(" ", "")

        # Formato brasileiro: 1.234,56
        if "," in valor_limpo and "." in valor_limpo:
            if valor_limpo.rfind(",") > valor_limpo.rfind("."):
                valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
            else:
                valor_limpo = valor_limpo.replace(",", "")

        # Formato brasileiro simples: 200,00
        elif "," in valor_limpo:
            valor_limpo = valor_limpo.replace(",", ".")

        # Formato americano: 200.00 → não mexe

        return float(valor_limpo)

    except:
        return 0.0

def identificar_veiculo(veiculo):
    marca = str(veiculo.get("marca", "")).strip()
    modelo = str(veiculo.get("modelo", "")).strip()
    placa = str(veiculo.get("placa", "")).strip()

    descricao = f"{marca} {modelo}".strip()
    if placa:
        descricao = f"{descricao} - {placa}" if descricao else placa

    return descricao.strip()


def texto_normalizado(texto):
    return str(texto).strip().lower()


# =========================
# HELPERS DE BUSCA POR TEXTO
# Mantém compatibilidade com os formulários atuais
# =========================
def buscar_cliente_por_nome(nome):
    sql = """
        SELECT TOP 1 id, nome, telefone, email
        FROM clientes
        WHERE LOWER(nome) = LOWER(?)
        ORDER BY id
    """
    return fetch_one(sql, (nome,))


def buscar_veiculo_por_descricao(descricao):
    veiculos = carregar_veiculos()
    descricao_normalizada = texto_normalizado(descricao)

    for veiculo in veiculos:
        if texto_normalizado(identificar_veiculo(veiculo)) == descricao_normalizada:
            return veiculo

    return None


def obter_cliente_id_por_form():
    cliente_id = request.form.get("cliente_id")
    if cliente_id:
        return int(cliente_id)

    cliente_nome = request.form.get("cliente", "").strip()
    if not cliente_nome:
        return None

    cliente = buscar_cliente_por_nome(cliente_nome)
    return cliente["id"] if cliente else None


def obter_veiculo_id_por_form():
    veiculo_id = request.form.get("veiculo_id")
    if veiculo_id:
        return int(veiculo_id)

    descricao = request.form.get("veiculo", "").strip()
    if not descricao:
        return None

    veiculo = buscar_veiculo_por_descricao(descricao)
    return veiculo["id"] if veiculo else None


# =========================
# CLIENTES
# =========================
def carregar_clientes():
    sql = """
        SELECT id, nome, telefone, email
        FROM clientes
        ORDER BY nome
    """
    return fetch_all(sql)


def buscar_cliente_por_id(cliente_id):
    sql = """
        SELECT id, nome, telefone, email
        FROM clientes
        WHERE id = ?
    """
    return fetch_one(sql, (cliente_id,))


# =========================
# VEÍCULOS
# =========================
def carregar_veiculos():
    sql = """
        SELECT
            v.id,
            v.cliente_id,
            c.nome AS cliente,
            v.modelo,
            v.marca,
            v.placa,
            v.cor
        FROM veiculos v
        INNER JOIN clientes c ON c.id = v.cliente_id
        ORDER BY v.id DESC
    """
    return fetch_all(sql)


def buscar_veiculo_por_id(veiculo_id):
    sql = """
        SELECT
            v.id,
            v.cliente_id,
            c.nome AS cliente,
            v.modelo,
            v.marca,
            v.placa,
            v.cor
        FROM veiculos v
        INNER JOIN clientes c ON c.id = v.cliente_id
        WHERE v.id = ?
    """
    return fetch_one(sql, (veiculo_id,))


# =========================
# SERVIÇOS
# =========================
def carregar_servicos():
    sql = """
        SELECT
            s.id,
            s.cliente_id,
            c.nome AS cliente,
            s.veiculo_id,
            v.marca,
            v.modelo,
            v.placa,
            CONCAT(
                v.marca, ' ', v.modelo,
                CASE
                    WHEN v.placa IS NOT NULL AND LTRIM(RTRIM(v.placa)) <> '' THEN ' - ' + v.placa
                    ELSE ''
                END
            ) AS veiculo,
            s.tipo_servico,
            CAST(s.valor AS DECIMAL(10,2)) AS valor,
            s.status,
            s.agendamento_id
        FROM servicos s
        INNER JOIN clientes c ON c.id = s.cliente_id
        INNER JOIN veiculos v ON v.id = s.veiculo_id
        ORDER BY s.id DESC
    """
    return fetch_all(sql)


def buscar_servico_por_id(servico_id):
    sql = """
        SELECT
            s.id,
            s.cliente_id,
            c.nome AS cliente,
            s.veiculo_id,
            v.marca,
            v.modelo,
            v.placa,
            CONCAT(
                v.marca, ' ', v.modelo,
                CASE
                    WHEN v.placa IS NOT NULL AND LTRIM(RTRIM(v.placa)) <> '' THEN ' - ' + v.placa
                    ELSE ''
                END
            ) AS veiculo,
            s.tipo_servico,
            CAST(s.valor AS DECIMAL(10,2)) AS valor,
            s.status,
            s.agendamento_id
        FROM servicos s
        INNER JOIN clientes c ON c.id = s.cliente_id
        INNER JOIN veiculos v ON v.id = s.veiculo_id
        WHERE s.id = ?
    """
    return fetch_one(sql, (servico_id,))


def normalizar_servicos():
    # Não é mais necessário com SQL Server,
    # mas mantido para compatibilidade com o fluxo do sistema.
    pass


# =========================
# AGENDAMENTOS
# =========================
def carregar_agendamentos():
    sql = """
        SELECT
            a.id,
            a.cliente_id,
            c.nome AS cliente,
            a.veiculo_id,
            v.marca,
            v.modelo,
            v.placa,
            CONCAT(
                v.marca, ' ', v.modelo,
                CASE
                    WHEN v.placa IS NOT NULL AND LTRIM(RTRIM(v.placa)) <> '' THEN ' - ' + v.placa
                    ELSE ''
                END
            ) AS veiculo,
            a.servico,
            CONVERT(VARCHAR(10), a.data, 23) AS data,
            LEFT(CONVERT(VARCHAR(8), a.hora, 108), 5) AS hora,
            a.status
        FROM agendamentos a
        INNER JOIN clientes c ON c.id = a.cliente_id
        INNER JOIN veiculos v ON v.id = a.veiculo_id
        ORDER BY a.data, a.hora
    """
    return fetch_all(sql)


def buscar_agendamento_por_id(agendamento_id):
    sql = """
        SELECT
            a.id,
            a.cliente_id,
            c.nome AS cliente,
            a.veiculo_id,
            v.marca,
            v.modelo,
            v.placa,
            CONCAT(
                v.marca, ' ', v.modelo,
                CASE
                    WHEN v.placa IS NOT NULL AND LTRIM(RTRIM(v.placa)) <> '' THEN ' - ' + v.placa
                    ELSE ''
                END
            ) AS veiculo,
            a.servico,
            CONVERT(VARCHAR(10), a.data, 23) AS data,
            LEFT(CONVERT(VARCHAR(8), a.hora, 108), 5) AS hora,
            a.status
        FROM agendamentos a
        INNER JOIN clientes c ON c.id = a.cliente_id
        INNER JOIN veiculos v ON v.id = a.veiculo_id
        WHERE a.id = ?
    """
    return fetch_one(sql, (agendamento_id,))


def normalizar_agendamentos():
    # Não é mais necessário com SQL Server,
    # mas mantido para compatibilidade com o fluxo do sistema.
    pass


def finalizar_agendamento_relacionado(servico):
    agendamento_id = servico.get("agendamento_id")

    if not agendamento_id:
        return

    execute_query("""
        UPDATE agendamentos
        SET status = 'Finalizado'
        WHERE id = ?
    """, (agendamento_id,))


def existe_conflito_agendamento(data_agendamento, hora_agendamento, ignorar_id=None):
    sql = """
        SELECT TOP 1 1 AS existe
        FROM agendamentos
        WHERE data = ?
          AND hora = ?
          AND status <> 'Finalizado'
    """
    params = [data_agendamento, hora_agendamento]

    if ignorar_id is not None:
        sql += " AND id <> ?"
        params.append(ignorar_id)

    return fetch_one(sql, tuple(params)) is not None


# =========================
# REGRAS DE EXCLUSÃO
# =========================
def cliente_possui_vinculos(cliente):
    cliente_id = cliente["id"]

    sql = """
        SELECT TOP 1 1 AS existe
        FROM (
            SELECT cliente_id FROM veiculos
            UNION ALL
            SELECT cliente_id FROM servicos
            UNION ALL
            SELECT cliente_id FROM agendamentos
        ) x
        WHERE x.cliente_id = ?
    """
    return fetch_one(sql, (cliente_id,)) is not None


def veiculo_possui_vinculos(veiculo):
    veiculo_id = veiculo["id"]

    sql = """
        SELECT TOP 1 1 AS existe
        FROM (
            SELECT veiculo_id FROM servicos
            UNION ALL
            SELECT veiculo_id FROM agendamentos
        ) x
        WHERE x.veiculo_id = ?
    """
    return fetch_one(sql, (veiculo_id,)) is not None


def servico_possui_vinculos(servico):
    return servico.get("agendamento_id") is not None


def agendamento_possui_vinculos(agendamento_id):
    sql = """
        SELECT TOP 1 1 AS existe
        FROM servicos
        WHERE agendamento_id = ?
    """
    return fetch_one(sql, (agendamento_id,)) is not None


# =========================
# LOGIN / LOGOUT
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        usuario_encontrado = usuario_autenticado(usuario, senha)

        if usuario_encontrado:
            session["usuario_logado"] = usuario_encontrado["usuario"]
            session["usuario_id"] = usuario_encontrado["id"]
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("inicio"))

        flash("Usuário ou senha inválidos.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "info")
    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================
@app.route("/")
@login_required
def inicio():
    normalizar_agendamentos()
    normalizar_servicos()

    clientes = carregar_clientes()
    veiculos = carregar_veiculos()
    servicos = carregar_servicos()
    agendamentos = carregar_agendamentos()

    hoje = date.today().isoformat()

    total_clientes = len(clientes)
    total_veiculos = len(veiculos)
    total_servicos = len(servicos)

    total_servicos_pendentes = len(
        [s for s in servicos if s.get("status", "Pendente") != "Concluído"]
    )

    total_agendamentos_ativos = len(
        [a for a in agendamentos if a.get("status", "Agendado") != "Finalizado"]
    )

    total_agendamentos_finalizados = len(
        [a for a in agendamentos if a.get("status", "Agendado") == "Finalizado"]
    )

    agendamentos_hoje = [
        a for a in agendamentos
        if a.get("data") == hoje and a.get("status", "Agendado") != "Finalizado"
    ]

    proximos_agendamentos = sorted(
        [a for a in agendamentos if a.get("status", "Agendado") != "Finalizado"],
        key=lambda x: (x.get("data", ""), x.get("hora", ""))
    )[:5]

    ultimos_finalizados = sorted(
        [a for a in agendamentos if a.get("status", "Agendado") == "Finalizado"],
        key=lambda x: (x.get("data", ""), x.get("hora", "")),
        reverse=True
    )[:5]

    valor_pendente = sum(
        converter_valor_para_float(s.get("valor", 0))
        for s in servicos
        if s.get("status", "Pendente") != "Concluído"
    )

    valor_concluido = sum(
        converter_valor_para_float(s.get("valor", 0))
        for s in servicos
        if s.get("status", "Pendente") == "Concluído"
    )

    return render_template(
        "index.html",
        total_clientes=total_clientes,
        total_veiculos=total_veiculos,
        total_servicos=total_servicos,
        total_servicos_pendentes=total_servicos_pendentes,
        total_agendamentos_ativos=total_agendamentos_ativos,
        total_agendamentos_finalizados=total_agendamentos_finalizados,
        total_agendamentos_hoje=len(agendamentos_hoje),
        valor_pendente=valor_pendente,
        valor_concluido=valor_concluido,
        proximos_agendamentos=proximos_agendamentos,
        ultimos_finalizados=ultimos_finalizados
    )


# =========================
# CLIENTES
# =========================
@app.route("/clientes")
@login_required
def clientes():
    lista_clientes = carregar_clientes()
    q = request.args.get("q", "").strip().lower()

    if q:
        lista_clientes = [
            cliente for cliente in lista_clientes
            if q in str(cliente.get("nome", "")).lower()
            or q in str(cliente.get("telefone", "")).lower()
            or q in str(cliente.get("email", "")).lower()
        ]

    return render_template("clientes.html", clientes=lista_clientes, q=q)


@app.route("/novo_cliente", methods=["GET", "POST"])
@login_required
def novo_cliente():
    if request.method == "POST":
        execute_query("""
            INSERT INTO clientes (nome, telefone, email)
            VALUES (?, ?, ?)
        """, (
            request.form["nome"],
            request.form["telefone"],
            request.form["email"]
        ))

        flash("Cliente cadastrado com sucesso.", "success")
        return redirect(url_for("clientes"))

    return render_template("novo_cliente.html")


@app.route("/consultar_cliente/<int:id>")
@login_required
def consultar_cliente(id):
    cliente = buscar_cliente_por_id(id)
    return render_template("consultar_cliente.html", cliente=cliente, id=id)


@app.route("/editar_cliente/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cliente(id):
    cliente = buscar_cliente_por_id(id)

    if not cliente:
        return render_template("editar_cliente.html", cliente=None, id=id)

    if request.method == "POST":
        execute_query("""
            UPDATE clientes
            SET nome = ?, telefone = ?, email = ?
            WHERE id = ?
        """, (
            request.form["nome"],
            request.form["telefone"],
            request.form["email"],
            id
        ))

        flash("Cliente atualizado com sucesso.", "success")
        return redirect(url_for("clientes"))

    return render_template("editar_cliente.html", cliente=cliente, id=id)


@app.route("/excluir_cliente/<int:id>", methods=["POST"])
@login_required
def excluir_cliente(id):
    cliente = buscar_cliente_por_id(id)

    if not cliente:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("clientes"))

    if cliente_possui_vinculos(cliente):
        flash("Este cliente não pode ser excluído porque possui vínculos com veículos, serviços ou agendamentos.", "warning")
        return redirect(url_for("clientes"))

    execute_query("DELETE FROM clientes WHERE id = ?", (id,))
    flash("Cliente excluído com sucesso.", "success")
    return redirect(url_for("clientes"))


# =========================
# VEÍCULOS
# =========================
@app.route("/veiculos")
@login_required
def veiculos():
    lista_veiculos = carregar_veiculos()
    q = request.args.get("q", "").strip().lower()

    if q:
        filtrados = []
        for veiculo in lista_veiculos:
            texto_veiculo = identificar_veiculo(veiculo).lower()
            if (
                q in str(veiculo.get("cliente", "")).lower()
                or q in str(veiculo.get("modelo", "")).lower()
                or q in str(veiculo.get("marca", "")).lower()
                or q in str(veiculo.get("placa", "")).lower()
                or q in texto_veiculo
            ):
                filtrados.append(veiculo)
        lista_veiculos = filtrados

    return render_template("veiculos.html", veiculos=lista_veiculos, q=q)


@app.route("/novo_veiculo", methods=["GET", "POST"])
@login_required
def novo_veiculo():
    if request.method == "POST":
        cliente_id = obter_cliente_id_por_form()

        if not cliente_id:
            flash("Cliente inválido ou não encontrado.", "danger")
            return redirect(url_for("novo_veiculo"))

        execute_query("""
            INSERT INTO veiculos (cliente_id, modelo, marca, placa, cor)
            VALUES (?, ?, ?, ?, ?)
        """, (
            cliente_id,
            request.form["modelo"],
            request.form["marca"],
            request.form["placa"],
            request.form["cor"]
        ))

        flash("Veículo cadastrado com sucesso.", "success")
        return redirect(url_for("veiculos"))

    clientes_lista = carregar_clientes()
    return render_template("novo_veiculo.html", clientes=clientes_lista)


@app.route("/consultar_veiculo/<int:id>")
@login_required
def consultar_veiculo(id):
    veiculo = buscar_veiculo_por_id(id)
    return render_template("consultar_veiculo.html", veiculo=veiculo, id=id)


@app.route("/editar_veiculo/<int:id>", methods=["GET", "POST"])
@login_required
def editar_veiculo(id):
    veiculo = buscar_veiculo_por_id(id)

    if not veiculo:
        return render_template("editar_veiculo.html", veiculo=None, id=id)

    if request.method == "POST":
        cliente_id = obter_cliente_id_por_form()

        if not cliente_id:
            flash("Cliente inválido ou não encontrado.", "danger")
            return redirect(url_for("editar_veiculo", id=id))

        execute_query("""
            UPDATE veiculos
            SET cliente_id = ?, modelo = ?, marca = ?, placa = ?, cor = ?
            WHERE id = ?
        """, (
            cliente_id,
            request.form["modelo"],
            request.form["marca"],
            request.form["placa"],
            request.form["cor"],
            id
        ))

        flash("Veículo atualizado com sucesso.", "success")
        return redirect(url_for("veiculos"))

    clientes_lista = carregar_clientes()
    return render_template("editar_veiculo.html", veiculo=veiculo, id=id, clientes=clientes_lista)


@app.route("/excluir_veiculo/<int:id>", methods=["POST"])
@login_required
def excluir_veiculo(id):
    veiculo = buscar_veiculo_por_id(id)

    if not veiculo:
        flash("Veículo não encontrado.", "danger")
        return redirect(url_for("veiculos"))

    if veiculo_possui_vinculos(veiculo):
        flash("Este veículo não pode ser excluído porque possui vínculos com serviços ou agendamentos.", "warning")
        return redirect(url_for("veiculos"))

    execute_query("DELETE FROM veiculos WHERE id = ?", (id,))
    flash("Veículo excluído com sucesso.", "success")
    return redirect(url_for("veiculos"))


# =========================
# SERVIÇOS
# =========================
@app.route("/servicos")
@login_required
def servicos():
    normalizar_servicos()
    lista_servicos = carregar_servicos()
    q = request.args.get("q", "").strip().lower()

    if q:
        lista_servicos = [
            servico for servico in lista_servicos
            if q in str(servico.get("cliente", "")).lower()
            or q in str(servico.get("veiculo", "")).lower()
            or q in str(servico.get("tipo_servico", "")).lower()
            or q in str(servico.get("status", "")).lower()
        ]

    return render_template("servicos.html", servicos=lista_servicos, q=q)


@app.route("/novo_servico", methods=["GET", "POST"])
@login_required
def novo_servico():
    normalizar_agendamentos()

    if request.method == "POST":
        cliente_id = obter_cliente_id_por_form()
        veiculo_id = obter_veiculo_id_por_form()

        if not cliente_id:
            flash("Cliente inválido ou não encontrado.", "danger")
            return redirect(url_for("novo_servico"))

        if not veiculo_id:
            flash("Veículo inválido ou não encontrado.", "danger")
            return redirect(url_for("novo_servico"))

        agendamento_id = request.form.get("agendamento_id")
        agendamento_id = int(agendamento_id) if agendamento_id else None

        execute_query("""
            INSERT INTO servicos (cliente_id, veiculo_id, tipo_servico, valor, status, agendamento_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            veiculo_id,
            request.form["tipo_servico"],
            converter_valor_para_float(request.form["valor"]),
            request.form["status"],
            agendamento_id
        ))

        flash("Serviço cadastrado com sucesso.", "success")
        return redirect(url_for("servicos"))

    agendamentos = carregar_agendamentos()
    agendamentos_ativos = [
        agendamento for agendamento in agendamentos
        if agendamento.get("status", "Agendado") != "Finalizado"
    ]

    clientes_lista = carregar_clientes()
    veiculos_lista = carregar_veiculos()

    return render_template(
        "novo_servico.html",
        agendamentos=agendamentos_ativos,
        clientes=clientes_lista,
        veiculos=veiculos_lista
    )


@app.route("/consultar_servico/<int:id>")
@login_required
def consultar_servico(id):
    servico = buscar_servico_por_id(id)
    return render_template("consultar_servico.html", servico=servico, id=id)


@app.route("/editar_servico/<int:id>", methods=["GET", "POST"])
@login_required
def editar_servico(id):
    normalizar_agendamentos()
    normalizar_servicos()

    servico = buscar_servico_por_id(id)

    if not servico:
        return render_template("editar_servico.html", servico=None, id=id, agendamentos=[])

    if request.method == "POST":
        status_anterior = servico.get("status", "Pendente")

        cliente_id = obter_cliente_id_por_form()
        veiculo_id = obter_veiculo_id_por_form()

        if not cliente_id:
            flash("Cliente inválido ou não encontrado.", "danger")
            return redirect(url_for("editar_servico", id=id))

        if not veiculo_id:
            flash("Veículo inválido ou não encontrado.", "danger")
            return redirect(url_for("editar_servico", id=id))

        agendamento_id = request.form.get("agendamento_id")
        agendamento_id = int(agendamento_id) if agendamento_id else None

        execute_query("""
            UPDATE servicos
            SET cliente_id = ?, veiculo_id = ?, tipo_servico = ?, valor = ?, status = ?, agendamento_id = ?
            WHERE id = ?
        """, (
            cliente_id,
            veiculo_id,
            request.form["tipo_servico"],
            converter_valor_para_float(request.form["valor"]),
            request.form["status"],
            agendamento_id,
            id
        ))

        servico_atualizado = buscar_servico_por_id(id)

        if status_anterior != "Concluído" and servico_atualizado["status"] == "Concluído":
            finalizar_agendamento_relacionado(servico_atualizado)

        flash("Serviço atualizado com sucesso.", "success")
        return redirect(url_for("servicos"))

    agendamentos = carregar_agendamentos()
    agendamentos_disponiveis = [
        agendamento for agendamento in agendamentos
        if agendamento.get("status", "Agendado") != "Finalizado"
        or agendamento["id"] == servico.get("agendamento_id")
    ]

    clientes_lista = carregar_clientes()
    veiculos_lista = carregar_veiculos()

    return render_template(
        "editar_servico.html",
        servico=servico,
        id=id,
        agendamentos=agendamentos_disponiveis,
        clientes=clientes_lista,
        veiculos=veiculos_lista
    )


@app.route("/concluir_servico/<int:id>")
@login_required
def concluir_servico(id):
    normalizar_servicos()

    execute_query("""
        UPDATE servicos
        SET status = 'Concluído'
        WHERE id = ?
    """, (id,))

    servico = buscar_servico_por_id(id)
    if servico:
        finalizar_agendamento_relacionado(servico)
        flash("Serviço concluído com sucesso.", "success")

    return redirect(url_for("servicos"))


@app.route("/servicos_pendentes")
@login_required
def servicos_pendentes():
    normalizar_servicos()
    lista_servicos = carregar_servicos()
    q = request.args.get("q", "").strip().lower()

    pendentes = [
        servico for servico in lista_servicos
        if servico.get("status", "Pendente") != "Concluído"
    ]

    if q:
        pendentes = [
            servico for servico in pendentes
            if q in str(servico.get("cliente", "")).lower()
            or q in str(servico.get("veiculo", "")).lower()
            or q in str(servico.get("tipo_servico", "")).lower()
            or q in str(servico.get("status", "")).lower()
        ]

    return render_template("servicos_pendentes.html", servicos=pendentes, q=q)


@app.route("/excluir_servico/<int:id>", methods=["POST"])
@login_required
def excluir_servico(id):
    servico = buscar_servico_por_id(id)

    if not servico:
        flash("Serviço não encontrado.", "danger")
        return redirect(url_for("servicos"))

    if servico_possui_vinculos(servico):
        flash("Este serviço não pode ser excluído porque está vinculado a um agendamento.", "warning")
        return redirect(url_for("servicos"))

    execute_query("DELETE FROM servicos WHERE id = ?", (id,))
    flash("Serviço excluído com sucesso.", "success")
    return redirect(url_for("servicos"))


# =========================
# AGENDAMENTOS
# =========================
@app.route("/agendamentos")
@login_required
def agendamentos():
    normalizar_agendamentos()
    lista_agendamentos = carregar_agendamentos()
    q = request.args.get("q", "").strip().lower()

    ativos = [
        agendamento for agendamento in lista_agendamentos
        if agendamento.get("status", "Agendado") != "Finalizado"
    ]

    if q:
        ativos = [
            agendamento for agendamento in ativos
            if q in str(agendamento.get("cliente", "")).lower()
            or q in str(agendamento.get("veiculo", "")).lower()
            or q in str(agendamento.get("servico", "")).lower()
            or q in str(agendamento.get("data", "")).lower()
            or q in str(agendamento.get("hora", "")).lower()
            or q in str(agendamento.get("status", "")).lower()
        ]

    ativos = sorted(ativos, key=lambda x: (x.get("data", ""), x.get("hora", "")))

    return render_template("agendamentos.html", agendamentos=ativos, q=q)


@app.route("/historico_agendamentos")
@login_required
def historico_agendamentos():
    normalizar_agendamentos()
    lista_agendamentos = carregar_agendamentos()
    q = request.args.get("q", "").strip().lower()

    finalizados = [
        agendamento for agendamento in lista_agendamentos
        if agendamento.get("status", "Agendado") == "Finalizado"
    ]

    if q:
        finalizados = [
            agendamento for agendamento in finalizados
            if q in str(agendamento.get("cliente", "")).lower()
            or q in str(agendamento.get("veiculo", "")).lower()
            or q in str(agendamento.get("servico", "")).lower()
            or q in str(agendamento.get("data", "")).lower()
            or q in str(agendamento.get("hora", "")).lower()
            or q in str(agendamento.get("status", "")).lower()
        ]

    finalizados = sorted(finalizados, key=lambda x: (x.get("data", ""), x.get("hora", "")), reverse=True)

    return render_template("historico_agendamentos.html", agendamentos=finalizados, q=q)


@app.route("/novo_agendamento", methods=["GET", "POST"])
@login_required
def novo_agendamento():
    if request.method == "POST":
        data_agendamento = request.form["data"]
        hora_agendamento = request.form["hora"]

        if existe_conflito_agendamento(data_agendamento, hora_agendamento):
            flash("Já existe um agendamento ativo para esta data e horário.", "danger")
            return redirect(url_for("novo_agendamento"))

        cliente_id = obter_cliente_id_por_form()
        veiculo_id = obter_veiculo_id_por_form()

        if not cliente_id:
            flash("Cliente inválido ou não encontrado.", "danger")
            return redirect(url_for("novo_agendamento"))

        if not veiculo_id:
            flash("Veículo inválido ou não encontrado.", "danger")
            return redirect(url_for("novo_agendamento"))

        execute_query("""
            INSERT INTO agendamentos (cliente_id, veiculo_id, servico, data, hora, status)
            VALUES (?, ?, ?, ?, ?, 'Agendado')
        """, (
            cliente_id,
            veiculo_id,
            request.form["servico"],
            data_agendamento,
            hora_agendamento
        ))

        flash("Agendamento cadastrado com sucesso.", "success")
        return redirect(url_for("agendamentos"))

    clientes_lista = carregar_clientes()
    veiculos_lista = carregar_veiculos()
    return render_template("novo_agendamento.html", clientes=clientes_lista, veiculos=veiculos_lista)


@app.route("/consultar_agendamento/<int:id>")
@login_required
def consultar_agendamento(id):
    normalizar_agendamentos()
    agendamento = buscar_agendamento_por_id(id)
    return render_template("consultar_agendamento.html", agendamento=agendamento, id=id)


@app.route("/editar_agendamento/<int:id>", methods=["GET", "POST"])
@login_required
def editar_agendamento(id):
    normalizar_agendamentos()
    agendamento = buscar_agendamento_por_id(id)

    if not agendamento:
        return render_template("editar_agendamento.html", agendamento=None, id=id)

    if request.method == "POST":
        data_agendamento = request.form["data"]
        hora_agendamento = request.form["hora"]

        if existe_conflito_agendamento(data_agendamento, hora_agendamento, ignorar_id=id):
            flash("Já existe outro agendamento ativo para esta data e horário.", "danger")
            return redirect(url_for("editar_agendamento", id=id))

        cliente_id = obter_cliente_id_por_form()
        veiculo_id = obter_veiculo_id_por_form()

        if not cliente_id:
            flash("Cliente inválido ou não encontrado.", "danger")
            return redirect(url_for("editar_agendamento", id=id))

        if not veiculo_id:
            flash("Veículo inválido ou não encontrado.", "danger")
            return redirect(url_for("editar_agendamento", id=id))

        execute_query("""
            UPDATE agendamentos
            SET cliente_id = ?, veiculo_id = ?, servico = ?, data = ?, hora = ?, status = ?
            WHERE id = ?
        """, (
            cliente_id,
            veiculo_id,
            request.form["servico"],
            data_agendamento,
            hora_agendamento,
            request.form["status"],
            id
        ))

        flash("Agendamento atualizado com sucesso.", "success")
        return redirect(url_for("agendamentos"))

    clientes_lista = carregar_clientes()
    veiculos_lista = carregar_veiculos()

    return render_template(
        "editar_agendamento.html",
        agendamento=agendamento,
        id=id,
        clientes=clientes_lista,
        veiculos=veiculos_lista
    )


@app.route("/excluir_agendamento/<int:id>", methods=["POST"])
@login_required
def excluir_agendamento(id):
    agendamento = buscar_agendamento_por_id(id)

    if not agendamento:
        flash("Agendamento não encontrado.", "danger")
        return redirect(url_for("agendamentos"))

    if agendamento_possui_vinculos(id):
        flash("Este agendamento não pode ser excluído porque está vinculado a um serviço.", "warning")
        return redirect(url_for("agendamentos"))

    execute_query("DELETE FROM agendamentos WHERE id = ?", (id,))
    flash("Agendamento excluído com sucesso.", "success")
    return redirect(url_for("agendamentos"))


if __name__ == "__main__":
    app.run(debug=True)