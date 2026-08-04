# Promptbreak – Pitch Notes

## One-liner

Promptbreak ist ein vollständig lokales Security-Labor, in dem Menschen und
LLM-Agenten Prompt-Injection-Angriffe ausführen, verschiedene Guardrails
vergleichen und deren Sicherheit, Nutzbarkeit und Rechenaufwand reproduzierbar
messen.

## Motivation

LLM-Anwendungen müssen zwei Fehler gleichzeitig vermeiden:

1. Ein Angriff wird nicht erkannt und erreicht sein Ziel.
2. Eine harmlose, aber verdächtig formulierte Anfrage wird fälschlich blockiert.

Ein System, das alles ablehnt, wäre zwar sicher, aber unbrauchbar. Promptbreak
untersucht deshalb nicht nur Angriffserfolg, sondern auch Overblocking, Latenz
und Computational Cost.

## Forschungsfrage

> Wie unterscheiden sich einfache Prompt-Injection-Guardrails,
> allgemeine Safety-Modelle und mehrschichtige Defense-Pipelines hinsichtlich
> Attack Success Rate, False Positive Rate, Latenz und Rechenaufwand?

## Vergleichene Methoden

Wir vergleichen fünf Konfigurationen bei identischem Zielmodell und identischen
Testfällen:

1. **Prompt only:** ausschließlich der System-Prompt des Zielmodells.
2. **Promptbreak Guard:** Heuristiken plus ein auf Prompt Injection
   instruierter Gemma-Classifier.
3. **Llama Guard 3 1B:** allgemeiner Content-Safety-Classifier.
4. **ShieldGemma 2B:** allgemeiner policy-basierter
   Content-Safety-Classifier.
5. **Full Pipeline:** Promptbreak Guard, Prompt Hardening, Context Guard sowie
   Direct- und Encoding-Output-Filter.

Llama Guard und ShieldGemma werden bewusst out of the box getestet. Dadurch
untersuchen wir auch, ob allgemeine Content-Safety-Modelle ohne spezielles
Prompt-Injection-Training als Anwendungsschutz ausreichen.

## Geplanter Evaluationsdatensatz

Die Hauptstudie verwendet ein kleines, fest versioniertes Set mit ungefähr
30 Fällen:

