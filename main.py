import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from database import db, create_document, get_documents

app = FastAPI(title="SignifyLearn API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Models (request/response) ---------
class GestureOut(BaseModel):
    name: str
    slug: str
    category: str
    difficulty: str
    thumbnail: Optional[str] = None

class GestureDetail(GestureOut):
    video_url: Optional[str] = None
    steps: List[str] = []
    examples: List[str] = []
    tags: List[str] = []

class ModuleOut(BaseModel):
    title: str
    slug: str
    summary: Optional[str] = None
    cover: Optional[str] = None
    difficulty: str = "Pemula"

class ModuleDetail(ModuleOut):
    lessons: List[str] = []

class QuizQuestion(BaseModel):
    module_slug: str
    prompt: str
    media: Optional[str] = None
    options: List[str]
    answer_index: int

class FavoriteIn(BaseModel):
    user_email: EmailStr
    gesture_slug: str

class UserProfile(BaseModel):
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    points: int = 0
    level: int = 1
    streak: int = 0
    badges: List[str] = []

class ProgressIn(BaseModel):
    user_email: EmailStr
    module_slug: str
    completed_lessons: List[int] = []

# --------- Utilities ---------

def ensure_seed_data():
    if db is None:
        return
    if "gesture" not in db.list_collection_names() or db["gesture"].count_documents({}) == 0:
        gestures = [
            {
                "name": "A",
                "slug": "a",
                "category": "A-Z",
                "difficulty": "Pemula",
                "thumbnail": "/gestures/a.png",
                "video_url": "https://videos.example.com/a.mp4",
                "steps": ["Angkat tangan kanan", "Bentuk huruf A"],
                "examples": ["Nama saya"],
                "tags": ["alphabet", "basic"],
            },
            {
                "name": "B",
                "slug": "b",
                "category": "A-Z",
                "difficulty": "Pemula",
                "thumbnail": "/gestures/b.png",
                "video_url": "https://videos.example.com/b.mp4",
                "steps": ["Angkat tangan", "Bentuk huruf B"],
                "examples": ["Belajar"],
                "tags": ["alphabet", "basic"],
            },
            {
                "name": "Terima Kasih",
                "slug": "terima-kasih",
                "category": "Kata Dasar",
                "difficulty": "Pemula",
                "thumbnail": "/gestures/terima-kasih.png",
                "video_url": "https://videos.example.com/thanks.mp4",
                "steps": ["Sentuh dagu", "Gerakkan tangan menjauh"],
                "examples": ["Terima kasih atas bantuanmu"],
                "tags": ["basic", "courtesy"],
            },
        ]
        db["gesture"].insert_many(gestures)
    if "module" not in db.list_collection_names() or db["module"].count_documents({}) == 0:
        modules = [
            {
                "title": "Dasar-Dasar Bahasa Isyarat",
                "slug": "dasar-dasar",
                "summary": "Mulai dari alfabet, angka, dan salam",
                "cover": "/covers/basic.png",
                "lessons": ["Alfabet", "Angka", "Salam"],
                "difficulty": "Pemula",
            },
            {
                "title": "Ekspresi Emosi",
                "slug": "ekspresi-emosi",
                "summary": "Bahasa isyarat untuk emosi umum",
                "cover": "/covers/emotion.png",
                "lessons": ["Senang", "Sedih", "Marah"],
                "difficulty": "Menengah",
            },
        ]
        db["module"].insert_many(modules)
    if "quizquestion" not in db.list_collection_names() or db["quizquestion"].count_documents({}) == 0:
        quizzes = [
            {
                "module_slug": "dasar-dasar",
                "prompt": "Gestur mana yang berarti 'Terima Kasih'?",
                "media": None,
                "options": ["Sentuh dagu lalu jauhkan tangan", "Kepal tangan", "Telapak ke atas"],
                "answer_index": 0,
            }
        ]
        db["quizquestion"].insert_many(quizzes)

ensure_seed_data()

# --------- Health/Test ---------
@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"message": "SignifyLearn API running"}

@app.api_route("/test", methods=["GET", "HEAD"])
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# --------- Gestures ---------
@app.get("/api/gestures", response_model=List[GestureOut])
def list_gestures(q: Optional[str] = Query(None), category: Optional[str] = None, page: int = 1, page_size: int = 20):
    if db is None:
        return []
    filters = {}
    if q:
        filters["name"] = {"$regex": q, "$options": "i"}
    if category:
        filters["category"] = category
    cursor = db["gesture"].find(filters).skip((page - 1) * page_size).limit(page_size)
    return [
        {
            "name": g.get("name"),
            "slug": g.get("slug"),
            "category": g.get("category"),
            "difficulty": g.get("difficulty", "Pemula"),
            "thumbnail": g.get("thumbnail"),
        }
        for g in cursor
    ]

