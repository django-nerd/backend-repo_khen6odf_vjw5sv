import os
from typing import List, Optional, Literal, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Sjakie – AI SuperApp API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Sjakie Backend is live"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from Sjakie backend!"}


# ---------- Health: Hangover Mode ----------
class HangoverRequest(BaseModel):
    weight_kg: Optional[float] = Field(None, gt=30, lt=250)
    severity: int = Field(2, ge=1, le=5, description="1=mild, 5=severe")
    include_heart_rate: Optional[int] = Field(None, ge=40, le=220)


@app.post("/api/hangover")
def hangover_mode(req: HangoverRequest):
    # Base hydration target (ml): 35 ml/kg/day baseline + severity bump
    if req.weight_kg:
        base_ml = req.weight_kg * 35
    else:
        base_ml = 2000

    severity_bump = [0, 250, 500, 750, 1000][req.severity - 1]
    target_ml = int(base_ml + severity_bump)

    # Simple schedule (every ~60–90 minutes)
    schedule = [
        {"time": "Now", "action": "Drink 500ml water 💧"},
        {"time": "+60 min", "action": "Drink 300ml water + snack (banana/toast)"},
        {"time": "+120 min", "action": "Electrolytes or bouillon"},
        {"time": "+180 min", "action": "Drink 300ml water"},
    ]

    tips = [
        "Cafeïne kan je hartslag boosten – rustig aan met koffie.",
        "Magnesium 200–400mg kan spierspanning verlichten.",
        "Geen paracetamol combineren met veel alcohol in je bloed.",
        "Slaap en licht bewegen > intens sporten vandaag.",
    ]

    hr_flag = None
    if req.include_heart_rate:
        hr = req.include_heart_rate
        if hr > 110:
            hr_flag = "Je hartslag is hoog. Chill, hydrateer en overweeg rust. Bij duizeligheid of pijn op de borst: medische hulp."
        elif hr < 50:
            hr_flag = "Onverwacht lage hartslag? Als je je beroerd voelt: laat iemand even checken."

    return {
        "target_hydration_ml": target_ml,
        "schedule": schedule,
        "supplements": [
            {"name": "Elektrolyten", "note": "natrium/kalium aanvullen"},
            {"name": "Magnesium", "note": "200–400mg"},
            {"name": "Gemberthee", "note": "tegen misselijkheid"},
        ],
        "tips": tips,
        "flags": hr_flag,
        "voice": "Drink nu 500ml water 💧 – je got this."
    }


# ---------- Drugs Mode (harm reduction) ----------
HARM_DB: Dict[str, Dict[str, Any]] = {
    "alcohol": {
        "risks": ["uitdroging", "coördinatieverlies", "blackouts"],
        "avoid_mix": ["paracetamol in hoge dosis", "benzodiazepines"],
        "dosage": "Max ~10 eenheden/week; bij 1 avond: 2–4 rustig aan",
        "aftercare": ["water + elektrolyten", "slaap", "licht eten"],
        "red_flags": ["aanhoudend braken", "bewustzijnsverlies", "ernstige buikpijn"],
    },
    "mdma": {
        "risks": ["oververhitting", "hyponatriëmie", "serotoninesyndroom"],
        "avoid_mix": ["ssri/snri", "maoi", "cocaïne", "ghb"],
        "dosage": "Laag: 1–1.5 mg/kg (max 100mg), nooit bijdoseren <3u",
        "aftercare": ["cooldown", "water maar niet overhydreren", "vit C", "rust"],
        "red_flags": ["hoge temp + verwardheid", "aanhoudende hartkloppingen"],
    },
    "cocaine": {
        "risks": ["hartritmestoornissen", "angst/paniek", "neusschade"],
        "avoid_mix": ["alcohol (coca-ethyleen)", "mdma", "ketamine"],
        "dosage": "Vermijd binges; lange pauzes; niet delen (hygiëne)",
        "aftercare": ["hydratatie", "zoutspoeling neus", "rust"],
        "red_flags": ["druk op borst", "flauwvallen", "ernstige hoofdpijn"],
    },
    "cannabis": {
        "risks": ["angst/paranoia", "reactietijd omlaag", "misselijkheid (CHS)"] ,
        "avoid_mix": ["alcohol (versterkt)", "ghb"],
        "dosage": "Start low, go slow (edibles: 2.5–5mg THC)",
        "aftercare": ["water", "suiker bij duizeligheid", "rustig ademhalen"],
        "red_flags": ["hevige paniek > 1u", "aanhoudend braken"]
    },
}


@app.get("/api/drugs/info")
def drug_info(substance: str):
    key = substance.strip().lower()
    if key not in HARM_DB:
        raise HTTPException(status_code=404, detail="Onbekend middel")
    data = HARM_DB[key]
    return {
        "substance": key,
        "education": {
            "risks": data["risks"],
            "avoid_combinations": data["avoid_mix"],
            "dosage_guidance": data["dosage"],
            "aftercare": data["aftercare"],
            "emergency_signs": data["red_flags"],
        },
        "voice": "Educatief, niet promotioneel. Blijf veilig. 🫶"
    }


