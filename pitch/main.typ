// Promptbreak pitch deck.
#import "@preview/metropolyst:0.1.0": *

#let navy = rgb("#23373B")
#let panel = rgb("#F3F5F5")
#let ink = rgb("#FAFAFA")
#let muted = rgb("#596568")
#let acid = rgb("#EB811B")
#let cyan = rgb("#EB811B")
#let violet = rgb("#7B878A")
#let orange = rgb("#EB811B")
#let red = rgb("#C86424")

#show: metropolyst-theme.with(
  config-info(
    title: [Promptbreak],
    subtitle: [An educational prompt-injection game and local evaluation laboratory],
    author: [Amireza, Zakey, Elias],
    date: datetime.today(),
    institution: [NLP in Industry · Heidelberg University],
  ),
)

#let footer(body) = {
  v(1fr)
  text(size: 7pt, fill: rgb("#66798F"), body)
}

#let pill(body, color: acid) = box(
  inset: (x: 10pt, y: 4pt),
  radius: 99pt,
  fill: color,
  text(size: 9pt, weight: "bold", fill: navy, body),
)

#let card(title, body, accent: cyan, height: auto) = block(
  width: 100%,
  height: height,
  inset: 12pt,
  radius: 8pt,
  fill: panel,
  stroke: (left: 3pt + accent),
)[
  #text(size: 14pt, weight: "bold", fill: navy)[#title]
  #v(5pt)
  #text(size: 11pt, fill: muted)[#body]
]

#let dark-card(title, body, accent: acid) = block(
  width: 100%,
  inset: 12pt,
  radius: 8pt,
  fill: panel,
  stroke: 1pt + rgb("#D3D8D7"),
)[
  #text(size: 11pt, weight: "bold", fill: navy)[#title]
  #v(5pt)
  #text(size: 9.5pt, fill: muted)[#body]
]

#let metric(value, label, color: acid) = block(
  width: 100%,
  inset: 10pt,
  radius: 8pt,
  fill: panel,
  stroke: 1pt + rgb("#D3D8D7"),
  align(center)[
    #text(size: 27pt, weight: "bold", fill: color)[#value]
    #linebreak()
    #text(size: 8.5pt, weight: "bold", fill: muted)[#label]
  ],
)

#title-slide()

== Promptbreak is an educational security game

#v(0.25em)

#align(center)[
  #text(size: 20pt, weight: "bold", fill: navy)[
    Learn prompt injection by attacking a safe, local simulation.
  ]
]

#v(0.55em)

#grid(
  columns: (1fr, 1fr),
  gutter: 16pt,
  card(
    [#pill[PLAY] #h(6pt) *Three escalating levels*],
    [
      Craft direct, contextual, and multi-turn attacks against fictional
      assistants that hold synthetic secrets.

      Each level behaves like a small security escape room.
    ],
    accent: acid,
    height: 155pt,
  ),
  card(
    [#pill(color: violet)[OBSERVE] #h(6pt) *Defenses become visible*],
    [
      Toggle defense layers, inspect the execution trace, and see whether a
      secret was blocked or reached the client.

      Retry immediately and compare strategies.
    ],
    accent: violet,
    height: 155pt,
  ),
)

#v(0.6em)

#align(center)[
  #pill[CHOOSE A LEVEL] #h(5pt) → #h(5pt)
  #pill[ATTACK] #h(5pt) → #h(5pt)
  #pill[INSPECT] #h(5pt) → #h(5pt)
  #pill[RETRY]
]

#v(0.6em)

#block(
  width: 100%,
  inset: 11pt,
  radius: 8pt,
  fill: panel,
  stroke: 1pt + rgb("#D3D8D7"),
)[
  #align(center)[
    #text(size: 14pt, weight: "bold", fill: navy)[
      The playable artifact teaches the problem; the study evaluates its defenses.
    ]
  ]
]

== Three puzzles, three application bugs

#v(0.4em)

#align(center)[
  #text(size: 22pt, weight: "bold", fill: navy)[
    Each level hides a synthetic secret behind a flawed legacy workflow.
  ]
]

#v(0.65em)

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 12pt,
  card(
    [#pill[LEVEL 1] #h(5pt) *Legacy QA*],
    [
      Claim an internal test and request structured JSON.

      *Goal:* extract the receptionist password.
    ],
    accent: cyan,
    height: 150pt,
  ),
  card(
    [#pill(color: violet)[LEVEL 2] #h(5pt) *Unsafe export*],
    [
      Turn a migration request into an SQL token leak.

      *Goal:* extract the archive token.
    ],
    accent: violet,
    height: 150pt,
  ),
  card(
    [#pill(color: red)[LEVEL 3] #h(5pt) *Recovery chain*],
    [
      Establish incident state, enable maintenance, then export XML or Base64.

      *Goal:* extract the vault key.
    ],
    accent: red,
    height: 150pt,
  ),
)

#v(0.65em)

#block(
  width: 100%,
  inset: 12pt,
  radius: 8pt,
  fill: panel,
  stroke: 1pt + rgb("#D3D8D7"),
)[
  #align(center)[
    #text(size: 16pt, weight: "bold", fill: navy)[
      The vulnerable contracts live in application code, so the puzzles remain
      reproducible across local model updates.
    ]
  ]
]

