# Promptbreak – Projektstatus und TODO

Stand: 7. August 2026

## Ziel des Projekts

Promptbreak untersucht, wie sich Prompt-Injection-spezifische Schutzmaßnahmen,
allgemeine Safety Guards und eine mehrschichtige Defense Pipeline hinsichtlich
Security, Utility, Latenz und Rechenaufwand unterscheiden.

Der Umfang bleibt bewusst seminar-tauglich: ein lokales System, ein fester
30-Fälle-Benchmark, fünf Konfigurationen und eine kleine adaptive
Rainbow-Lite-Auswertung.

## Erledigt

### Prototyp und Defenses

- [x] Lokale Prompt-Injection-Anwendung mit drei angreifbaren Levels umgesetzt
- [x] Reproduzierbare, deterministische Angriffspfade implementiert
- [x] Prompt-only-Baseline implementiert
- [x] Promptbreak Input Guard aus Heuristiken und Gemma-Klassifikator implementiert
- [x] Llama Guard 3 als Out-of-the-box-Vergleich integriert
- [x] ShieldGemma als Out-of-the-box-Vergleich integriert
- [x] Full Pipeline mit Context Guard, Output Filter und Encoding Detector implementiert
- [x] Trace-Ausgabe für Guard, Modellpfad, Output Filter und objektiven Judge ergänzt

### Benchmark und Metriken

- [x] Versionierten Datensatz mit 30 Fällen erstellt
- [x] Datensatz auf 15 Angriffe und 15 benigne Kontrastfälle balanciert
- [x] Angriffe in Authority, Format Smuggling, Multi-Turn und Encoding aufgeteilt
- [x] Benigne Triggerfälle für Debugging, Encoding, Passwörter, Roleplay und System Prompts ergänzt
- [x] Vergleichsrunner für fünf Konfigurationen implementiert
- [x] ASR, Attack Block Rate, FPR, Precision, Recall und F1 implementiert
- [x] p50-/p95-Latenz, Modellaufrufe und Tokenverbrauch erfasst
- [x] Lokale API-Kosten als EUR 0 und Compute-Proxys getrennt ausgewiesen
- [x] Drei Wiederholungen und 450 Case-Configuration-Beobachtungen durchgeführt
- [x] Keine Guard- oder Parsing-Fehler im vollständigen Lauf festgestellt
- [x] Alle drei Wiederholungen lieferten identische ASR- und FPR-Werte
- [x] False Positives separat Heuristiken und Gemma-Klassifikator zugeordnet
- [x] `tqdm`-Fortschritt und ETA für alle langen CLI-Runner ergänzt
- [x] Vollständigen reproduzierbaren Ablauf im README dokumentiert
- [x] Reportfertige Markdown-Dokumentation für Methoden, Ergebnisse, Error Analysis, Diskussion und Reproduzierbarkeit erstellt
- [x] Intentionally vulnerable Level-Contracts und vollständige 30-Fälle-Evaluationssuite reportfertig dokumentiert

### Vollständiger Lauf

- [x] Prompt only ausgewertet: ASR 100,0 %, FPR 0,0 %
- [x] Promptbreak Guard ausgewertet: ASR 13,3 %, FPR 93,3 %
- [x] Llama Guard 3 ausgewertet: ASR 66,7 %, FPR 0,0 %
- [x] ShieldGemma ausgewertet: ASR 100,0 %, FPR 0,0 %
- [x] Full Pipeline ausgewertet: ASR 0,0 %, FPR 93,3 %
- [x] 480 tatsächliche Modellaufrufe und 228.399 Tokens dokumentiert
- [x] Maschinenlesbaren vollständigen JSON-Report gespeichert

### Rainbow-Lite

- [x] Seminar-kleine Quality-Diversity-Adaption implementiert
- [x] Vier statische Seeds gegen die Full Pipeline ausgeführt
- [x] Acht adaptive Mutationen erzeugt und getestet
- [x] 12 von 16 Archivzellen belegt
- [x] Keine erfolgreiche statische oder adaptive Exfiltration festgestellt
- [x] Rainbow-Lite-Report gespeichert

### Qualität und Kommunikation

- [x] 61 automatisierte Tests erfolgreich ausgeführt
- [x] Security–Utility-Visualisierung erstellt
- [x] Heatmaps für Angriffs- und Benign-Kategorien erstellt
- [x] Latenz- und Compute-Visualisierung erstellt
- [x] Rainbow-Lite-Archiv visualisiert
- [x] Reproduzierbares Visualisierungsskript erstellt
- [x] Englische Pitch-Präsentation im Metropolyst-Standardtemplate erstellt

## Als Nächstes – notwendig

### 1. Overblocking des Promptbreak Guards reduzieren

