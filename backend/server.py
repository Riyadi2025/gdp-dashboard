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
    body_type: Optional[str] = None  # ectomorph, mesomorph, endomorph
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    available_equipment: Optional[List[str]] = []
    workout_days_per_week: Optional[int] = 3
    workout_duration_minutes: Optional[int] = 45
    injuries_restrictions: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    onboarding_complete: bool = False

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    fitness_goal: Optional[str] = None
    fitness_level: Optional[str] = None
    body_type: Optional[str] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    available_equipment: Optional[List[str]] = None
    workout_days_per_week: Optional[int] = None
    workout_duration_minutes: Optional[int] = None
    injuries_restrictions: Optional[str] = None
    dietary_restrictions: Optional[str] = None
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

# ==================== NUTRITION MODELS ====================

class Meal(BaseModel):
    name: str
    time: str  # e.g., "7:00 AM"
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    ingredients: List[str]
    instructions: str
    image_url: Optional[str] = None

class DailyMealPlan(BaseModel):
    day: str  # Monday, Tuesday, etc
    meals: List[Meal]
    total_calories: int
    total_protein_g: int
    total_carbs_g: int
    total_fat_g: int
    snacks: List[str]
    hydration_tip: str

class NutritionPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    plan_name: str
    description: str
    goal: str
    body_type: str  # ectomorph, mesomorph, endomorph
    daily_calories: int
    protein_target_g: int
    carbs_target_g: int
    fat_target_g: int
    meal_plans: List[DailyMealPlan]
    tips: List[str]
    foods_to_avoid: List[str]
    foods_to_include: List[str]
    active: bool = True

class NutritionPlanRequest(BaseModel):
    body_type: Optional[str] = None  # ectomorph, mesomorph, endomorph
    dietary_restrictions: Optional[str] = None  # vegan, vegetarian, keto, etc
    custom_instructions: Optional[str] = None

class NutritionPlanListItem(BaseModel):
    id: str
    plan_name: str
    goal: str
    body_type: str
    daily_calories: int
    created_at: datetime
    active: bool

# Meal image mapping
MEAL_IMAGES = {
    "breakfast": "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=400&q=80",
    "lunch": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80",
    "dinner": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&q=80",
    "snack": "https://images.unsplash.com/photo-1568702846914-96b305d2uj38?w=400&q=80",
    "protein": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=400&q=80",
    "salad": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&q=80",
    "chicken": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?w=400&q=80",
    "fish": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=400&q=80",
    "eggs": "https://images.unsplash.com/photo-1482049016gy-2c3e12099f93?w=400&q=80",
    "oatmeal": "https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=400&q=80",
    "smoothie": "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=400&q=80",
    "default": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400&q=80"
}

def get_meal_image(meal_name: str) -> str:
    """Get image URL for a meal based on name matching"""
    name_lower = meal_name.lower()
    for key, url in MEAL_IMAGES.items():
        if key in name_lower:
            return url
    return MEAL_IMAGES["default"]

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
        
        # Add images to exercises
        for day in plan_data.get("workout_days", []):
            for exercise in day.get("exercises", []):
                exercise["image_url"] = get_exercise_image(exercise.get("name", ""))
        
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
        "body_type": None,
        "age": None,
        "weight_kg": None,
        "height_cm": None,
        "available_equipment": [],
        "workout_days_per_week": 3,
        "workout_duration_minutes": 45,
        "injuries_restrictions": None,
        "dietary_restrictions": None,
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

# ==================== NUTRITION PLAN GENERATION ====================