# ---------- Future Self (simple scoring) ----------
class FutureSelfInput(BaseModel):
    sleep_hours: float = Field(..., ge=0, le=14)
    steps_per_day: int = Field(..., ge=0, le=50000)
    alcohol_units_per_week: int = Field(..., ge=0, le=70)
    screen_time_hours: float = Field(..., ge=0, le=18)


@app.post("/api/future-self")
def future_self_score(payload: FutureSelfInput):
    # Simple weighted scoring (100 = great)
    score = 100

    # Sleep: target 7–9
    if payload.sleep_hours < 7:
        score -= int((7 - payload.sleep_hours) * 5)
    elif payload.sleep_hours > 9:
        score -= int((payload.sleep_hours - 9) * 3)

    # Steps: target 8k–12k
    if payload.steps_per_day < 8000:
        score -= int((8000 - payload.steps_per_day) / 400)
    elif payload.steps_per_day > 15000:
        score -= int((payload.steps_per_day - 15000) / 1000)

    # Alcohol
    score -= min(payload.alcohol_units_per_week * 2, 30)

    # Screen time (>6 starts to deduct)
    if payload.screen_time_hours > 6:
        score -= int((payload.screen_time_hours - 6) * 3)

    score = max(0, min(100, score))

    # Dimensions
    energy = max(0, min(100, 50 + (payload.sleep_hours - 7) * 8 - (payload.alcohol_units_per_week)))
    mobility = max(0, min(100, 50 + (payload.steps_per_day - 8000) / 120))
    mental = max(0, min(100, 60 - (payload.screen_time_hours - 3) * 6 + (payload.sleep_hours - 7) * 5))
    injury = max(0, min(100, 70 - (payload.steps_per_day - 10000) / 200 - payload.alcohol_units_per_week))

    summary = "Bro… Future You wordt een wandelende café latte als je zo doorgaat. ☕👀" if score < 60 else "Lekker bezig. Kleine tweaks en je future self glimt. ✨"

    return {
        "score": score,
        "dimensions": {
            "energy": int(energy),
            "mobility": int(mobility),
            "mental_balance": int(mental),
            "injury_risk": int(injury)
        },
        "summary": summary
    }


# ---------- Triage Assistant (rule-based v1) ----------
class TriageTurn(BaseModel):
    message: str

class TriageState(BaseModel):
    chief_complaint: Optional[str] = None
    answers: List[Dict[str, str]] = []

class TriageStepResponse(BaseModel):
    question: Optional[str] = None
    outcome: Optional[str] = None
    level: Optional[Literal['emergency','urgent','routine']] = None
    tips: Optional[List[str]] = None
    tone: str


@app.post("/api/triage/start", response_model=TriageStepResponse)
def triage_start(turn: TriageTurn):
    text = turn.message.lower()
    # Simple parsing for abdominal pain case
    if "buik" in text or "buikpijn" in text:
        return TriageStepResponse(
            question="Oef, vervelend! Wanneer begon het? 🤔 (uren/dagen)",
            tone="Jong, vriendelijk, speels. Korte zinnen."
        )
    return TriageStepResponse(
        question="Vertel kort wat er speelt. Waar doet het pijn of wat valt op?",
        tone="Empathisch en duidelijk."
    )


class TriageNextInput(BaseModel):
    context: str = Field(..., description="free text context or previous answer")
    complaint: Optional[str] = None
    last_answer: Optional[str] = None


@app.post("/api/triage/next", response_model=TriageStepResponse)
def triage_next(data: TriageNextInput):
    ctx = f"{data.complaint or ''} {data.context or ''} {data.last_answer or ''}".lower()

    # Abdominal pain mini-tree
    if any(k in ctx for k in ["buik", "buikpijn", "maag", "onderbuik"]):
        if any(k in ctx for k in ["uren", "gister", "gisteren", "vandaag", "net"]):
            return TriageStepResponse(question="Is het stekend of dof?", tone="Kort en duidelijk.")
        if any(k in ctx for k in ["stekend"]):
            return TriageStepResponse(question="Heb je koorts of moet je braken? 🤒", tone="Empathisch.")
        if any(k in ctx for k in ["koorts", "braak", "braken", "overgeven"]):
            return TriageStepResponse(
                outcome="Dit klinkt serieus, maat. Kan appendicitis zijn. Bel je huisarts vandaag nog.",
                level="urgent",
                tips=["Niet eten/drinken als je misselijk bent", "Regel vervoer als lopen pijn doet"],
                tone="Eerlijk en direct."
            )
        # default follow-up
        return TriageStepResponse(question="Is de pijn constant of komt het in golven?", tone="Neutral")

    # Fallback generic path
    if any(k in ctx for k in ["flauwvallen", "borstpijn", "kortademig"]):
        return TriageStepResponse(
            outcome="Klinkt als spoed. Bel 112 of ga naar de SEH.", level="emergency", tips=["Blijf niet alleen"], tone="Urgent"
        )

    return TriageStepResponse(question="Oké. Waar zit het precies en hoe lang al?", tone="Vriendelijk")


# ---------- Utilities ----------
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception:
        response["database"] = "❌ Database module not found"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