@app.get("/api/gestures/{slug}", response_model=GestureDetail)
def get_gesture(slug: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    doc = db["gesture"].find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Gesture not found")
    return {
        "name": doc.get("name"),
        "slug": doc.get("slug"),
        "category": doc.get("category"),
        "difficulty": doc.get("difficulty", "Pemula"),
        "thumbnail": doc.get("thumbnail"),
        "video_url": doc.get("video_url"),
        "steps": doc.get("steps", []),
        "examples": doc.get("examples", []),
        "tags": doc.get("tags", []),
    }

# --------- Modules ---------
@app.get("/api/modules", response_model=List[ModuleOut])
def list_modules():
    if db is None:
        return []
    cursor = db["module"].find({})
    return [
        {
            "title": m.get("title"),
            "slug": m.get("slug"),
            "summary": m.get("summary"),
            "cover": m.get("cover"),
            "difficulty": m.get("difficulty", "Pemula"),
        }
        for m in cursor
    ]

@app.get("/api/modules/{slug}", response_model=ModuleDetail)
def get_module(slug: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    m = db["module"].find_one({"slug": slug})
    if not m:
        raise HTTPException(status_code=404, detail="Module not found")
    return {
        "title": m.get("title"),
        "slug": m.get("slug"),
        "summary": m.get("summary"),
        "cover": m.get("cover"),
        "lessons": m.get("lessons", []),
        "difficulty": m.get("difficulty", "Pemula"),
    }

# --------- Quizzes ---------
@app.get("/api/quizzes/{module_slug}", response_model=List[QuizQuestion])
def get_quiz(module_slug: str):
    if db is None:
        return []
    cursor = db["quizquestion"].find({"module_slug": module_slug})
    return [
        {
            "module_slug": q.get("module_slug"),
            "prompt": q.get("prompt"),
            "media": q.get("media"),
            "options": q.get("options", []),
            "answer_index": q.get("answer_index", 0),
        }
        for q in cursor
    ]

# --------- Favorites ---------
@app.get("/api/favorites")
def list_favorites(user_email: EmailStr):
    if db is None:
        return []
    favs = db["favorite"].find({"user_email": user_email})
    return [{"user_email": f.get("user_email"), "gesture_slug": f.get("gesture_slug") } for f in favs]

@app.post("/api/favorites")
def add_favorite(payload: FavoriteIn):
    if db is None:
        return {"ok": False}
    existing = db["favorite"].find_one({"user_email": payload.user_email, "gesture_slug": payload.gesture_slug})
    if existing:
        return {"ok": True}
    create_document("favorite", payload.model_dump())
    return {"ok": True}

# --------- Profile ---------
@app.get("/api/profile", response_model=UserProfile)
def get_profile(email: EmailStr):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    u = db["user"].find_one({"email": str(email)})
    if not u:
        # create a minimal profile on the fly
        profile = {"name": "Pengguna", "email": str(email), "points": 120, "level": 2, "streak": 5, "badges": ["Pemula"]}
        create_document("user", profile)
        u = db["user"].find_one({"email": str(email)})
    return {
        "name": u.get("name", "Pengguna"),
        "email": u.get("email"),
        "avatar": u.get("avatar"),
        "points": u.get("points", 0),
        "level": u.get("level", 1),
        "streak": u.get("streak", 0),
        "badges": u.get("badges", []),
    }

# --------- Progress ---------
@app.get("/api/progress")
def get_progress(user_email: EmailStr, module_slug: str):
    if db is None:
        return {"completed_lessons": []}
    p = db["progress"].find_one({"user_email": str(user_email), "module_slug": module_slug})
    return {"completed_lessons": p.get("completed_lessons", [])} if p else {"completed_lessons": []}

@app.post("/api/progress")
def set_progress(payload: ProgressIn):
    if db is None:
        return {"ok": False}
    db["progress"].update_one(
        {"user_email": payload.user_email, "module_slug": payload.module_slug},
        {"$set": {"completed_lessons": payload.completed_lessons}},
        upsert=True,
    )
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