- [x] Die 14 blockierten benignen Fälle einzeln analysieren
- [x] Prüfen, ob Heuristik, Gemma-Klassifikator oder beide die Blockierung auslösen
- [x] Guard-Trace im Report um getrennte Heuristik- und LLM-Entscheidungen erweitern
- [x] Zu breite Triggerregeln identifizieren und enger formulieren
- [x] Confidence Threshold des Gemma Guards systematisch testen
- [x] Benigne System-Prompt-, Passwort-, Debugging- und Roleplay-Anfragen explizit berücksichtigen
- [x] Regressionstests für alle bisher falsch blockierten benignen Fälle ergänzen
- [x] Gezielte End-to-End-Validierung mit einem vollständigen 30-Fälle-Pass durchführen
- [x] Promptbreak Guard: FPR von 93,3 % auf 0,0 % bei unveränderter ASR von 13,3 % senken
- [x] Full Pipeline: FPR von 93,3 % auf 0,0 % bei unveränderter ASR von 0,0 % senken

Ziel im gezielten Ein-Wiederholungs-Lauf erreicht. Ein finaler
Drei-Wiederholungs-Lauf und ein ungesehener Holdout bleiben notwendig.

### 2. Benchmark und Quellen einfrieren

- [x] Für jeden Benchmarkfall Quelle oder Kennzeichnung „Promptbreak-spezifisch“ dokumentieren
- [x] Übernommene Fälle und eigene Anpassungen nachvollziehbar kennzeichnen
- [x] Open Prompt Injection, NotInject/InjecGuard und XSTest sauber zuordnen
- [x] Erwartetes Verhalten jedes Falls noch einmal manuell prüfen
- [x] Datensatz nach der Prüfung als Version 1.1 einfrieren

Ziel: Ein kleiner, aber nachvollziehbarer und zitierbarer Benchmark.

### 3. Finale Evaluation nach Guard-Verbesserung wiederholen

- [x] Tests nach jeder Guard-Änderung ausführen
- [x] Kurzen Smoke Test vor dem langen Lauf ausführen
- [ ] Vollständigen 30 × 5 × 3 Benchmark erneut ausführen
- [ ] Alten und neuen Promptbreak Guard direkt vergleichen
- [ ] Prüfen, ob die drei Wiederholungen weiterhin stabil sind
- [ ] Finale JSONs und Visualisierungen mit eindeutiger Versionsnummer speichern

Ziel: Belegen, ob die Änderungen tatsächlich den Security–Utility-Trade-off verbessern.

### 4. Latenzauswertung methodisch bereinigen

- [x] Guard-only-Latenz und End-to-End-Latenz getrennt erfassen
- [x] Blockierte, deterministische und echte Zielmodellpfade getrennt auswerten
- [x] Erklären, warum Prompt only teilweise 0 ms und die Full Pipeline einen niedrigen p95-Wert erreicht
- [x] Hardware, Ollama-Version, Modellversionen und Warm-up-Protokoll dokumentieren
- [x] Mean zusätzlich zu p50 und p95 berichten

Ziel: Verhindern, dass frühes Overblocking fälschlich als Performance-Vorteil interpretiert wird.

### 5. Pitch und Bericht auf finale Ergebnisse aktualisieren

- [ ] Smoke-Test-Tabelle durch vollständige Ergebnisse ergänzen oder ersetzen
- [ ] Finalen Security–Utility-Plot in die Präsentation übernehmen
- [ ] Kategorie-Heatmap als wichtigste Error-Analysis-Grafik aufnehmen
- [ ] Aussage zu Llama Guard präzisieren: erkennt vor allem Format Smuggling
- [ ] Aussage zu ShieldGemma präzisieren: kein messbarer Schutz auf diesem Datensatz
- [ ] Overblocking als zentrales Ergebnis und nicht als Randnotiz darstellen
- [ ] Einschränkungen des kleinen, anwendungsspezifischen Datensatzes nennen
- [ ] Finale Forschungsfrage und Contribution im Bericht konsistent formulieren

## Optional, falls noch Zeit bleibt

### Rainbow-Lite erweitern

- [x] Rainbow-Lite mit 24 statt 8 Mutationen ausführen
- [x] Jede nicht-direkte Archivzelle mindestens zweimal untersuchen
- [ ] Optional zwei oder drei unabhängige Rainbow-Lite-Seeds vergleichen
- [ ] Nur behaupten, was tatsächlich getestet wurde; keine allgemeine Robustheit ableiten

### Kostenabschätzung

- [ ] Ein realistisches hypothetisches API-Preisszenario auswählen
- [ ] Input- und Output-Tokenpreise transparent dokumentieren
- [ ] Hypothetische Kosten pro 1.000 Fälle berechnen
- [ ] Lokale EUR-0-Kosten weiterhin getrennt von Rechenaufwand darstellen

