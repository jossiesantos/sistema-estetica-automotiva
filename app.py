from flask import Flask, render_template

app = Flask(__name__)

# =========================
# PÁGINA INICIAL
# =========================
@app.route("/")
def inicio():
    return render_template("index.html")


# =========================
# CLIENTES
# =========================
@app.route("/clientes")
def clientes():
    return render_template("clientes.html")


@app.route("/novo_cliente")
def novo_cliente():
    return render_template("novo_cliente.html")


@app.route("/consultar_cliente/<int:id>")
def consultar_cliente(id):
    clientes = {
        1: {"nome": "João Silva", "telefone": "(14) 99999-1111", "email": "joao@email.com"},
        2: {"nome": "Maria Souza", "telefone": "(14) 98888-2222", "email": "maria@email.com"}
    }

    cliente = clientes.get(id)
    return render_template("consultar_cliente.html", cliente=cliente, id=id)


@app.route("/editar_cliente/<int:id>")
def editar_cliente(id):
    clientes = {
        1: {"nome": "João Silva", "telefone": "(14) 99999-1111", "email": "joao@email.com"},
        2: {"nome": "Maria Souza", "telefone": "(14) 98888-2222", "email": "maria@email.com"}
    }

    cliente = clientes.get(id)
    return render_template("editar_cliente.html", cliente=cliente, id=id)


# =========================
# VEÍCULOS
# =========================
@app.route("/veiculos")
def veiculos():
    return render_template("veiculos.html")


@app.route("/novo_veiculo")
def novo_veiculo():
    return render_template("novo_veiculo.html")


@app.route("/consultar_veiculo/<int:id>")
def consultar_veiculo(id):
    veiculos = {
        1: {
            "cliente": "João Silva",
            "modelo": "Gol",
            "marca": "Volkswagen",
            "placa": "ABC-1234",
            "cor": "Branco"
        },
        2: {
            "cliente": "Maria Souza",
            "modelo": "HB20",
            "marca": "Hyundai",
            "placa": "DEF-5678",
            "cor": "Prata"
        }
    }

    veiculo = veiculos.get(id)
    return render_template("consultar_veiculo.html", veiculo=veiculo, id=id)


@app.route("/editar_veiculo/<int:id>")
def editar_veiculo(id):
    veiculos = {
        1: {
            "cliente": "João Silva",
            "modelo": "Gol",
            "marca": "Volkswagen",
            "placa": "ABC-1234",
            "cor": "Branco"
        },
        2: {
            "cliente": "Maria Souza",
            "modelo": "HB20",
            "marca": "Hyundai",
            "placa": "DEF-5678",
            "cor": "Prata"
        }
    }

    veiculo = veiculos.get(id)
    return render_template("editar_veiculo.html", veiculo=veiculo, id=id)


# =========================
# SERVIÇOS
# =========================
@app.route("/servicos")
def servicos():
    return render_template("servicos.html")


@app.route("/servicos_pendentes")
def servicos_pendentes():
    return render_template("servicos_pendentes.html")


# =========================
# AGENDAMENTOS
# =========================
@app.route("/agendamentos")
def agendamentos():
    return render_template("agendamentos.html")


# =========================
# EXECUÇÃO
# =========================
@app.route("/novo_servico")
def novo_servico():
    return render_template("novo_servico.html")

@app.route("/consultar_servico/<int:id>")
def consultar_servico(id):
    servicos = {
        1: {
            "cliente": "João Silva",
            "veiculo": "Gol",
            "tipo_servico": "Lavagem Completa",
            "valor": "80,00",
            "status": "Pendente"
        },
        2: {
            "cliente": "Maria Souza",
            "veiculo": "HB20",
            "tipo_servico": "Polimento",
            "valor": "120,00",
            "status": "Em andamento"
        }
    }

    servico = servicos.get(id)
    return render_template("consultar_servico.html", servico=servico, id=id)

@app.route("/editar_servico/<int:id>")
def editar_servico(id):
    servicos = {
        1: {
            "cliente": "João Silva",
            "veiculo": "Gol",
            "tipo_servico": "Lavagem Completa",
            "valor": "80,00",
            "status": "Pendente"
        },
        2: {
            "cliente": "Maria Souza",
            "veiculo": "HB20",
            "tipo_servico": "Polimento",
            "valor": "120,00",
            "status": "Em andamento"
        }
    }

    servico = servicos.get(id)
    return render_template("editar_servico.html", servico=servico, id=id)
@app.route("/novo_agendamento")
def novo_agendamento():
    return render_template("novo_agendamento.html")


@app.route("/consultar_agendamento/<int:id>")
def consultar_agendamento(id):

    agendamentos = {
        1: {
            "cliente": "João Silva",
            "veiculo": "Gol",
            "servico": "Lavagem Completa",
            "data": "10/03/2026",
            "hora": "09:00"
        },
        2: {
            "cliente": "Maria Souza",
            "veiculo": "HB20",
            "servico": "Polimento",
            "data": "11/03/2026",
            "hora": "14:00"
        }
    }

    agendamento = agendamentos.get(id)

    return render_template("consultar_agendamento.html", agendamento=agendamento, id=id)


@app.route("/editar_agendamento/<int:id>")
def editar_agendamento(id):

    agendamentos = {
        1: {
            "cliente": "João Silva",
            "veiculo": "Gol",
            "servico": "Lavagem Completa",
            "data": "10/03/2026",
            "hora": "09:00"
        },
        2: {
            "cliente": "Maria Souza",
            "veiculo": "HB20",
            "servico": "Polimento",
            "data": "11/03/2026",
            "hora": "14:00"
        }
    }

    agendamento = agendamentos.get(id)

    return render_template("editar_agendamento.html", agendamento=agendamento, id=id)
if __name__ == "__main__":
    app.run(debug=True)