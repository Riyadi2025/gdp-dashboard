import { useState, useEffect, createContext, useContext, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Dumbbell, Zap, Target, Clock, Calendar, ChevronRight, LogOut, User, Plus, Loader2, CheckCircle, AlertCircle, Menu, X, Flame, Trophy, Utensils, Apple, Scale, BarChart3, Timer, ShoppingCart, Award, TrendingUp, Play, Pause, RotateCcw, ChevronLeft, Star } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const LOGO_URL = "https://customer-assets.emergentagent.com/job_fit-momentum/artifacts/6781x21v_TheMotivAction%20Logo3.png";

// Auth Context
const AuthContext = createContext(null);
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};

// API helper
const createAuthApi = (token) => axios.create({ baseURL: API, headers: token ? { Authorization: `Bearer ${token}` } : {} });

// ==================== REUSABLE COMPONENTS ====================

const Button = ({ children, variant = "primary", size = "md", disabled, loading, className = "", ...props }) => {
  const variants = {
    primary: "bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white shadow-lg shadow-orange-500/25",
    secondary: "bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700",
    ghost: "bg-transparent hover:bg-zinc-800 text-zinc-300",
    green: "bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white shadow-lg shadow-green-500/25",
    purple: "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg shadow-purple-500/25",
  };
  const sizes = { sm: "px-4 py-2 text-sm", md: "px-6 py-3 text-base", lg: "px-8 py-4 text-lg" };
  return (
    <button className={`font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`} disabled={disabled || loading} {...props}>
      {loading && <Loader2 className="w-5 h-5 animate-spin" />}
      {children}
    </button>
  );
};

const Input = ({ label, error, className = "", ...props }) => (
  <div className="space-y-2">
    {label && <label className="block text-sm font-medium text-zinc-300">{label}</label>}
    <input className={`w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all ${error ? 'border-red-500' : ''} ${className}`} {...props} />
    {error && <p className="text-sm text-red-500">{error}</p>}
  </div>
);

const Select = ({ label, options, className = "", ...props }) => (
  <div className="space-y-2">
    {label && <label className="block text-sm font-medium text-zinc-300">{label}</label>}
    <select className={`w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-orange-500 ${className}`} {...props}>
      {options.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
    </select>
  </div>
);

const Card = ({ children, className = "", ...props }) => (
  <div className={`bg-zinc-900 border border-zinc-800 rounded-2xl p-6 ${className}`} {...props}>{children}</div>
);

const Toast = ({ message, type = "success", onClose }) => {
  useEffect(() => { const t = setTimeout(onClose, 4000); return () => clearTimeout(t); }, [onClose]);
  return (
    <div className={`fixed bottom-6 right-6 flex items-center gap-3 px-6 py-4 rounded-xl shadow-xl z-50 animate-slide-up ${type === 'success' ? 'bg-green-500' : type === 'achievement' ? 'bg-purple-500' : 'bg-red-500'} text-white`}>
      {type === 'success' ? <CheckCircle className="w-5 h-5" /> : type === 'achievement' ? <Trophy className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
      <span>{message}</span>
    </div>
  );
};

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">{title}</h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        {children}
      </Card>
    </div>
  );
};

// ==================== REST TIMER COMPONENT ====================

const RestTimer = ({ duration, onComplete }) => {
  const [timeLeft, setTimeLeft] = useState(duration);
  const [isRunning, setIsRunning] = useState(true);

  useEffect(() => {
    if (!isRunning || timeLeft <= 0) {
      if (timeLeft <= 0) onComplete?.();
      return;
    }
    const timer = setInterval(() => setTimeLeft(t => t - 1), 1000);
    return () => clearInterval(timer);
  }, [isRunning, timeLeft, onComplete]);

  const reset = () => { setTimeLeft(duration); setIsRunning(true); };
  const progress = ((duration - timeLeft) / duration) * 100;

  return (
    <div className="bg-zinc-800 rounded-xl p-4 text-center">
      <div className="text-4xl font-bold text-orange-500 mb-2">{Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}</div>
      <div className="w-full bg-zinc-700 rounded-full h-2 mb-3">
        <div className="bg-orange-500 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
      </div>
      <div className="flex gap-2 justify-center">
        <button onClick={() => setIsRunning(!isRunning)} className="p-2 bg-zinc-700 rounded-lg hover:bg-zinc-600">
          {isRunning ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
        </button>
        <button onClick={reset} className="p-2 bg-zinc-700 rounded-lg hover:bg-zinc-600"><RotateCcw className="w-5 h-5" /></button>
      </div>
    </div>
  );
};

// ==================== AUTH PAGE ====================

const AuthPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: "", password: "", name: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const endpoint = isLogin ? "/auth/login" : "/auth/register";
      const payload = isLogin ? { email: formData.email, password: formData.password } : formData;
      const response = await axios.post(`${API}${endpoint}`, payload);
      onLogin(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img src={LOGO_URL} alt="MotivAction" className="h-32 mx-auto mb-4 drop-shadow-2xl" />
          <p className="text-zinc-400">Transform your fitness with AI-powered workouts</p>
        </div>
        <Card>
          <div className="flex mb-6 bg-zinc-800 rounded-xl p-1">
            <button onClick={() => setIsLogin(true)} className={`flex-1 py-3 rounded-lg font-medium transition-all ${isLogin ? 'bg-orange-500 text-white' : 'text-zinc-400 hover:text-white'}`}>Sign In</button>
            <button onClick={() => setIsLogin(false)} className={`flex-1 py-3 rounded-lg font-medium transition-all ${!isLogin ? 'bg-orange-500 text-white' : 'text-zinc-400 hover:text-white'}`}>Sign Up</button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && <Input label="Full Name" type="text" placeholder="John Doe" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required data-testid="register-name-input" />}
            <Input label="Email" type="email" placeholder="you@example.com" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required data-testid="auth-email-input" />
            <Input label="Password" type="password" placeholder="••••••••" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} required data-testid="auth-password-input" />
            {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400 text-sm">{error}</div>}
            <Button type="submit" loading={loading} className="w-full" data-testid="auth-submit-btn">{isLogin ? "Sign In" : "Create Account"}</Button>
          </form>
        </Card>
      </div>
    </div>
  );
};

