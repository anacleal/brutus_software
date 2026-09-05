# Brutus App — Plataforma de Treinos da Atlética

Sistema web para gerenciamento de treinos da Atlética Brutus. Permite que os
membros criem contas, cadastrem sua modalidade preferida, criem treinos,
pesquisem e se inscrevam em treinos disponíveis, e acompanhem seu histórico
de participação.

## Funcionalidades principais

- Cadastro e autenticação de usuários (com foto de perfil e modalidade preferida)
- Dashboard com próximos treinos, recomendações e notificações
- Listagem de treinos com busca e filtros (modalidade, data, local, preço, vagas)
- Criação de treinos (gratuitos ou pagos) com limite de participantes
- Inscrição/cancelamento em treinos com um clique
- Perfil do usuário com histórico (próximos, participados, criados)
- Navegação responsiva (desktop e mobile)

## Stack

- **Backend:** Python + Django (Django REST Framework, se o front for desacoplado)
- **Frontend:** *(definir — SPA separado ou templates Django)*
- **Banco de dados:** PostgreSQL
- **Versionamento:** Git + GitHub

## Estrutura do repositório

```
brutus-app/
├── backend/
│   ├── manage.py
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── dev.txt
│   │   └── prod.txt
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── users/
│   │   ├── modalidades/
│   │   ├── treinos/
│   │   ├── inscricoes/
│   │   ├── notificacoes/
│   │   └── core/
│   ├── static/
│   ├── media/
│   └── tests/
├── frontend/
├── docs/
│   ├── setup.md
│   └── ARQUITETURA.md
├── .github/
│   └── workflows/
├── .gitignore
├── .env.example
├── docker-compose.yml
└── README.md
```

Veja **[docs/ARQUITETURA.md](docs/ARQUITETURA.md)** para uma explicação
detalhada do que deve estar em cada pasta e em cada app Django, com base nas
histórias de usuário do projeto.

## Como rodar o projeto localmente

### Pré-requisitos
- Python 3.11+
- pip / venv
- PostgreSQL
- Git

### Passo a passo

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd brutus-app/backend
   ```

2. **Crie e ative um ambiente virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements/dev.txt
   ```

4. **Configure as variáveis de ambiente**
   ```bash
   cp .env.example .env
   # edite o .env com suas configurações locais (SECRET_KEY, banco, etc.)
   ```

5. **Rode as migrações**
   ```bash
   python manage.py migrate
   ```

6. **Crie um superusuário (opcional, para acessar o admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Rode o servidor de desenvolvimento**
   ```bash
   python manage.py runserver
   ```

8. Acesse em `http://localhost:8000`

## Fluxo de branches

- `main` — produção. **Protegida**: só recebe merges via Pull Request, com
  pelo menos 1 aprovação e checks de CI passando.
- `develop` — branch de integração. Todas as features são mergeadas aqui
  antes de ir para `main`.
- `feature/nome-da-feature` — branches de trabalho individuais, criadas a
  partir de `develop`.

Fluxo básico:
```bash
git checkout develop
git pull
git checkout -b feature/cadastro-usuario
# ... commits ...
git push origin feature/cadastro-usuario
# abrir PR para develop
```

## Padrão de commits

Recomenda-se usar [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

## Time

*(adicionar aqui os membros da equipe e responsabilidades)*