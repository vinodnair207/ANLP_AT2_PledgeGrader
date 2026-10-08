# Rule-Based Baseline Tuning Notes
## Overview

The rule-based baseline classifies pledge text into three target classes:

- `none`
- `net_zero`
- `reduction`

It also checks four robustness signals:

- target year
- Scope 3 coverage
- offset use
- interim milestones

Rule refinement was performed using the 516-sentence validation split. The held-out 517-sentence test split was not used to tune the final revised baseline.

## Initial validation performance

Before the final rounds of rule refinement, the rule-based classifier achieved:

- Accuracy: 0.8624
- Macro F1: 0.8550

The largest weakness was the `net_zero` class. Precision was high (0.9153), but recall was lower (0.7660), showing that the rules were conservative and missed several valid net-zero expressions.

## Validation errors identified

### Net-zero target errors

Validation error analysis showed that the initial rules failed to recognise several semantically equivalent ways of expressing net-zero targets, including:

- carbon neutrality
- climate neutrality
- net greenhouse gas neutral
- emission neutral
- zero greenhouse gas emissions
- zero CO2 emissions
- real zero
- net neutrality
- `(net)-zero`
- neutrality of greenhouse gas emissions

Some remaining validation errors were intentionally not converted into new rules. These included implicit commitments such as membership of climate initiatives, multilingual wording, and references to the Paris Agreement that did not explicitly state a net-zero target. Adding highly specific rules for these cases could reduce generalisability.

### Reduction target errors

The original reduction patterns also missed several common formulations, particularly where the percentage appeared before the reduction expression. Examples included forms such as:

- `22.6% GHG reduction`
- `30-40% reduction by FY2030`
- `50% CO2 emissions reduction target`
- `reduction in greenhouse gases`
- `emissions reduction target`
- `eliminate 60% of emissions`
- `minimize GHG emissions by 55%`

The rules were expanded to capture these general linguistic patterns rather than individual validation sentences.

### Mixed-target passages

Some passages contained both a quantified emissions-reduction target and an explicit net-zero target. Because the dataset uses a single target label, these cases can be ambiguous for a deterministic rule system.

The classifier retains its existing precedence for explicit net-zero wording rather than adding example-specific exceptions for individual mixed-target validation cases.

## Robustness-signal rule improvements

The four robustness-signal rules were also made more precise.

### Target year

The original rule could treat almost any year as a target year. It was changed to require target-related context, such as:

- `by 2030`
- `before 2050`
- `target year 2040`
- `net zero by 2050`

This reduces false positives from baseline years or publication years.

### Scope 3

Scope 3 detection was restricted to explicit Scope 3 or equivalent value-chain and supply-chain language rather than relying on overly broad indirect-emissions wording.

### Offset use

The offset rule was changed so that simply mentioning words such as `offset` or `carbon credit` is not sufficient. The text must indicate how offsets, credits, or removals are used or not used in relation to the pledge.

### Interim milestones

The milestone rule was changed so that a single final target such as `net zero by 2030` is not automatically treated as an interim milestone. It instead looks for explicit interim-target language or a nearer-term quantified target on the pathway to a later final target.

## Final validation performance

After validation-only rule refinement, performance increased to:

- Accuracy: 0.9380
- Macro F1: 0.9356

Per-class validation F1 scores were:

- `none`: 0.9513
- `net_zero`: 0.9514
- `reduction`: 0.9041

The final unit-test suite contained 72 passing tests.

After the rules were frozen, the revised baseline was evaluated on the common 517-sentence held-out test set. The test set was used for final measurement rather than further tuning.

## Data-separation confirmation

The 100 sentences in the human signal-labelling sheet were not used to tune the target-year, Scope 3, offset-use, or interim-milestone rules.

Held-out test-set sentences were also not used to tune those signal rules.

Signal-rule development was based on the agreed project definitions and handcrafted unit-test cases. Target-classification rule refinement used only the 516-sentence validation split.

The final held-out test evaluation was run only after the revised rules had been frozen.