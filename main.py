import os
import random
import requests
from flask import Flask, render_template, request, url_for
from werkzeug.utils import redirect
from models import Ingrediente, database
from deep_translator import GoogleTranslator

# Configuração do Aplicativo Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dispensa.db'

# Inicialização do Banco de Dados
database.init_app(app) # Conecta o banco de dados ao aplicativo Flask

with app.app_context():
    database.create_all()
    print("Tabelas criadas/verificadas com sucesso!")

# Contexto do Aplicativo: Cria as tabelas no banco de dados se elas não existirem
with app.app_context():
    pass # As tabelas são gerenciadas automaticamente pelo modelo em 'models.py'

# --- ROTAS PRINCIPAIS ---

@app.route("/")
def dashboard():
    """
        Rota da Página Inicial (Dashboard).
        Busca todos os ingredientes cadastrados no banco de dados,
        calcula o total de itens e renderiza a página 'index.html'.
        """
    todos = Ingrediente.query.all()
    total = len(todos)

    # Retorna o template index.html passando a lista e o total
    return render_template('index.html', ingredientes=todos, total_itens=total)

# --- ROTAS DE AÇÕES NO ESTOQUE ---

@app.route("/adicionar/<int:id>")
def adicionar(id):
    """
        Rota para Aumentar a Quantidade de um Ingrediente (+1).
        Busca o ingrediente pelo ID, incrementa a quantidade e,
        se necessário, reativa o status 'esta_disponivel' para True.
        """
    item = Ingrediente.query.get(id)
    if item:
        item.quantidade += 1
        # Se a quantidade for maior que zero, o status deve ser True (ativado)
        item.esta_disponivel = True
        database.session.commit() # Salva a alteração
    return redirect(url_for('dashboard'))

@app.route("/remover/<int:id>")
def remover(id):
    """
        Rota para Diminuir a Quantidade de um Ingrediente (-1).
        Busca o ingrediente pelo ID, decrementa a quantidade e,
        se chegar a zero, desativa o status 'esta_disponivel' para False.
        """
    item = Ingrediente.query.get(id)
    if item:
        if item.quantidade > 0:
            item.quantidade -= 1
            # Atualização automática do status baseada na quantidade
            # Se qtd > 0 é True, se não, é False
            item.esta_disponivel = True if item.quantidade > 0 else False
            database.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/excluir/<int:id>")
def excluir(id):
    """
        Rota para Excluir um Ingrediente Definitivamente.
        Busca o ingrediente pelo ID e remove o registro do banco de dados.
        """
    # Método moderno para buscar e excluir usando a sessão (database.session)
    item = database.session.get(Ingrediente, id)

    if item:
        # Marca o item para excluir
        database.session.delete(item)
        #Confirma a exclusão
        database.session.commit()

    #Volta para a página inicial
    return redirect(url_for('dashboard'))

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    """
        Rota para Cadastrar um Novo Ingrediente.
        Recebe os dados do formulário via método POST, cria um objeto
        da classe 'Ingrediente' e salva no banco de dados.
        Em seguida, redireciona para a página inicial.
        """
    # Coleta os dados do formulário HTML
    nome = request.form.get("nome")
    cat = request.form.get("categoria")
    qtd = float(request.form.get("quantidade"))
    und = request.form.get("unidade")

    # Cria a nova instância do ingrediente (id é gerado automaticamente)
    novo = Ingrediente(nome=nome, categoria=cat, quantidade=qtd, unidade=und)

    # Adiciona e confirma as alterações no banco de dados (commit)
    database.session.add(novo)
    database.session.commit()

    # Redireciona o usuário de volta para o dashboard
    return redirect(url_for('dashboard'))


import os


