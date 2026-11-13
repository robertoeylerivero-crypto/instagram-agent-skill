# Search Console: migração pousadaaurema.com.br → auremabooking.com.br

Nenhuma ferramenta conectada aqui consegue fazer isso no lugar do dono: precisa ser feito na conta Google que administra o site.
Tempo: uns 10 minutos.

Situação em 13/11/2026: o domínio antigo redireciona com 301 e mantém o caminho de cada página (correto).
Segundo o Semrush, o antigo ainda tem 45 palavras no Google e o novo tem 1.

## Passo a passo
1. Abra https://search.google.com/search-console com a conta Google do site.
2. **Propriedade do site novo**: se ainda não existir, "Adicionar propriedade" → tipo **Domínio** → `auremabooking.com.br` → confirmar pelo registro TXT no DNS.
   (O site já tem a meta de verificação do Google; se usar o tipo "Prefixo do URL", com `https://auremabooking.com.br/`, ela deve validar sozinha.)
3. Na propriedade nova: **Sitemaps** → enviar `sitemap-index.xml` → deve aparecer "Sucesso" (98 URLs).
4. Na propriedade nova: **Inspeção de URL** → colar `https://auremabooking.com.br/` → **Solicitar indexação**.
   Repetir para `/pousada-na-praia-do-rosa/`, `/acomodacoes/` e `/blog/praia-do-rosa-para-familias/`.
5. Na propriedade **antiga** (`pousadaaurema.com.br`; precisa estar verificada): Configurações (engrenagem) → **Mudança de endereço** → escolher `auremabooking.com.br` → Validar e atualizar.
   O Google confere os 301 e passa a transferir os sinais.
6. Não desligue o redirecionamento nem deixe o domínio antigo expirar: mantenha os dois por pelo menos 1 ano.

## Para eu acompanhar toda segunda
Conectando o Search Console no Windsor.ai (o mesmo que já lê o Instagram), o relatório semanal passa a trazer as páginas indexadas e os cliques/impressões reais do Google, sem depender de estimativa.
