 LLM-Powered Email Extraction System

Backend / AI Engineer Assessment – Task Harmony

Project Overview

This project implements an LLM-based information extraction pipeline to automatically extract structured shipment details from freight forwarding pricing enquiry emails. The system processes unstructured email content, applies business rules, validates outputs, and measures accuracy against a provided ground truth dataset.

The goal is not only high accuracy on sample emails, but also robust generalization to unseen emails using a clean, scalable design.

 High-Level Approach

The overall flow of the system is:

Emails (input JSON)
→ Business rules + Prompted LLM extraction
→ Post-processing & validation
→ Structured output (output.json)
→ Accuracy evaluation against ground_truth.json

Key design principle:
 Use the LLM for semantic understanding, and deterministic code for business logic.

Project Structure
task-harmony-email-extraction/
├── README.md                 # Project explanation & design decisions
├── requirements.txt          # Python dependencies
├── schemas.py                # Pydantic output schema
├── prompts.py                # Prompt versions & rules
├── extract.py                # Main extraction pipeline
├── evaluate.py               # Accuracy calculation
├── output.json               # Generated predictions (50 emails)
├── emails_input.json         # Input emails
├── ground_truth.json         # Expected outputs
├── port_codes_reference.json # UN/LOCODE mapping
└── .env.example              # API key template

 Setup Instructions
pip install -r requirements.txt
python extract.py      # Generates output.json
python evaluate.py     # Prints accuracy metrics


Environment variable setup:

GROQ_API_KEY=your_api_key_here

 Extraction Logic Explained
1. Input Processing

Each email contains:

id

subject

body

The email body always takes precedence over the subject, as it contains richer context.

2. LLM-Based Semantic Extraction

The Groq LLM (llama-3.3-70b-versatile, temperature = 0) is used only to extract:

Origin port name

Destination port name

Incoterm

Cargo weight (kg)

Cargo volume (CBM)

Dangerous goods flag

The model is instructed to return strict JSON only, ensuring deterministic parsing.

3. Business Rules (Post-Processing)

After LLM extraction, deterministic rules are applied:

Product Line

Destination in India → pl_sea_import_lcl

Origin in India → pl_sea_export_lcl

Port Resolution

Extracted port names are matched against port_codes_reference.json

Canonical UN/LOCODE and port name are assigned

If not found → null

Incoterm Handling

Missing or ambiguous → default to FOB

Dangerous Goods Detection

Keywords: DG, IMO, IMDG, UN, Class X

Negations like non-hazardous override positives

Null Safety

Missing values → null

Script never crashes on malformed input

4. Validation with Pydantic

All outputs are validated using a Pydantic model, ensuring:

Correct data types

Optional numeric fields

Schema consistency across all emails

 Accuracy Evaluation

The evaluate.py script compares:

output.json

ground_truth.json

Evaluated fields (9 per email):

product_line

origin_port_code

origin_port_name

destination_port_code

destination_port_name

incoterm

cargo_weight_kg

cargo_cbm

is_dangerous

Overall Accuracy Formula:

(total correct fields) / (total fields)


This provides a transparent, measurable metric after every iteration.

 Prompt Evolution (Iteration Log)
Prompt v1 – Basic Extraction

Accuracy: ~60–65%

Issues:

Inconsistent port names

Missing incoterms

Weak DG detection

Prompt v2 – Rule-Guided Extraction

Accuracy: ~75–80%

Improvements:

Explicit incoterm defaults

Clear DG detection rules

Remaining issues:

Ambiguous port references

Prompt v3 – Final Version

Accuracy: ~80%+

Enhancements:

Strict JSON-only output

Business rules embedded in prompt

Clear precedence rules (Body > Subject)

This iterative process mirrors real-world LLM system development.

 Error Handling Strategy

Rate limits / timeouts

Retry with backoff

Graceful termination if token limit reached

Failed extraction

Email is still included in output with null fields

Ensures no data loss

Malformed inputs

Defensive parsing prevents crashes

This design ensures production-safe behavior.

 Edge Cases Handled

Subject vs Body conflicts

Multiple ports mentioned

Multiple shipments → first shipment only

Ambiguous incoterms

Non-hazardous negations

Missing or unknown ports

 System Design (High Level)

For 10,000 emails/day under $500/month:

Queue-based ingestion

Batch LLM calls

Caching repeated patterns

Monitoring accuracy drift

Monitoring accuracy drops:

Track field-level accuracy trends

Sample manual audits

Prompt regression testing

Multilingual emails:

Language detection

Same extraction pipeline

Separate accuracy benchmarks per language
