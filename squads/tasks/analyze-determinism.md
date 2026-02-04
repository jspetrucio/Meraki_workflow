# Task: Analyze Determinism Opportunities

**Task ID:** analyze-determinism
**Version:** 1.0.0
**Purpose:** Analisar tasks/squads e identificar o que poderia ser código determinístico (Worker) ao invés de LLM (Agent)
**Orchestrator:** @squad-architect
**Mode:** Analysis (read-only)
**Pattern:** EXEC-DT-002

---

## Task Anatomy

| Field | Value |
|-------|-------|
| **task_name** | Analyze Determinism Opportunities |
| **status** | `pending` |
| **responsible_executor** | @squad-architect |
| **execution_type** | Agent |
| **input** | `task_file` ou `squad_name` |
| **output** | Relatório de oportunidades de determinização |
| **action_items** | Analisar, classificar, recomendar |
| **acceptance_criteria** | Cada task analisada tem classificação e justificativa |

---

## Overview

Este comando analisa tasks existentes e identifica:

1. **Tasks que DEVERIAM ser Worker** (código) mas estão como Agent (LLM)
2. **Tasks que estão corretas** como Agent
3. **Tasks que poderiam migrar** de Agent → Worker com algumas modificações
4. **ROI estimado** da conversão

```
*analyze-determinism {target}

Onde {target} pode ser:
- task_file: "squads/copy/tasks/generate-headlines.md"
- squad_name: "copy" (analisa todas as tasks do squad)
- "all" (analisa todos os squads)
```

---

## PHASE 0: TARGET IDENTIFICATION

**Duration:** 1-2 minutes

### Step 0.1: Parse Target

```yaml
parse_target:
  if_file:
    action: "Analisar única task"
    path: "{target}"

  if_squad:
    action: "Listar todas tasks do squad"
    glob: "squads/{target}/tasks/*.md"

  if_all:
    action: "Listar todas tasks de todos squads"
    glob: "squads/*/tasks/*.md"
    exclude:
      - "squads/squad-creator/*"  # Meta-squad, não analisar
```

### Step 0.2: Load Tasks

```yaml
load_tasks:
  for_each_file:
    - read: "{file_path}"
    - extract:
        - task_name
        - execution_type (se existir)
        - purpose/description
        - inputs
        - outputs
        - action_items/steps
```

---

## PHASE 1: DETERMINISM ANALYSIS

**Duration:** 2-5 minutes per task

### Step 1.1: Apply Decision Tree (Reverse)

Para cada task, aplicar as 6 perguntas do `executor-decision-tree.md` para determinar o executor CORRETO:

```yaml
analyze_task:
  task: "{task_name}"

  questions:
    q1_deterministic:
      question: "Output é 100% previsível dado o input?"
      analyze:
        - "Inputs são estruturados ou texto livre?"
        - "Output tem formato fixo ou varia?"
        - "Há interpretação necessária?"
      indicators:
        deterministic:
          - "Input é JSON/YAML/CSV estruturado"
          - "Output é transformação direta"
          - "Não há 'análise' ou 'interpretação'"
          - "Palavras: formatar, converter, validar, calcular"
        non_deterministic:
          - "Input é texto livre"
          - "Output depende de contexto"
          - "Palavras: analisar, interpretar, gerar, criar, sugerir"

    q2_pure_function:
      question: "Pode ser função pura f(x) → y?"
      analyze:
        - "Mesma entrada sempre gera mesma saída?"
        - "Há side effects?"
        - "Depende de estado externo?"
      indicators:
        pure:
          - "Transformação de dados"
          - "Validação com regras fixas"
          - "Cálculo matemático"
        impure:
          - "Depende de contexto de conversa"
          - "Requer conhecimento do mundo"
          - "Output é criativo/variável"

    q2a_lib_exists:
      question: "Existe biblioteca/API que faz isso?"
      search:
        - "npm search {keywords}"
        - "pip search {keywords}"
        - "Conhecimento de libs comuns"
      common_libs:
        validation: ["zod", "yup", "joi", "pydantic"]
        parsing: ["cheerio", "beautifulsoup", "pdf-parse"]
        formatting: ["prettier", "black", "date-fns"]
        data: ["lodash", "pandas", "jq"]

    q2b_frequency:
      question: "Task é executada com frequência?"
      estimate:
        - "Quantas vezes por dia/semana/mês?"
        - "É parte de pipeline automatizado?"
        - "É trigger manual ou automático?"
      thresholds:
        high: "> 50 execuções/mês → Worker vale a pena"
        medium: "10-50 execuções/mês → Avaliar complexidade"
        low: "< 10 execuções/mês → Agent pode ser OK"
```

### Step 1.2: Classification

