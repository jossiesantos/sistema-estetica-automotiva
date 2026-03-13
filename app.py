import json
import os
from functools import wraps
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "sistema_estetica_automotiva_chave_secreta_123"

ARQUIVO_CLIENTES = "clientes.json"
ARQUIVO_VEICULOS = "veiculos.json"
ARQUIVO_SERVICOS = "servicos.json"
ARQUIVO_AGENDAMENTOS = "agendamentos.json"

USUARIOS = [
    {"id": 1, "usuario": "admin", "senha": "1234"}
]


# =========================
# FUNÇÕES GENÉRICAS
# =========================
def carregar_json(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario_logado" not in session:
            flash("Faça login para acessar o sistema.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def usuario_autenticado(usuario, senha):
    for item in USUARIOS:
        if item["usuario"] == usuario and item["senha"] == senha:
            return item
    return None


def converter_valor_para_float(valor):
    try:
        valor_limpo = str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor_limpo)
    except:
        return 0.0


def identificar_veiculo(veiculo):
    marca = veiculo.get("marca", "").strip()
    modelo = veiculo.get("modelo", "").strip()
    placa = veiculo.get("placa", "").strip()

    descricao = f"{marca} {modelo}".strip()
    if placa:
        descricao = f"{descricao} - {placa}" if descricao else placa

    return descricao.strip()


def texto_normalizado(texto):
    return str(texto).strip().lower()


# =========================
# CLIENTES
# =========================
def carregar_clientes():
    return carregar_json(ARQUIVO_CLIENTES)


def salvar_clientes(clientes):
    salvar_json(ARQUIVO_CLIENTES, clientes)


def buscar_cliente_por_id(cliente_id):
    clientes = carregar_clientes()
    for cliente in clientes:
        if cliente["id"] == cliente_id:
            return cliente
    return None


def proximo_id_clientes():
    clientes = carregar_clientes()
    if not clientes:
        return 1
    return max(cliente["id"] for cliente in clientes) + 1


# =========================
# VEÍCULOS
# =========================
def carregar_veiculos():
    return carregar_json(ARQUIVO_VEICULOS)


def salvar_veiculos(veiculos):
    salvar_json(ARQUIVO_VEICULOS, veiculos)


def buscar_veiculo_por_id(veiculo_id):
    veiculos = carregar_veiculos()
    for veiculo in veiculos:
        if veiculo["id"] == veiculo_id:
            return veiculo
    return None


def proximo_id_veiculos():
    veiculos = carregar_veiculos()
    if not veiculos:
        return 1
    return max(veiculo["id"] for veiculo in veiculos) + 1


# =========================
# SERVIÇOS
# =========================
def carregar_servicos():
    return carregar_json(ARQUIVO_SERVICOS)


def salvar_servicos(servicos):
    salvar_json(ARQUIVO_SERVICOS, servicos)


def buscar_servico_por_id(servico_id):
    servicos = carregar_servicos()
    for servico in servicos:
        if servico["id"] == servico_id:
            return servico
    return None


def proximo_id_servicos():
    servicos = carregar_servicos()
    if not servicos:
        return 1
    return max(servico["id"] for servico in servicos) + 1


def normalizar_servicos():
    servicos = carregar_servicos()
    alterou = False

    for servico in servicos:
        if "status" not in servico:
            servico["status"] = "Pendente"
            alterou = True
        if "agendamento_id" not in servico:
            servico["agendamento_id"] = None
            alterou = True

    if alterou:
        salvar_servicos(servicos)


# =========================
# AGENDAMENTOS
# =========================
def carregar_agendamentos():
    return carregar_json(ARQUIVO_AGENDAMENTOS)


def salvar_agendamentos(agendamentos):
    salvar_json(ARQUIVO_AGENDAMENTOS, agendamentos)


def buscar_agendamento_por_id(agendamento_id):
    agendamentos = carregar_agendamentos()
    for agendamento in agendamentos:
        if agendamento["id"] == agendamento_id:
            return agendamento
    return None


def proximo_id_agendamentos():
    agendamentos = carregar_agendamentos()
    if not agendamentos:
        return 1
    return max(agendamento["id"] for agendamento in agendamentos) + 1


def normalizar_agendamentos():
    agendamentos = carregar_agendamentos()
    alterou = False

    for agendamento in agendamentos:
        if "status" not in agendamento:
            agendamento["status"] = "Agendado"
            alterou = True

    if alterou:
        salvar_agendamentos(agendamentos)


def finalizar_agendamento_relacionado(servico):
    agendamento_id = servico.get("agendamento_id")

    if not agendamento_id:
        return

    agendamentos = carregar_agendamentos()
    alterou = False

    for agendamento in agendamentos:
        if agendamento["id"] == agendamento_id:
            agendamento["status"] = "Finalizado"
            alterou = True
            break

    if alterou:
        salvar_agendamentos(agendamentos)


def existe_conflito_agendamento(data_agendamento, hora_agendamento, ignorar_id=None):
    normalizar_agendamentos()
    agendamentos = carregar_agendamentos()

    for agendamento in agendamentos:
        if ignorar_id is not None and agendamento["id"] == ignorar_id:
            continue

        status = agendamento.get("status", "Agendado").strip().lower()

        if status == "finalizado":
            continue

        if agendamento.get("data") == data_agendamento and agendamento.get("hora") == hora_agendamento:
            return True

    return False


# =========================
# REGRAS DE EXCLUSÃO
# =========================
def cliente_possui_vinculos(cliente):
    nome_cliente = texto_normalizado(cliente.get("nome", ""))

    veiculos = carregar_veiculos()
    servicos = carregar_servicos()
    agendamentos = carregar_agendamentos()

    for veiculo in veiculos:
        if texto_normalizado(veiculo.get("cliente", "")) == nome_cliente:
            return True

    for servico in servicos:
        if texto_normalizado(servico.get("cliente", "")) == nome_cliente:
            return True

    for agendamento in agendamentos:
        if texto_normalizado(agendamento.get("cliente", "")) == nome_cliente:
            return True

    return False


def veiculo_possui_vinculos(veiculo):
    candidatos = set()

    placa = texto_normalizado(veiculo.get("placa", ""))
    modelo = texto_normalizado(veiculo.get("modelo", ""))
    marca = texto_normalizado(veiculo.get("marca", ""))
    descricao = texto_normalizado(identificar_veiculo(veiculo))
    marca_modelo = texto_normalizado(f"{veiculo.get('marca', '')} {veiculo.get('modelo', '')}".strip())

    for item in [placa, modelo, marca, descricao, marca_modelo]:
        if item:
            candidatos.add(item)

    servicos = carregar_servicos()
    agendamentos = carregar_agendamentos()

    for servico in servicos:
        if texto_normalizado(servico.get("veiculo", "")) in candidatos:
            return True

    for agendamento in agendamentos:
        if texto_normalizado(agendamento.get("veiculo", "")) in candidatos:
            return True

    return False


def servico_possui_vinculos(servico):
    return servico.get("agendamento_id") is not None


def agendamento_possui_vinculos(agendamento_id):
    servicos = carregar_servicos()
    for servico in servicos:
        if servico.get("agendamento_id") == agendamento_id:
            return True
    return False


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
            if q in cliente.get("nome", "").lower()
            or q in cliente.get("telefone", "").lower()
            or q in cliente.get("email", "").lower()
        ]

    return render_template("clientes.html", clientes=lista_clientes, q=q)


