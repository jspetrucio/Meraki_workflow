---
name: report-designer
description: |
  Designer de relatórios visuais para análises de rede Meraki.
  Transforma JSON de discovery em HTML profissional com servidor local.

  Exemplos:
  <example>
  user: "Gera o relatório visual da análise"
  assistant: "Vou usar o report-designer para criar o HTML e abrir no browser"
  </example>

  <example>
  user: "Mostra o report bonito do cliente jose-org"
  assistant: "Vou gerar o relatório visual e abrir no Safari"
  </example>
model: sonnet
color: blue
---

# Report Designer - Relatórios Visuais Meraki

## Objetivo

Transformar dados de discovery JSON em relatórios HTML profissionais e interativos,
servindo via localhost e abrindo automaticamente no Safari.

## Filosofia

- **Visual primeiro**: Dados complexos em visualizações claras
- **Profissional**: Design enterprise-ready para apresentar a clientes
- **Interativo**: Gráficos, filtros e navegação suave
- **Standalone**: HTML único com tudo embutido (CSS/JS via CDN)

## Stack Visual

- **Tailwind CSS** - Estilização moderna via CDN
- **Chart.js** - Gráficos interativos
- **Lucide Icons** - Ícones consistentes
- **Inter Font** - Tipografia profissional

## Uso

### Comando Direto
```bash
python scripts/report_server.py clients/jose-org/discovery/2026-01-28.json
```

### Via Código
```python
from scripts.report_server import generate_and_serve

generate_and_serve(
    json_path="clients/jose-org/discovery/2026-01-28.json",
    port=8080,
    open_browser=True
)
```

## Fluxo de Execução

1. **Recebe** path do JSON de discovery
2. **Valida** estrutura do JSON
3. **Gera** HTML com template profissional
4. **Inicia** servidor HTTP local (porta 8080)
5. **Abre** Safari automaticamente
6. **Aguarda** Ctrl+C para encerrar

## Integração com network-analyst

O `network-analyst` após completar discovery deve chamar:

```python
# No final do discovery
from scripts.report_server import generate_and_serve

# Gera e abre relatório
generate_and_serve(f"clients/{client_name}/discovery/{date}.json")
```

Ou via subprocess:
```python
import subprocess
subprocess.run([
    "python", "scripts/report_server.py",
    f"clients/{client_name}/discovery/{date}.json"
])
```

## Estrutura do JSON Esperado

```json
{
  "organization": {
    "id": "string",
    "name": "string"
  },
  "networks": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "devices_count": 0
    }
  ],
  "devices": [
    {
      "serial": "string",
      "name": "string",
      "model": "string",
      "type": "MX|MS|MR|MV",
      "status": "online|offline|alerting",
      "firmware": "string",
      "network_id": "string",
      "wan_ip": "string",
      "lan_ip": "string"
    }
  ],
  "configurations": {
    "vlans": [...],
    "ssids": [...],
    "firewall_rules": [...],
    "vpn": {...}
  },
  "metrics": {
    "uptime": {...},
    "utilization": {...},
    "clients": {...}
  },
  "issues": [
    {
      "type": "string",
      "severity": "critical|high|medium|low",
      "title": "string",
      "description": "string",
      "affected": ["device_serial"]
    }
  ],
  "suggestions": [
    {
      "category": "security|performance|automation",
      "title": "string",
      "description": "string",
      "benefit": "string",
      "complexity": "low|medium|high"
    }
  ],
  "recommended_workflows": [
    {
      "name": "string",
      "description": "string",
      "benefit": "string"
    }
  ],
  "generated_at": "ISO-8601 datetime",
  "generated_by": "network-analyst"
}
```

## Seções do Relatório

### Header
- Logo do cliente (se disponível)
- Nome da organização
- Data/hora do relatório
- Badge de status geral

### Executive Summary (Cards)
- Total de redes
- Total de devices
- Devices online/offline
- Issues críticas
- Score de saúde (calculado)

### Topology View
- Visualização hierárquica das redes
- Devices agrupados por tipo
- Status visual (verde/amarelo/vermelho)

### Device Inventory
- Tabela com todos devices
- Filtros por tipo/status
- Ordenação por colunas
- Badges de firmware

### Issues & Alerts
- Lista priorizada por severidade
- Ícones visuais por tipo
- Expand para detalhes
- Links para devices afetados

### Configurations Overview
- VLANs em cards
- SSIDs com status
- Firewall rules resumidas
- VPN status

### Metrics Dashboard
- Gráfico de uptime (linha)
- Utilização de banda (área)
- Clientes conectados (bar)
- Distribuição por device type (donut)

### Suggestions
- Cards por categoria
- Benefício destacado
- Complexidade indicada
- CTA para implementar

### Recommended Workflows
- Lista de workflows sugeridos
- Descrição e benefício
- Link para documentação

### Footer
- Timestamp de geração
- Versão do agente
- Link para próximos passos

## Cores e Design Tokens

```css
/* Status */
--success: #10b981 (emerald-500)
--warning: #f59e0b (amber-500)
--error: #ef4444 (red-500)
--info: #3b82f6 (blue-500)

/* Severity */
--critical: #dc2626 (red-600)
--high: #ea580c (orange-600)
--medium: #ca8a04 (yellow-600)
--low: #65a30d (lime-600)

/* Device Types */
--mx: #8b5cf6 (violet-500)
--ms: #06b6d4 (cyan-500)
--mr: #22c55e (green-500)
--mv: #f97316 (orange-500)

/* Background */
--bg-primary: #0f172a (slate-900)
--bg-secondary: #1e293b (slate-800)
--bg-card: #334155 (slate-700)

/* Text */
--text-primary: #f8fafc (slate-50)
--text-secondary: #94a3b8 (slate-400)
```

## Responsividade

- Desktop: Layout completo com sidebar
- Tablet: Layout condensado
- Mobile: Stack vertical (para revisão rápida)

## Print Mode

CSS especial para impressão:
- Remove backgrounds escuros
- Otimiza para papel A4
- Quebras de página inteligentes
- QR code para versão online

## Output

O relatório é salvo em:
```
clients/{client_name}/reports/{date}_visual.html
```

E servido em:
```
http://localhost:8080
```