```yaml
classify_task:
  categories:

    SHOULD_BE_WORKER:
      criteria:
        - "q1 = deterministic"
        - "q2 = pure function possível"
        - "q2a = lib existe OU implementação simples"
      recommendation: "Converter para Worker (código)"
      priority: "HIGH"

    COULD_BE_WORKER:
      criteria:
        - "q1 = mostly deterministic"
        - "q2 = pode ser função com algumas edge cases"
        - "Frequência alta justifica investimento"
      recommendation: "Considerar conversão com fallback"
      priority: "MEDIUM"

    CORRECTLY_AGENT:
      criteria:
        - "q1 = non-deterministic"
        - "Requer interpretação de linguagem natural"
        - "Output é criativo/analítico"
      recommendation: "Manter como Agent"
      priority: "NONE"

    SHOULD_BE_HYBRID:
      criteria:
        - "É Agent mas impacto de erro é médio/alto"
        - "Output vai para cliente/externo"
      recommendation: "Adicionar validação humana"
      priority: "MEDIUM"

    MISCLASSIFIED:
      criteria:
        - "execution_type atual não bate com análise"
      recommendation: "Reclassificar executor"
      priority: "HIGH"
```

---

## PHASE 2: ROI CALCULATION

**Duration:** 1-2 minutes

### Step 2.1: Estimate Costs

```yaml
calculate_roi:
  per_task:
    current_cost:
      if_agent:
        tokens_per_execution: "{estimate based on task complexity}"
        cost_per_1000_tokens: "$0.003 (input) + $0.015 (output)"
        executions_per_month: "{estimate}"
        monthly_cost: "{calculation}"

    potential_cost:
      if_worker:
        compute_per_execution: "$0.0001"
        monthly_cost: "{calculation}"

    savings:
      monthly: "{current - potential}"
      annual: "{monthly × 12}"

    conversion_effort:
      simple: "2-4 hours (lib exists)"
      medium: "1-2 days (need to implement)"
      complex: "3-5 days (edge cases)"

    payback_period:
      formula: "conversion_effort_cost / monthly_savings"
      threshold: "< 3 months = worth it"
```

---

## PHASE 3: REPORT GENERATION

**Duration:** 2-3 minutes

### Step 3.1: Generate Report

```yaml
report_template: |
  # Determinism Analysis Report

  **Target:** {target}
  **Date:** {date}
  **Tasks Analyzed:** {count}

  ---

  ## Executive Summary

  | Category | Count | Potential Monthly Savings |
  |----------|-------|---------------------------|
  | Should be Worker | {n} | ${savings} |
  | Could be Worker | {n} | ${savings} |
  | Correctly Agent | {n} | - |
  | Should be Hybrid | {n} | - |
  | Misclassified | {n} | - |

  **Total Potential Savings:** ${total}/month (${annual}/year)

  ---

  ## 🔴 HIGH PRIORITY: Should Be Worker

  Tasks que estão usando LLM mas poderiam ser código determinístico:

  ### {task_name}

  **Current:** Agent
  **Recommended:** Worker
  **Reason:** {analysis}

  **Evidence:**
  - Input: {input_type} → Estruturado ✅
  - Output: {output_type} → Previsível ✅
  - Lib exists: {lib_name} ✅

  **Implementation:**
  ```python
  # Sugestão de implementação
  {code_suggestion}
  ```

  **ROI:**
  - Current cost: ${current}/month
  - After conversion: ${after}/month
  - Savings: ${savings}/month
  - Conversion effort: {hours}h
  - Payback: {days} days

  ---

  ## 🟡 MEDIUM PRIORITY: Could Be Worker

  Tasks que poderiam ser Worker com algumas modificações:

  ### {task_name}

  **Current:** Agent
  **Recommended:** Worker with fallback to Agent
  **Reason:** {analysis}

  **Blockers:**
  - {blocker_1}
  - {blocker_2}

  **Path to Worker:**
  1. {step_1}
  2. {step_2}
  3. {step_3}

  ---

  ## ✅ CORRECTLY CLASSIFIED: Agent

  Tasks que corretamente usam LLM:

  | Task | Reason |
  |------|--------|
  | {task_name} | {reason} |

  ---

  ## ⚠️ SHOULD ADD VALIDATION: Hybrid

  Tasks Agent que deveriam ter validação humana:

  | Task | Impact Level | Recommendation |
  |------|--------------|----------------|
  | {task_name} | {level} | Add human review |

  ---

  ## Action Items

  ### Immediate (this week)
  - [ ] Convert {task_1} to Worker
  - [ ] Convert {task_2} to Worker

  ### Short-term (this month)
  - [ ] Evaluate {task_3} for conversion
  - [ ] Add Hybrid validation to {task_4}

  ### Backlog
  - [ ] Monitor {task_5} for patterns
```

---

## PHASE 4: IMPLEMENTATION SUGGESTIONS

### Step 4.1: Generate Code Stubs

