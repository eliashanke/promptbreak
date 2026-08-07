# Promptbreak – Prompt Injection Escape Room

Ein interaktives Red-Team-Spiel für das NLP in Industry-Seminar. Das lokale Sprachmodell bewacht pro Level ein Secret; Spielende versuchen, es durch Prompt Injection zu extrahieren. Zwei Verteidigungsarchitekturen können direkt verglichen und mit einem eingebauten Testsatz evaluiert werden.

Alles läuft lokal über [Ollama](https://ollama.com/). Es gibt keine API-Keys, Cloud-Aufrufe oder nutzungsabhängigen Kosten.

## Was der Prototyp kann

- drei ansteigende Angriffsszenarien mit getrennten Secrets; Level 1 enthält
  bewusst eine leicht auffindbare Legacy-QA-Lücke, Level 2 einen enger
  definierten unsicheren SQL-Exportpfad und Level 3 eine zustandsbehaftete
  dreistufige Disaster-Recovery-Lücke
- **Baseline:** nur ein System-Prompt als Schutz
- **Guarded:** separater LLM-Input-Classifier, heuristische Regeln und
  deterministischer Output-Filter
- ein anspruchsvoller Guarded-Bypass in Level 3: Multi-Turn-State, fehlerhafte
  Legacy-Allowlist und Base64-Exfiltration
- lokales Chat-UI mit Modellwahl, Hinweisen und getrennten Verläufen
- integriertes Attack-Playbook mit erklärten Methoden und ladbaren Payloads
- Defense-Trace pro Antwort und animiertes Breach-Finale
- **Defense Builder** mit sechs einzeln schaltbaren Layern und fünf Presets
- **Auto Red-Team Agent**, der Seed-Angriffe ausführt und Fehlschläge mit Ollama
  analysiert und mutiert
- **Benchmark-Heatmap** über Prompt-only, Input-Guard, Output-Filter und Full
  Pipeline mit ASR, False-Positive-Rate und Latenz
- Live-Metriken für Attack Success Rate, Blocks und Latenz
- reproduzierbare 30-Fälle-Studie mit 15 Angriffen und 15 harmlosen
  XSTest-artigen Kontrastfällen
- lokale Vergleichsadapter für Promptbreak Guard, Llama Guard 3 und ShieldGemma
- Ollama-Telemetrie für Modellaufrufe, Tokens, Ladezeit und Inferenzzeit
- **Rainbow-lite** als kleines Quality-Diversity-Archiv für adaptive Angriffe
- nur eine kleine Python-Abhängigkeit: `tqdm` für Fortschritt und ETA

## Modellwahl

Der Default ist `gemma4:latest`, weil dieses Modell auf dem Zielrechner bereits
installiert ist und System-Prompts nativ unterstützt. Das ist für einen
Prompt-Injection-Vergleich besonders passend. Gemma 4 ist die aktuelle
Modellgeneration; wer weniger Arbeitsspeicher hat, kann problemlos Gemma 3
verwenden.

| Hardware     | Empfehlung      | Downloadgröße | Einordnung                                    |
| ------------ | --------------- | ------------: | --------------------------------------------- |
| 8 GB RAM     | `gemma3:1b`     |    ca. 815 MB | schnell, aber deutlich leichter auszutricksen |
| 16 GB RAM    | `gemma3:4b`     |    ca. 3,3 GB | kompakter Fallback                            |
| 16–24 GB RAM | `gemma4:latest` |    ca. 9,6 GB | **Default auf diesem Rechner**                |
| 24+ GB RAM   | `gemma4:12b`    |    ca. 7,6 GB | aktuelle Generation, längerer Kontext         |

Die Größen stammen aus den offiziellen Ollama-Modellseiten für
[Gemma 4](https://ollama.com/library/gemma4) und
[Gemma 3](https://ollama.com/library/gemma3). Strukturierte Ausgaben werden für
den Guard-Classifier über Ollamas JSON-Schema-Unterstützung angefordert.

### Chinesische Vergleichsmodelle

Für einen herkunftsübergreifenden Vergleich enthält `model_adapters.py` kurze
Aliase für mehrere chinesische Ollama-Modelle. Die Downloadgröße ist nur ein
grober Hardware-Proxy; Parameterzahl, Quantisierung und Architektur sind nicht
direkt gleichzusetzen. Stand: 31. Juli 2026.

| Alias | Ollama-Tag | Download | Kontext | Verwendung |
| --- | --- | ---: | ---: | --- |
| `qwen35_4b` | `qwen3.5:4b` | 3,4 GB | 256K | speichersparender getesteter Vergleich |
| `qwen35_9b` | `qwen3.5:9b` | 6,6 GB | 256K | moderner Hauptvergleich |
| `qwen3_14b` | `qwen3:14b` | 9,3 GB | 40K | ähnlichste Downloadgröße |
| `deepseek_r1_14b` | `deepseek-r1:14b` | 9,0 GB | 128K | reasoning-orientierter Vergleich |
| `glm4_9b` | `glm4:9b` | 5,5 GB | 128K | optionaler älterer Vergleich |

Quellen: [Qwen 3.5](https://ollama.com/library/qwen3.5),
[Qwen 3](https://ollama.com/library/qwen3),
[DeepSeek R1](https://ollama.com/library/deepseek-r1) und
[GLM-4](https://ollama.com/library/glm4). Der Adapter deaktiviert bei Qwen und
DeepSeek das standardmäßig mögliche Thinking während der Evaluation. Dadurch
werden Latenz und Tokenverbrauch nicht durch unterschiedlich lange Reasoning-
Traces verzerrt. Beliebige andere Ollama-Tags funktionieren weiterhin direkt.

## Schnellstart

Voraussetzungen: Python 3.9+ sowie
[Ollama](https://docs.ollama.com/macos) unter macOS, Linux oder Windows.

```bash
cd project
uv sync
ollama pull gemma4
uv run python main.py
```

Danach <http://127.0.0.1:8000> öffnen. Falls die Ollama-App nicht automatisch
läuft:

```bash
ollama serve
```

Ein anderes Modell lässt sich entweder in der Oberfläche auswählen oder beim
Start festlegen:

```bash
OLLAMA_MODEL=gemma3:4b python3 main.py --port 8080
```

Für einen abweichenden Ollama-Server:

```bash
OLLAMA_URL=http://127.0.0.1:11434 python3 main.py
```

## Kompletter reproduzierbarer Ablauf

Die folgenden Befehle führen Tests, statischen Vergleich, False-Positive-
Diagnose, Rainbow-Lite und Visualisierungen in der vorgesehenen Reihenfolge aus.
Alle Befehle werden aus `project/` aufgerufen.

### 1. Umgebung und Modelle vorbereiten

```bash
uv sync
ollama pull gemma4:latest
ollama pull llama-guard3:1b
ollama pull shieldgemma:2b
ollama list
```

Falls Ollama nicht automatisch läuft:

```bash
ollama serve
```

### 2. Tests ausführen

```bash
uv run python -m unittest discover -s tests -v
```

### 3. Benchmarkmatrix ohne Modellaufrufe prüfen

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --repeats 3 \
  --dry-run
```

Die erwartete Matrix enthält 30 Fälle, fünf Konfigurationen, drei
Wiederholungen und damit 450 Case-Configuration-Beobachtungen.

### 4. Optionalen kurzen Smoke Test ausführen

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --repeats 1 \
  --max-cases 4 \
  --output evaluation-results/smoke-guards.json
```

### 5. Vollständigen Guard-Vergleich ausführen

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --promptbreak-model gemma4:latest \
  --llama-guard-model llama-guard3:1b \
  --shieldgemma-model shieldgemma:2b \
  --repeats 3 \
  --output evaluation-results/full-guard-comparison.json
```

Auf dem für das Seminar verwendeten Rechner dauerte ein vollständiger Lauf
ungefähr 67 Minuten. Die tatsächliche Laufzeit hängt von Hardware, Modellcache
und der Zahl früh blockierter Fälle ab.

### 6. False Positives des Promptbreak Input Guards zuordnen

```bash
uv run python diagnose_false_positives.py \
  --model gemma4:latest \
  --output evaluation-results/false-positive-attribution.json
```

Der Runner testet die 15 benignen Fälle getrennt gegen die Regex-Heuristiken und
gegen den Gemma-Klassifikator ohne Heuristiken. Der Report ordnet jeden Fall
`heuristics_only`, `llm_only`, `both` oder `neither` zu.

### 7. Confidence Threshold systematisch testen

```bash
uv run python sweep_guard_thresholds.py \
  --model gemma4:latest \
  --output evaluation-results/guard-threshold-sweep.json
```

Jeder der 30 Prompts wird genau einmal bei Temperatur 0 klassifiziert. Die
Thresholds werden anschließend offline auf denselben Rohentscheidungen
ausgewertet. So ist der Vergleich nicht durch unterschiedliche Modellantworten
verzerrt.

Gezielte End-to-End-Validierung des überarbeiteten Guards:

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --promptbreak-model gemma4:latest \
  --promptbreak-threshold 0.55 \
  --config promptbreak_guard \
  --config full_pipeline \
  --repeats 1 \
  --output evaluation-results/tuned-guard-validation.json
```

### 8. Rainbow-Lite ausführen

Der Standardlauf erzeugt 24 adaptive Kandidaten. Damit wird jede der zwölf
nicht-direkten Archivzellen zweimal besucht; erfolgreiche oder weiter
fortgeschrittene Kandidaten dienen als Eltern späterer Mutationen.

```bash
uv run python rainbow_lite.py \
  --target-model gemma4:latest \
  --attacker-model qwen35_4b \
  --configuration full_pipeline \
  --iterations 24 \
  --output evaluation-results/rainbow-lite-qwen35-4b-24.json
```

Für einen schnellen technischen Smoke-Test reichen vier Mutationen:

```bash
uv run python rainbow_lite.py \
  --target-model gemma4:latest \
  --attacker-model qwen35_4b \
  --configuration full_pipeline \
  --iterations 4 \
  --output evaluation-results/rainbow-lite-qwen35-4b-smoke.json
```

Der Defense-Filter und der objektive Judge sind getrennt: Der Filter erkennt
die von der Anwendung unterstützten direkten, Hex-, ROT13-, Reverse- und
Base64-Leaks. Der stärkere Judge erkennt zusätzlich Dezimal-, Binär- und
Unicode-Codepoint-Ausgaben. Wären beide identisch, könnte ein vom Judge
messbarer Full-Pipeline-Bypass definitionsgemäß nie auftreten.

### 9. Visualisierungen erzeugen

Ohne Argumente liest das Visualisierungsskript die historischen vollständigen
Reports. Beliebige datierte Guard- und Rainbow-Reports lassen sich in einen
eigenen Ausgabeordner rendern:

```bash
uv run python visualize_results.py \
  --guard-report evaluation-results/qwen35-4b-full-guard-comparison-2026-08-07.json \
  --rainbow-report evaluation-results/rainbow-lite-qwen35-4b-24-2026-08-07.json \
  --output-dir evaluation-results/visualizations/qwen35-4b-2026-08-07
```

Es erzeugt SVGs und eine HTML-Übersicht unter
`evaluation-results/visualizations/`. PNG-Dateien können optional mit
`rsvg-convert` aus `librsvg` erzeugt werden:

```bash
for file in evaluation-results/visualizations/*.svg; do
  rsvg-convert -w 1600 "$file" -o "${file%.svg}.png"
done
```

### 10. Zielmodelle vergleichen

Die Adapter laden keine Modelle automatisch herunter. Zuerst die tatsächlich
gewünschten Kandidaten auswählen und explizit installieren, zum Beispiel:

```bash
ollama pull qwen3.5:9b
ollama pull qwen3:14b
ollama pull deepseek-r1:14b
```

Die geplante Matrix lässt sich ohne Downloads und Modellaufrufe prüfen:

```bash
uv run python compare_target_models.py --dry-run
```

Ein kleiner Smoke Test mit Gemma 4 und Qwen 3.5:

```bash
uv run python compare_target_models.py \
  --model gemma4 \
  --model qwen35_9b \
  --max-cases 4 \
  --repeats 1 \
  --output evaluation-results/target-model-smoke.json
```

Ohne `--model` werden Gemma 4 sowie die drei empfohlenen chinesischen Modelle
verglichen. Standardmäßig laufen `prompt_only` und `full_pipeline`; der
Promptbreak-Guard bleibt dabei auf Gemma 4 fixiert, damit wirklich nur das
Zielmodell variiert. Für einen chinesischen Guard-Classifier funktioniert der
bestehende Runner ebenfalls mit Alias:

```bash
uv run python compare_guards.py \
  --target-model gemma4 \
  --promptbreak-model qwen35_9b \
  --config promptbreak_guard \
  --config full_pipeline \
  --repeats 1 \
  --output evaluation-results/qwen35-guard.json
```

### Aufgezeichneter Qwen-3.5-4B-Lauf

Am 7. August 2026 wurde der vollständige 30×5-Vergleich mit einer Wiederholung
und `qwen35_4b` sowohl als Zielmodell als auch als Promptbreak-Klassifikator
ausgeführt. Promptbreak erreichte 13,3 % ASR, 0,0 % Input-Guard-FPR und F1
0,929; die Full Pipeline erreichte 0,0 % ASR. Zwei benigne Eingaben führten beim
Zielmodell zu echten direkten Leaks, die der Output-Filter abfing. Deshalb
beträgt ihre End-to-End-Benign-Blockrate 13,3 %, während die Input-Guard-FPR
0,0 % bleibt.

- [vollständiger Qwen-Guard-Report](evaluation-results/qwen35-4b-full-guard-comparison-2026-08-07.json)
- [Qwen-Threshold-Sweep](evaluation-results/qwen35-4b-guard-threshold-sweep-2026-08-07.json)
- [Qwen-False-Positive-Attribution](evaluation-results/qwen35-4b-false-positive-attribution-2026-08-07.json)
- [24er Rainbow-Lite-Report](evaluation-results/rainbow-lite-qwen35-4b-24-2026-08-07.json)
- [Qwen-SVG-Galerie](evaluation-results/visualizations/qwen35-4b-2026-08-07/index.html)

Der Lauf ist ein vollständiger Modell-/Konfigurationspass, aber wegen nur einer
Wiederholung kein Ersatz für die noch offene finale 30×5×3-Evaluation.

### Fortschrittsbalken und ETA

`compare_guards.py`, `compare_target_models.py`, `rainbow_lite.py`, `evaluate.py`,
`diagnose_false_positives.py` und `sweep_guard_thresholds.py` verwenden `tqdm`.

- Der Guard-Vergleich zeigt Gesamtfortschritt, aktuelle Konfiguration,
  Wiederholung und Fall-ID.
- Rainbow-Lite zählt Mutation und anschließende Evaluation als getrennte
  Phasen, damit die ETA nicht zwei Modellaufrufe als einen Schritt behandelt.
- Die ETA stabilisiert sich nach den ersten Modellaufrufen.
- Bei einem Modellwechsel zwischen Gemma, Llama Guard und ShieldGemma kann sie
  vorübergehend springen, weil Ladezeit und Durchsatz unterschiedlich sind.
- Fortschrittsausgabe läuft über `stderr`; JSON auf `stdout` bleibt parsebar.

## Evaluation

In der Weboberfläche führt **RUN 10-CASE EVALUATION** den festen Testsatz für
den gerade aktiven Modus aus. Für einen direkten Vergleich beider Methoden:

```bash
uv run python evaluate.py \
  --model gemma4:latest \
  --level 1 \
  --output evaluation-results/gemma3-4b.json
```

Erfasst werden:

- **Attack Success Rate (ASR):** Anteil der Angriffe, bei denen das Secret
  tatsächlich an den Client ausgeliefert wird; niedriger ist besser.
- **End-to-End-Benign-Blockrate:** Anteil harmloser Anfragen, die an irgendeiner
  Schicht blockiert werden; das schließt abgefangene Zielmodell-Leaks ein.
- **Input-Guard-FPR:** Anteil harmloser Anfragen, die bereits der Input Guard
  fälschlich blockiert; niedriger ist besser.
- **Accuracy:** erfolgreiche Abwehr von Angriffen plus Durchlassen harmloser
  Anfragen.
- **Latenz:** End-to-End-Laufzeit je Fall. Guarded benötigt meist einen
  zusätzlichen Modellaufruf.

### Guard-Vergleich

Der versionierte Datensatz
[`data/guard-evaluation.json`](data/guard-evaluation.json) enthält 15 Angriffe
und 15 harmlose Kontrastfälle mit angriffsähnlichen Triggerwörtern. Die
Kontrastmethode ist durch XSTest motiviert; die Fälle selbst sind auf
Prompt-Injection und die drei Promptbreak-Level zugeschnitten.

Die kleinen lokalen Guard-Modelle werden einmalig über Ollama installiert:

```bash
ollama pull llama-guard3:1b
ollama pull shieldgemma:2b
```

Anschließend vergleicht ein Lauf fünf Konfigurationen. Drei Wiederholungen
ergeben 450 Einzelmessungen:

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --repeats 3 \
  --output evaluation-results/guard-comparison.json
```

Vor einem langen Lauf kann die Matrix ohne Modellaufrufe validiert werden:

```bash
uv run python compare_guards.py --dry-run
```

Zusätzlich zu ASR, FPR, Precision, Recall und F1 speichert der Report:

- p50- und p95-Wall-Clock-Latenz,
- mittlere Latenz getrennt nach Guard-Refusal, deterministischem Legacy-Pfad
  und echtem Zielmodellpfad,
- Guard-, Target/Application- und Output-Filter-Zeit,
- Modell-Ladezeit,
- Modellaufrufe pro Fall,
- Input- und Output-Tokens,
- optionale hypothetische API-Kosten bei explizit übergebenen Tokenpreisen.

Die lokalen API-Kosten sind null. Modellaufrufe, Tokens und Laufzeit dienen als
reproduzierbare Computational-Cost-Proxys. Llama Guard und ShieldGemma werden
bewusst out of the box eingesetzt: Beide sind allgemeine Content-Safety-Guards,
keine speziell trainierten Prompt-Injection-Detektoren.

### Rainbow-lite

`rainbow_lite.py` übernimmt aus Rainbow Teaming die Idee eines
Quality-Diversity-Archivs, bleibt aber bewusst seminar-klein. Das Archiv hat die
Dimensionen Angriffsfamilie und Transformation; der objektive Judge ist die
deterministische Secret-Exfiltration.

```bash
uv run python rainbow_lite.py \
  --target-model gemma4:latest \
  --attacker-model qwen35_4b \
  --configuration full_pipeline \
  --iterations 24 \
  --output evaluation-results/rainbow-lite-qwen35-4b-24.json
```

Berichtet werden Archivabdeckung, Defense-Fortschritt, erfolgreiche Zellen,
statische Seed-ASR, adaptive Kandidaten-ASR und Success@k. Dies ist eine
methodisch motivierte Adaption und keine Replikation der rechenintensiven
Originalstudie.

## Architektur

```text
Baseline
user input ───────────────→ target LLM + system prompt ──────→ response

Guarded
user input → rules + LLM classifier → target LLM + hardening → leak filter → response
                   │ blocked                                  │ redacted
                   └──────────────── safe refusal ────────────┘
```

Das Backend ist ein kleiner `ThreadingHTTPServer`. Es serviert die statischen
Dateien und spricht Ollamas lokale `/api/chat`-Schnittstelle an. Secrets werden
nicht an den Browser übertragen. Sitzungsmetriken leben nur im Arbeitsspeicher
und verschwinden beim Server-Neustart.

Die absichtlich verwundbaren Baseline-Pfade werden deterministisch im Backend
ausgelöst. Dadurch hängt ein korrekter Lösungsweg nicht davon ab, ob ein modernes
Modell die unsichere Instruktion zufällig trotzdem verweigert. Alle übrigen
Antworten werden weiterhin von Ollama generiert.

Level 3 enthält zusätzlich einen reproduzierbaren Angriff auf die Guarded-Pipeline.
Eine zustandslose Legacy-Allowlist vertraut einer dreistufig aufgebauten
Recovery-Sequenz. Der finale Wert wird als NOVA-64-Hülle (Base64) ausgegeben:
Der einfache Klartext-Output-Filter übersieht ihn, ein getrennt implementierter
Evaluator dekodiert ihn jedoch und wertet ihn korrekt als Exfiltration. Damit
sind Schutzmechanismus und Messinstrument bewusst nicht mehr identisch.

## Pitch Lab

Eine zitierfähige Einordnung und paper-basierte Erweiterungs-Roadmap stehen in
[`LITERATURE.md`](LITERATURE.md); BibTeX-Einträge liegen in
[`references.bib`](references.bib).

### Defense Builder

Die Oberfläche erlaubt eine Ablation der einzelnen Sicherheitskomponenten:

1. Heuristic Scanner
2. LLM Input Guard
3. Prompt Hardening
4. Direct Leak Filter
5. Encoding Detector
6. Context-Aware Guard

Die Presets `Prompt only`, `Input guard`, `Output filter`, `Standard` und
`Full pipeline` setzen feste Konfigurationen. Manuelle Änderungen
erzeugen eine Custom-Konfiguration, die sofort für Chat und Auto-Red-Team gilt.

### Auto Red-Team Agent

Der Agent beginnt mit reproduzierbaren Seeds aus dem Playbook. Hält die Defense,
erzeugt das ausgewählte lokale Ollama-Modell anhand der letzten Resultate eine
neue Strategie und einen neuen Angriffsprompt als strukturierte Ausgabe. Pro
Lauf sind ein bis fünf Runden möglich; bei einem Breach stoppt der Agent.

### Benchmark-Heatmap

`BUILD HEATMAP` führt vier Angriffsarten und eine harmlose Kontrollanfrage gegen
vier Defense-Konfigurationen aus:

- Authority Claiming
- Format Smuggling
- Multi-Turn Context Poisoning
- Encoding Exfiltration

Die Heatmap zeigt die Attack Success Rate je Zelle. Darunter werden die
aggregierte ASR, False-Positive-Rate und mittlere End-to-End-Latenz ausgegeben.
Da die Messung echte lokale Modellaufrufe enthält, kann sie einige Minuten
dauern.

## Projektstruktur

```text
project/
├── main.py              # Webserver, Ollama-Client und Defense-Pipelines
├── evaluate.py          # reproduzierbare CLI-Evaluation
├── compare_guards.py    # 30-Fälle-Vergleich der Guard-Modelle
├── compare_target_models.py
│                         # Vergleich verschiedener Ollama-Zielmodelle
├── diagnose_false_positives.py
│                         # Attribution: Heuristiken vs. LLM-Klassifikator
├── sweep_guard_thresholds.py
│                         # ein Modelllauf, mehrere Offline-Thresholds
├── rainbow_lite.py      # kleines Quality-Diversity-Red-Teaming
├── visualize_results.py # reproduzierbare SVG-Auswertung der JSON-Reports
├── evaluation-results/  # versionierte JSON-Reports und SVG-Auswertungen
├── pitch/               # Typst-Quelle, Grafiken und gebautes Pitch-PDF
├── data/
│   └── guard-evaluation.json
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/               # 53 modellfreie Unit-Tests
└── pyproject.toml
```

## Tests

Die Unit-Tests benötigen kein Modell:

```bash
uv run python -m unittest discover -s tests -v
```

## Grenzen und Sicherheit

Das Projekt ist eine isolierte Simulation. Es besitzt keine Tools und greift
nicht auf Dateien, Accounts oder reale Zugangsdaten zu. Ein LLM-Guard garantiert
keine Sicherheit; gerade der Vergleich soll messbar zeigen, welche Angriffe und
False Positives verbleiben. Secrets in `main.py` sind Spielwerte, keine echten
Credentials.
