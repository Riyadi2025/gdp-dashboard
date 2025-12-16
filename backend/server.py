from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'motivaction_db')]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'motivaction-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 1440))

# Emergent LLM Key for Claude
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app
app = FastAPI(title="MotivAction API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Fitness profile fields
    fitness_goal: Optional[str] = None  # weight_loss, muscle_gain, endurance, general_fitness
    fitness_level: Optional[str] = None  # beginner, intermediate, advanced
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    available_equipment: Optional[List[str]] = []
    workout_days_per_week: Optional[int] = 3
    workout_duration_minutes: Optional[int] = 45
    injuries_restrictions: Optional[str] = None
    onboarding_complete: bool = False

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    fitness_goal: Optional[str] = None
    fitness_level: Optional[str] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    available_equipment: Optional[List[str]] = None
    workout_days_per_week: Optional[int] = None
    workout_duration_minutes: Optional[int] = None
    injuries_restrictions: Optional[str] = None
    onboarding_complete: Optional[bool] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class Exercise(BaseModel):
    name: str
    sets: int
    reps: str  # Can be "10-12" or "30 seconds" etc
    rest_seconds: int
    notes: Optional[str] = None
    muscle_group: str
    image_url: Optional[str] = None

# Exercise image mapping for common exercises
EXERCISE_IMAGES = {
    # Chest exercises
    "bench press": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&q=80",
    "barbell bench press": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&q=80",
    "dumbbell chest press": "https://images.unsplash.com/photo-1598268030450-7a476f602406?w=400&q=80",
    "incline press": "https://images.unsplash.com/photo-1598268030450-7a476f602406?w=400&q=80",
    "push-ups": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400&q=80",
    "chest fly": "https://images.unsplash.com/photo-1598268030450-7a476f602406?w=400&q=80",
    # Back exercises
    "pull-ups": "https://images.unsplash.com/photo-1598971457999-ca4ef48a9a71?w=400&q=80",
    "chin-ups": "https://images.unsplash.com/photo-1598971457999-ca4ef48a9a71?w=400&q=80",
    "barbell rows": "https://images.unsplash.com/photo-1603287681836-b174ce5074c2?w=400&q=80",
    "bent-over rows": "https://images.unsplash.com/photo-1603287681836-b174ce5074c2?w=400&q=80",
    "dumbbell rows": "https://images.unsplash.com/photo-1603287681836-b174ce5074c2?w=400&q=80",
    "lat pulldown": "https://images.unsplash.com/photo-1534368786749-b63e05c92717?w=400&q=80",
    "deadlift": "https://images.unsplash.com/photo-1566241142559-40e1dab266c6?w=400&q=80",
    "romanian deadlift": "https://images.unsplash.com/photo-1566241142559-40e1dab266c6?w=400&q=80",
    # Shoulder exercises
    "shoulder press": "https://images.unsplash.com/photo-1532029837206-abbe2b7620e3?w=400&q=80",
    "dumbbell shoulder press": "https://images.unsplash.com/photo-1532029837206-abbe2b7620e3?w=400&q=80",
    "lateral raises": "https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400&q=80",
    "front raises": "https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400&q=80",
    # Leg exercises
    "squats": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400&q=80",
    "barbell squats": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400&q=80",
    "back squats": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400&q=80",
    "lunges": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&q=80",
    "leg press": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&q=80",
    "leg curls": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&q=80",
    "calf raises": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&q=80",
    "split squats": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&q=80",
    "step-ups": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&q=80",
    # Arm exercises
    "bicep curls": "https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400&q=80",
    "hammer curls": "https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400&q=80",
    "tricep dips": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400&q=80",
    "tricep extensions": "https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400&q=80",
    "close-grip press": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&q=80",
    # Core exercises
    "plank": "https://images.unsplash.com/photo-1566241142559-40e1dab266c6?w=400&q=80",
    "crunches": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&q=80",
    "russian twists": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&q=80",
    # Default
    "default": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&q=80"
}

def get_exercise_image(exercise_name: str) -> str:
    """Get image URL for an exercise based on name matching"""
    name_lower = exercise_name.lower()
    for key, url in EXERCISE_IMAGES.items():
        if key in name_lower or name_lower in key:
            return url
    return EXERCISE_IMAGES["default"]

class WorkoutDay(BaseModel):
    day: str  # Monday, Tuesday, etc
    workout_type: str  # Push, Pull, Legs, Full Body, etc
    exercises: List[Exercise]
    estimated_duration_minutes: int
    warmup_notes: str
    cooldown_notes: str

class WorkoutPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    plan_name: str
    description: str
    goal: str
    level: str
    duration_weeks: int
    workout_days: List[WorkoutDay]
    tips: List[str]
    active: bool = True

class WorkoutPlanRequest(BaseModel):
    custom_instructions: Optional[str] = None

class WorkoutPlanListItem(BaseModel):
    id: str
    plan_name: str
    goal: str
    level: str
    created_at: datetime
    active: bool

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Convert timestamp
        if isinstance(user_doc.get('created_at'), str):
            user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
        
        return UserProfile(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AI WORKOUT GENERATION ====================

async def generate_workout_plan_with_ai(user: UserProfile, custom_instructions: Optional[str] = None) -> dict:
    """Generate a personalized workout plan using Claude via Emergent Integration"""
    
    # Use Emergent LLM integration with Claude
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"workout-{user.id}-{uuid.uuid4()}",
        system_message="You are an expert fitness coach creating personalized workout plans."
    ).with_model("anthropic", "claude-sonnet-4-20250514")
    
    equipment_str = ", ".join(user.available_equipment) if user.available_equipment else "No equipment (bodyweight only)"
    
    prompt = f"""You are an expert fitness coach creating a personalized workout plan.

USER PROFILE:
- Name: {user.name}
- Fitness Goal: {user.fitness_goal or 'general fitness'}
- Fitness Level: {user.fitness_level or 'beginner'}
- Age: {user.age or 'Not specified'}
- Weight: {user.weight_kg or 'Not specified'} kg
- Height: {user.height_cm or 'Not specified'} cm
- Available Equipment: {equipment_str}
- Workout Days Per Week: {user.workout_days_per_week or 3}
- Preferred Workout Duration: {user.workout_duration_minutes or 45} minutes
- Injuries/Restrictions: {user.injuries_restrictions or 'None mentioned'}

{f'CUSTOM INSTRUCTIONS: {custom_instructions}' if custom_instructions else ''}

Create a detailed {user.workout_days_per_week or 3}-day workout plan. Return ONLY valid JSON (no markdown, no code blocks) in this exact structure:

{{
    "plan_name": "Creative motivating name for this plan",
    "description": "Brief description of the plan and expected outcomes",
    "goal": "{user.fitness_goal or 'general_fitness'}",
    "level": "{user.fitness_level or 'beginner'}",
    "duration_weeks": 4,
    "workout_days": [
        {{
            "day": "Day 1 - Monday",
            "workout_type": "Type of workout (e.g., Push, Full Body)",
            "exercises": [
                {{
                    "name": "Exercise name",
                    "sets": 3,
                    "reps": "10-12",
                    "rest_seconds": 60,
                    "notes": "Form tips or modifications",
                    "muscle_group": "Primary muscle group"
                }}
            ],
            "estimated_duration_minutes": 45,
            "warmup_notes": "5-min warmup routine",
            "cooldown_notes": "5-min cooldown routine"
        }}
    ],
    "tips": ["Tip 1", "Tip 2", "Tip 3"]
}}

Include 4-6 exercises per workout day. Make exercises appropriate for the user's level and equipment. Be specific with exercise names and provide helpful form notes."""

    try:
        user_msg = UserMessage(text=prompt)
        response = await chat.send_message(user_msg)
        response_text = response.strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        plan_data = json.loads(response_text.strip())
        return plan_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        logger.error(f"Response was: {response_text[:500]}...")
        raise HTTPException(status_code=500, detail="Failed to parse workout plan from AI")
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate workout plan: {str(e)}")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fitness_goal": None,
        "fitness_level": None,
        "age": None,
        "weight_kg": None,
        "height_cm": None,
        "available_equipment": [],
        "workout_days_per_week": 3,
        "workout_duration_minutes": 45,
        "injuries_restrictions": None,
        "onboarding_complete": False
    }
    
    await db.users.insert_one(user_doc)
    
    # Create token
    token = create_access_token(user_id)
    
    # Return user without password
    user_doc.pop('password_hash')
    user_doc.pop('_id', None)
    user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return TokenResponse(access_token=token, user=UserProfile(**user_doc))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user_doc['id'])
    
    # Return user without password
    user_doc.pop('password_hash')
    user_doc.pop('_id', None)
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return TokenResponse(access_token=token, user=UserProfile(**user_doc))

