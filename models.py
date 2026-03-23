from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class Ingrediente(database.Model):
    id = database.Column(database.Integer, primary_key=True)

    nome = database.Column(database.String(100), nullable=False, unique=True)

    categoria = database.Column(database.String(50), nullable=False)

    esta_disponivel = database.Column(database.Boolean, default=True)

    quantidade = database.Column(database.Float, default=0.0)

    unidade = database.Column(database.String(20), default="unidade")


    def __repr__(self):
        return f"<Ingrediente {self.nome}>"