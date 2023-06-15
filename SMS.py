import sqlite3
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = '87862936'  # Chave secreta para sessões

# Função auxiliar para criar uma nova conexão com o banco de dados
def get_db_connection():
    conn = sqlite3.connect('usuarios.db')
    conn.row_factory = sqlite3.Row
    return conn

# Criando o banco de dados e a tabela de usuários se eles não existirem
def create_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           nome TEXT,
                           senha TEXT,
                           status TEXT)''')
        conn.commit()

# Função auxiliar para fechar a conexão com o banco de dados
def close_db_connection(exception=None):
    conn = get_db_connection()
    conn.close()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            # Verifique as credenciais do usuário
            cursor.execute("SELECT * FROM usuarios WHERE nome=? AND senha=?", (username, password))
            usuario = cursor.fetchone()
            
            if usuario:
                if usuario['status'] == 'Desativado':
                    return redirect('/acesso_negado')
                else:
                    session['autenticado'] = True
                    session['usuario'] = usuario['nome']  # Nome do usuário
                    return redirect('https://bot-bolsa.streamlit.app/')
            else:
                # Caso as credenciais sejam inválidas, renderize a página de login novamente
                return render_template('login.html', mensagem='Credenciais inválidas')
        
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            # Verifique se o usuário já está cadastrado
            cursor.execute("SELECT * FROM usuarios WHERE nome=?", (username,))
            usuario = cursor.fetchone()
            
            if usuario:
                return render_template('cadastro.html', mensagem='Usuário já cadastrado')
            
            # Insere o novo usuário no banco de dados
            cursor.execute("INSERT INTO usuarios (nome, senha, status) VALUES (?, ?, ?)", (username, password, 'Ativo'))
            conn.commit()
            
            # Redirecione para a página de dashboard após o cadastro
            session['autenticado'] = True
            session['usuario'] = username
            return redirect('/dashboard')
        
    return render_template('cadastro.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Verifique se o usuário está autenticado
    if 'autenticado' in session and session['autenticado']:
        # Obtenha o nome do usuário atual
        usuario_atual = session['usuario']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if request.method == 'POST':
                username = request.form['username']
                
                # Localize o usuário no banco de dados
                cursor.execute("SELECT * FROM usuarios WHERE nome=?", (username,))
                usuario = cursor.fetchone()
                
                if usuario:
                    # Alterne o status do usuário entre Ativo e Desativado
                    novo_status = 'Ativo' if usuario['status'] == 'Desativado' else 'Desativado'
                    cursor.execute("UPDATE usuarios SET status=? WHERE nome=?", (novo_status, username))
                    conn.commit()
                    
                    # Redirecione para a página de dashboard após a atualização
                    return redirect('/dashboard')
                else:
                    return render_template('dashboard.html', mensagem='Usuário não encontrado')
            
            # Obtenha todos os usuários do banco de dados
            cursor.execute("SELECT * FROM usuarios")
            usuarios = cursor.fetchall()
            
            return render_template('dashboard.html', usuarios=usuarios, usuario_atual=usuario_atual)
    else:
        # Caso o usuário não esteja autenticado, redirecione para a página de login
        return redirect('/login')

@app.route('/acesso_negado', methods=['GET'])
def acesso_negado():
    return render_template('acesso_negado.html')

if __name__ == '__main__':
    create_database()  # Criar o banco de dados e a tabela
    app.teardown_appcontext(close_db_connection)
    app.run(debug=True)