@api_router.get("/auth/me", response_model=UserProfile)
async def get_me(current_user: UserProfile = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

# ==================== USER PROFILE ROUTES ====================

@api_router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Update user profile (including onboarding data)"""
    update_data = {k: v for k, v in profile_update.model_dump().items() if v is not None}
    
    if not update_data:
        return current_user
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_data}
    )
    
    # Get updated user
    user_doc = await db.users.find_one({"id": current_user.id}, {"_id": 0, "password_hash": 0})
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return UserProfile(**user_doc)

# ==================== WORKOUT PLAN ROUTES ====================

@api_router.post("/workout-plans/generate", response_model=WorkoutPlan)
async def generate_workout_plan(
    request: WorkoutPlanRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Generate a new AI-powered workout plan"""
    # Deactivate existing active plans
    await db.workout_plans.update_many(
        {"user_id": current_user.id, "active": True},
        {"$set": {"active": False}}
    )
    
    # Generate new plan with AI
    plan_data = await generate_workout_plan_with_ai(current_user, request.custom_instructions)
    
    # Create workout plan document
    plan = WorkoutPlan(
        user_id=current_user.id,
        **plan_data
    )
    
    # Save to database
    plan_doc = plan.model_dump()
    plan_doc['created_at'] = plan_doc['created_at'].isoformat()
    await db.workout_plans.insert_one(plan_doc)
    
    return plan

@api_router.get("/workout-plans", response_model=List[WorkoutPlanListItem])
async def get_workout_plans(current_user: UserProfile = Depends(get_current_user)):
    """Get all workout plans for current user"""
    plans = await db.workout_plans.find(
        {"user_id": current_user.id},
        {"_id": 0, "id": 1, "plan_name": 1, "goal": 1, "level": 1, "created_at": 1, "active": 1}
    ).sort("created_at", -1).to_list(100)
    
    for plan in plans:
        if isinstance(plan.get('created_at'), str):
            plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return plans

@api_router.get("/workout-plans/active", response_model=Optional[WorkoutPlan])
async def get_active_workout_plan(current_user: UserProfile = Depends(get_current_user)):
    """Get the active workout plan"""
    plan = await db.workout_plans.find_one(
        {"user_id": current_user.id, "active": True},
        {"_id": 0}
    )
    
    if not plan:
        return None
    
    if isinstance(plan.get('created_at'), str):
        plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return WorkoutPlan(**plan)

@api_router.get("/workout-plans/{plan_id}", response_model=WorkoutPlan)
async def get_workout_plan(plan_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get a specific workout plan"""
    plan = await db.workout_plans.find_one(
        {"id": plan_id, "user_id": current_user.id},
        {"_id": 0}
    )
    
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    if isinstance(plan.get('created_at'), str):
        plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return WorkoutPlan(**plan)

@api_router.put("/workout-plans/{plan_id}/activate")
async def activate_workout_plan(plan_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Set a workout plan as active"""
    # Check plan exists and belongs to user
    plan = await db.workout_plans.find_one({"id": plan_id, "user_id": current_user.id})
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    # Deactivate all other plans
    await db.workout_plans.update_many(
        {"user_id": current_user.id},
        {"$set": {"active": False}}
    )
    
    # Activate this plan
    await db.workout_plans.update_one(
        {"id": plan_id},
        {"$set": {"active": True}}
    )
    
    return {"message": "Plan activated successfully"}

@api_router.delete("/workout-plans/{plan_id}")
async def delete_workout_plan(plan_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Delete a workout plan"""
    result = await db.workout_plans.delete_one({"id": plan_id, "user_id": current_user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    return {"message": "Plan deleted successfully"}

# ==================== HEALTH & ROOT ====================

@api_router.get("/")
async def root():
    return {"message": "MotivAction API - Your AI Fitness Coach", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "motivaction"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