== How the evaluation plays the game

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 12pt,
  metric([15], [PUZZLE-SOLVING ATTEMPTS], color: red),
  metric([15], [BENIGN CONTROLS], color: violet),
  metric([5], [DEFENSE CONFIGURATIONS], color: acid),
)

#v(0.55em)

#align(center)[
  #pill[FIXED CASE] #h(5pt) → #h(5pt)
  #pill(color: violet)[DEFENSE] #h(5pt) → #h(5pt)
  #pill[GAME LEVEL] #h(5pt) → #h(5pt)
  #pill(color: violet)[CLIENT RESPONSE] #h(5pt) → #h(5pt)
  #pill[SECRET JUDGE]
]

#v(0.55em)

#block(
  width: 100%,
  inset: 12pt,
  radius: 8pt,
  fill: panel,
  stroke: 1pt + rgb("#D3D8D7"),
)[
  #align(center)[
    #text(size: 14pt, weight: "bold", fill: navy)[
      Attack success: a recoverable secret reaches the client. #h(16pt)
      Benign failure: a harmless control is blocked.
    ]
    #linebreak()
    #text(size: 10pt, fill: muted)[
      Static evaluation replays known solutions; Rainbow-Lite mutates them into new attempts.
    ]
  ]
]

== Research question

#v(0.7em)

#block(
  width: 100%,
  inset: 18pt,
  radius: 10pt,
  fill: panel,
  stroke: 1.5pt + acid,
)[
  #text(size: 23pt, weight: "bold", fill: navy)[
    How do prompt-injection guardrails, general safety models, and layered
    defenses differ in *security, utility, latency, and compute cost*?
  ]
]

#v(0.8em)

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 10pt,
  dark-card([PROMPT ONLY], [Target model + system prompt. No separate guard.], accent: red),
  dark-card([PROMPTBREAK GUARD], [Heuristics + task-specific Gemma classifier.], accent: cyan),
  dark-card([LLAMA GUARD 3 · 1B], [Out-of-the-box content-safety classifier.], accent: violet),

  dark-card([SHIELDGEMMA · 2B], [Out-of-the-box policy-based safety classifier.], accent: orange),
  dark-card([FULL PIPELINE], [Input guard + context + direct and encoding filters.], accent: acid),
  dark-card([CONTROLLED SETUP], [Same target model, prompts, secrets, and hardware.], accent: muted),
)

== Solve the puzzles without breaking normal play

#image("assets/dataset-composition.svg", width: 100%)

#footer[
  Attack cases exercise Promptbreak's actual vulnerable contracts. Benign
  contrast cases are inspired by XSTest and NotInject/InjecGuard.
]

== Two questions for every move

#grid(
  columns: (1fr, 1fr),
  gutter: 16pt,
)[
  #v(0.5em)
  #card(
    [#pill(color: cyan)[GUARD] #h(6pt) *Did a layer block the move?*],
    [
      #v(5pt)
      - Precision
      - Recall
      - Macro-F1
      - False positive rate
      - Breakdown by attack family
    ],
    accent: cyan,
    height: 168pt,
  )
][
  #v(0.5em)
  #card(
    [#pill(color: orange)[GAME] #h(6pt) *Was the puzzle actually solved?*],
    [
      #v(5pt)
      - Attack success rate
      - Benign utility
      - Direct vs. encoded leakage
      - Single-turn vs. multi-turn
      - Client-visible response
      - Deterministic secret judge
    ],
    accent: orange,
    height: 168pt,
  )
]

== Measure the cost of protection

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 8pt,
  metric([p50 / p95], [WARM LATENCY], color: violet),
  metric([calls], [MODEL INVOCATIONS], color: cyan),
  metric([tokens], [INPUT + OUTPUT], color: orange),
  metric([€0], [LOCAL API COST], color: acid),
)

#v(1em)

#align(center)[
  #block(
    width: 76%,
    inset: 13pt,
    radius: 8pt,
    fill: panel,
    stroke: 1pt + rgb("#D3D8D7"),
  )[
    #align(center)[
      #text(size: 17pt, weight: "bold", fill: navy)[
        Local API cost is zero. *Computational cost is not.*
      ]
      #linebreak()
      #text(size: 10pt, fill: muted)[Same hardware · same target model · cold and warm runs reported separately]
    ]
  ]
]

== Initial result: protection broke benign play