@app.route("/gerar_lista")
def gerar_lista():
    """
    Função de Automação de Compras.
    Identifica ingredientes com estoque zerado ou indisponíveis,
    gera um arquivo de texto (.txt) e o disponibiliza para visualização.
    """
    # 1. Busca itens que precisam de reposição
    faltando = Ingrediente.query.filter((Ingrediente.quantidade == 0) | (Ingrediente.esta_disponivel == False)).all()

    if not faltando:
        # Se não falta nada, avisamos no Dashboard
        todos = Ingrediente.query.all()
        return render_template('index.html', ingredientes=todos, total_itens=len(todos),
                               erro="🎉 Tudo em dia! Você não precisa comprar nada agora.")

    # 2. Cria o conteúdo da lista
    conteúdo = "🛒 LISTA DE COMPRAS - DISPENSA ANDERSON\n"
    conteúdo += "--------------------------------------\n"
    for item in faltando:
        conteúdo += f"[ ] {item.nome} ({item.categoria})\n"

    # 3. Salva um arquivo temporário (Boa prática de sistemas)
    caminho_arquivo = "lista_de_compras.txt"
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(conteúdo)

    # 4. Mostra a lista na tela para o usuário
    todos = Ingrediente.query.all()
    return render_template('index.html', ingredientes=todos, total_itens=len(todos), lista_texto=conteúdo)

# 2. Cria o conteúdo da lista


# --- ROTAS DE INTELIGÊNCIA ---

@app.route("/sugerir")
def sugerir_receita():
    """
        Rota para Sugestão Simples de Janta (Antiga).
        Sorteia uma proteína e um carboidrato que estão disponíveis.
        Retorna a frase da sugestão para o HTML.
        """
    # Busca apenas o que tem no estoque (quantidade > 0)
    disponiveis = Ingrediente.query.filter(Ingrediente.quantidade > 0).all()
    # Cria uma lista de nomes em minúsculo para a lógica de 'if'
    nomes = [item.nome.lower() for item in disponiveis]

    # Lógica de 'if' para as receitas favoritas
    if "frango" in nomes and "arroz" in nomes:
        sugestao = "🍗 Que tal uma Canja de Galinha caprichada?"
    elif "carne" in nomes and "feijão" in nomes:
        sugestao = "🍲 Hora de um Feijão Tropeiro mineiro!"
    # Se tiver mais de um item, faz um improviso
    elif len(nomes) > 1:
        # Sorteia dois itens aleatórios da lista de disponíveis
        item1 = random.choice(disponiveis)
        item2 = random.choice(disponiveis)
        sugestao = f"🎲 Improviso do Chef:{item1.nome} com {item2}!"
    else:
        sugestao = "⚠️ Estoque muito baixo para sugerir algo especial."

    todos = Ingrediente.query.all()
    # Retorna o dashboard com a sugestão fixa na variável 'receita_externa'
    return render_template('index.html', ingredientes=todos, total_itens=len(todos), receita_externa=sugestao)


@app.route("/consultar_receitas")
def consultar_receitas():
    """
    Função automatizada que busca receitas na web, traduz os resultados
    para português e exibe os detalhes completos (foto e preparo).
    """
    disponiveis = Ingrediente.query.filter(Ingrediente.quantidade > 0).all()
    nome_prato, foto_prato, preparo_prato, erro = "", "", "", ""

    # Criamos o objeto tradutor (de inglês para português)
    tradutor = GoogleTranslator(source='en', target='pt')

    for item in disponiveis:
        traducoes = {"Arroz": "Rice", "Frango": "Chicken", "Carne": "Beef", "Feijão": "Beans"}
        termo_busca = traducoes.get(item.nome, item.nome)

        url_busca = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={termo_busca}"
        try:
            res_busca = requests.get(url_busca, timeout=5).json()
            if res_busca and res_busca.get('meals'):
                prato = random.choice(res_busca['meals'])

                # Busca os detalhes
                res_detalhes = requests.get(
                    f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={prato['idMeal']}").json()
                if res_detalhes and res_detalhes.get('meals'):
                    detalhes = res_detalhes['meals'][0]

                    # AUTOMAÇÃO DE TRADUÇÃO: Traduzimos o nome e o preparo
                    nome_prato = tradutor.translate(detalhes['strMeal'])
                    preparo_prato = tradutor.translate(detalhes['strInstructions'])
                    foto_prato = detalhes['strMealThumb']
                    break
        except:
            continue

    if not nome_prato:
        erro = "Não encontrei receitas para traduzir no momento."

    todos = Ingrediente.query.all()
    return render_template('index.html', ingredientes=todos, total_itens=len(todos),
                           erro=erro, nome_receita=nome_prato,
                           foto_receita=foto_prato, preparo_receita=preparo_prato)



if __name__ == "__main__":
    # O Render injeta a porta automaticamente nesta variável de ambiente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)