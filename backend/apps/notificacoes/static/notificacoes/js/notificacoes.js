/* Painel de notificações flutuante.
   - abre e fecha pelo sino (qualquer elemento com data-notificacoes-toggle);
   - fecha ao clicar fora ou com a tecla Esc;
   - "Marcar todas como lidas" funciona sem recarregar a página. */
(function () {
    "use strict";

    const painel = document.getElementById("notificacoes-painel");
    if (!painel) return;

    const botoes = document.querySelectorAll("[data-notificacoes-toggle]");
    const FOLGA_PX = 12; // distância entre a borda de baixo do cabeçalho e o painel

    // O painel é "fixed". Em vez de um número fixo no CSS, a posição vertical é calculada na hora
    // de abrir, a partir do cabeçalho que contém o sino: assim ele nunca encosta no cabeçalho,
    // não importa a altura dele (desktop, celular, ou algo empurrando a página).
    function posicionar(botao) {
        const referencia = botao.closest("header") || botao;
        painel.style.top = Math.round(referencia.getBoundingClientRect().bottom + FOLGA_PX) + "px";
    }

    function definirAberto(aberto, botao) {
        if (aberto && botao) posicionar(botao);
        painel.hidden = !aberto;
        botoes.forEach((b) => b.setAttribute("aria-expanded", String(aberto)));
        if (aberto) painel.focus();
    }

    botoes.forEach((botao) => {
        botao.addEventListener("click", (evento) => {
            evento.stopPropagation(); // senão o "clique fora" abaixo fecharia o painel logo em seguida
            definirAberto(painel.hidden, botao);
        });
    });

    // mudar o tamanho da janela pode trocar de layout (desktop <-> celular): fecha em vez de ficar mal posicionado
    window.addEventListener("resize", () => {
        if (!painel.hidden) definirAberto(false);
    });

    document.addEventListener("click", (evento) => {
        if (!painel.hidden && !painel.contains(evento.target)) definirAberto(false);
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && !painel.hidden) {
            definirAberto(false);
            if (botoes.length) botoes[0].focus();
        }
    });

    // --- marcar como lidas, sem recarregar ---------------------------------
    const formulario = painel.querySelector("[data-notificacoes-marcar-lidas]");

    function mostrarTudoComoLido() {
        painel.querySelectorAll(".notificacao--nova").forEach((item) => item.classList.remove("notificacao--nova"));
        const contador = painel.querySelector(".notificacoes__contador");
        if (contador) contador.remove();
        formulario.remove();
        // a bolinha vermelha do sino (fica na página, marcada com data-notificacoes-indicador)
        document.querySelectorAll("[data-notificacoes-indicador]").forEach((bolinha) => bolinha.remove());
    }

    if (formulario) {
        formulario.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            formulario.querySelector("button").disabled = true;
            try {
                const resposta = await fetch(formulario.action, {
                    method: "POST",
                    body: new FormData(formulario), // leva o csrfmiddlewaretoken
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                });
                if (!resposta.ok) throw new Error("falha ao marcar como lidas");
                mostrarTudoComoLido();
            } catch (erro) {
                formulario.submit(); // plano B: envio normal do formulário (a página recarrega)
            }
        });
    }
})();