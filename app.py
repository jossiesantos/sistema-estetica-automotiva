from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/clientes")
def clientes():
    return render_template("clientes.html")

@app.route("/veiculos")
def veiculos():
    return render_template("veiculos.html")

@app.route("/servicos")
def servicos():
    return render_template("servicos.html")

@app.route("/agendamentos")
def agendamentos():
    return render_template("agendamentos.html")

@app.route("/servicos_pendentes")
def servicos_pendentes():
    return render_template("servicos_pendentes.html")

if __name__ == "__main__":
    app.run(debug=True)