@app.route("/novo_cliente", methods=["GET", "POST"])
@login_required
def novo_cliente():
    if request.method == "POST":
        clientes = carregar_clientes()

        novo = {
            "id": proximo_id_clientes(),
            "nome": request.form["nome"],
            "telefone": request.form["telefone"],
            "email": request.form["email"]
        }

        clientes.append(novo)
        salvar_clientes(clientes)
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
    clientes = carregar_clientes()
    cliente = None

    for item in clientes:
        if item["id"] == id:
            cliente = item
            break

    if not cliente:
        return render_template("editar_cliente.html", cliente=None, id=id)

    if request.method == "POST":
        cliente["nome"] = request.form["nome"]
        cliente["telefone"] = request.form["telefone"]
        cliente["email"] = request.form["email"]

        salvar_clientes(clientes)
        flash("Cliente atualizado com sucesso.", "success")
        return redirect(url_for("clientes"))

    return render_template("editar_cliente.html", cliente=cliente, id=id)


@app.route("/excluir_cliente/<int:id>", methods=["POST"])
@login_required
def excluir_cliente(id):
    clientes = carregar_clientes()
    cliente = buscar_cliente_por_id(id)

    if not cliente:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for("clientes"))

    if cliente_possui_vinculos(cliente):
        flash("Este cliente não pode ser excluído porque possui vínculos com veículos, serviços ou agendamentos.", "warning")
        return redirect(url_for("clientes"))

    clientes = [c for c in clientes if c["id"] != id]
    salvar_clientes(clientes)
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
                q in veiculo.get("cliente", "").lower()
                or q in veiculo.get("modelo", "").lower()
                or q in veiculo.get("marca", "").lower()
                or q in veiculo.get("placa", "").lower()
                or q in texto_veiculo
            ):
                filtrados.append(veiculo)
        lista_veiculos = filtrados

    return render_template("veiculos.html", veiculos=lista_veiculos, q=q)