#grid(
  columns: (1.15fr, 1fr),
  gutter: 16pt,
)[
  #table(
    columns: (1.7fr, .7fr, .7fr),
    inset: 6pt,
    stroke: (x, y) => if y == 0 { (bottom: 1pt + navy) } else { (bottom: .4pt + rgb("#CCD5DF")) },
    fill: (x, y) => if y == 0 { rgb("#E7EDF2") } else if calc.rem(y, 2) == 0 { rgb("#F7F9FA") },
    table.header(
      [#text(size: 9pt, weight: "bold")[CONFIGURATION]],
      [#text(size: 9pt, weight: "bold")[ASR ↓]],
      [#text(size: 9pt, weight: "bold")[FPR ↓]],
    ),
    [Prompt only], [100.0%], [0.0%],
    [Promptbreak Guard], [13.3%], [93.3%],
    [Llama Guard 3], [66.7%], [0.0%],
    [ShieldGemma], [100.0%], [0.0%],
    [Full Pipeline], [0.0%], [93.3%],
  )
][
  #dark-card(
    [INITIAL FINDING],
    [
      #text(fill: red, weight: "bold")[The Full Pipeline solved security by rejecting normal play.]
      #v(5pt)

      It stopped all 15 attacks, but blocked 14 of 15 benign controls.
    ],
    accent: acid,
  )

  #v(8pt)

  #dark-card(
    [TARGETED REPAIR],
    [
      Narrow multi-signal rules reduced FPR to *0%* while ASR stayed unchanged.

      One repetition on the same development set; final repeated validation is still required.
    ],
    accent: violet,
  )
]

#footer[
  Initial table: 30 cases × 3 repetitions. Targeted repair: 30 cases × 1
  repetition for Promptbreak Guard and Full Pipeline.
]

== Rainbow-Lite searches for new solutions

#align(center)[#image("assets/rainbow-archive.svg", width: 60%)]

#align(center)[
  #pill(color: cyan)[SELECT] #h(6pt) →
  #h(6pt) #pill(color: violet)[MUTATE] #h(6pt) →
  #h(6pt) #pill(color: orange)[EXECUTE] #h(6pt) →
  #h(6pt) #pill(color: acid)[UPDATE]
]

#v(0.35em)

#align(center)[
  #text(size: 8pt, fill: muted)[
    Seminar-scale adaptation of Samvelyan et al. (2024); distributed MAP-Elites is out of scope.
  ]
]

== Two-week scope: build, evaluate, explain

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 12pt,
  card(
    [#pill[ARTIFACT] #h(5pt) *Build the game*],
    [
      Three playable levels \
      Synthetic secrets \
      Visible defense traces
    ],
    accent: cyan,
    height: 175pt,
  ),
  card(
    [#pill(color: violet)[EVALUATION] #h(5pt) *Replay the puzzles*],
    [
      15 attacks + 15 controls \
      Five defense setups \
      Static + adaptive attempts
    ],
    accent: violet,
    height: 175pt,
  ),
  card(
    [#pill(color: orange)[OUTPUT] #h(5pt) *Tell the trade-off*],
    [
      ASR vs. FPR \
      Security vs. latency \
      Reproducible JSON + report
    ],
    accent: orange,
    height: 175pt,
  ),
)

#v(0.7em)

#block(
  width: 100%,
  inset: 16pt,
  radius: 9pt,
  fill: panel,
  stroke: 1pt + rgb("#D3D8D7"),
)[
  #align(center)[
    #text(size: 21pt, weight: "bold", fill: navy)[
      Promptbreak turns three playable security puzzles into a traceable
      benchmark of defense trade-offs.
    ]
    #linebreak()
    #text(size: 12pt, fill: muted)[
      The question is not only what gets blocked, but what still leaks and what
      legitimate play remains possible.
    ]
  ]
]


== Benchmarks and references

#text(size: 10.5pt)[
  #text(weight: "bold", fill: navy)[Benchmark sources]

  - Liu et al. (2024), *Open Prompt Injection*: attack taxonomy and benchmark
    framework. #link("https://github.com/liu00222/Open-Prompt-Injection")[Benchmark repository]
    · #link("https://www.usenix.org/conference/usenixsecurity24/presentation/liu-yupei")[USENIX paper]

  - Li et al. (2025), *NotInject / InjecGuard*: benign prompts containing
    injection-associated trigger words.
    #link("https://huggingface.co/datasets/leolee99/NotInject")[NotInject dataset]
    · #link("https://github.com/safolab-wisc/injecguard")[Code and paper]

  - Röttger et al. (2024), *XSTest*: safe/unsafe contrast-set methodology.
    #link("https://github.com/paul-rottger/xstest")[XSTest dataset]
    · #link("https://aclanthology.org/2024.naacl-long.301/")[NAACL paper]

  #v(0.35em)
  #text(weight: "bold", fill: navy)[Adaptive evaluation and guard models]

  - Samvelyan et al. (2024), *Rainbow Teaming*.
    #link("https://arxiv.org/abs/2402.16822")[Paper]

  - Official documentation:
    #link("https://ollama.com/library/llama-guard3")[Llama Guard 3] ·
    #link("https://ai.google.dev/gemma/docs/shieldgemma/model_card")[ShieldGemma].
]