async def generate_nutrition_plan_with_ai(user: UserProfile, body_type: str, dietary_restrictions: Optional[str] = None, custom_instructions: Optional[str] = None) -> dict:
    """Generate a personalized nutrition plan using Claude via Emergent Integration"""
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"nutrition-{user.id}-{uuid.uuid4()}",
        system_message="You are an expert nutritionist creating personalized meal plans."
    ).with_model("anthropic", "claude-sonnet-4-20250514")
    
    # Calculate base calories based on body type and goal
    base_calories = 2000
    if user.weight_kg and user.height_cm and user.age:
        # Basic BMR calculation (Mifflin-St Jeor)
        bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age + 5
        activity_multiplier = 1.55  # Moderate activity
        base_calories = int(bmr * activity_multiplier)
        
        # Adjust based on goal
        if user.fitness_goal == "weight_loss":
            base_calories = int(base_calories * 0.8)  # 20% deficit
        elif user.fitness_goal == "muscle_gain":
            base_calories = int(base_calories * 1.15)  # 15% surplus
    
    prompt = f"""You are an expert nutritionist creating a personalized meal plan.

USER PROFILE:
- Name: {user.name}
- Fitness Goal: {user.fitness_goal or 'general fitness'}
- Body Type: {body_type}
- Age: {user.age or 'Not specified'}
- Weight: {user.weight_kg or 'Not specified'} kg
- Height: {user.height_cm or 'Not specified'} cm
- Estimated Daily Calories: {base_calories}
- Dietary Restrictions: {dietary_restrictions or 'None mentioned'}

{f'CUSTOM INSTRUCTIONS: {custom_instructions}' if custom_instructions else ''}

BODY TYPE CONSIDERATIONS:
- Ectomorph: Higher carb intake, frequent meals, calorie-dense foods
- Mesomorph: Balanced macros, moderate portions
- Endomorph: Lower carb, higher protein, controlled portions

Create a 3-day sample meal plan that can be repeated. Return ONLY valid JSON (no markdown) in this structure:

{{
    "plan_name": "Creative name",
    "description": "Brief description",
    "goal": "{user.fitness_goal or 'general_fitness'}",
    "body_type": "{body_type}",
    "daily_calories": {base_calories},
    "protein_target_g": {int(base_calories * 0.3 / 4)},
    "carbs_target_g": {int(base_calories * 0.4 / 4)},
    "fat_target_g": {int(base_calories * 0.3 / 9)},
    "meal_plans": [
        {{
            "day": "Day 1",
            "meals": [
                {{"name": "Meal name", "time": "7:00 AM", "calories": 450, "protein_g": 35, "carbs_g": 40, "fat_g": 15, "ingredients": ["item1", "item2"], "instructions": "Brief instructions"}}
            ],
            "total_calories": {base_calories},
            "total_protein_g": {int(base_calories * 0.3 / 4)},
            "total_carbs_g": {int(base_calories * 0.4 / 4)},
            "total_fat_g": {int(base_calories * 0.3 / 9)},
            "snacks": ["Snack 1"],
            "hydration_tip": "Hydration tip"
        }}
    ],
    "tips": ["Tip 1", "Tip 2"],
    "foods_to_avoid": ["Food 1", "Food 2"],
    "foods_to_include": ["Food 1", "Food 2"]
}}

Include 3 meals per day (breakfast, lunch, dinner). Keep instructions SHORT."""

    try:
        user_msg = UserMessage(text=prompt)
        response = await chat.send_message(user_msg)
        response_text = response.strip()
        
        # Clean up response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        plan_data = json.loads(response_text.strip())
        
        # Add images to meals
        for day in plan_data.get("meal_plans", []):
            for meal in day.get("meals", []):
                meal["image_url"] = get_meal_image(meal.get("name", ""))
        
        return plan_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse nutrition plan from AI")
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate nutrition plan: {str(e)}")

# ==================== NUTRITION PLAN ROUTES ====================