@app.route("/novo_veiculo", methods=["GET", "POST"])
@login_required
def novo_veiculo():
    if request.method == "POST":
        veiculos = carregar_veiculos()

        novo = {
            "id": proximo_id_veiculos(),
            "cliente": request.form["cliente"],
            "modelo": request.form["modelo"],
            "marca": request.form["marca"],
            "placa": request.form["placa"],
            "cor": request.form["cor"]
        }

        veiculos.append(novo)
        salvar_veiculos(veiculos)
        flash("Veículo cadastrado com sucesso.", "success")
        return redirect(url_for("veiculos"))

    return render_template("novo_veiculo.html")


@app.route("/consultar_veiculo/<int:id>")
@login_required
def consultar_veiculo(id):
    veiculo = buscar_veiculo_por_id(id)
    return render_template("consultar_veiculo.html", veiculo=veiculo, id=id)


@app.route("/editar_veiculo/<int:id>", methods=["GET", "POST"])
@login_required
def editar_veiculo(id):
    veiculos = carregar_veiculos()
    veiculo = None

    for item in veiculos:
        if item["id"] == id:
            veiculo = item
            break

    if not veiculo:
        return render_template("editar_veiculo.html", veiculo=None, id=id)

    if request.method == "POST":
        veiculo["cliente"] = request.form["cliente"]
        veiculo["modelo"] = request.form["modelo"]
        veiculo["marca"] = request.form["marca"]
        veiculo["placa"] = request.form["placa"]
        veiculo["cor"] = request.form["cor"]

        salvar_veiculos(veiculos)
        flash("Veículo atualizado com sucesso.", "success")
        return redirect(url_for("veiculos"))

    return render_template("editar_veiculo.html", veiculo=veiculo, id=id)


@app.route("/excluir_veiculo/<int:id>", methods=["POST"])
@login_required
def excluir_veiculo(id):
    veiculos = carregar_veiculos()
    veiculo = buscar_veiculo_por_id(id)

    if not veiculo:
        flash("Veículo não encontrado.", "danger")
        return redirect(url_for("veiculos"))

    if veiculo_possui_vinculos(veiculo):
        flash("Este veículo não pode ser excluído porque possui vínculos com serviços ou agendamentos.", "warning")
        return redirect(url_for("veiculos"))

    veiculos = [v for v in veiculos if v["id"] != id]
    salvar_veiculos(veiculos)
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
            if q in servico.get("cliente", "").lower()
            or q in servico.get("veiculo", "").lower()
            or q in servico.get("tipo_servico", "").lower()
            or q in servico.get("status", "").lower()
        ]

    return render_template("servicos.html", servicos=lista_servicos, q=q)


@app.route("/novo_servico", methods=["GET", "POST"])
@login_required
def novo_servico():
    normalizar_agendamentos()

    if request.method == "POST":
        servicos = carregar_servicos()

        agendamento_id = request.form.get("agendamento_id")
        agendamento_id = int(agendamento_id) if agendamento_id else None

        novo = {
            "id": proximo_id_servicos(),
            "cliente": request.form["cliente"],
            "veiculo": request.form["veiculo"],
            "tipo_servico": request.form["tipo_servico"],
            "valor": request.form["valor"],
            "status": request.form["status"],
            "agendamento_id": agendamento_id
        }

        servicos.append(novo)
        salvar_servicos(servicos)
        flash("Serviço cadastrado com sucesso.", "success")
        return redirect(url_for("servicos"))

    agendamentos = carregar_agendamentos()
    agendamentos_ativos = [
        agendamento for agendamento in agendamentos
        if agendamento.get("status", "Agendado") != "Finalizado"
    ]

    return render_template("novo_servico.html", agendamentos=agendamentos_ativos)


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

    servicos = carregar_servicos()
    servico = None

    for item in servicos:
        if item["id"] == id:
            servico = item
            break

    if not servico:
        return render_template("editar_servico.html", servico=None, id=id, agendamentos=[])

    if request.method == "POST":
        status_anterior = servico.get("status", "Pendente")

        agendamento_id = request.form.get("agendamento_id")
        agendamento_id = int(agendamento_id) if agendamento_id else None

        servico["cliente"] = request.form["cliente"]
        servico["veiculo"] = request.form["veiculo"]
        servico["tipo_servico"] = request.form["tipo_servico"]
        servico["valor"] = request.form["valor"]
        servico["status"] = request.form["status"]
        servico["agendamento_id"] = agendamento_id

        salvar_servicos(servicos)

        if status_anterior != "Concluído" and servico["status"] == "Concluído":
            finalizar_agendamento_relacionado(servico)

        flash("Serviço atualizado com sucesso.", "success")
        return redirect(url_for("servicos"))

    agendamentos = carregar_agendamentos()
    agendamentos_disponiveis = [
        agendamento for agendamento in agendamentos
        if agendamento.get("status", "Agendado") != "Finalizado"
        or agendamento["id"] == servico.get("agendamento_id")
    ]

    return render_template(
        "editar_servico.html",
        servico=servico,
        id=id,
        agendamentos=agendamentos_disponiveis
    )


