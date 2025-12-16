import { useState, useEffect, createContext, useContext, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Dumbbell, Zap, Target, Clock, Calendar, ChevronRight, LogOut, User, Plus, Loader2, CheckCircle, AlertCircle, Menu, X, Flame, Trophy } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};

// API helper with auth
const createAuthApi = (token) => {
  const instance = axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return instance;
};

// ==================== COMPONENTS ====================

const Button = ({ children, variant = "primary", size = "md", disabled, loading, className = "", ...props }) => {
  const baseClasses = "font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white shadow-lg shadow-orange-500/25",
    secondary: "bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700",
    ghost: "bg-transparent hover:bg-zinc-800 text-zinc-300",
    outline: "border-2 border-orange-500 text-orange-500 hover:bg-orange-500 hover:text-white",
  };
  const sizes = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg",
  };
  
  return (
    <button 
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`} 
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="w-5 h-5 animate-spin" />}
      {children}
    </button>
  );
};

const Input = ({ label, error, className = "", ...props }) => (
  <div className="space-y-2">
    {label && <label className="block text-sm font-medium text-zinc-300">{label}</label>}
    <input
      className={`w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all ${error ? 'border-red-500' : ''} ${className}`}
      {...props}
    />
    {error && <p className="text-sm text-red-500">{error}</p>}
  </div>
);

const Select = ({ label, options, error, className = "", ...props }) => (
  <div className="space-y-2">
    {label && <label className="block text-sm font-medium text-zinc-300">{label}</label>}
    <select
      className={`w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all ${className}`}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
    {error && <p className="text-sm text-red-500">{error}</p>}
  </div>
);

const Card = ({ children, className = "", ...props }) => (
  <div className={`bg-zinc-900 border border-zinc-800 rounded-2xl p-6 ${className}`} {...props}>
    {children}
  </div>
);

const Toast = ({ message, type = "success", onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`fixed bottom-6 right-6 flex items-center gap-3 px-6 py-4 rounded-xl shadow-xl z-50 animate-slide-up ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white`}>
      {type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
      <span>{message}</span>
    </div>
  );
};

// ==================== AUTH PAGES ====================

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
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center shadow-lg shadow-orange-500/30">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <span className="text-3xl font-bold text-white">MotivAction</span>
          </div>
          <p className="text-zinc-400">Transform your fitness with AI-powered workouts</p>
        </div>

        <Card>
          <div className="flex mb-6 bg-zinc-800 rounded-xl p-1">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-3 rounded-lg font-medium transition-all ${isLogin ? 'bg-orange-500 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 rounded-lg font-medium transition-all ${!isLogin ? 'bg-orange-500 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <Input
                label="Full Name"
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                data-testid="register-name-input"
              />
            )}
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              data-testid="auth-email-input"
            />
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              data-testid="auth-password-input"
            />

            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400 text-sm">
                {error}
              </div>
            )}

            <Button type="submit" loading={loading} className="w-full" data-testid="auth-submit-btn">
              {isLogin ? "Sign In" : "Create Account"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};

// ==================== ONBOARDING ====================

const OnboardingPage = ({ onComplete }) => {
  const { user, token, refreshUser } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState({
    fitness_goal: "general_fitness",
    fitness_level: "beginner",
    age: "",
    weight_kg: "",
    height_cm: "",
    available_equipment: [],
    workout_days_per_week: 3,
    workout_duration_minutes: 45,
    injuries_restrictions: "",
  });

  const equipmentOptions = [
    "Dumbbells", "Barbell", "Kettlebells", "Pull-up Bar", "Resistance Bands",
    "Bench", "Cable Machine", "Treadmill", "Stationary Bike", "Rowing Machine"
  ];

  const toggleEquipment = (item) => {
    setProfileData(prev => ({
      ...prev,
      available_equipment: prev.available_equipment.includes(item)
        ? prev.available_equipment.filter(e => e !== item)
        : [...prev.available_equipment, item]
    }));
  };

  const handleNext = () => setStep(s => Math.min(s + 1, 4));
  const handleBack = () => setStep(s => Math.max(s - 1, 1));

  const handleComplete = async () => {
    setLoading(true);
    try {
      const api = createAuthApi(token);
      await api.put("/profile", { 
        ...profileData, 
        onboarding_complete: true,
        age: profileData.age ? parseInt(profileData.age) : null,
        weight_kg: profileData.weight_kg ? parseFloat(profileData.weight_kg) : null,
        height_cm: profileData.height_cm ? parseFloat(profileData.height_cm) : null,
      });
      await refreshUser();
      onComplete();
    } catch (err) {
      console.error("Failed to save profile:", err);
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Target className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">What's your fitness goal?</h2>
              <p className="text-zinc-400">This helps us create the perfect plan for you</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {[
                { value: "weight_loss", label: "Lose Weight", icon: "🔥" },
                { value: "muscle_gain", label: "Build Muscle", icon: "💪" },
                { value: "endurance", label: "Improve Endurance", icon: "🏃" },
                { value: "general_fitness", label: "General Fitness", icon: "⚡" },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setProfileData({ ...profileData, fitness_goal: opt.value })}
                  className={`p-6 rounded-2xl border-2 transition-all text-left ${
                    profileData.fitness_goal === opt.value 
                      ? 'border-orange-500 bg-orange-500/10' 
                      : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'
                  }`}
                  data-testid={`goal-${opt.value}`}
                >
                  <span className="text-3xl mb-3 block">{opt.icon}</span>
                  <span className="text-white font-medium">{opt.label}</span>
                </button>
              ))}
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Trophy className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Your fitness level?</h2>
              <p className="text-zinc-400">Be honest - we'll match your workouts accordingly</p>
            </div>
            <div className="space-y-4">
              {[
                { value: "beginner", label: "Beginner", desc: "New to working out or returning after a long break" },
                { value: "intermediate", label: "Intermediate", desc: "Consistent workout routine for 6+ months" },
                { value: "advanced", label: "Advanced", desc: "Years of training experience with solid technique" },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setProfileData({ ...profileData, fitness_level: opt.value })}
                  className={`w-full p-5 rounded-2xl border-2 transition-all text-left ${
                    profileData.fitness_level === opt.value 
                      ? 'border-orange-500 bg-orange-500/10' 
                      : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'
                  }`}
                  data-testid={`level-${opt.value}`}
                >
                  <span className="text-white font-semibold block mb-1">{opt.label}</span>
                  <span className="text-zinc-400 text-sm">{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <User className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Tell us about yourself</h2>
              <p className="text-zinc-400">Optional but helps personalize your plan</p>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <Input label="Age" type="number" placeholder="25" value={profileData.age} onChange={(e) => setProfileData({ ...profileData, age: e.target.value })} data-testid="onboarding-age" />
              <Input label="Weight (kg)" type="number" placeholder="70" value={profileData.weight_kg} onChange={(e) => setProfileData({ ...profileData, weight_kg: e.target.value })} data-testid="onboarding-weight" />
              <Input label="Height (cm)" type="number" placeholder="175" value={profileData.height_cm} onChange={(e) => setProfileData({ ...profileData, height_cm: e.target.value })} data-testid="onboarding-height" />
            </div>
            <Input
              label="Any injuries or restrictions?"
              placeholder="e.g., Bad knee, lower back issues..."
              value={profileData.injuries_restrictions}
              onChange={(e) => setProfileData({ ...profileData, injuries_restrictions: e.target.value })}
              data-testid="onboarding-injuries"
            />
          </div>
        );
      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Dumbbell className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Your workout setup</h2>
              <p className="text-zinc-400">What equipment do you have access to?</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {equipmentOptions.map(item => (
                <button
                  key={item}
                  onClick={() => toggleEquipment(item)}
                  className={`p-4 rounded-xl border transition-all text-sm font-medium ${
                    profileData.available_equipment.includes(item)
                      ? 'border-orange-500 bg-orange-500/20 text-orange-400'
                      : 'border-zinc-700 bg-zinc-800/50 text-zinc-300 hover:border-zinc-600'
                  }`}
                  data-testid={`equipment-${item.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  {item}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-4 mt-6">
              <Select
                label="Days per week"
                value={profileData.workout_days_per_week}
                onChange={(e) => setProfileData({ ...profileData, workout_days_per_week: parseInt(e.target.value) })}
                options={[2,3,4,5,6].map(n => ({ value: n, label: `${n} days` }))}
                data-testid="onboarding-days"
              />
              <Select
                label="Session duration"
                value={profileData.workout_duration_minutes}
                onChange={(e) => setProfileData({ ...profileData, workout_duration_minutes: parseInt(e.target.value) })}
                options={[30,45,60,75,90].map(n => ({ value: n, label: `${n} minutes` }))}
                data-testid="onboarding-duration"
              />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3, 4].map(s => (
            <div
              key={s}
              className={`h-2 flex-1 rounded-full transition-all ${s <= step ? 'bg-orange-500' : 'bg-zinc-800'}`}
            />
          ))}
        </div>

        <Card className="mb-6">
          {renderStep()}
        </Card>

        <div className="flex gap-4">
          {step > 1 && (
            <Button variant="secondary" onClick={handleBack} className="flex-1" data-testid="onboarding-back">
              Back
            </Button>
          )}
          {step < 4 ? (
            <Button onClick={handleNext} className="flex-1" data-testid="onboarding-next">
              Continue <ChevronRight className="w-5 h-5" />
            </Button>
          ) : (
            <Button onClick={handleComplete} loading={loading} className="flex-1" data-testid="onboarding-complete">
              Generate My Plan <Zap className="w-5 h-5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

// ==================== MAIN DASHBOARD ====================

const Dashboard = () => {
  const { user, token, logout } = useAuth();
  const [activePlan, setActivePlan] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedDay, setSelectedDay] = useState(0);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [toast, setToast] = useState(null);
  const [customInstructions, setCustomInstructions] = useState("");
  const [showNewPlanModal, setShowNewPlanModal] = useState(false);

  const api = createAuthApi(token);

  const fetchData = useCallback(async () => {
    try {
      const [activePlanRes, plansRes] = await Promise.all([
        api.get("/workout-plans/active"),
        api.get("/workout-plans"),
      ]);
      setActivePlan(activePlanRes.data);
      setPlans(plansRes.data);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchData();
  }, []);

  const generateNewPlan = async () => {
    setGenerating(true);
    setShowNewPlanModal(false);
    try {
      const response = await api.post("/workout-plans/generate", { 
        custom_instructions: customInstructions || null 
      });
      setActivePlan(response.data);
      setPlans(prev => [{ 
        id: response.data.id, 
        plan_name: response.data.plan_name, 
        goal: response.data.goal,
        level: response.data.level,
        created_at: response.data.created_at,
        active: true 
      }, ...prev.map(p => ({ ...p, active: false }))]);
      setToast({ message: "New workout plan generated! 💪", type: "success" });
      setCustomInstructions("");
    } catch (err) {
      setToast({ message: "Failed to generate plan. Try again.", type: "error" });
    } finally {
      setGenerating(false);
    }
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

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-zinc-950/95 backdrop-blur border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white hidden sm:block">MotivAction</span>
          </div>
          
          <div className="flex items-center gap-4">
            <Button 
              onClick={() => setShowNewPlanModal(true)} 
              disabled={generating}
              size="sm"
              data-testid="generate-plan-btn"
            >
              {generating ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Plus className="w-4 h-4" /> New Plan</>}
            </Button>
            
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="md:hidden p-2 text-zinc-400 hover:text-white"
            >
              {showMobileMenu ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>

            <div className="hidden md:flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-zinc-800 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-zinc-400" />
                </div>
                <span className="text-zinc-300 font-medium">{user.name}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={logout} data-testid="logout-btn">
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {showMobileMenu && (
          <div className="md:hidden border-t border-zinc-800 px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-zinc-800 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-zinc-400" />
                </div>
                <span className="text-zinc-300">{user.name}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="w-4 h-4" /> Logout
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            {activePlan ? `Let's crush it, ${user.name.split(' ')[0]}! 🔥` : `Welcome, ${user.name.split(' ')[0]}!`}
          </h1>
          <p className="text-zinc-400">
            {activePlan ? activePlan.description : "Generate your first AI-powered workout plan to get started."}
          </p>
        </div>

        {!activePlan ? (
          /* No Plan State */
          <Card className="text-center py-16">
            <div className="w-20 h-20 bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <Dumbbell className="w-10 h-10 text-orange-500" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">Ready to Transform?</h2>
            <p className="text-zinc-400 max-w-md mx-auto mb-8">
              Our AI will create a personalized workout plan based on your goals, fitness level, and available equipment.
            </p>
            <Button onClick={() => setShowNewPlanModal(true)} size="lg" data-testid="first-plan-btn">
              <Zap className="w-5 h-5" /> Generate My Plan
            </Button>
          </Card>
        ) : (
          /* Active Plan View */
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Plan Overview */}
            <div className="lg:col-span-2 space-y-6">
              {/* Plan Header */}
              <Card>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white mb-1" data-testid="plan-name">{activePlan.plan_name}</h2>
                    <div className="flex items-center gap-4 text-sm text-zinc-400">
                      <span className="flex items-center gap-1">
                        <Target className="w-4 h-4 text-orange-500" />
                        {activePlan.goal.replace('_', ' ')}
                      </span>
                      <span className="flex items-center gap-1">
                        <Trophy className="w-4 h-4 text-orange-500" />
                        {activePlan.level}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4 text-orange-500" />
                        {activePlan.duration_weeks} weeks
                      </span>
                    </div>
                  </div>
                </div>

                {/* Day Selector */}
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {activePlan.workout_days.map((day, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedDay(idx)}
                      className={`flex-shrink-0 px-4 py-3 rounded-xl transition-all ${
                        selectedDay === idx
                          ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white'
                          : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                      }`}
                      data-testid={`day-selector-${idx}`}
                    >
                      <div className="text-xs opacity-75">Day {idx + 1}</div>
                      <div className="font-semibold text-sm">{day.workout_type}</div>
                    </button>
                  ))}
                </div>
              </Card>

              {/* Current Workout */}
              {currentWorkout && (
                <Card>
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-white">{currentWorkout.day}</h3>
                    <div className="flex items-center gap-2 text-zinc-400 text-sm">
                      <Clock className="w-4 h-4" />
                      {currentWorkout.estimated_duration_minutes} min
                    </div>
                  </div>

                  {/* Warmup */}
                  <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-4 mb-6">
                    <div className="flex items-center gap-2 text-orange-400 font-medium mb-2">
                      <Flame className="w-4 h-4" /> Warm-up
                    </div>
                    <p className="text-zinc-300 text-sm">{currentWorkout.warmup_notes}</p>
                  </div>

                  {/* Exercises */}
                  <div className="space-y-4">
                    {currentWorkout.exercises.map((exercise, idx) => (
                      <div 
                        key={idx} 
                        className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700/50"
                        data-testid={`exercise-${idx}`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="text-white font-semibold">{exercise.name}</h4>
                            <span className="text-xs text-orange-400 bg-orange-500/10 px-2 py-1 rounded-full">
                              {exercise.muscle_group}
                            </span>
                          </div>
                          <div className="text-right text-sm">
                            <div className="text-white font-medium">{exercise.sets} × {exercise.reps}</div>
                            <div className="text-zinc-500">{exercise.rest_seconds}s rest</div>
                          </div>
                        </div>
                        {exercise.notes && (
                          <p className="text-zinc-400 text-sm mt-2 pt-2 border-t border-zinc-700/50">
                            💡 {exercise.notes}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Cooldown */}
                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mt-6">
                    <div className="flex items-center gap-2 text-blue-400 font-medium mb-2">
                      <CheckCircle className="w-4 h-4" /> Cool-down
                    </div>
                    <p className="text-zinc-300 text-sm">{currentWorkout.cooldown_notes}</p>
                  </div>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Tips Card */}
              <Card>
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-orange-500" /> Pro Tips
                </h3>
                <div className="space-y-3">
                  {activePlan.tips.map((tip, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <span className="w-6 h-6 bg-orange-500/10 text-orange-500 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium">
                        {idx + 1}
                      </span>
                      <p className="text-zinc-300 text-sm">{tip}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Plan History */}
              {plans.length > 1 && (
                <Card>
                  <h3 className="text-lg font-bold text-white mb-4">Plan History</h3>
                  <div className="space-y-3">
                    {plans.slice(0, 5).map((plan) => (
                      <div 
                        key={plan.id} 
                        className={`p-3 rounded-xl border cursor-pointer transition-all ${
                          plan.active 
                            ? 'border-orange-500 bg-orange-500/10' 
                            : 'border-zinc-700 hover:border-zinc-600'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-white font-medium text-sm">{plan.plan_name}</p>
                            <p className="text-zinc-500 text-xs">
                              {new Date(plan.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          {plan.active && (
                            <span className="text-xs bg-orange-500 text-white px-2 py-1 rounded-full">Active</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}
      </main>

      {/* New Plan Modal */}
      {showNewPlanModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Generate New Plan</h2>
            <p className="text-zinc-400 text-sm mb-4">
              Our AI will create a fresh workout plan based on your profile. 
              Add any special requests below (optional).
            </p>
            <textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="e.g., Focus more on upper body, include more cardio, avoid jumping exercises..."
              className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none h-24 mb-4"
              data-testid="custom-instructions-input"
            />
            <div className="flex gap-3">
              <Button variant="secondary" onClick={() => setShowNewPlanModal(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={generateNewPlan} className="flex-1" data-testid="confirm-generate-btn">
                <Zap className="w-4 h-4" /> Generate
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Toast */}
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};

// ==================== MAIN APP ====================

function App() {
  const [authState, setAuthState] = useState({ user: null, token: null, loading: true });

  useEffect(() => {
    const token = localStorage.getItem("motivaction_token");
    const user = localStorage.getItem("motivaction_user");
    if (token && user) {
      setAuthState({ token, user: JSON.parse(user), loading: false });
    } else {
      setAuthState({ user: null, token: null, loading: false });
    }
  }, []);

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
    } catch (err) {
      console.error("Failed to refresh user:", err);
    }
  };

  if (authState.loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-orange-500 animate-spin" />
      </div>
    );
  }

  if (!authState.user) {
    return <AuthPage onLogin={handleLogin} />;
  }

  return (
    <AuthContext.Provider value={{ 
      user: authState.user, 
      token: authState.token, 
      logout: handleLogout, 
      refreshUser 
    }}>
      {!authState.user.onboarding_complete ? (
        <OnboardingPage onComplete={refreshUser} />
      ) : (
        <Dashboard />
      )}
    </AuthContext.Provider>
  );
}

export default App;