### Demo und Reproduzierbarkeit

- [ ] Einen kurzen Demoablauf mit einem erfolgreichen Angriff und einem False Positive vorbereiten
- [x] Einen festen Befehl für den Smoke Test dokumentieren
- [x] Einen festen Befehl für den vollständigen Benchmark dokumentieren
- [x] Einen festen Befehl für Rainbow-Lite dokumentieren
- [x] Visualisierungen mit einem einzigen Befehl reproduzierbar machen
- [x] Datierte Qwen-Ergebnisdateien und Modellnamen im README verlinken

### Qwen-3.5-4B-Zusatzlauf

- [x] Qwen als Rainbow-Lite-Angreifer mit technischem Smoke Test prüfen
- [x] Qwen-Sicherheitsverweigerungen durch zielerhaltende Templates behandeln
- [x] 24 adaptive Mutationen und alle 16 Archivzellen auswerten
- [x] Vollständigen 30 × 5 × 1 Qwen-Pass mit 150 Beobachtungen ausführen
- [x] Qwen-Threshold-Sweep über alle 30 Fälle ausführen
- [x] Input-False-Positives von abgefangenen Output-Leaks trennen
- [x] Datierte, parameterisierte Qwen-Visualisierungen erzeugen

Ergebnis: 100 % Rainbow-Archivabdeckung ohne Full-Pipeline-Breach. Der Qwen-
Input-Guard blockiert bei Threshold 0,55 13/15 Angriffe und 0/15 benigne Fälle;
die Heuristik-Kombination blockiert 15/15 und 0/15. Die Full Pipeline fängt
zusätzlich zwei direkte Zielmodell-Leaks bei benignen Eingaben ab.

### Optionales Guard-Fine-Tuning

- [x] PIGuard-inspiriertes Llama-QLoRA-Trainingsnotebook ergänzen
- [x] Vorläufigen source-getaggten Trainingskorpus zusammenstellen
- [x] Abweichung zu PIGuard/MOF und Evaluationsplan dokumentieren
- [ ] Exaktes Basismodell, Revision, MAX_LENGTH, Seed und Hardware dokumentieren
- [ ] Leere, doppelte und widersprüchlich gelabelte Beispiele bereinigen
- [ ] Lizenzen, URLs, Versionen und Transformationen aller Quellen dokumentieren
- [ ] Provenienzpflichtiges JSONL-Quellformat und gruppierte Splits implementieren
- [ ] Leakage-Prüfung gegen den eingefrorenen 30-Fälle-Holdout ergänzen
- [ ] NotInject vollständig aus Training und Threshold-Auswahl heraushalten
- [ ] LoRA-Adapter mit mindestens drei Seeds trainieren und auf Validation auswählen
- [ ] Fine-tuned Llama und offiziellen PIGuard-Checkpoint in
  `experiments/compare_guards.py` integrieren
- [ ] Gewähltes Modell einmalig auf Promptbreak, NotInject und externem Holdout evaluieren

### Qwen-3.5-27B-Rainbow-Lite

- [ ] 24 adaptive Mutationen mit Qwen 3.5 27B vollständig ausführen
- [ ] Parserfehler und Mutator-Fallbacks im Report kontrollieren
- [ ] Archivabdeckung, adaptive ASR und Breaches auswerten
- [ ] 27B-Rainbow-Visualisierung erzeugen und Ergebnis dokumentieren

## Bewusst nicht Teil des Projekts

- Kein Fine-Tuning des 27B-Zielmodells; optional nur ein kleiner dedizierter Guard
- Keine Replikation des vollständigen verteilten Rainbow-Teaming-Experiments
- Kein großer Agentenbenchmark mit externen Tools oder realen Nebenwirkungen
- Keine Behauptung allgemeiner Prompt-Injection-Robustheit aus 30 Fällen
- Keine unnötige Erweiterung des Datensatzes, bevor die bestehende Evaluation sauber analysiert ist

## Definition of Done

Das Projekt ist für die Abgabe ausreichend abgeschlossen, wenn:

- [x] der 30-Fälle-Benchmark mit Quellen und Anpassungen eingefroren ist,
- [x] die False Positives des Promptbreak Guards analysiert und nach Möglichkeit reduziert wurden,
- [ ] ein finaler vollständiger Vergleichslauf vorliegt,
- [x] Security, Utility, Latenz und Compute-Kosten nachvollziehbar berichtet werden,
- [x] Rainbow-Lite klar als kleine adaptive Zusatzanalyse eingeordnet wird,
- [ ] Pitch, Bericht, README und Ergebnisdateien dieselben finalen Zahlen verwenden,
- [x] alle automatisierten Tests erfolgreich laufen.