@app.route("/concluir_servico/<int:id>")
@login_required
def concluir_servico(id):
    normalizar_servicos()
    servicos = carregar_servicos()

    for servico in servicos:
        if servico["id"] == id:
            servico["status"] = "Concluído"
            salvar_servicos(servicos)
            finalizar_agendamento_relacionado(servico)
            flash("Serviço concluído com sucesso.", "success")
            break

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
            if q in servico.get("cliente", "").lower()
            or q in servico.get("veiculo", "").lower()
            or q in servico.get("tipo_servico", "").lower()
            or q in servico.get("status", "").lower()
        ]

    return render_template("servicos_pendentes.html", servicos=pendentes, q=q)


@app.route("/excluir_servico/<int:id>", methods=["POST"])
@login_required
def excluir_servico(id):
    servicos = carregar_servicos()
    servico = buscar_servico_por_id(id)

    if not servico:
        flash("Serviço não encontrado.", "danger")
        return redirect(url_for("servicos"))

    if servico_possui_vinculos(servico):
        flash("Este serviço não pode ser excluído porque está vinculado a um agendamento.", "warning")
        return redirect(url_for("servicos"))

    servicos = [s for s in servicos if s["id"] != id]
    salvar_servicos(servicos)
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
            if q in agendamento.get("cliente", "").lower()
            or q in agendamento.get("veiculo", "").lower()
            or q in agendamento.get("servico", "").lower()
            or q in agendamento.get("data", "").lower()
            or q in agendamento.get("hora", "").lower()
            or q in agendamento.get("status", "").lower()
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
            if q in agendamento.get("cliente", "").lower()
            or q in agendamento.get("veiculo", "").lower()
            or q in agendamento.get("servico", "").lower()
            or q in agendamento.get("data", "").lower()
            or q in agendamento.get("hora", "").lower()
            or q in agendamento.get("status", "").lower()
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

        agendamentos = carregar_agendamentos()

        novo = {
            "id": proximo_id_agendamentos(),
            "cliente": request.form["cliente"],
            "veiculo": request.form["veiculo"],
            "servico": request.form["servico"],
            "data": data_agendamento,
            "hora": hora_agendamento,
            "status": "Agendado"
        }

        agendamentos.append(novo)
        salvar_agendamentos(agendamentos)
        flash("Agendamento cadastrado com sucesso.", "success")
        return redirect(url_for("agendamentos"))

    return render_template("novo_agendamento.html")


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
    agendamentos = carregar_agendamentos()
    agendamento = None

    for item in agendamentos:
        if item["id"] == id:
            agendamento = item
            break

    if not agendamento:
        return render_template("editar_agendamento.html", agendamento=None, id=id)

    if request.method == "POST":
        data_agendamento = request.form["data"]
        hora_agendamento = request.form["hora"]

        if existe_conflito_agendamento(data_agendamento, hora_agendamento, ignorar_id=id):
            flash("Já existe outro agendamento ativo para esta data e horário.", "danger")
            return redirect(url_for("editar_agendamento", id=id))

        agendamento["cliente"] = request.form["cliente"]
        agendamento["veiculo"] = request.form["veiculo"]
        agendamento["servico"] = request.form["servico"]
        agendamento["data"] = data_agendamento
        agendamento["hora"] = hora_agendamento
        agendamento["status"] = request.form["status"]

        salvar_agendamentos(agendamentos)
        flash("Agendamento atualizado com sucesso.", "success")
        return redirect(url_for("agendamentos"))

    return render_template("editar_agendamento.html", agendamento=agendamento, id=id)


@app.route("/excluir_agendamento/<int:id>", methods=["POST"])
@login_required
def excluir_agendamento(id):
    agendamentos = carregar_agendamentos()
    agendamento = buscar_agendamento_por_id(id)

    if not agendamento:
        flash("Agendamento não encontrado.", "danger")
        return redirect(url_for("agendamentos"))

    if agendamento_possui_vinculos(id):
        flash("Este agendamento não pode ser excluído porque está vinculado a um serviço.", "warning")
        return redirect(url_for("agendamentos"))

    agendamentos = [a for a in agendamentos if a["id"] != id]
    salvar_agendamentos(agendamentos)
    flash("Agendamento excluído com sucesso.", "success")
    return redirect(url_for("agendamentos"))


if __name__ == "__main__":
    app.run(debug=True)