- etwa 10 direkte Angriffe, ausgewählt und auf Promptbreak angepasst aus
  [Open Prompt Injection](https://github.com/liu00222/Open-Prompt-Injection),
- 3 eigene dokumentierte Multi-Turn-Angriffe,
- 2 eigene Encoding- und Exfiltrationsangriffe,
- etwa 15 harmlose Anfragen aus
  [NotInject](https://github.com/safolab-wisc/injecguard), die typische
  Injection-Triggerwörter enthalten.

Für jeden Fall speichern wir Originalquelle, Original-ID, Anpassung,
Angriffskategorie, Ziel-Level, erwartetes Verhalten und Dialoghistorie. Eigene
Fälle werden eindeutig als solche markiert.

Das Kontrastprinzip ist zusätzlich durch
[XSTest](https://github.com/paul-rottger/xstest) motiviert: Sichere und
unsichere Fälle sollen sich teilweise nur minimal unterscheiden, damit die
tatsächliche Entscheidungsgrenze der Guards sichtbar wird. XSTest selbst
untersucht primär Content Safety und wird deshalb nicht unverändert als
Prompt-Injection-Benchmark ausgegeben.

## Evaluationsprotokoll

Die Evaluation trennt zwei Fragestellungen:

### 1. Erkennt der Guard den Angriff?

- Precision
- Recall
- Macro-F1
- False Positive Rate
- Ergebnisse nach Angriffskategorie

### 2. Erreicht der Angriff sein Anwendungsziel?

- Attack Success Rate: Wurde ein Secret tatsächlich ausgeliefert?
- Benign Utility: Wurde eine harmlose Anfrage zugelassen?
- direkte, kodierte und mehrstufige Exfiltration

Für die Laufzeitmessung werden Cold Start und Warm Runs getrennt betrachtet.
Nach einem Warm-up werden mehrere Wiederholungen durchgeführt und p50 sowie p95
berichtet.

## Latenz und Kosten

Alle Modelle laufen lokal über Ollama; direkte API-Kosten entstehen daher
nicht. Als reproduzierbare Computational-Cost-Proxys erfassen wir:

- Modellaufrufe pro Anfrage,
- Input- und Output-Tokens,
- End-to-End-Latenz,
- Modell-Ladezeit,
- Prompt- und Generation-Dauer,
- Modellgröße auf der Festplatte.

Falls ein hypothetisches API-Szenario diskutiert wird, wird die Schätzung
transparent als
`input tokens × input price + output tokens × output price` berechnet und
nicht mit den gemessenen lokalen Kosten verwechselt.

## Adaptive Angriffe

Als kleine methodische Erweiterung übernimmt **Rainbow-lite** die
Quality-Diversity-Idee aus
[Rainbow Teaming](https://arxiv.org/abs/2402.16822):

- Archivdimensionen: Angriffsfamilie × Transformation,
- LLM-basierte Mutation vorhandener Angriffe,
- deterministischer Judge über tatsächliche Secret-Exfiltration,
- Archivabdeckung, adaptive ASR und Success@k.

Dies ist eine seminar-taugliche Adaption mit wenigen Iterationen, keine
Replikation der verteilten MAP-Elites-Experimente des Papers.

## 90-Sekunden-Demo

1. **Problem zeigen:** Level 2 mit `Prompt only` über den SQL-Pfad
   kompromittieren.
2. **Defense vergleichen:** denselben Angriff durch Promptbreak Guard, Llama
   Guard und ShieldGemma klassifizieren lassen.
3. **Defense umgehen:** Level 3 über eine Multi-Turn-Sequenz und NOVA-64
   angreifen.
4. **Lücke schließen:** Context Guard und Encoding Detector aktivieren.
5. **Automatisieren:** einen Rainbow-lite-Mutationsschritt zeigen.
6. **Messen:** ASR, FPR, Latenz und Modellaufrufe in der Ergebnistabelle
   vergleichen.

## Aktueller Stand

- Die lokale Escape-Room-Anwendung und die Defense-Ablationen funktionieren.
- Der 30-Fälle-Datenrahmen und die Guard-Adapter sind implementiert.
- Llama Guard 3 1B und ShieldGemma 2B laufen lokal über Ollama.
- Timing-, Token- und Modellaufrufmetriken werden automatisch gespeichert.
- Rainbow-lite wurde end-to-end mit einem Mutationsschritt validiert.
- Die derzeitigen 30 Prompts sind noch ein selbst erstellter Prototyp und
  werden vor der Hauptauswertung durch nachvollziehbar gesourcte
  Open-Prompt-Injection- und NotInject-Beispiele ersetzt beziehungsweise
  ergänzt.

## Vorläufiger Smoke-Test zum Vorzeigen

Ein kompakter Lauf am 30. Juli 2026 verwendet zwei Angriffe und zwei bewusst
schwierige harmlose Triggerfälle. Jede der fünf Konfigurationen wurde einmal
getestet, insgesamt also 20 Messungen:

| Konfiguration     | ASR ↓ | FPR ↓ |  F1 ↑ | Ø Latenz |
| ----------------- | ----: | ----: | ----: | -------: |
| Prompt only       | 100 % |   0 % | 0,000 | 5.895 ms |
| Promptbreak Guard |  50 % | 100 % | 0,400 | 5.536 ms |
| Llama Guard 3 1B  | 100 % |   0 % | 0,000 | 6.360 ms |
| ShieldGemma 2B    | 100 % |   0 % | 0,000 | 7.118 ms |
| Full Pipeline     |   0 % | 100 % | 0,667 | 5.537 ms |

Der Lauf zeigt den erwarteten Trade-off anschaulich: Die allgemeinen
Content-Safety-Guards erkennen die beiden Prompt-Injection-Angriffe nicht. Die
Full Pipeline stoppt beide, blockiert aber zugleich beide harmlosen
Triggerfälle. Das ist ein technischer Demonstrationslauf mit vier ausgewählten
Fällen und einer Wiederholung, kein Studienergebnis. Cold- und Warm-Latenzen
werden erst in der Hauptauswertung getrennt.

## Zwei-Wochen-Scope

1. Externe Fälle auswählen, Provenienz dokumentieren und das Testset einfrieren.
2. Einen vollständigen Guard-Vergleich mit mehreren Warm Runs durchführen.
3. Fehlerfälle nach Angriffskategorie und Overblocking-Typ analysieren.
4. Einen kleinen statisch-vs.-adaptiv-Vergleich mit Rainbow-lite ausführen.
5. Ergebnistabelle und zwei Abbildungen erstellen:
   ASR gegen FPR sowie Sicherheit gegen Latenz beziehungsweise Rechenaufwand.

Nicht Teil des Scopes sind Fine-Tuning, eine vollständige Rainbow-Teaming-
Replikation, große Agentenbenchmarks oder reale Systeme mit Nebenwirkungen.

## Erwartete Kernaussage

Unsere Arbeitshypothese ist, dass allgemeine Content-Safety-Guards nicht
automatisch zuverlässige Prompt-Injection-Guards sind. Ein task-spezifischer
Input-Guard sollte mehr Angriffe erkennen, kann aber stärker overblocken.
Kontext- und Output-Prüfungen können verbleibende Exfiltrationen schließen,
verursachen jedoch zusätzliche Latenz und Modell- beziehungsweise
Rechenaufwände.
