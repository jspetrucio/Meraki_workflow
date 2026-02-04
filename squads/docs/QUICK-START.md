# Quick Start: Resumo Rápido

> **Este é um RESUMO.** Para tutorial completo com exemplos, veja [TUTORIAL-COMPLETO.md](./TUTORIAL-COMPLETO.md).
>
> **Primeira vez?** Comece por [POR-ONDE-COMECAR.md](./POR-ONDE-COMECAR.md).

---

## Pré-requisitos

- Claude Code ativo
- Acesso ao repositório mmos

---

## Passo 1: Ativar o Squad Architect (30 seg)

```
@squad-creator
```

Você verá o greeting do Squad Architect. Ele está pronto para receber comandos.

---

## Passo 2: Solicitar Criação do Squad (1 min)

Simplesmente diga o que você quer:

```
Quero um squad de copywriting
```

**O que acontece:**
1. Squad Architect inicia automaticamente a pesquisa
2. NÃO pergunta "quer pesquisar?" - já vai direto
3. Executa 3-5 iterações de pesquisa com devil's advocate

---

## Passo 3: Pre-Flight (1 min)

O sistema pergunta sobre o modo de execução:

```
┌─────────────────────────────────────────────────────────────────┐
│ PRE-FLIGHT: CRIAÇÃO DE SQUAD                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Como você quer executar?                                        │
│                                                                 │
│ 🚀 YOLO    - Não tenho materiais (60-75% fidelity)             │
│ 💎 QUALITY - Tenho livros/PDFs (85-95% fidelity)               │
│ 🔀 HYBRID  - Tenho materiais de alguns experts                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Escolha:**
- **YOLO** se quer rapidez e não tem materiais
- **QUALITY** se tem livros/PDFs dos experts
- **HYBRID** se tem materiais de alguns, não de todos

---

## Passo 4: Aprovar Elite Minds (1 min)

Após a pesquisa, você vê os resultados:

```
┌─────────────────────────────────────────────────────────────────┐
│ ELITE MINDS ENCONTRADOS                                         │
├──────────────────┬──────────┬───────────────────────────────────┤
│ Mind             │ Tier     │ Framework Principal               │
├──────────────────┼──────────┼───────────────────────────────────┤
│ Gary Halbert     │ Tier 1   │ The Boron Letters Method          │
│ Eugene Schwartz  │ Tier 0   │ Levels of Awareness               │
│ Dan Kennedy      │ Tier 1   │ No B.S. Direct Marketing          │
│ Claude Hopkins   │ Tier 0   │ Scientific Advertising            │
│ David Ogilvy     │ Tier 1   │ Ogilvy on Advertising             │
└──────────────────┴──────────┴───────────────────────────────────┘

Criar agentes baseados nestes minds?
```

Responda **sim** para prosseguir.

---

## Passo 5: Aguardar Criação (2-3 min)

O sistema executa automaticamente:

```
✓ Coletando fontes para Gary Halbert...
✓ Extraindo Voice DNA...
✓ Extraindo Thinking DNA...
✓ Rodando Smoke Tests (3/3)...
✓ Criando agent.md...

[Repetir para cada mind]

✓ Criando orchestrator...
✓ Gerando workflows...
✓ Validando squad...
✓ Gerando Quality Dashboard...
```

---

## Passo 6: Receber o Squad Pronto

```
┌─────────────────────────────────────────────────────────────────┐
│ ✅ SQUAD CRIADO: copy                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Agents: 6 (5 experts + 1 orchestrator)                          │
│ Quality Score: 8.2/10                                           │
│ Fidelity Estimate: 72%                                          │
│                                                                 │
│ Ativação: @copy                                                 │
│ Dashboard: squads/copy/docs/quality-dashboard.md                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Usar o Squad

```
@copy
```

Agora você tem acesso a todos os agents do squad:

```
@copy:gary-halbert    → Sales letters no estilo Halbert
@copy:eugene-schwartz → Análise de awareness levels
@copy:dan-kennedy     → Direct response marketing
```

---

## Resumo do Fluxo

```
@squad-creator
      ↓
"Quero um squad de {domínio}"
      ↓
Escolher modo (YOLO/QUALITY/HYBRID)
      ↓
Aprovar elite minds
      ↓
Aguardar criação automática
      ↓
@{squad} para usar
```

---

## Comandos Úteis

| Comando | O que faz |
|---------|-----------|
| `*create-squad` | Criar novo squad (com workflow guiado) |
| `*clone-mind {name}` | Clonar um expert específico |
| `*validate-squad {name}` | Validar squad existente |
| `*quality-dashboard {name}` | Gerar dashboard de qualidade |
| `*help` | Ver todos os comandos |

---

## Próximos Passos

1. **Entender os conceitos:** Leia [CONCEPTS.md](./CONCEPTS.md)
2. **Ver diagramas:** Leia [ARCHITECTURE-DIAGRAMS.md](./ARCHITECTURE-DIAGRAMS.md)
3. **Problemas?** Leia [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## Exemplo Real: 30 Segundos

```
User: @squad-creator
Bot:  🎨 Squad Architect ready...

User: Quero um squad de copywriting
Bot:  I'll research the best minds in copywriting. Starting...
      [pesquisa 3-5 iterações]

Bot:  Found 6 elite minds. Create agents?
User: sim

Bot:  [cria automaticamente]
      ✅ Squad copy criado! Ative com @copy
```

**É isso.** Sem configuração, sem setup, sem complicação.

---

**Squad Architect | Quick Start v1.0**
*"De zero a squad em 5 minutos."*