Para tasks classificadas como SHOULD_BE_WORKER, gerar sugestão de implementação:

```yaml
code_generation:
  for_each_should_be_worker:
    analyze:
      - "Qual é a transformação core?"
      - "Quais libs usar?"
      - "Quais edge cases?"

    generate:
      script_template: |
        #!/usr/bin/env python3
        """
        Worker: {task_name}

        Converted from Agent to deterministic code.
        Original task: {task_file}
        """

        import {libs}

        def {function_name}(input_data: dict) -> dict:
            """
            {description}

            Args:
                input_data: {input_schema}

            Returns:
                {output_schema}
            """
            # Validation
            {validation_code}

            # Core transformation
            {transformation_code}

            # Output
            return {output}


        if __name__ == "__main__":
            # Example usage
            result = {function_name}({example_input})
            print(result)
```

---

## Examples

### Example 1: Analyzing Single Task

```
User: *analyze-determinism squads/copy/tasks/format-testimonial.md

Agent:
📊 **Determinism Analysis: format-testimonial**

**Current Classification:** Agent
**Recommended Classification:** Worker ✅

**Analysis:**

| Question | Answer | Evidence |
|----------|--------|----------|
| Q1: Output previsível? | ✅ SIM | Input é objeto com campos fixos, output é string formatada |
| Q2: Função pura? | ✅ SIM | Mesma entrada sempre gera mesma saída |
| Q2a: Lib existe? | ✅ SIM | Template string nativo |
| Q2b: Frequência? | ALTA | ~200 execuções/mês |

**Recommendation:** CONVERT TO WORKER

**Suggested Implementation:**
```python
def format_testimonial(data: dict) -> str:
    return f'"{data["quote"]}" - {data["name"]}, {data["title"]}'
```

**ROI:**
- Current: $15/month (Agent tokens)
- After: $0.02/month (compute)
- Savings: $14.98/month ($180/year)
- Effort: 1 hour
- Payback: Immediate
```

### Example 2: Analyzing Full Squad

```
User: *analyze-determinism copy

Agent:
📊 **Determinism Analysis: Squad copy**

**Tasks Analyzed:** 15
**Date:** 2026-02-03

## Summary

| Category | Count | Monthly Savings |
|----------|-------|-----------------|
| 🔴 Should be Worker | 3 | $45 |
| 🟡 Could be Worker | 2 | $20 |
| ✅ Correctly Agent | 8 | - |
| ⚠️ Should be Hybrid | 2 | - |

**Total Potential Savings:** $65/month ($780/year)

## 🔴 HIGH PRIORITY

### 1. format-testimonial.md
- Current: Agent → Recommended: Worker
- Reason: Template string simples
- Savings: $15/month

### 2. validate-headline-length.md
- Current: Agent → Recommended: Worker
- Reason: Validação de caracteres é determinística
- Savings: $20/month

### 3. count-power-words.md
- Current: Agent → Recommended: Worker
- Reason: Contagem contra lista fixa
- Savings: $10/month

## ✅ CORRECTLY AGENT

| Task | Reason |
|------|--------|
| generate-sales-page | Criação de copy requer interpretação |
| analyze-competitor | Análise semântica de texto |
| rewrite-for-audience | Adaptação criativa |
...
```

---

## Command Variants

```yaml
commands:
  basic:
    - "*analyze-determinism {task_file}"
    - "*analyze-determinism {squad_name}"
    - "*analyze-determinism all"

  with_options:
    - "*analyze-determinism {target} --verbose"      # Mostra análise detalhada de cada pergunta
    - "*analyze-determinism {target} --roi-only"     # Só mostra cálculo de ROI
    - "*analyze-determinism {target} --generate-code" # Gera código para Workers sugeridos
    - "*analyze-determinism {target} --output {file}" # Salva relatório em arquivo
```

---

## Quality Gate

```yaml
quality_gate:
  id: "DET_ANALYSIS_001"
  name: "Determinism Analysis Quality"

  blocking:
    - "Cada task tem classificação"
    - "Classificação tem justificativa"
    - "ROI calculado para conversões"

  warning:
    - "Sugestão de código para Workers"
    - "Action items priorizados"
```

---

## Integration Points

### Post-Analysis Actions

```yaml
post_analysis:
  if_should_be_worker:
    suggest:
      - "Quer que eu crie o script Worker para {task}?"
      - "Quer que eu atualize a task para execution_type: Worker?"

  if_should_be_hybrid:
    suggest:
      - "Quer que eu adicione human_review ao {task}?"

  if_misclassified:
    suggest:
      - "Quer que eu corrija o execution_type de {task}?"
```

---

## Related Documents

- `executor-decision-tree.md` - Decision tree usado na análise
- `executor-matrix-framework.md` - Perfis de executores
- `create-task.md` - Workflow de criação (usa mesma lógica)

---

**END OF TASK**
