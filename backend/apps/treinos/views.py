import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import TreinoCreateForm
from .models import ModalidadeEsportiva, Treino


@login_required
def treinos_view(request):
    treinos = (
        Treino.objects.select_related("modalidade")
        .annotate(total_inscricoes=Count("inscricoes"))
        .order_by("id")
    )

    if "text/html" in request.headers.get("Accept", ""):
        pesquisa = request.GET.get("q", "").strip()
        nome = request.GET.get("nome", "").strip()
        modalidade_id = request.GET.get("modalidade", "")
        gratuito = request.GET.get("gratuito") == "1"
        com_vagas = request.GET.get("com_vagas") == "1"

        if pesquisa:
            treinos = treinos.filter(
                Q(nome__icontains=pesquisa)
                | Q(modalidade__nome__icontains=pesquisa)
                | Q(local__icontains=pesquisa)
            )
        elif nome:
            treinos = treinos.filter(nome__icontains=nome)
            pesquisa = nome
        if modalidade_id:
            treinos = treinos.filter(modalidade_id=modalidade_id)
        if gratuito:
            treinos = treinos.filter(Q(custo__isnull=True) | Q(custo=0))
        if com_vagas:
            treinos = treinos.filter(
                Q(limite_participantes__isnull=True)
                | Q(total_inscricoes__lt=F("limite_participantes"))
            )

        total_treinos = Treino.objects.count()
        return render(
            request,
            "treinos/listagem.html",
            {
                "treinos": treinos,
                "pesquisa": pesquisa,
                "modalidades": ModalidadeEsportiva.objects.order_by("nome"),
                "modalidade_selecionada": modalidade_id,
                "gratuito": gratuito,
                "com_vagas": com_vagas,
                "total_treinos": total_treinos,
                "tem_filtros": bool(
                    pesquisa or modalidade_id or gratuito or com_vagas
                ),
            },
        )

    nome = request.GET.get("nome", "").strip()
    if nome:
        treinos = treinos.filter(nome__icontains=nome)

    return JsonResponse(
        {
            "treinos": [
                {
                    "id": treino.id,
                    "criador": treino.criador_id,
                    "modalidade_id": treino.modalidade_id,
                    "nome": treino.nome,
                    "limite_participantes": treino.limite_participantes,
                    "local": treino.local,
                    "data_hora": treino.data_hora.isoformat(),
                    "duracao": treino.duracao,
                    "custo": (
                        int(treino.custo)
                        if treino.custo == treino.custo.to_integral_value()
                        else float(treino.custo)
                    ) if treino.custo is not None else None,
                    "observacoes": treino.observacoes,
                    "created_at": treino.created_at.isoformat(),
                }
                for treino in treinos
            ]
        }
    )


def _render_create_workout(request, form, status=200, submitted=False):
    return render(
        request,
        "treinos/criar_treino.html",
        {
            "form": form,
            "modalidades": ModalidadeEsportiva.objects.order_by("nome"),
            "submitted": submitted,
            "today": timezone.localdate().isoformat(),
        },
        status=status,
    )


@require_http_methods(["GET", "POST"])
def criar_treino_view(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return _render_create_workout(request, TreinoCreateForm())

    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "É necessário estar autenticado para criar um treino."},
            status=401,
        )

    is_json = request.content_type == "application/json"
    if is_json:
        try:
            dados = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {"errors": {"body": ["O corpo da requisição deve conter um JSON válido."]}},
                status=400,
            )
        if not isinstance(dados, dict):
            return JsonResponse(
                {"errors": {"body": ["O corpo da requisição deve ser um objeto JSON."]}},
                status=400,
            )
    else:
        dados = request.POST

    is_form_submission = not is_json and dados.get("_form_submission") == "1"
    form = TreinoCreateForm(dados)
    form.is_valid()
    modalidade = None
    modalidade_id = form.cleaned_data.get("modalidade_id")
    if modalidade_id is not None:
        modalidade = ModalidadeEsportiva.objects.filter(pk=modalidade_id).first()
        if modalidade is None:
            form.add_error(
                "modalidade_id",
                "A modalidade esportiva informada não existe.",
            )

    if form.errors:
        if is_form_submission:
            return _render_create_workout(request, form, status=400)
        return JsonResponse(
            {
                "errors": {
                    campo: [str(erro) for erro in erros]
                    for campo, erros in form.errors.items()
                }
            },
            status=400,
        )

    dados_validados = form.cleaned_data
    treino = Treino.objects.create(
        criador=request.user,
        modalidade=modalidade,
        nome=dados_validados["nome"],
        limite_participantes=dados_validados["limite_participantes"],
        local=dados_validados["local"],
        data_hora=dados_validados["data_hora"],
        duracao=dados_validados["duracao"],
        custo=dados_validados["custo"],
        observacoes=dados_validados["observacoes"] or None,
    )

    if is_form_submission:
        return _render_create_workout(
            request,
            TreinoCreateForm(),
            submitted=True,
        )

    custo = treino.custo
    if custo is not None:
        custo = (
            int(custo)
            if custo == custo.to_integral_value()
            else float(custo)
        )

    return JsonResponse(
        {
            "message": "Treino criado com sucesso.",
            "treino": {
                "id": treino.id,
                "criador": treino.criador_id,
                "modalidade_id": treino.modalidade_id,
                "nome": treino.nome,
                "limite_participantes": treino.limite_participantes,
                "local": treino.local,
                "data_hora": treino.data_hora.isoformat(),
                "duracao": treino.duracao,
                "custo": custo,
                "observacoes": treino.observacoes,
                "created_at": treino.created_at.isoformat(),
            },
        },
        status=201,
    )
