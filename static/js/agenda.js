function iniciarAgenda() {
    const form = document.querySelector(".agenda");
    if (!form) return;
    const alvo = form.querySelector("[data-resumo-alvo]");

    const mostrarDia = (agenda, dia) => {
      agenda.querySelectorAll(".dia-pill").forEach((b) => b.setAttribute("aria-selected", b.dataset.dia === dia ? "true" : "false"));
      agenda.querySelectorAll(".prof__painel").forEach((p) => { p.hidden = p.dataset.dia !== dia; });
    };

    form.querySelectorAll("[data-agenda]").forEach((agenda) => {
      agenda.querySelectorAll(".dia-pill").forEach((botao) => {
        botao.addEventListener("click", () => mostrarDia(agenda, botao.dataset.dia));
      });
    });

    const pre = form.dataset.escolha;
    if (pre) {
      const radio = Array.from(form.querySelectorAll('input[name="escolha"]')).find((i) => i.value === pre);
      if (radio) radio.checked = true;
    }

    const atualizar = () => {
      const marcado = form.querySelector('input[name="escolha"]:checked');
      if (!marcado) return;
      alvo.textContent = marcado.dataset.resumo;
      const painel = marcado.closest(".prof__painel");
      if (painel && painel.hidden) mostrarDia(painel.closest("[data-agenda]"), painel.dataset.dia);
    };
    form.addEventListener("change", atualizar);
    atualizar();
  }
  document.addEventListener("DOMContentLoaded", iniciarAgenda);
  document.addEventListener("htmx:afterSettle", iniciarAgenda);
