// Máscaras de CPF, telefone e CEP, busca de endereço pelo CEP e botão de mostrar senha.
(function () {
  const mascaras = {
    cpf: (v) => v.slice(0, 11)
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2"),
    telefone: (v) => {
      v = v.slice(0, 11);
      if (v.length <= 10) return v.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{4})(\d)/, "$1-$2");
      return v.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{5})(\d)/, "$1-$2");
    },
    cep: (v) => v.slice(0, 8).replace(/(\d{5})(\d)/, "$1-$2"),
  };

  function aplicarMascara(campo) {
    const tipo = campo.dataset.mascara;
    if (!mascaras[tipo]) return;
    const formatar = () => { campo.value = mascaras[tipo](campo.value.replace(/\D/g, "")); };
    campo.addEventListener("input", formatar);
    formatar();
  }

  function buscarCep(campo) {
    campo.addEventListener("blur", async () => {
      const cep = campo.value.replace(/\D/g, "");
      if (cep.length !== 8) return;
      const form = campo.form;
      const preencher = (nome, valor) => {
        const alvo = form.querySelector(`[name="${nome}"]`);
        if (alvo && valor && !alvo.value) alvo.value = valor;
      };
      try {
        campo.setAttribute("aria-busy", "true");
        const resposta = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const dados = await resposta.json();
        if (dados.erro) return;
        preencher("endereco", dados.logradouro);
        preencher("bairro", dados.bairro);
        preencher("cidade", dados.localidade);
        preencher("uf", dados.uf);
      } catch (e) {
        /* sem internet ou serviço fora do ar: a pessoa preenche à mão */
      } finally {
        campo.removeAttribute("aria-busy");
      }
    });
  }

  function botaoSenha(campo) {
    if (campo.dataset.olhoPronto) return;
    campo.dataset.olhoPronto = "1";
    const envoltorio = document.createElement("div");
    envoltorio.className = "senha";
    campo.parentNode.insertBefore(envoltorio, campo);
    envoltorio.appendChild(campo);
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "senha__olho";
    botao.setAttribute("aria-label", "Mostrar senha");
    botao.innerHTML = '<i class="ph ph-eye"></i>';
    botao.addEventListener("click", () => {
      const mostrar = campo.type === "password";
      campo.type = mostrar ? "text" : "password";
      botao.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
      botao.innerHTML = mostrar ? '<i class="ph ph-eye-slash"></i>' : '<i class="ph ph-eye"></i>';
    });
    envoltorio.appendChild(botao);
  }

  function iniciar(raiz) {
    raiz.querySelectorAll("[data-mascara]").forEach(aplicarMascara);
    raiz.querySelectorAll("[data-viacep]").forEach(buscarCep);
    raiz.querySelectorAll('.campo input[type="password"]').forEach(botaoSenha);
  }

  document.addEventListener("DOMContentLoaded", () => iniciar(document));
  document.addEventListener("htmx:afterSettle", (e) => iniciar(e.target));
})();