@api_router.post("/nutrition-plans/generate", response_model=NutritionPlan)
async def generate_nutrition_plan(
    request: NutritionPlanRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Generate a new AI-powered nutrition plan"""
    # Deactivate existing active plans
    await db.nutrition_plans.update_many(
        {"user_id": current_user.id, "active": True},
        {"$set": {"active": False}}
    )
    
    body_type = request.body_type or "mesomorph"  # Default to balanced
    
    # Generate new plan with AI
    plan_data = await generate_nutrition_plan_with_ai(
        current_user, 
        body_type, 
        request.dietary_restrictions,
        request.custom_instructions
    )
    
    # Create nutrition plan document
    plan = NutritionPlan(
        user_id=current_user.id,
        **plan_data
    )
    
    # Save to database
    plan_doc = plan.model_dump()
    plan_doc['created_at'] = plan_doc['created_at'].isoformat()
    await db.nutrition_plans.insert_one(plan_doc)
    
    return plan

@api_router.get("/nutrition-plans", response_model=List[NutritionPlanListItem])
async def get_nutrition_plans(current_user: UserProfile = Depends(get_current_user)):
    """Get all nutrition plans for current user"""
    plans = await db.nutrition_plans.find(
        {"user_id": current_user.id},
        {"_id": 0, "id": 1, "plan_name": 1, "goal": 1, "body_type": 1, "daily_calories": 1, "created_at": 1, "active": 1}
    ).sort("created_at", -1).to_list(100)
    
    for plan in plans:
        if isinstance(plan.get('created_at'), str):
            plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return plans

@api_router.get("/nutrition-plans/active", response_model=Optional[NutritionPlan])
async def get_active_nutrition_plan(current_user: UserProfile = Depends(get_current_user)):
    """Get the active nutrition plan"""
    plan = await db.nutrition_plans.find_one(
        {"user_id": current_user.id, "active": True},
        {"_id": 0}
    )
    
    if not plan:
        return None
    
    if isinstance(plan.get('created_at'), str):
        plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return NutritionPlan(**plan)

@api_router.get("/nutrition-plans/{plan_id}", response_model=NutritionPlan)
async def get_nutrition_plan(plan_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get a specific nutrition plan"""
    plan = await db.nutrition_plans.find_one(
        {"id": plan_id, "user_id": current_user.id},
        {"_id": 0}
    )
    
    if not plan:
        raise HTTPException(status_code=404, detail="Nutrition plan not found")
    
    if isinstance(plan.get('created_at'), str):
        plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return NutritionPlan(**plan)

@api_router.delete("/nutrition-plans/{plan_id}")
async def delete_nutrition_plan(plan_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Delete a nutrition plan"""
    result = await db.nutrition_plans.delete_one({"id": plan_id, "user_id": current_user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nutrition plan not found")
    
    return {"message": "Plan deleted successfully"}

# ==================== PROGRESS TRACKING MODELS ====================

class ProgressEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str  # YYYY-MM-DD format
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    arms_cm: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProgressEntryCreate(BaseModel):
    date: str
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    arms_cm: Optional[float] = None
    notes: Optional[str] = None

class WorkoutLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    workout_plan_id: str
    day_index: int
    date: str
    exercises: List[dict]  # [{exercise_name, sets_completed, reps_completed, weight_used, notes}]
    duration_minutes: int
    completed: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkoutLogCreate(BaseModel):
    workout_plan_id: str
    day_index: int
    date: str
    exercises: List[dict]
    duration_minutes: int

class PersonalRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    exercise_name: str
    weight_kg: float
    reps: int
    date: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Achievement(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None

class UserStats(BaseModel):
    total_workouts: int
    current_streak: int
    longest_streak: int
    total_weight_lifted_kg: float
    achievements: List[Achievement]
    level: int
    xp: int
    xp_to_next_level: int

class ScheduledWorkout(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    workout_plan_id: str
    day_index: int
    scheduled_date: str
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScheduledWorkoutCreate(BaseModel):
    workout_plan_id: str
    day_index: int
    scheduled_date: str

class GroceryItem(BaseModel):
    name: str
    quantity: str
    category: str
    checked: bool = False

class GroceryList(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    nutrition_plan_id: str
    items: List[GroceryItem]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DailyChallenge(BaseModel):
    id: str
    name: str
    description: str
    xp_reward: int
    type: str  # workout, nutrition, habit
    target: int
    current: int
    completed: bool = False

class LeaderboardEntry(BaseModel):
    user_id: str
    user_name: str
    xp: int
    level: int
    streak: int
    rank: int

# ==================== PROGRESS TRACKING ROUTES ====================

@api_router.post("/progress", response_model=ProgressEntry)
async def add_progress_entry(
    entry: ProgressEntryCreate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Add a progress tracking entry"""
    progress = ProgressEntry(user_id=current_user.id, **entry.model_dump())
    progress_doc = progress.model_dump()
    progress_doc['created_at'] = progress_doc['created_at'].isoformat()
    await db.progress.insert_one(progress_doc)
    return progress

@api_router.get("/progress", response_model=List[ProgressEntry])
async def get_progress(current_user: UserProfile = Depends(get_current_user)):
    """Get all progress entries"""
    entries = await db.progress.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("date", -1).to_list(365)
    
    for entry in entries:
        if isinstance(entry.get('created_at'), str):
            entry['created_at'] = datetime.fromisoformat(entry['created_at'])
    
    return entries

@api_router.delete("/progress/{entry_id}")
async def delete_progress_entry(entry_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Delete a progress entry"""
    result = await db.progress.delete_one({"id": entry_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}

# ==================== WORKOUT LOGGING ROUTES ====================

@api_router.post("/workout-logs", response_model=WorkoutLog)
async def log_workout(
    log: WorkoutLogCreate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Log a completed workout"""
    workout_log = WorkoutLog(user_id=current_user.id, **log.model_dump())
    log_doc = workout_log.model_dump()
    log_doc['created_at'] = log_doc['created_at'].isoformat()
    await db.workout_logs.insert_one(log_doc)
    
    # Update user stats (XP, streaks)
    await update_user_stats(current_user.id, "workout_complete")
    
    # Check for personal records
    for exercise in log.exercises:
        if exercise.get('weight_used') and exercise.get('reps_completed'):
            await check_and_update_pr(
                current_user.id, 
                exercise['exercise_name'], 
                exercise['weight_used'], 
                exercise['reps_completed'],
                log.date
            )
    
    return workout_log

@api_router.get("/workout-logs", response_model=List[WorkoutLog])
async def get_workout_logs(current_user: UserProfile = Depends(get_current_user)):
    """Get workout history"""
    logs = await db.workout_logs.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    
    for log in logs:
        if isinstance(log.get('created_at'), str):
            log['created_at'] = datetime.fromisoformat(log['created_at'])
    
    return logs

@api_router.get("/workout-logs/calendar")
async def get_workout_calendar(
    month: int,
    year: int,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get workout calendar for a month"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    logs = await db.workout_logs.find(
        {"user_id": current_user.id, "date": {"$gte": start_date, "$lt": end_date}},
        {"_id": 0, "date": 1, "day_index": 1, "completed": 1}
    ).to_list(50)
    
    scheduled = await db.scheduled_workouts.find(
        {"user_id": current_user.id, "scheduled_date": {"$gte": start_date, "$lt": end_date}},
        {"_id": 0}
    ).to_list(50)
    
    return {"completed": logs, "scheduled": scheduled}

# ==================== PERSONAL RECORDS ROUTES ====================

@api_router.get("/personal-records", response_model=List[PersonalRecord])
async def get_personal_records(current_user: UserProfile = Depends(get_current_user)):
    """Get all personal records"""
    records = await db.personal_records.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for record in records:
        if isinstance(record.get('created_at'), str):
            record['created_at'] = datetime.fromisoformat(record['created_at'])
    
    return records

async def check_and_update_pr(user_id: str, exercise_name: str, weight: float, reps, date: str):
    """Check if this is a new personal record"""
    # Convert reps to int if it's a string like "8-10"
    try:
        if isinstance(reps, str):
            reps = int(reps.split('-')[0].split()[0])  # Take first number
        reps = int(reps)
    except (ValueError, AttributeError):
        reps = 10  # Default
    
    existing_pr = await db.personal_records.find_one({
        "user_id": user_id,
        "exercise_name": exercise_name
    })
    
    # Calculate 1RM estimate (Epley formula)
    new_1rm = weight * (1 + reps / 30)
    
    if not existing_pr:
        # Create new PR
        pr = PersonalRecord(
            user_id=user_id,
            exercise_name=exercise_name,
            weight_kg=weight,
            reps=reps,
            date=date
        )
        pr_doc = pr.model_dump()
        pr_doc['created_at'] = pr_doc['created_at'].isoformat()
        await db.personal_records.insert_one(pr_doc)
    else:
        old_1rm = existing_pr['weight_kg'] * (1 + existing_pr['reps'] / 30)
        if new_1rm > old_1rm:
            await db.personal_records.update_one(
                {"id": existing_pr['id']},
                {"$set": {"weight_kg": weight, "reps": reps, "date": date}}
            )

# ==================== USER STATS & GAMIFICATION ====================

ACHIEVEMENTS = [
    {"id": "first_workout", "name": "First Step", "description": "Complete your first workout", "icon": "🎯", "xp": 100},
    {"id": "streak_7", "name": "Week Warrior", "description": "7-day workout streak", "icon": "🔥", "xp": 500},
    {"id": "streak_30", "name": "Monthly Master", "description": "30-day workout streak", "icon": "⚡", "xp": 2000},
    {"id": "workouts_10", "name": "Getting Serious", "description": "Complete 10 workouts", "icon": "💪", "xp": 300},
    {"id": "workouts_50", "name": "Dedicated", "description": "Complete 50 workouts", "icon": "🏆", "xp": 1500},
    {"id": "workouts_100", "name": "Century Club", "description": "Complete 100 workouts", "icon": "👑", "xp": 5000},
    {"id": "pr_set", "name": "Record Breaker", "description": "Set a personal record", "icon": "🚀", "xp": 200},
    {"id": "weight_logged", "name": "Tracking Pro", "description": "Log your weight 10 times", "icon": "📊", "xp": 250},
]

def calculate_level(xp: int) -> tuple:
    """Calculate level and XP to next level"""
    level = 1
    xp_for_level = 100
    remaining_xp = xp
    
    while remaining_xp >= xp_for_level:
        remaining_xp -= xp_for_level
        level += 1
        xp_for_level = int(xp_for_level * 1.5)
    
    return level, xp_for_level - remaining_xp

async def update_user_stats(user_id: str, action: str):
    """Update user stats based on action"""
    stats = await db.user_stats.find_one({"user_id": user_id})
    
    if not stats:
        stats = {
            "user_id": user_id,
            "total_workouts": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "total_weight_lifted_kg": 0,
            "xp": 0,
            "unlocked_achievements": [],
            "last_workout_date": None
        }
    
    new_achievements = []
    
    if action == "workout_complete":
        stats["total_workouts"] += 1
        stats["xp"] += 50  # Base XP per workout
        
        # Update streak
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        if stats.get("last_workout_date") == yesterday:
            stats["current_streak"] += 1
        elif stats.get("last_workout_date") != today:
            stats["current_streak"] = 1
        
        stats["last_workout_date"] = today
        stats["longest_streak"] = max(stats["longest_streak"], stats["current_streak"])
        
        # Check achievements
        if stats["total_workouts"] == 1 and "first_workout" not in stats["unlocked_achievements"]:
            stats["unlocked_achievements"].append("first_workout")
            stats["xp"] += 100
            new_achievements.append("first_workout")
        
        if stats["total_workouts"] >= 10 and "workouts_10" not in stats["unlocked_achievements"]:
            stats["unlocked_achievements"].append("workouts_10")
            stats["xp"] += 300
            new_achievements.append("workouts_10")
        
        if stats["total_workouts"] >= 50 and "workouts_50" not in stats["unlocked_achievements"]:
            stats["unlocked_achievements"].append("workouts_50")
            stats["xp"] += 1500
            new_achievements.append("workouts_50")
        
        if stats["current_streak"] >= 7 and "streak_7" not in stats["unlocked_achievements"]:
            stats["unlocked_achievements"].append("streak_7")
            stats["xp"] += 500
            new_achievements.append("streak_7")
        
        if stats["current_streak"] >= 30 and "streak_30" not in stats["unlocked_achievements"]:
            stats["unlocked_achievements"].append("streak_30")
            stats["xp"] += 2000
            new_achievements.append("streak_30")
    
    await db.user_stats.update_one(
        {"user_id": user_id},
        {"$set": stats},
        upsert=True
    )
    
    return new_achievements

@api_router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: UserProfile = Depends(get_current_user)):
    """Get user statistics and achievements"""
    stats = await db.user_stats.find_one({"user_id": current_user.id})
    
    if not stats:
        stats = {
            "total_workouts": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "total_weight_lifted_kg": 0,
            "xp": 0,
            "unlocked_achievements": []
        }
    
    level, xp_to_next = calculate_level(stats.get("xp", 0))
    
    achievements = []
    for ach in ACHIEVEMENTS:
        achievements.append(Achievement(
            id=ach["id"],
            name=ach["name"],
            description=ach["description"],
            icon=ach["icon"],
            unlocked=ach["id"] in stats.get("unlocked_achievements", [])
        ))
    
    return UserStats(
        total_workouts=stats.get("total_workouts", 0),
        current_streak=stats.get("current_streak", 0),
        longest_streak=stats.get("longest_streak", 0),
        total_weight_lifted_kg=stats.get("total_weight_lifted_kg", 0),
        achievements=achievements,
        level=level,
        xp=stats.get("xp", 0),
        xp_to_next_level=xp_to_next
    )

@api_router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    """Get global leaderboard"""
    stats = await db.user_stats.find({}).sort("xp", -1).to_list(50)
    
    leaderboard = []
    for rank, stat in enumerate(stats, 1):
        user = await db.users.find_one({"id": stat["user_id"]}, {"name": 1})
        if user:
            level, _ = calculate_level(stat.get("xp", 0))
            leaderboard.append(LeaderboardEntry(
                user_id=stat["user_id"],
                user_name=user.get("name", "Anonymous"),
                xp=stat.get("xp", 0),
                level=level,
                streak=stat.get("current_streak", 0),
                rank=rank
            ))
    
    return leaderboard

@api_router.get("/daily-challenges", response_model=List[DailyChallenge])
async def get_daily_challenges(current_user: UserProfile = Depends(get_current_user)):
    """Get today's challenges"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get today's workout count
    workout_count = await db.workout_logs.count_documents({
        "user_id": current_user.id,
        "date": today
    })
    
    # Get today's progress log
    progress_logged = await db.progress.count_documents({
        "user_id": current_user.id,
        "date": today
    })
    
    challenges = [
        DailyChallenge(
            id="daily_workout",
            name="Daily Grind",
            description="Complete a workout today",
            xp_reward=100,
            type="workout",
            target=1,
            current=min(workout_count, 1),
            completed=workout_count >= 1
        ),
        DailyChallenge(
            id="log_progress",
            name="Track It",
            description="Log your progress today",
            xp_reward=50,
            type="habit",
            target=1,
            current=min(progress_logged, 1),
            completed=progress_logged >= 1
        ),
        DailyChallenge(
            id="hydration",
            name="Stay Hydrated",
            description="Drink 8 glasses of water",
            xp_reward=30,
            type="habit",
            target=8,
            current=0,
            completed=False
        )
    ]
    
    return challenges

# ==================== SCHEDULING ROUTES ====================

@api_router.post("/schedule", response_model=ScheduledWorkout)
async def schedule_workout(
    schedule: ScheduledWorkoutCreate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Schedule a workout"""
    scheduled = ScheduledWorkout(user_id=current_user.id, **schedule.model_dump())
    doc = scheduled.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.scheduled_workouts.insert_one(doc)
    return scheduled

@api_router.get("/schedule")
async def get_schedule(current_user: UserProfile = Depends(get_current_user)):
    """Get all scheduled workouts"""
    schedules = await db.scheduled_workouts.find(
        {"user_id": current_user.id, "completed": False},
        {"_id": 0}
    ).sort("scheduled_date", 1).to_list(100)
    return schedules

@api_router.put("/schedule/{schedule_id}/complete")
async def complete_scheduled_workout(schedule_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Mark scheduled workout as complete"""
    result = await db.scheduled_workouts.update_one(
        {"id": schedule_id, "user_id": current_user.id},
        {"$set": {"completed": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Scheduled workout not found")
    return {"message": "Marked as complete"}

# ==================== GROCERY LIST ROUTES ====================

@api_router.post("/grocery-list/generate")
async def generate_grocery_list(
    nutrition_plan_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Generate grocery list from nutrition plan"""
    plan = await db.nutrition_plans.find_one({
        "id": nutrition_plan_id,
        "user_id": current_user.id
    })
    
    if not plan:
        raise HTTPException(status_code=404, detail="Nutrition plan not found")
    
    # Extract all ingredients
    ingredients_dict = {}
    for day in plan.get("meal_plans", []):
        for meal in day.get("meals", []):
            for ingredient in meal.get("ingredients", []):
                # Simple aggregation - in real app would parse quantities
                if ingredient.lower() not in ingredients_dict:
                    ingredients_dict[ingredient.lower()] = {
                        "name": ingredient,
                        "quantity": "As needed",
                        "category": categorize_ingredient(ingredient),
                        "checked": False
                    }
    
    items = [GroceryItem(**item) for item in ingredients_dict.values()]
    
    grocery_list = GroceryList(
        user_id=current_user.id,
        nutrition_plan_id=nutrition_plan_id,
        items=items
    )
    
    doc = grocery_list.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.grocery_lists.insert_one(doc)
    
    return grocery_list

def categorize_ingredient(ingredient: str) -> str:
    """Categorize ingredient for grocery list"""
    ingredient_lower = ingredient.lower()
    
    proteins = ["chicken", "beef", "fish", "salmon", "tuna", "eggs", "turkey", "pork", "shrimp"]
    dairy = ["milk", "cheese", "yogurt", "butter", "cream"]
    produce = ["banana", "apple", "berries", "spinach", "broccoli", "tomato", "onion", "garlic", "avocado", "lettuce"]
    grains = ["rice", "oats", "bread", "pasta", "quinoa", "cereal"]
    
    for p in proteins:
        if p in ingredient_lower:
            return "Protein"
    for d in dairy:
        if d in ingredient_lower:
            return "Dairy"
    for pr in produce:
        if pr in ingredient_lower:
            return "Produce"
    for g in grains:
        if g in ingredient_lower:
            return "Grains"
    
    return "Other"

@api_router.get("/grocery-list")
async def get_grocery_lists(current_user: UserProfile = Depends(get_current_user)):
    """Get user's grocery lists"""
    lists = await db.grocery_lists.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    return lists

@api_router.put("/grocery-list/{list_id}/item/{item_name}/toggle")
async def toggle_grocery_item(list_id: str, item_name: str, current_user: UserProfile = Depends(get_current_user)):
    """Toggle grocery item checked status"""
    grocery_list = await db.grocery_lists.find_one({
        "id": list_id,
        "user_id": current_user.id
    })
    
    if not grocery_list:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    
    items = grocery_list.get("items", [])
    for item in items:
        if item["name"].lower() == item_name.lower():
            item["checked"] = not item["checked"]
            break
    
    await db.grocery_lists.update_one(
        {"id": list_id},
        {"$set": {"items": items}}
    )
    
    return {"message": "Item toggled"}

# ==================== MEAL SWAP ROUTES ====================

@api_router.post("/nutrition-plans/{plan_id}/swap-meal")
async def swap_meal(
    plan_id: str,
    day_index: int,
    meal_index: int,
    current_user: UserProfile = Depends(get_current_user)
):
    """Swap a meal with an AI-generated alternative"""
    plan = await db.nutrition_plans.find_one({
        "id": plan_id,
        "user_id": current_user.id
    })
    
    if not plan:
        raise HTTPException(status_code=404, detail="Nutrition plan not found")
    
    current_meal = plan["meal_plans"][day_index]["meals"][meal_index]
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"swap-{current_user.id}-{uuid.uuid4()}",
        system_message="You are a nutritionist. Generate meal alternatives."
    ).with_model("anthropic", "claude-sonnet-4-20250514")
    
    prompt = f"""Generate a healthy alternative meal to replace: {current_meal['name']}
Target: ~{current_meal['calories']} calories, ~{current_meal['protein_g']}g protein

Return ONLY valid JSON:
{{"name": "Meal Name", "time": "{current_meal['time']}", "calories": {current_meal['calories']}, "protein_g": {current_meal['protein_g']}, "carbs_g": {current_meal['carbs_g']}, "fat_g": {current_meal['fat_g']}, "ingredients": ["item1", "item2"], "instructions": "Brief instructions"}}"""

    try:
        user_msg = UserMessage(text=prompt)
        response = await chat.send_message(user_msg)
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        new_meal = json.loads(response_text.strip())
        new_meal["image_url"] = get_meal_image(new_meal.get("name", ""))
        
        # Update the plan
        plan["meal_plans"][day_index]["meals"][meal_index] = new_meal
        await db.nutrition_plans.update_one(
            {"id": plan_id},
            {"$set": {"meal_plans": plan["meal_plans"]}}
        )
        
        return new_meal
    except Exception as e:
        logger.error(f"Meal swap error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate alternative meal")

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