// ==================== ONBOARDING ====================

const OnboardingPage = ({ onComplete }) => {
  const { token, refreshUser } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState({
    fitness_goal: "general_fitness", fitness_level: "beginner", body_type: "mesomorph",
    age: "", weight_kg: "", height_cm: "", available_equipment: [],
    workout_days_per_week: 3, workout_duration_minutes: 45, injuries_restrictions: "", dietary_restrictions: "",
  });

  const equipmentOptions = ["Dumbbells", "Barbell", "Kettlebells", "Pull-up Bar", "Resistance Bands", "Bench", "Cable Machine", "Treadmill", "Stationary Bike", "Rowing Machine"];
  const toggleEquipment = (item) => setProfileData(prev => ({ ...prev, available_equipment: prev.available_equipment.includes(item) ? prev.available_equipment.filter(e => e !== item) : [...prev.available_equipment, item] }));

  const handleComplete = async () => {
    setLoading(true);
    try {
      const api = createAuthApi(token);
      await api.put("/profile", { ...profileData, onboarding_complete: true, age: profileData.age ? parseInt(profileData.age) : null, weight_kg: profileData.weight_kg ? parseFloat(profileData.weight_kg) : null, height_cm: profileData.height_cm ? parseFloat(profileData.height_cm) : null });
      await refreshUser();
      onComplete();
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const steps = [
    { title: "What's your fitness goal?", icon: <Target className="w-8 h-8 text-white" />,
      content: (
        <div className="grid grid-cols-2 gap-4">
          {[{ value: "weight_loss", label: "Lose Weight", icon: "🔥" }, { value: "muscle_gain", label: "Build Muscle", icon: "💪" }, { value: "endurance", label: "Improve Endurance", icon: "🏃" }, { value: "general_fitness", label: "General Fitness", icon: "⚡" }].map(opt => (
            <button key={opt.value} onClick={() => setProfileData({ ...profileData, fitness_goal: opt.value })} className={`p-6 rounded-2xl border-2 transition-all text-left ${profileData.fitness_goal === opt.value ? 'border-orange-500 bg-orange-500/10' : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'}`}>
              <span className="text-3xl mb-3 block">{opt.icon}</span>
              <span className="text-white font-medium">{opt.label}</span>
            </button>
          ))}
        </div>
      )
    },
    { title: "Your fitness level?", icon: <Trophy className="w-8 h-8 text-white" />,
      content: (
        <div className="space-y-4">
          {[{ value: "beginner", label: "Beginner", desc: "New to working out" }, { value: "intermediate", label: "Intermediate", desc: "6+ months experience" }, { value: "advanced", label: "Advanced", desc: "Years of training" }].map(opt => (
            <button key={opt.value} onClick={() => setProfileData({ ...profileData, fitness_level: opt.value })} className={`w-full p-5 rounded-2xl border-2 transition-all text-left ${profileData.fitness_level === opt.value ? 'border-orange-500 bg-orange-500/10' : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'}`}>
              <span className="text-white font-semibold block mb-1">{opt.label}</span>
              <span className="text-zinc-400 text-sm">{opt.desc}</span>
            </button>
          ))}
        </div>
      )
    },
    { title: "What's your body type?", icon: <Scale className="w-8 h-8 text-white" />,
      content: (
        <div className="space-y-4">
          {[{ value: "ectomorph", label: "Ectomorph", desc: "Lean, fast metabolism", icon: "🏃‍♂️" }, { value: "mesomorph", label: "Mesomorph", desc: "Athletic, gains muscle easily", icon: "💪" }, { value: "endomorph", label: "Endomorph", desc: "Wider build, slower metabolism", icon: "🏋️" }].map(opt => (
            <button key={opt.value} onClick={() => setProfileData({ ...profileData, body_type: opt.value })} className={`w-full p-5 rounded-2xl border-2 transition-all text-left ${profileData.body_type === opt.value ? 'border-green-500 bg-green-500/10' : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'}`}>
              <div className="flex items-center gap-3"><span className="text-2xl">{opt.icon}</span><div><span className="text-white font-semibold block">{opt.label}</span><span className="text-zinc-400 text-sm">{opt.desc}</span></div></div>
            </button>
          ))}
        </div>
      )
    },
    { title: "Tell us about yourself", icon: <User className="w-8 h-8 text-white" />,
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Input label="Age" type="number" placeholder="25" value={profileData.age} onChange={(e) => setProfileData({ ...profileData, age: e.target.value })} />
            <Input label="Weight (kg)" type="number" placeholder="70" value={profileData.weight_kg} onChange={(e) => setProfileData({ ...profileData, weight_kg: e.target.value })} />
            <Input label="Height (cm)" type="number" placeholder="175" value={profileData.height_cm} onChange={(e) => setProfileData({ ...profileData, height_cm: e.target.value })} />
          </div>
          <Input label="Injuries or restrictions?" placeholder="e.g., Bad knee..." value={profileData.injuries_restrictions} onChange={(e) => setProfileData({ ...profileData, injuries_restrictions: e.target.value })} />
          <Input label="Dietary restrictions?" placeholder="e.g., Vegetarian..." value={profileData.dietary_restrictions} onChange={(e) => setProfileData({ ...profileData, dietary_restrictions: e.target.value })} />
        </div>
      )
    },
    { title: "Your workout setup", icon: <Dumbbell className="w-8 h-8 text-white" />,
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {equipmentOptions.map(item => (
              <button key={item} onClick={() => toggleEquipment(item)} className={`p-4 rounded-xl border transition-all text-sm font-medium ${profileData.available_equipment.includes(item) ? 'border-orange-500 bg-orange-500/20 text-orange-400' : 'border-zinc-700 bg-zinc-800/50 text-zinc-300 hover:border-zinc-600'}`}>{item}</button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Days/week" value={profileData.workout_days_per_week} onChange={(e) => setProfileData({ ...profileData, workout_days_per_week: parseInt(e.target.value) })} options={[2,3,4,5,6].map(n => ({ value: n, label: `${n} days` }))} />
            <Select label="Duration" value={profileData.workout_duration_minutes} onChange={(e) => setProfileData({ ...profileData, workout_duration_minutes: parseInt(e.target.value) })} options={[30,45,60,75,90].map(n => ({ value: n, label: `${n} min` }))} />
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="flex gap-2 mb-8">{[1,2,3,4,5].map(s => <div key={s} className={`h-2 flex-1 rounded-full transition-all ${s <= step ? 'bg-orange-500' : 'bg-zinc-800'}`} />)}</div>
        <Card className="mb-6">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">{steps[step-1].icon}</div>
            <h2 className="text-2xl font-bold text-white mb-2">{steps[step-1].title}</h2>
          </div>
          {steps[step-1].content}
        </Card>
        <div className="flex gap-4">
          {step > 1 && <Button variant="secondary" onClick={() => setStep(s => s - 1)} className="flex-1">Back</Button>}
          {step < 5 ? <Button onClick={() => setStep(s => s + 1)} className="flex-1">Continue <ChevronRight className="w-5 h-5" /></Button>
            : <Button onClick={handleComplete} loading={loading} className="flex-1">Get Started <Zap className="w-5 h-5" /></Button>}
        </div>
      </div>
    </div>
  );
};

// ==================== MAIN DASHBOARD ====================

const Dashboard = () => {
  const { user, token, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("workout");
  const [activePlan, setActivePlan] = useState(null);
  const [nutritionPlan, setNutritionPlan] = useState(null);
  const [stats, setStats] = useState(null);
  const [progress, setProgress] = useState([]);
  const [workoutLogs, setWorkoutLogs] = useState([]);
  const [personalRecords, setPersonalRecords] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [groceryList, setGroceryList] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatingNutrition, setGeneratingNutrition] = useState(false);
  const [selectedDay, setSelectedDay] = useState(0);
  const [selectedNutritionDay, setSelectedNutritionDay] = useState(0);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [toast, setToast] = useState(null);
  const [showNewPlanModal, setShowNewPlanModal] = useState(false);
  const [showNewNutritionModal, setShowNewNutritionModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [showWorkoutLogger, setShowWorkoutLogger] = useState(false);
  const [showRestTimer, setShowRestTimer] = useState(false);
  const [restDuration, setRestDuration] = useState(60);
  const [customInstructions, setCustomInstructions] = useState("");
  const [nutritionBodyType, setNutritionBodyType] = useState(user.body_type || "mesomorph");
  const [progressForm, setProgressForm] = useState({ date: new Date().toISOString().split('T')[0], weight_kg: "", body_fat_percent: "", notes: "" });
  const [workoutLogForm, setWorkoutLogForm] = useState({ exercises: [] });

  const api = createAuthApi(token);

  const fetchData = useCallback(async () => {
    try {
      const [activePlanRes, nutritionPlanRes, statsRes, progressRes, logsRes, prsRes, leaderboardRes, challengesRes] = await Promise.all([
        api.get("/workout-plans/active").catch(() => ({ data: null })),
        api.get("/nutrition-plans/active").catch(() => ({ data: null })),
        api.get("/stats").catch(() => ({ data: null })),
        api.get("/progress").catch(() => ({ data: [] })),
        api.get("/workout-logs").catch(() => ({ data: [] })),
        api.get("/personal-records").catch(() => ({ data: [] })),
        api.get("/leaderboard").catch(() => ({ data: [] })),
        api.get("/daily-challenges").catch(() => ({ data: [] })),
      ]);
      setActivePlan(activePlanRes.data);
      setNutritionPlan(nutritionPlanRes.data);
      setStats(statsRes.data);
      setProgress(progressRes.data || []);
      setWorkoutLogs(logsRes.data || []);
      setPersonalRecords(prsRes.data || []);
      setLeaderboard(leaderboardRes.data || []);
      setChallenges(challengesRes.data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const generateNewPlan = async () => {
    setGenerating(true);
    setShowNewPlanModal(false);
    try {
      const response = await api.post("/workout-plans/generate", { custom_instructions: customInstructions || null });
      setActivePlan(response.data);
      setToast({ message: "New workout plan generated! 💪", type: "success" });
      setCustomInstructions("");
    } catch (err) { setToast({ message: "Failed to generate plan", type: "error" }); }
    finally { setGenerating(false); }
  };

  const generateNutritionPlan = async () => {
    setGeneratingNutrition(true);
    setShowNewNutritionModal(false);
    try {
      const response = await api.post("/nutrition-plans/generate", { body_type: nutritionBodyType, dietary_restrictions: user.dietary_restrictions, custom_instructions: customInstructions || null });
      setNutritionPlan(response.data);
      setToast({ message: "New nutrition plan generated! 🥗", type: "success" });
      setCustomInstructions("");
    } catch (err) { setToast({ message: "Failed to generate nutrition plan", type: "error" }); }
    finally { setGeneratingNutrition(false); }
  };

  const logProgress = async () => {
    try {
      await api.post("/progress", progressForm);
      setToast({ message: "Progress logged! 📊", type: "success" });
      setShowProgressModal(false);
      setProgressForm({ date: new Date().toISOString().split('T')[0], weight_kg: "", body_fat_percent: "", notes: "" });
      fetchData();
    } catch (err) { setToast({ message: "Failed to log progress", type: "error" }); }
  };

  const logWorkout = async () => {
    if (!activePlan) return;
    try {
      await api.post("/workout-logs", {
        workout_plan_id: activePlan.id,
        day_index: selectedDay,
        date: new Date().toISOString().split('T')[0],
        exercises: workoutLogForm.exercises,
        duration_minutes: activePlan.workout_days[selectedDay]?.estimated_duration_minutes || 45
      });
      setToast({ message: "Workout logged! Great job! 🎉", type: "success" });
      setShowWorkoutLogger(false);
      fetchData();
    } catch (err) { setToast({ message: "Failed to log workout", type: "error" }); }
  };

  const generateGroceryList = async () => {
    if (!nutritionPlan) return;
    try {
      const response = await api.post(`/grocery-list/generate?nutrition_plan_id=${nutritionPlan.id}`);
      setGroceryList(response.data);
      setToast({ message: "Grocery list generated! 🛒", type: "success" });
    } catch (err) { setToast({ message: "Failed to generate grocery list", type: "error" }); }
  };

  const swapMeal = async (dayIndex, mealIndex) => {
    if (!nutritionPlan) return;
    try {
      const response = await api.post(`/nutrition-plans/${nutritionPlan.id}/swap-meal?day_index=${dayIndex}&meal_index=${mealIndex}`);
      const updatedMealPlans = [...nutritionPlan.meal_plans];
      updatedMealPlans[dayIndex].meals[mealIndex] = response.data;
      setNutritionPlan({ ...nutritionPlan, meal_plans: updatedMealPlans });
      setToast({ message: "Meal swapped! 🔄", type: "success" });
    } catch (err) { setToast({ message: "Failed to swap meal", type: "error" }); }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-orange-500 animate-spin mx-auto mb-4" />
          <p className="text-zinc-400">Loading your fitness journey...</p>
        </div>
      </div>
    );
  }

  const currentWorkout = activePlan?.workout_days?.[selectedDay];
  const currentMealDay = nutritionPlan?.meal_plans?.[selectedNutritionDay];

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-zinc-950/95 backdrop-blur border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={LOGO_URL} alt="MotivAction" className="h-12" />
          </div>
          
          {/* Stats Bar */}
          {stats && (
            <div className="hidden lg:flex items-center gap-6">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
                  <Star className="w-4 h-4 text-purple-400" />
                </div>
                <div><div className="text-white font-bold">Lvl {stats.level}</div><div className="text-zinc-500 text-xs">{stats.xp} XP</div></div>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-8 h-8 bg-orange-500/20 rounded-lg flex items-center justify-center">
                  <Flame className="w-4 h-4 text-orange-400" />
                </div>
                <div><div className="text-white font-bold">{stats.current_streak}</div><div className="text-zinc-500 text-xs">Streak</div></div>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <Dumbbell className="w-4 h-4 text-green-400" />
                </div>
                <div><div className="text-white font-bold">{stats.total_workouts}</div><div className="text-zinc-500 text-xs">Workouts</div></div>
              </div>
            </div>
          )}
          
          <div className="flex items-center gap-3">
            <button onClick={() => setShowMobileMenu(!showMobileMenu)} className="md:hidden p-2 text-zinc-400 hover:text-white">
              {showMobileMenu ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <div className="hidden md:flex items-center gap-3">
              <span className="text-zinc-300 font-medium">{user.name}</span>
              <Button variant="ghost" size="sm" onClick={logout}><LogOut className="w-4 h-4" /></Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Navigation Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {[
            { id: "workout", label: "Workouts", icon: <Dumbbell className="w-4 h-4" />, color: "orange" },
            { id: "nutrition", label: "Nutrition", icon: <Utensils className="w-4 h-4" />, color: "green" },
            { id: "progress", label: "Progress", icon: <BarChart3 className="w-4 h-4" />, color: "blue" },
            { id: "achievements", label: "Achievements", icon: <Trophy className="w-4 h-4" />, color: "purple" },
            { id: "calendar", label: "Calendar", icon: <Calendar className="w-4 h-4" />, color: "pink" },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all whitespace-nowrap ${activeTab === tab.id ? `bg-${tab.color}-500 text-white` : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}`} style={activeTab === tab.id ? { background: tab.color === 'orange' ? 'linear-gradient(to right, #f97316, #ef4444)' : tab.color === 'green' ? 'linear-gradient(to right, #22c55e, #10b981)' : tab.color === 'blue' ? 'linear-gradient(to right, #3b82f6, #6366f1)' : tab.color === 'purple' ? 'linear-gradient(to right, #a855f7, #ec4899)' : 'linear-gradient(to right, #ec4899, #f43f5e)' } : {}}>
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* WORKOUT TAB */}
        {activeTab === "workout" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white">{activePlan ? `Today's Workout` : 'Get Started'}</h1>
                <p className="text-zinc-400">{activePlan?.description || "Generate your personalized workout plan"}</p>
              </div>
              <div className="flex gap-2">
                {activePlan && <Button variant="purple" size="sm" onClick={() => { setWorkoutLogForm({ exercises: currentWorkout?.exercises.map(e => ({ exercise_name: e.name, sets_completed: e.sets, reps_completed: e.reps, weight_used: 0, notes: "" })) || [] }); setShowWorkoutLogger(true); }}><CheckCircle className="w-4 h-4" /> Log Workout</Button>}
                <Button onClick={() => setShowNewPlanModal(true)} disabled={generating} size="sm">{generating ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Plus className="w-4 h-4" /> New Plan</>}</Button>
              </div>
            </div>

            {!activePlan ? (
              <Card className="text-center py-16">
                <div className="w-20 h-20 bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-3xl flex items-center justify-center mx-auto mb-6"><Dumbbell className="w-10 h-10 text-orange-500" /></div>
                <h2 className="text-2xl font-bold text-white mb-3">Ready to Transform?</h2>
                <p className="text-zinc-400 max-w-md mx-auto mb-8">Our AI creates personalized workout plans based on your goals and equipment.</p>
                <Button onClick={() => setShowNewPlanModal(true)} size="lg"><Zap className="w-5 h-5" /> Generate My Plan</Button>
              </Card>
            ) : (
              <div className="grid lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <Card>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-lg font-bold text-white">{activePlan.plan_name}</h2>
                      <div className="flex items-center gap-2">
                        <button onClick={() => { setRestDuration(60); setShowRestTimer(true); }} className="p-2 bg-zinc-800 rounded-lg hover:bg-zinc-700"><Timer className="w-5 h-5 text-orange-400" /></button>
                      </div>
                    </div>
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {activePlan.workout_days.map((day, idx) => (
                        <button key={idx} onClick={() => setSelectedDay(idx)} className={`flex-shrink-0 px-4 py-3 rounded-xl transition-all ${selectedDay === idx ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}`}>
                          <div className="text-xs opacity-75">Day {idx + 1}</div>
                          <div className="font-semibold text-sm">{day.workout_type}</div>
                        </button>
                      ))}
                    </div>
                  </Card>

                  {currentWorkout && (
                    <Card>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-white">{currentWorkout.day}</h3>
                        <span className="text-zinc-400 text-sm flex items-center gap-1"><Clock className="w-4 h-4" />{currentWorkout.estimated_duration_minutes} min</span>
                      </div>
                      <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-4 mb-4">
                        <div className="flex items-center gap-2 text-orange-400 font-medium mb-1"><Flame className="w-4 h-4" /> Warm-up</div>
                        <p className="text-zinc-300 text-sm">{currentWorkout.warmup_notes}</p>
                      </div>
                      <div className="space-y-4">
                        {currentWorkout.exercises.map((exercise, idx) => (
                          <div key={idx} className="bg-zinc-800/50 rounded-xl overflow-hidden border border-zinc-700/50">
                            {exercise.image_url && <div className="h-32 overflow-hidden"><img src={exercise.image_url} alt={exercise.name} className="w-full h-full object-cover" loading="lazy" /></div>}
                            <div className="p-4">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <h4 className="text-white font-semibold">{exercise.name}</h4>
                                  <span className="text-xs text-orange-400 bg-orange-500/10 px-2 py-1 rounded-full">{exercise.muscle_group}</span>
                                </div>
                                <div className="text-right">
                                  <div className="text-white font-medium">{exercise.sets} × {exercise.reps}</div>
                                  <button onClick={() => { setRestDuration(exercise.rest_seconds); setShowRestTimer(true); }} className="text-zinc-500 text-sm hover:text-orange-400">{exercise.rest_seconds}s rest</button>
                                </div>
                              </div>
                              {exercise.notes && <p className="text-zinc-400 text-sm mt-2 pt-2 border-t border-zinc-700/50">💡 {exercise.notes}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mt-4">
                        <div className="flex items-center gap-2 text-blue-400 font-medium mb-1"><CheckCircle className="w-4 h-4" /> Cool-down</div>
                        <p className="text-zinc-300 text-sm">{currentWorkout.cooldown_notes}</p>
                      </div>
                    </Card>
                  )}
                </div>

                <div className="space-y-6">
                  {showRestTimer && (
                    <Card>
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Timer className="w-5 h-5 text-orange-500" /> Rest Timer</h3>
                      <RestTimer duration={restDuration} onComplete={() => setToast({ message: "Rest complete! Time for next set! 💪", type: "success" })} />
                      <button onClick={() => setShowRestTimer(false)} className="w-full mt-3 text-zinc-400 hover:text-white text-sm">Close Timer</button>
                    </Card>
                  )}
                  
                  {personalRecords.length > 0 && (
                    <Card>
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-green-500" /> Personal Records</h3>
                      <div className="space-y-3">
                        {personalRecords.slice(0, 5).map((pr, idx) => (
                          <div key={idx} className="flex items-center justify-between bg-zinc-800/50 rounded-lg p-3">
                            <span className="text-zinc-300 text-sm">{pr.exercise_name}</span>
                            <span className="text-green-400 font-bold">{pr.weight_kg}kg × {pr.reps}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}

                  <Card>
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Zap className="w-5 h-5 text-orange-500" /> Pro Tips</h3>
                    <div className="space-y-3">
                      {activePlan?.tips?.slice(0, 3).map((tip, idx) => (
                        <div key={idx} className="flex items-start gap-3">
                          <span className="w-6 h-6 bg-orange-500/10 text-orange-500 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium">{idx + 1}</span>
                          <p className="text-zinc-300 text-sm">{tip}</p>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              </div>
            )}
          </div>
        )}

        {/* NUTRITION TAB */}
        {activeTab === "nutrition" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white">{nutritionPlan ? 'Your Meal Plan' : 'Nutrition Plan'}</h1>
                <p className="text-zinc-400">{nutritionPlan?.description || "Generate your personalized nutrition plan"}</p>
              </div>
              <div className="flex gap-2">
                {nutritionPlan && <Button variant="secondary" size="sm" onClick={generateGroceryList}><ShoppingCart className="w-4 h-4" /> Grocery List</Button>}
                <Button variant="green" onClick={() => setShowNewNutritionModal(true)} disabled={generatingNutrition} size="sm">{generatingNutrition ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Plus className="w-4 h-4" /> New Plan</>}</Button>
              </div>
            </div>

            {!nutritionPlan ? (
              <Card className="text-center py-16">
                <div className="w-20 h-20 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-3xl flex items-center justify-center mx-auto mb-6"><Apple className="w-10 h-10 text-green-500" /></div>
                <h2 className="text-2xl font-bold text-white mb-3">Fuel Your Goals</h2>
                <p className="text-zinc-400 max-w-md mx-auto mb-8">Get a personalized meal plan based on your body type and fitness goals.</p>
                <Button onClick={() => setShowNewNutritionModal(true)} size="lg" variant="green"><Zap className="w-5 h-5" /> Generate Nutrition Plan</Button>
              </Card>
            ) : (
              <div className="grid lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <Card>
                    <div className="flex items-start justify-between mb-4">
                      <h2 className="text-lg font-bold text-white">{nutritionPlan.plan_name}</h2>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-green-400">{nutritionPlan.daily_calories}</div>
                        <div className="text-zinc-500 text-xs">cal/day</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="bg-blue-500/10 rounded-xl p-3 text-center"><div className="text-blue-400 text-xl font-bold">{nutritionPlan.protein_target_g}g</div><div className="text-zinc-400 text-xs">Protein</div></div>
                      <div className="bg-yellow-500/10 rounded-xl p-3 text-center"><div className="text-yellow-400 text-xl font-bold">{nutritionPlan.carbs_target_g}g</div><div className="text-zinc-400 text-xs">Carbs</div></div>
                      <div className="bg-pink-500/10 rounded-xl p-3 text-center"><div className="text-pink-400 text-xl font-bold">{nutritionPlan.fat_target_g}g</div><div className="text-zinc-400 text-xs">Fat</div></div>
                    </div>
                    <div className="flex gap-2 overflow-x-auto">
                      {nutritionPlan.meal_plans.map((day, idx) => (
                        <button key={idx} onClick={() => setSelectedNutritionDay(idx)} className={`flex-shrink-0 px-4 py-2 rounded-xl transition-all ${selectedNutritionDay === idx ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}`}>{day.day}</button>
                      ))}
                    </div>
                  </Card>

                  {currentMealDay && (
                    <Card>
                      <h3 className="text-lg font-bold text-white mb-4">{currentMealDay.day} Meals</h3>
                      <div className="space-y-4">
                        {currentMealDay.meals.map((meal, idx) => (
                          <div key={idx} className="bg-zinc-800/50 rounded-xl overflow-hidden border border-zinc-700/50">
                            {meal.image_url && <div className="h-36 overflow-hidden"><img src={meal.image_url} alt={meal.name} className="w-full h-full object-cover" loading="lazy" /></div>}
                            <div className="p-4">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <span className="text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded-full">{meal.time}</span>
                                  <h4 className="text-white font-semibold mt-2">{meal.name}</h4>
                                </div>
                                <div className="text-right">
                                  <div className="text-white font-medium">{meal.calories} cal</div>
                                  <button onClick={() => swapMeal(selectedNutritionDay, idx)} className="text-green-400 text-xs hover:underline">🔄 Swap</button>
                                </div>
                              </div>
                              <div className="text-zinc-500 text-xs mb-2">P: {meal.protein_g}g • C: {meal.carbs_g}g • F: {meal.fat_g}g</div>
                              <div className="text-zinc-400 text-sm"><strong>Ingredients:</strong> {meal.ingredients.join(", ")}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                      {currentMealDay.snacks?.length > 0 && (
                        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 mt-4">
                          <div className="text-green-400 font-medium mb-2">🍎 Snack Options</div>
                          <ul className="text-zinc-300 text-sm list-disc list-inside">{currentMealDay.snacks.map((s, i) => <li key={i}>{s}</li>)}</ul>
                        </div>
                      )}
                    </Card>
                  )}
                </div>

                <div className="space-y-6">
                  {groceryList && (
                    <Card>
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><ShoppingCart className="w-5 h-5 text-green-500" /> Grocery List</h3>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {groceryList.items?.map((item, idx) => (
                          <div key={idx} className={`flex items-center gap-2 p-2 rounded-lg ${item.checked ? 'bg-green-500/10' : 'bg-zinc-800/50'}`}>
                            <input type="checkbox" checked={item.checked} onChange={() => {}} className="rounded" />
                            <span className={`text-sm ${item.checked ? 'text-zinc-500 line-through' : 'text-zinc-300'}`}>{item.name}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}

                  <Card>
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><CheckCircle className="w-5 h-5 text-green-500" /> Foods to Include</h3>
                    <div className="flex flex-wrap gap-2">{nutritionPlan?.foods_to_include?.map((f, i) => <span key={i} className="bg-green-500/10 text-green-400 px-3 py-1 rounded-full text-sm">{f}</span>)}</div>
                  </Card>

                  <Card>
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><AlertCircle className="w-5 h-5 text-red-500" /> Foods to Avoid</h3>
                    <div className="flex flex-wrap gap-2">{nutritionPlan?.foods_to_avoid?.map((f, i) => <span key={i} className="bg-red-500/10 text-red-400 px-3 py-1 rounded-full text-sm">{f}</span>)}</div>
                  </Card>
                </div>
              </div>
            )}
          </div>
        )}

        {/* PROGRESS TAB */}
        {activeTab === "progress" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div><h1 className="text-2xl font-bold text-white">Progress Tracking</h1><p className="text-zinc-400">Monitor your fitness journey</p></div>
              <Button onClick={() => setShowProgressModal(true)} size="sm"><Plus className="w-4 h-4" /> Log Progress</Button>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border-orange-500/20">
                <div className="text-zinc-400 text-sm mb-1">Total Workouts</div>
                <div className="text-3xl font-bold text-white">{stats?.total_workouts || 0}</div>
              </Card>
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
                <div className="text-zinc-400 text-sm mb-1">Current Streak</div>
                <div className="text-3xl font-bold text-white flex items-center gap-2">{stats?.current_streak || 0} <Flame className="w-6 h-6 text-orange-500" /></div>
              </Card>
              <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
                <div className="text-zinc-400 text-sm mb-1">Longest Streak</div>
                <div className="text-3xl font-bold text-white">{stats?.longest_streak || 0}</div>
              </Card>
              <Card className="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border-blue-500/20">
                <div className="text-zinc-400 text-sm mb-1">Level</div>
                <div className="text-3xl font-bold text-white">{stats?.level || 1}</div>
                <div className="text-xs text-zinc-500">{stats?.xp || 0} / {(stats?.xp || 0) + (stats?.xp_to_next_level || 100)} XP</div>
              </Card>
            </div>

            {progress.length > 0 && (
              <Card>
                <h3 className="text-lg font-bold text-white mb-4">Weight Progress</h3>
                <div className="space-y-3">
                  {progress.slice(0, 10).map((entry, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-zinc-800/50 rounded-lg p-3">
                      <span className="text-zinc-400 text-sm">{entry.date}</span>
                      <div className="flex items-center gap-4">
                        {entry.weight_kg && <span className="text-white font-medium">{entry.weight_kg} kg</span>}
                        {entry.body_fat_percent && <span className="text-zinc-400">{entry.body_fat_percent}% BF</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {workoutLogs.length > 0 && (
              <Card>
                <h3 className="text-lg font-bold text-white mb-4">Recent Workouts</h3>
                <div className="space-y-3">
                  {workoutLogs.slice(0, 5).map((log, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-zinc-800/50 rounded-lg p-3">
                      <div><div className="text-white font-medium">Day {log.day_index + 1}</div><div className="text-zinc-500 text-xs">{log.date}</div></div>
                      <div className="text-green-400 flex items-center gap-1"><CheckCircle className="w-4 h-4" /> {log.duration_minutes} min</div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}

        {/* ACHIEVEMENTS TAB */}
        {activeTab === "achievements" && (
          <div className="space-y-6">
            <div><h1 className="text-2xl font-bold text-white">Achievements & Leaderboard</h1><p className="text-zinc-400">Your accomplishments and rankings</p></div>

            {/* Daily Challenges */}
            <Card>
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Target className="w-5 h-5 text-orange-500" /> Daily Challenges</h3>
              <div className="grid md:grid-cols-3 gap-4">
                {challenges.map((challenge, idx) => (
                  <div key={idx} className={`p-4 rounded-xl border ${challenge.completed ? 'bg-green-500/10 border-green-500/30' : 'bg-zinc-800/50 border-zinc-700'}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">{challenge.name}</span>
                      <span className="text-yellow-400 text-sm">+{challenge.xp_reward} XP</span>
                    </div>
                    <p className="text-zinc-400 text-sm mb-2">{challenge.description}</p>
                    <div className="w-full bg-zinc-700 rounded-full h-2">
                      <div className={`h-2 rounded-full ${challenge.completed ? 'bg-green-500' : 'bg-orange-500'}`} style={{ width: `${(challenge.current / challenge.target) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Achievements */}
            <Card>
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Award className="w-5 h-5 text-purple-500" /> Achievements</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {stats?.achievements?.map((ach, idx) => (
                  <div key={idx} className={`p-4 rounded-xl text-center ${ach.unlocked ? 'bg-purple-500/10 border border-purple-500/30' : 'bg-zinc-800/30 opacity-50'}`}>
                    <div className="text-3xl mb-2">{ach.icon}</div>
                    <div className="text-white font-medium text-sm">{ach.name}</div>
                    <div className="text-zinc-500 text-xs">{ach.description}</div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Leaderboard */}
            <Card>
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Trophy className="w-5 h-5 text-yellow-500" /> Leaderboard</h3>
              <div className="space-y-3">
                {leaderboard.slice(0, 10).map((entry, idx) => (
                  <div key={idx} className={`flex items-center justify-between p-3 rounded-xl ${entry.user_id === user.id ? 'bg-orange-500/10 border border-orange-500/30' : 'bg-zinc-800/50'}`}>
                    <div className="flex items-center gap-3">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${idx === 0 ? 'bg-yellow-500 text-black' : idx === 1 ? 'bg-zinc-400 text-black' : idx === 2 ? 'bg-amber-600 text-white' : 'bg-zinc-700 text-white'}`}>{entry.rank}</span>
                      <div><div className="text-white font-medium">{entry.user_name}</div><div className="text-zinc-500 text-xs">Level {entry.level}</div></div>
                    </div>
                    <div className="text-right">
                      <div className="text-purple-400 font-bold">{entry.xp} XP</div>
                      <div className="text-zinc-500 text-xs flex items-center gap-1"><Flame className="w-3 h-3 text-orange-400" />{entry.streak}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* CALENDAR TAB */}
        {activeTab === "calendar" && (
          <div className="space-y-6">
            <div><h1 className="text-2xl font-bold text-white">Workout Calendar</h1><p className="text-zinc-400">Plan and track your workout schedule</p></div>
            <Card>
              <div className="text-center py-12">
                <Calendar className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">Calendar View Coming Soon</h3>
                <p className="text-zinc-400">Schedule your workouts and see your progress over time</p>
              </div>
            </Card>
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <h3 className="text-lg font-bold text-white mb-4">This Week</h3>
                <div className="space-y-2">
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                      <span className="text-zinc-300">{day}</span>
                      {workoutLogs.some(l => new Date(l.date).getDay() === (idx + 1) % 7) 
                        ? <CheckCircle className="w-5 h-5 text-green-500" /> 
                        : <div className="w-5 h-5 border-2 border-zinc-600 rounded-full" />}
                    </div>
                  ))}
                </div>
              </Card>
              <Card>
                <h3 className="text-lg font-bold text-white mb-4">Quick Stats</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between"><span className="text-zinc-400">This Week</span><span className="text-white font-bold">{workoutLogs.filter(l => { const d = new Date(l.date); const now = new Date(); const weekAgo = new Date(now.setDate(now.getDate() - 7)); return d >= weekAgo; }).length} workouts</span></div>
                  <div className="flex items-center justify-between"><span className="text-zinc-400">This Month</span><span className="text-white font-bold">{workoutLogs.filter(l => { const d = new Date(l.date); const now = new Date(); return d.getMonth() === now.getMonth(); }).length} workouts</span></div>
                  <div className="flex items-center justify-between"><span className="text-zinc-400">Best Streak</span><span className="text-white font-bold">{stats?.longest_streak || 0} days</span></div>
                </div>
              </Card>
            </div>
          </div>
        )}
      </main>

      {/* MODALS */}
      <Modal isOpen={showNewPlanModal} onClose={() => setShowNewPlanModal(false)} title="Generate New Workout Plan">
        <p className="text-zinc-400 text-sm mb-4">Add custom instructions for your AI coach (optional).</p>
        <textarea value={customInstructions} onChange={(e) => setCustomInstructions(e.target.value)} placeholder="e.g., Focus on upper body, avoid jumping..." className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 resize-none h-24 mb-4" />
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setShowNewPlanModal(false)} className="flex-1">Cancel</Button>
          <Button onClick={generateNewPlan} className="flex-1"><Zap className="w-4 h-4" /> Generate</Button>
        </div>
      </Modal>

      <Modal isOpen={showNewNutritionModal} onClose={() => setShowNewNutritionModal(false)} title="Generate Nutrition Plan">
        <Select label="Body Type" value={nutritionBodyType} onChange={(e) => setNutritionBodyType(e.target.value)} options={[{ value: "ectomorph", label: "Ectomorph - Fast metabolism" }, { value: "mesomorph", label: "Mesomorph - Athletic build" }, { value: "endomorph", label: "Endomorph - Slower metabolism" }]} className="mb-4" />
        <textarea value={customInstructions} onChange={(e) => setCustomInstructions(e.target.value)} placeholder="e.g., High protein, avoid dairy..." className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 resize-none h-24 mb-4" />
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setShowNewNutritionModal(false)} className="flex-1">Cancel</Button>
          <Button onClick={generateNutritionPlan} variant="green" className="flex-1"><Zap className="w-4 h-4" /> Generate</Button>
        </div>
      </Modal>

      <Modal isOpen={showProgressModal} onClose={() => setShowProgressModal(false)} title="Log Progress">
        <div className="space-y-4 mb-4">
          <Input label="Date" type="date" value={progressForm.date} onChange={(e) => setProgressForm({ ...progressForm, date: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Weight (kg)" type="number" placeholder="70" value={progressForm.weight_kg} onChange={(e) => setProgressForm({ ...progressForm, weight_kg: e.target.value })} />
            <Input label="Body Fat %" type="number" placeholder="15" value={progressForm.body_fat_percent} onChange={(e) => setProgressForm({ ...progressForm, body_fat_percent: e.target.value })} />
          </div>
          <Input label="Notes" placeholder="How are you feeling?" value={progressForm.notes} onChange={(e) => setProgressForm({ ...progressForm, notes: e.target.value })} />
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setShowProgressModal(false)} className="flex-1">Cancel</Button>
          <Button onClick={logProgress} variant="purple" className="flex-1"><CheckCircle className="w-4 h-4" /> Save</Button>
        </div>
      </Modal>

      <Modal isOpen={showWorkoutLogger} onClose={() => setShowWorkoutLogger(false)} title="Log Workout">
        <p className="text-zinc-400 text-sm mb-4">Log your completed workout for today.</p>
        {currentWorkout && (
          <div className="space-y-3 max-h-64 overflow-y-auto mb-4">
            {currentWorkout.exercises.map((ex, idx) => (
              <div key={idx} className="bg-zinc-800/50 rounded-lg p-3">
                <div className="text-white font-medium mb-2">{ex.name}</div>
                <div className="grid grid-cols-3 gap-2">
                  <Input placeholder="Sets" type="number" value={workoutLogForm.exercises[idx]?.sets_completed || ex.sets} onChange={(e) => { const updated = [...workoutLogForm.exercises]; updated[idx] = { ...updated[idx], sets_completed: parseInt(e.target.value) }; setWorkoutLogForm({ ...workoutLogForm, exercises: updated }); }} />
                  <Input placeholder="Reps" value={workoutLogForm.exercises[idx]?.reps_completed || ex.reps} onChange={(e) => { const updated = [...workoutLogForm.exercises]; updated[idx] = { ...updated[idx], reps_completed: e.target.value }; setWorkoutLogForm({ ...workoutLogForm, exercises: updated }); }} />
                  <Input placeholder="kg" type="number" value={workoutLogForm.exercises[idx]?.weight_used || ""} onChange={(e) => { const updated = [...workoutLogForm.exercises]; updated[idx] = { ...updated[idx], weight_used: parseFloat(e.target.value) }; setWorkoutLogForm({ ...workoutLogForm, exercises: updated }); }} />
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setShowWorkoutLogger(false)} className="flex-1">Cancel</Button>
          <Button onClick={logWorkout} variant="green" className="flex-1"><CheckCircle className="w-4 h-4" /> Complete</Button>
        </div>
      </Modal>

      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};

// ==================== MAIN APP ====================

function App() {
  const [authState, setAuthState] = useState(() => {
    const token = localStorage.getItem("motivaction_token");
    const user = localStorage.getItem("motivaction_user");
    if (token && user) return { token, user: JSON.parse(user), loading: false };
    return { user: null, token: null, loading: false };
  });

  const handleLogin = (data) => {
    localStorage.setItem("motivaction_token", data.access_token);
    localStorage.setItem("motivaction_user", JSON.stringify(data.user));
    setAuthState({ token: data.access_token, user: data.user, loading: false });
  };

  const handleLogout = () => {
    localStorage.removeItem("motivaction_token");
    localStorage.removeItem("motivaction_user");
    setAuthState({ user: null, token: null, loading: false });
  };

  const refreshUser = async () => {
    if (!authState.token) return;
    try {
      const api = createAuthApi(authState.token);
      const response = await api.get("/auth/me");
      localStorage.setItem("motivaction_user", JSON.stringify(response.data));
      setAuthState(prev => ({ ...prev, user: response.data }));
    } catch (err) { console.error(err); }
  };

  if (authState.loading) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center"><Loader2 className="w-10 h-10 text-orange-500 animate-spin" /></div>;
  if (!authState.user) return <AuthPage onLogin={handleLogin} />;

  return (
    <AuthContext.Provider value={{ user: authState.user, token: authState.token, logout: handleLogout, refreshUser }}>
      {!authState.user.onboarding_complete ? <OnboardingPage onComplete={refreshUser} /> : <Dashboard />}
    </AuthContext.Provider>
  );
}

export default App;
