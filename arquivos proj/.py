from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  # Importação correta de text
from datetime import datetime
import hashlib

app = Flask(__name__)

app.secret_key = 'Lepe'

app.config['SQLALCHEMY_DATABASE_URI'] = \
    '{SGDB}://{usuario}:{senha}@{servidor}/{database}'.format(
        SGDB='mysql+mysqlconnector',
        usuario='root',
        senha='',
        servidor='localhost',
        database='bd_projetoPY'
    )

db = SQLAlchemy(app)

class Usuarios(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(32), nullable=False, unique=True)
    senha = db.Column(db.String(32), nullable=False)
    dtcria = db.Column(db.DateTime, default=db.func.now())
    estatus = db.Column(db.String(1), default='')

    anotacoes = db.relationship('Anotacoes', backref='usuario', cascade='all, delete-orphan')

class Anotacoes(db.Model):
    __tablename__ = 'anotacoes'

    id = db.Column(db.Integer, primary_key=True)
    nome_anotacao = db.Column(db.String(50), nullable=False)
    descricao_anotacao = db.Column(db.String(200), nullable=True)
    data_anotacao = db.Column(db.Date, nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def login():
    error_message = None  # Inicializa com nenhum erro
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        
        senha_md5 = hashlib.md5(senha.encode()).hexdigest()  # Converte a senha para MD5

        user = Usuarios.query.filter_by(email=email, senha=senha_md5).first()

        if user:
            session['logged_in'] = True
            session['user_id'] = user.id_usuario  # Armazena o ID do usuário na sessão
            return redirect(url_for('lista_anotacoes'))
        else:
            error_message = "Login falhou. Verifique o e-mail e a senha."

    return render_template('login.html', error_message = error_message)

@app.route('/cadastrarUsuario', methods=['GET', 'POST'])
def cadastrarUsuario():
    error_message = None  # Inicializa com nenhum erro
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        
        try:
            # Verificar se o email já está cadastrado
            existing_user = db.session.execute(
                text("SELECT * FROM usuarios WHERE email = :email"),
                {'email': email}
            ).fetchone()
            
            if existing_user:
                error_message = "E-mail já cadastrado. Tente outro."
            else:
                # Inserir o novo usuário no banco de dados
                db.session.execute(
                    text("""
                        INSERT INTO usuarios (nome, email, senha)
                        VALUES (:nome, :email, md5(:senha))
                    """),
                    {'nome': nome, 'email': email, 'senha': password}
                )
                db.session.commit()  # Confirma a transação no banco
                
                # Redireciona para a tela de login após o cadastro
                return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()  # Reverte a transação em caso de erro
            error_message = f"Erro ao cadastrar: {str(e)}"
    
    return render_template('cadastro.html', error_message=error_message)


@app.route('/lista', methods=['GET'])
def lista_anotacoes():
    # Verifique se o usuário está logado
    if 'logged_in' not in session:
        return redirect(url_for('login'))  # Redirecione para a página de login se não estiver logado

    user_id = session.get('user_id')

    lista_tabela = Anotacoes.query.filter_by(id_usuario=user_id).order_by(Anotacoes.data_anotacao.asc()).all()

    return render_template("lista.html",
                           descricao="Bem-vindo ao seu bloco de anotações",
                           bloco_anotacoes=lista_tabela)

@app.route('/sobre')
def sobre():
    # Verifique se o usuário está logado
    if 'logged_in' not in session:
        return redirect(url_for('login'))  # Redirecione para a página de login se não estiver logado
    return render_template("sobre.html")

@app.route('/cadastrar')
def cadastrar_tarefa():
    if 'logged_in' not in session:
        return redirect(url_for('login'))  # Verifica se está logado
    return render_template("cadastrar.html")

@app.route("/inserir", methods=['POST'])
def adicionar_anotacao():
    if 'logged_in' not in session:  # Verifica se o usuário está logado
        return redirect(url_for('login'))  # Redireciona para a tela de login

    # Obtém os dados do formulário
    nome = request.form['txtNome']
    descricao = request.form['txtDescricao']
    data = request.form['txtData']

    # Converte a data para o formato datetime ou define como None
    if data:
        try:
            data = datetime.strptime(data, '%d/%m/%Y')  # Ajusta o formato da data
        except ValueError:
            print("Formato de data inválido")
            return redirect(url_for('cadastrar_tarefa'))  # Redireciona para o formulário
    else:
        data = None

    # Obtém o ID do usuário logado a partir da sessão
    user_id = session.get('user_id')

    # Cria a nova anotação associada ao usuário logado
    nova_anotacao = Anotacoes(
        nome_anotacao=nome,
        descricao_anotacao=descricao,
        data_anotacao=data,
        id_usuario=user_id  # Associação ao usuário logado
    )

    # Salva a anotação no banco de dados
    db.session.add(nova_anotacao)
    db.session.commit()

    return redirect(url_for('lista_anotacoes'))  # Redireciona para a lista de anotações


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_registro(id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))  # Verifica se está logado
    editar_anota = db.session.get(Anotacoes, id)

    if request.method == 'POST':
        editar_anota.nome_anotacao = request.form['txtNome']
        editar_anota.descricao_anotacao = request.form['txtDescricao']
        data = request.form['txtData']

        if data:
            try:
                editar_anota.data_anotacao = datetime.strptime(data, '%d/%m/%Y')  # Converte para datetime
            except ValueError:
                print("Formato de data inválido")
                return redirect(f'/editar/{id}')  # Redireciona se a data for inválida
        else:
            editar_anota.data_anotacao = None  # Se a data não foi fornecida, define como None

        db.session.commit()
        return redirect('/lista')

    return render_template('editar.html', anotacoes=editar_anota)

@app.route("/excluir/<int:id>", methods=['POST'])
def excluir_registro(id):
    # Verifique se o usuário está logado
    if 'logged_in' not in session:
        return redirect(url_for('login'))  # Redirecione para a página de login se não estiver logado
    excluir_anota = db.session.get(Anotacoes, id)

    if request.method == 'POST':
        db.session.delete(excluir_anota)
        db.session.commit()

    return redirect('/lista')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove o estado de login
    return redirect(url_for('login'))  # Redireciona para a página de login

# Executando a aplicação
if __name__ == "__main__":
    app.run(debug=True)  # Adicione debug=True para facilitar o desenvolvimento
