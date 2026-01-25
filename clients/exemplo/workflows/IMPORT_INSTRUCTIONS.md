# Como Importar o Workflow: Device Offline Handler

## 1. Localizar o Arquivo

O workflow foi salvo em:
```
/Users/josdasil/Documents/Meraki_Workflow/clients/exemplo/workflows/device-offline-handler.json
```

## 2. Acessar Meraki Dashboard

1. Acesse https://dashboard.meraki.com
2. Selecione a organizacao: **exemplo**
3. Va para **Organization > Workflows**

## 3. Importar o Workflow

1. Clique em **Import Workflow**
2. Selecione o arquivo `device-offline-handler.json`
3. Revise as configuracoes:
   - Nome: Device Offline Handler
   - Triggers: 1 configurado(s)
   - Actions: 3 configurada(s)
4. Clique em **Import**

## 4. Configurar Credenciais (se necessario)

Este workflow pode precisar de credenciais para:
- Slack (webhook URL)

## 5. Ativar o Workflow

1. Apos importar, o workflow estara **desativado**
2. Clique no workflow para abrir detalhes
3. Clique em **Enable** para ativar
4. Teste o workflow com um trigger manual (se aplicavel)

## 6. Monitorar Execucoes

- Visualizar execucoes: **Organization > Workflows > Executions**
- Logs de cada execucao mostram sucesso/falha de cada acao

---

**Workflow criado em:** 2026-01-24 17:17
