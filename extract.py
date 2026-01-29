import json, time, os
from groq import Groq
from dotenv import load_dotenv
from schemas import EmailExtraction
from prompts import EXTRACTION_PROMPT
from tqdm import tqdm

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- LOAD INPUTS ----------------
with open("emails_input.json", "r", encoding="utf-8") as f:
    emails = json.load(f)

with open("port_codes_reference.json", "r", encoding="utf-8") as f:
    ports = json.load(f)

# ---------------- PORT LOOKUP ----------------
PORT_LOOKUP = {}
for p in ports:
    PORT_LOOKUP.setdefault(p["name"].lower(), []).append(
        (p["code"], p["name"])
    )

def resolve_port(name):
    if not name:
        return None, None

    name = name.lower().strip()

    # exact match first
    if name in PORT_LOOKUP:
        return PORT_LOOKUP[name][0]

    # fuzzy fallback
    for k, v in PORT_LOOKUP.items():
        if k in name or name in k:
            return v[0]

    return None, None

# ---------------- INCOTERM NORMALIZATION ----------------
VALID_INCOTERMS = {
    "FOB","CIF","CFR","EXW","DDP","DAP","FCA","CPT","CIP","DPU"
}

def normalize_incoterm(val):
    if not val:
        return "FOB"
    v = val.strip().upper()
    return v if v in VALID_INCOTERMS else "FOB"

# ---------------- LLM CALL ----------------
def call_llm(subject, body):
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Subject: {subject}\nBody: {body}"}
        ]
    )

    raw = res.choices[0].message.content.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    return json.loads(raw[start:end])

# ---------------- MAIN LOOP ----------------
results = []

for email in tqdm(emails):
    try:
        data = call_llm(email["subject"], email["body"])

        origin_code, origin_name = resolve_port(data.get("origin_port_name"))
        dest_code, dest_name = resolve_port(data.get("destination_port_name"))

        # 🔥 STRONG PRODUCT LINE LOGIC
        product_line = None
        if origin_code and origin_code.startswith("IN") and dest_code:
            product_line = "pl_sea_export_lcl"
        elif dest_code and dest_code.startswith("IN") and origin_code:
            product_line = "pl_sea_import_lcl"

        # 🔥 DANGEROUS GOODS OVERRIDE
        text = f"{email['subject']} {email['body']}".lower()
        if any(x in text for x in ["non-dg", "non hazardous", "not dangerous"]):
            is_dg = False
        elif any(x in text for x in ["dg", "imo", "imdg", "un ", "class "]):
            is_dg = True
        else:
            is_dg = data.get("is_dangerous", False)

        record = EmailExtraction(
            id=email["id"],
            product_line=product_line,
            origin_port_code=origin_code,
            origin_port_name=origin_name,
            destination_port_code=dest_code,
            destination_port_name=dest_name,
            incoterm=normalize_incoterm(data.get("incoterm")),
            cargo_weight_kg=data.get("cargo_weight_kg"),
            cargo_cbm=data.get("cargo_cbm"),
            is_dangerous=is_dg
        )

        results.append(record.model_dump())

    except Exception as e:
        msg = str(e)
        print("🚨 LLM ERROR:", msg)

        if "429" in msg or "rate limit" in msg.lower():
            print("🚨 Token limit reached. Stop run.")
            break

        results.append({
            "id": email["id"],
            "product_line": None,
            "origin_port_code": None,
            "origin_port_name": None,
            "destination_port_code": None,
            "destination_port_name": None,
            "incoterm": "FOB",
            "cargo_weight_kg": None,
            "cargo_cbm": None,
            "is_dangerous": False
        })

# ---------------- SAVE OUTPUT ----------------
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"✅ output.json generated ({len(results)} records)")
