# Arquitetura e Organização do Repositório

Este documento explica **o que deve estar em cada pasta**, para que qualquer
pessoa da equipe saiba onde criar ou procurar código. A divisão dos apps
Django foi pensada a partir das histórias de usuário do projeto (autenticação,
dashboard, listagem de treinos, detalhes, criação, perfil e navegação).

---

## `backend/config/`

Configuração global do projeto Django (o antigo diretório que o
`django-admin startproject` cria).

- `settings/base.py` — configurações comuns a todos os ambientes (apps
  instalados, middlewares, templates, banco padrão).
- `settings/dev.py` — herda de `base.py`, ativa `DEBUG=True`, usa SQLite ou
  Postgres local, ferramentas de debug.
- `settings/prod.py` — herda de `base.py`, `DEBUG=False`, configura
  `ALLOWED_HOSTS`, banco de produção, arquivos estáticos via WhiteNoise/S3.
- `urls.py` — roteamento raiz, que inclui as `urls.py` de cada app.
- `wsgi.py` / `asgi.py` — pontos de entrada para deploy.

**Não deve conter** lógica de negócio, models ou views — só configuração.

---

## `backend/apps/users/`

Tudo relacionado a **conta e identidade do usuário**.

Cobre as histórias: US-01 a US-06 (cadastro, foto de perfil, login, logout,
recuperação de senha, navegação entre login/cadastro) e US-31/US-32 (visualizar
e editar perfil).

- `models.py` — modelo de usuário customizado (estendendo `AbstractUser`),
  campo de foto de perfil, campo de modalidade preferida (FK para
  `modalidades`).
- `views.py` / `serializers.py` — cadastro, login, logout, reset de senha,
  visualização e edição de perfil.
- `forms.py` (se usar templates Django) — formulário de cadastro/edição.
- `urls.py` — rotas `/auth/...` e `/perfil/...`.

---

## `backend/apps/modalidades/`

Cadastro das modalidades esportivas oferecidas pela atlética (futebol, vôlei,
natação etc.). É referenciado por `users` (modalidade preferida), por
`treinos` (modalidade do treino) e usado nos filtros de busca (US-16).

- `models.py` — modelo simples `Modalidade` (nome, ícone/cor, descrição).
- Pode ter um app pequeno, mantido separado dos demais porque é referenciado
  por múltiplos outros apps — evita dependência circular entre `users` e
  `treinos`.

---

## `backend/apps/treinos/`

O coração do sistema: criação, listagem, busca/filtro e detalhamento de
treinos.

Cobre: US-08/US-09/US-10/US-13 (cards no dashboard, recomendações, botão de
criar treino), US-14 a US-21 (listagem, busca, filtros, indicadores visuais de
lotado/gratuito/inscrito), US-22 a US-24 (tela de detalhes, vagas,
participantes confirmados) e US-27 a US-30 (formulário de criação, treino
gratuito/pago, validação de erros, cancelamento da criação).

- `models.py` — modelo `Treino` (nome, modalidade FK, data, horário, local,
  valor, limite de participantes, descrição, criador FK para `users`).
- `views.py` — listagem com filtros/busca, detalhe do treino, criação,
  recomendações baseadas na modalidade preferida do usuário.
- `filters.py` — lógica de filtro (modalidade, data, faixa de preço,
  disponibilidade de vagas).
- `serializers.py` (se API) — inclui campos calculados como "vagas
  restantes" e "está lotado".

---

## `backend/apps/inscricoes/`

Relação entre usuário e treino: quem está inscrito em quê. Separado de
`treinos` porque é uma tabela de relacionamento com regras próprias
(cancelamento, controle de vaga), não um atributo do treino em si.

Cobre: US-20 (identificar treinos em que já estou inscrito), US-25 (inscrição
com um clique) e US-26 (cancelar participação).

- `models.py` — modelo `Inscricao` (usuário FK, treino FK, data da
  inscrição, status).
- `views.py` — endpoints de inscrever/cancelar, com validação de vaga
  disponível e duplicidade.
- Essa separação também facilita o cálculo de "participantes confirmados"
  (US-24) e o histórico do perfil (US-33: próximos, participados, criados).

---

## `backend/apps/notificacoes/`

Cobre US-12 (notificações na tela inicial) e complementa US-36 (feedback
visual de ações). Pode começar simples (notificações no banco) e evoluir para
e-mail/push depois.

- `models.py` — modelo `Notificacao` (usuário FK, mensagem, lida/não lida,
  tipo, data).
- Disparada por sinais (`signals.py`) quando eventos relevantes acontecem
  (ex.: inscrição confirmada, treino cancelado).

---

## `backend/apps/core/`

Utilitários e código compartilhado entre apps — nunca deve conter modelos de
negócio próprios.

- Models abstratos (ex.: `TimestampedModel` com `created_at`/`updated_at`
  reutilizado por `treinos`, `inscricoes` etc.)
- Mixins de permissão, paginação customizada, exceptions handlers.
- Helpers de resposta padronizada para mensagens de sucesso/erro (US-36) e
  loaders/estado de carregamento no front (US-37).

---

## `backend/requirements/`

- `base.txt` — dependências sempre necessárias (Django, djangorestframework,
  Pillow para upload de foto de perfil, django-filter para os filtros de
  busca).
- `dev.txt` — herda de `base.txt` + ferramentas de desenvolvimento
  (django-debug-toolbar, pytest-django, black, flake8).
- `prod.txt` — herda de `base.txt` + gunicorn, whitenoise/boto3 (se usar S3
  para as fotos de perfil e mídia dos treinos).

---

## `backend/static/` e `backend/media/`

- `static/` — CSS/JS/imagens do próprio sistema (se usar templates Django).
- `media/` — uploads de usuários: fotos de perfil (US-02) e eventuais imagens
  de treino. **Nunca versionar** (entra no `.gitignore`).

---

## `backend/tests/`

Testes automatizados, organizados espelhando os apps (`tests/users/`,
`tests/treinos/`, etc.). Cada história de usuário relevante deveria ter pelo
menos um teste de aceitação correspondente.

---

## `frontend/`

Reservado para o código do frontend, caso seja um SPA separado (React/Vue) em
vez de templates Django. Cobre as histórias de UX/navegação: US-34
(menu de navegação), US-35 (responsividade mobile), US-36 (feedback visual)
e US-37 (indicadores de carregamento). Estrutura interna a definir conforme o
framework escolhido.

---

## `docs/`

- `setup.md` — instruções detalhadas de setup (complementa o README).
- `ARQUITETURA.md` — este arquivo.
- Pode receber depois: `decisoes-tecnicas.md`, diagramas de modelo de dados,
  etc.

---

## `.github/workflows/`

Pipelines de CI: rodar lint e testes automaticamente a cada push/PR, e
bloquear merge na `main` se algo falhar (reforça a proteção de branch exigida
no critério de aceitação).

---

## Resumo rápido para quem está começando

| Se você vai mexer em... | Vá para... |
|---|---|
| Login, cadastro, perfil | `apps/users/` |
| Lista de esportes/modalidades | `apps/modalidades/` |
| Criar, listar, filtrar, detalhar treino | `apps/treinos/` |
| Inscrever/cancelar em treino | `apps/inscricoes/` |
| Notificações | `apps/notificacoes/` |
| Algo usado por vários apps (base model, permissão) | `apps/core/` |
| Configuração geral do Django | `config/` |
| Tela, componente, navegação | `frontend/` |