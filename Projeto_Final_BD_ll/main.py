from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email  # Importar Email aqui
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devs.db'  # Banco de dados SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap5(app)

db = SQLAlchemy(app)

# Modelo de Usuário
class Developer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    cel = db.Column(db.String(20), nullable=False)
    habilidades = db.Column(db.Text, nullable=False)

class DevSkipCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dev_id = db.Column(db.Integer, db.ForeignKey('developer.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

class CompanySkipDev(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    dev_id = db.Column(db.Integer, db.ForeignKey('developer.id'), nullable=False)

class DevForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    cel = StringField('Celular', validators=[DataRequired()])
    habilidades = TextAreaField('Habilidades', validators=[DataRequired()])
    submit= SubmitField('Cadastrar')

class DevLoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Modelo de Empresa
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)  # Essa linha deve estar presente
    telefone = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.Text, nullable=False)

# Formulário de Cadastro para Empresa
class CompanyForm(FlaskForm):
    name = StringField('Nome da Empresa', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    descricao = TextAreaField('Descrição da Empresa', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

# Formulário de Login para Empresa
class CompanyLoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CompanyEditForm(FlaskForm):
    name = StringField('Nome da Empresa', validators=[DataRequired()])
    descricao = TextAreaField('Descrição da Empresa', validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

class DevEditForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    habilidades = TextAreaField('Habilidades', validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dev_id = db.Column(db.Integer, db.ForeignKey('developer.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    match_date = db.Column(db.DateTime, default=db.func.current_timestamp())

def check_if_match_exists(dev_id, company_id):
    print(f"Checking match for Developer ID: {dev_id}, Company ID: {company_id}")
    match = Match.query.filter_by(dev_id=dev_id, company_id=company_id).first()
    print(f"Match found: {match}")
    return match is not None

##########################################################################

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dev/login", methods=["GET", "POST"])
def dev_login():
    form = DevLoginForm()

    if request.method == "POST":  # Verifique se é uma solicitação POST
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            
            # Verificando se o desenvolvedor existe no banco de dados usando SQLAlchemy
            developer = Developer.query.filter_by(email=email).first()

            # Verificar se o desenvolvedor foi encontrado e se a senha está correta
            if developer and developer.password == password:
                # Armazena o ID do desenvolvedor na sessão
                session['developer_id'] = developer.id

                # Redireciona para o perfil
                return redirect(url_for('dev_profile'))
            else:
                # Exibe uma mensagem de erro se as credenciais forem inválidas
                flash('Credenciais inválidas. Tente novamente.', 'danger')

        else:
            print("Erros de validação:", form.errors)

    # Se for um GET ou a validação falhar, renderize a página de login novamente
    return render_template("dev_login.html", form=form)


@app.route("/dev/profile")
def dev_profile():
    # Verifica se o desenvolvedor está logado (se o ID está na sessão)
    if 'developer_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('dev_login'))

    # Obtém o ID do desenvolvedor armazenado na sessão
    developer_id = session['developer_id']

    # Busca o desenvolvedor no banco de dados
    developer = Developer.query.get(developer_id)

    # Se o desenvolvedor não for encontrado
    if developer is None:
        flash('Desenvolvedor não encontrado.', 'danger')
        return redirect(url_for('dev_login'))

    # Prepara os dados do desenvolvedor para enviar ao template
    developer_info = {
        "name": developer.name,
        "email": developer.email,
        "cel": developer.cel,
        "habilidades": developer.habilidades
    }

    # Renderiza o template passando as informações do desenvolvedor
    return render_template("dev_profile.html", developer=developer_info)

@app.route("/dev/edit_profile", methods=["GET", "POST"])
def dev_edit_profile():
    if 'developer_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('dev_login'))

    dev_id = session['developer_id']
    developer = Developer.query.get_or_404(dev_id)
    form = DevEditForm(obj=developer)

    if form.validate_on_submit():
        developer.name = form.name.data
        developer.habilidades = form.habilidades.data
        db.session.commit()
        flash('Perfil do desenvolvedor atualizado com sucesso!', 'success')
        return redirect(url_for('dev_profile'))

    return render_template("dev_edit_profile.html", form=form)


@app.route("/company/edit_profile", methods=["GET", "POST"])
def company_edit_profile():
    if 'company_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('company_login'))

    company_id = session['company_id']
    company = Company.query.get_or_404(company_id)
    form = CompanyEditForm(obj=company)

    if form.validate_on_submit():
        company.name = form.name.data
        company.descricao = form.descricao.data
        db.session.commit()
        flash('Perfil da empresa atualizado com sucesso!', 'success')
        return redirect(url_for('company_profile'))

    return render_template("company_edit_profile.html", form=form)

@app.route("/dev/register", methods=["GET", "POST"])
def dev_register():
    form = DevForm()

    if form.validate_on_submit():
        # Verificar se o email já existe
        existing_dev_email = Developer.query.filter_by(email=form.email.data).first()
        existing_dev_pass = Developer.query.filter_by(password=form.password.data).first()
        
        if existing_dev_email and existing_dev_pass:
            flash('Esse email já está registrado. Por favor, use outro.', 'danger')
            return redirect(url_for('dev_register'))

        try:
            # Criar novo desenvolvedor e salvar no banco de dados
            new_dev = Developer(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data,
                cel=form.cel.data,
                habilidades=form.habilidades.data
            )
            db.session.add(new_dev)
            db.session.commit()
            flash('Desenvolvedor registrado com sucesso!', 'success')
            return redirect(url_for('home'))
        
        except Exception as e:
            # Tratar erros de banco de dados e fazer rollback em caso de falha
            db.session.rollback()
            flash(f'Ocorreu um erro ao registrar o desenvolvedor: {str(e)}', 'danger')

    return render_template("dev_register.html", form=form)

# Rota para registrar empresas
@app.route("/company/register", methods=["GET", "POST"])
def company_register():
    form = CompanyForm()
    if form.validate_on_submit():
        # Verificar se o e-mail já está registrado
        existing_company = Company.query.filter_by(email=form.email.data).first()
        if existing_company:
            flash('Esse e-mail já está registrado. Por favor, use outro.', 'danger')
            return redirect(url_for('company_register'))

        # Criar nova empresa e salvar no banco de dados
        new_company = Company(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,  # Hash da senha
            telefone=form.telefone.data,
            descricao=form.descricao.data
        )
        db.session.add(new_company)
        db.session.commit()  # Salvar no banco
        flash('Empresa registrada com sucesso!', 'success')
        return redirect(url_for('home'))
    return render_template("company_register.html", form=form)

# Rota para login de empresas
@app.route("/company/login", methods=["GET", "POST"])
def company_login():
    form = CompanyLoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Verificar se o e-mail da empresa existe no banco de dados
            email = form.email.data
            password = form.password.data

            company = Company.query.filter_by(email=email).first()
            if company and company.password == password:  # Verifique se a senha está correta
                # Armazena o ID da empresa na sessão
                session['company_id'] = company.id

                # Redireciona para o perfil da empresa
                flash(f'Bem-vindo, {company.name}!', 'success')
                return redirect(url_for('company_profile'))
            else:
                # Login falhou
                print("Erros de validação:", form.errors)
                flash('E-mail ou senha inválidos. Tente novamente.', 'danger')
                return redirect(url_for('company_login'))
    return render_template("company_login.html", form=form)

@app.route("/company/profile")
def company_profile():
    # Verifica se a empresa está logada (você pode usar sessão semelhante ao que fez para desenvolvedores)
    if 'company_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('company_login'))

    # Obtém o ID da empresa armazenado na sessão
    company_id = session['company_id']

    # Busca a empresa no banco de dados
    company = Company.query.get(company_id)

    # Se a empresa não for encontrada
    if company is None:
        flash('Empresa não encontrada.', 'danger')
        return redirect(url_for('company_login'))

    # Prepara os dados da empresa para enviar ao template
    company_info = {
        "name": company.name,
        "email": company.email,
        "telefone": company.telefone,
        "descricao": company.descricao
    }

    # Renderiza o template passando as informações da empresa
    return render_template("company_profile.html", company=company_info)

@app.route("/dev/logout")
def dev_logout():
    session.pop('developer_id', None)  # Remove o ID do desenvolvedor da sessão
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('dev_login'))

@app.route("/company/logout")
def company_logout():
    session.pop('company_id', None)  # Remove o ID da empresa da sessão
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('company_login'))

##########################################################################

def get_evaluated_company_ids(dev_id):
    evaluated_matches = Match.query.filter_by(dev_id=dev_id).all()
    # Certifique-se de que a função não está chamando a si mesma aqui
    evaluated_company_ids = [match.company_id for match in evaluated_matches]
    return evaluated_company_ids

def get_next_empresa_for_dev(dev_id):
    # Obtém todas as empresas que não foram avaliadas pelo desenvolvedor
    evaluated_company_ids = get_evaluated_company_ids(dev_id)  # Implemente esta função conforme necessário

    # Busca a próxima empresa que o desenvolvedor ainda não avaliou
    next_company = Company.query.filter(Company.id.notin_(evaluated_company_ids)).first()

    return next_company

def get_next_dev_for_company(company_id):
    # Obtém os IDs dos desenvolvedores que a empresa já pulou
    skipped_dev_ids = get_skipped_dev_ids(company_id)
    
    # Obtém os IDs dos desenvolvedores que já têm um match com a empresa
    matched_dev_ids = Match.query.filter_by(company_id=company_id).with_entities(Match.dev_id).all()
    matched_dev_ids = [dev_id[0] for dev_id in matched_dev_ids]  # Extrai apenas os IDs

    # Retorna o próximo desenvolvedor que a empresa ainda não avaliou
    return Developer.query.filter(
        ~Developer.id.in_(skipped_dev_ids), 
        ~Developer.id.in_(matched_dev_ids)
    ).first()



def get_skipped_company_ids(dev_id):
    # Retorna uma lista de IDs de empresas que o desenvolvedor passou
    skipped = DevSkipCompany.query.filter_by(dev_id=dev_id).all()
    return [s.company_id for s in skipped]

def get_skipped_dev_ids(company_id):
    # Retorna uma lista de IDs de desenvolvedores que a empresa passou
    skipped = CompanySkipDev.query.filter_by(company_id=company_id).all()
    return [s.dev_id for s in skipped]

@app.route("/dev/skip/<int:company_id>", methods=["GET"])
def dev_skip(company_id):
    # Verifica se o dev está logado
    if 'developer_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('dev_login'))

    # Obtém o ID do dev a partir da sessão
    dev_id = session['developer_id']

    # Registrar o skip da empresa
    skip = DevSkipCompany(dev_id=dev_id, company_id=company_id)
    db.session.add(skip)
    db.session.commit()

    # Busca a próxima empresa
    next_empresa = get_next_empresa_for_dev(dev_id)

    if next_empresa:
        # Se houver uma próxima empresa, renderiza a página de match
        return render_template("dev_match.html", empresa=next_empresa)
    else:
        # Caso contrário, exibe uma mensagem informando que não há mais empresas
        flash('Nenhuma nova empresa disponível no momento.', 'info')
        return redirect(url_for('dev_profile'))
    
@app.route("/company/skip/<int:dev_id>", methods=["GET"])
def company_skip(dev_id):
    # Verifica se a empresa está logada
    if 'company_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('company_login'))

    # Obtém o ID da empresa a partir da sessão
    company_id = session['company_id']

    # Registrar o skip do desenvolvedor
    skip = CompanySkipDev(company_id=company_id, dev_id=dev_id)
    db.session.add(skip)
    db.session.commit()

    # Busca o próximo desenvolvedor
    next_dev = get_next_dev_for_company(company_id)

    if next_dev:
        # Se houver um próximo desenvolvedor, renderiza a página de match
        return render_template("company_match.html", dev=next_dev)
    else:
        # Caso contrário, exibe uma mensagem informando que não há mais desenvolvedores
        flash('Nenhum novo desenvolvedor disponível no momento.', 'info')
        return redirect(url_for('company_profile'))
    
@app.route("/company/match", methods=["GET", "POST"])
def company_match():
    # Verifica se a empresa está logada
    if 'company_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('company_login'))

    # Obtém o ID da empresa armazenado na sessão
    company_id = session['company_id']

    # Busca o próximo desenvolvedor que a empresa ainda não avaliou
    next_dev = get_next_dev_for_company(company_id)
    
    if request.method == "POST":
        print(f"Next Developer: {next_dev}")
        if next_dev:  # Se o desenvolvedor estiver disponível
            if 'skip' in request.form:  # Se a empresa decidiu pular o desenvolvedor
                print(f"Skipped Developer: {next_dev.name}")
                
                # Registra que a empresa pulou o desenvolvedor
                # Você pode criar um registro ou lógica adicional aqui se necessário

                # Busca o próximo desenvolvedor
                next_dev = get_next_dev_for_company(company_id)
                return render_template("company_match.html", dev=next_dev)
                
            elif 'match' in request.form:  # Se a empresa decidiu dar match
                print(f"Request Form: {request.form}")  # Debug
                
                if not check_if_match_exists(next_dev.id, company_id):  # Verifica se o match já existe
                    new_match = Match(dev_id=next_dev.id, company_id=company_id)
                    db.session.add(new_match)
                    db.session.commit()
                    flash(f'Match com o desenvolvedor {next_dev.name} realizado com sucesso!', 'success')
                    print(f"Match created for Developer ID: {next_dev.id}, Company ID: {company_id}")  # Debug
                else:
                    flash(f'Você já deu match com o desenvolvedor {next_dev.name}.', 'info')
                
                # Busca o próximo desenvolvedor após tentar dar match
                next_dev = get_next_dev_for_company(company_id)
                print(f"Next Developer after match: {next_dev}")  # Debug

                # Verifica se há um próximo desenvolvedor
                if next_dev:
                    return render_template("company_match.html", dev=next_dev)
                else:
                    flash('Nenhum novo desenvolvedor disponível no momento.', 'info')
                    return redirect(url_for('company_profile'))  # Redireciona para o perfil da empresa

    # Renderiza a página de match com o desenvolvedor atual, se não for um POST
    return render_template("company_match.html", dev=next_dev)



@app.route("/dev/match", methods=["GET", "POST"])
def dev_match():
    # Verifica se o desenvolvedor está logado
    print("Aqui 1")
    if 'developer_id' not in session:
        print("Aqui 2")
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('dev_login'))

    # Obtém o ID do desenvolvedor armazenado na sessão
    dev_id = session['developer_id']

    # Busca a próxima empresa que o desenvolvedor ainda não avaliou
    next_company = get_next_empresa_for_dev(dev_id)

    # Verifique se há uma empresa disponível
    if not next_company:
        print("Aqui 3")
        flash('Nenhuma nova empresa disponível ou houve um erro na busca.', 'warning')
        return redirect(url_for('dev_profile'))

    # Lógica de POST para match ou skip
    if request.method == "POST":
        print("Aqui 4")
        if next_company:  # Se uma empresa estiver disponível
            print("Aqui 5")
            if 'skip' in request.form:
                return dev_skip(next_company.id)
            elif 'match' in request.form:
                print("Aqui 6")
                if not check_if_match_exists(dev_id, next_company.id):
                    print("Aqui 7")
                    new_match = Match(dev_id=dev_id, company_id=next_company.id)
                    db.session.add(new_match)
                    db.session.commit()
                    flash(f'Match com a empresa {next_company.name} realizado com sucesso!', 'success')
                else:
                    flash(f'Você já deu match com a empresa {next_company.name}.', 'info')
                next_company = get_next_empresa_for_dev(dev_id)

    # Renderiza a página dev_match com os dados da empresa
    return render_template("dev_match.html", company=next_company)



with app.app_context():
    db.create_all()

if __name__ == '__main__':

    app.run(debug=True, port=6001)