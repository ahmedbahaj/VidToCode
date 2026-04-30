# VidToCode

VidToCode is a research project that converts the **spoken narration** of programming tutorial videos into **executable source code**, without the need to rely on video frames, screen capture, or OCR.

Most prior work extracts code visually (from screenshots or screencasts). VidToCode takes a different angle: the instructor's voice already contains everything needed to understand and reconstruct the code. The system listens to what is being explained and generates runnable code from that narration alone.

**Team:** Ahmed Bahaj, Abdullah Misar, Yazeed Bafaqih, Albaraa Alnahari  
**Supervisors:** Dr. Mohammed Alahmadi  
**Institution:** University of Jeddah — Software Construction, 2026

--

## Project Phases

| Phase | Title | Status |
|---|---|---|
| 1 | Literature Review | Completed |
| 2 | Dataset Collection & Project Plan | Completed |
| 3 | Full Implementation & Evaluation | Ongoing |

---

## Dataset

The dataset consists of **36 manually curated YouTube programming tutorial videos** across 4 languages, stratified by length and topic.

### Languages
- Python
- Java
- C++
- JavaScript

### Stratification

| Dimension | Categories |
|---|---|
| Length | Short (5–8 min) · Medium (8–15 min) · Long (15–20 min) |
| Topic | Algorithms · Core Language Tasks · Small Applications |

Each language contains **3 videos per length tier** (3 short + 3 medium + 3 long = 9 per language × 4 languages = 36 total).

### Per-video artifacts

Each video entry is a folder containing:

| File | Description |
|---|---|
| `transcript.txt` | Timestamped spoken narration, one line per caption segment (`[seconds] text`) |
| `<source>.<ext>` | Final runnable source code as written in the tutorial |
| `output.txt` | Expected program output when the code is executed |
| `metadata.json` | Video metadata: title, video ID, channel, upload date, duration, view count, description |
---

## Directory Map

```
VidToCode/
│
├── data/                                  # Raw dataset (Phase 2 — complete)
│   ├── extract_youtube_data.py            # YouTube transcript + metadata extractor
│   ├── python/
│   │   ├── short/  medium/  long/
│   │   │   └── <short|medium|long>_N/
│   │   │       ├── transcript.txt
│   │   │       ├── main.py
│   │   │       ├── output.txt
│   │   │       └── metadata.json
│   ├── java/                              # same structure, Code.java
│   ├── cpp/                               # same structure, main.cpp
│   └── javascript/                        # same structure, index.js / script.js
│
├── preprocessing/                         # Phase 3 — transcript → structured input
│   ├── clean.py                           # Remove fillers, normalize, segment clips
│   ├── annotate.py                        # Pedagogical tagging (intent labeling)
│   └── build_dataset.py                   # Produce final training/eval splits
│
├── annotations/                           # Phase 3 — processed dataset outputs
│   ├── <lang>/<length>/<id>.json          # Structured annotation per video
│   └── splits/
│       ├── train.json
│       ├── val.json
│       └── test.json
│
├── approaches/                            # Phase 3 — one folder per approach
│   ├── approach_1_zero_shot/              # Raw transcript → LLM → code
│   │   └── run.py
│   ├── approach_2_structured/             # Structured transcript → LLM → code
│   │   └── run.py
│   └── approach_3_finetune/               # Structured → docstring → fine-tuned CodeGen2
│       ├── train.py
│       └── run.py
│
├── eval/                                  # Phase 3 — evaluation methodology & scripts
│   ├── README.md                          # CS and CodeBLEU definitions, split, comparison table
│   ├── evaluate.py                        # Evaluation runner (CS + CodeBLEU)
│   └── results/                           # Output logs and score tables
│
├── notebooks/                             # Exploratory analysis & visualizations
│
├── presentations/
│   ├── SW Construction Phase 1.pdf        # Literature review
│   └── SW Construction Phase 2.pdf        # Project plan
│
└── README.md
```

---

## Methodology

Three approaches are evaluated against each other, each isolating a single variable:

| # | Input | Model | What it answers |
|---|---|---|---|
| 1 | Raw transcript | LLM (zero-shot) | Can an LLM go directly from noisy narration to code? |
| 2 | Structured / annotated transcript | LLM (zero-shot) | Does the Phase 2 preprocessing actually help? |
| 3 | Structured transcript → LLM-generated docstring | Fine-tuned CodeGen2 | Does the teacher-student setup improve over zero-shot? |

- **1 vs 2** isolates the value of the annotation and cleaning pipeline
- **2 vs 3** isolates whether fine-tuning CodeGen2 adds anything on top of zero-shot
- Approach 3 requires the train/test split; approaches 1 and 2 are evaluated on all 36 samples

---

## Annotation Format (Phase 3 target)

Each raw transcript segment will be transformed into a structured JSON record:

```json
{
  "narration": "add a for loop to iterate over the list",
  "intent": "implementation",
  "code_snippet": "for item in my_list:",
  "line_range": [12, 12]
}
```

**Intent labels:** `implementation` · `explanation` · `debugging` · `refactoring`
