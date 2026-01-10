import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const LOGO_URL = "https://customer-assets.emergentagent.com/job_fit-momentum/artifacts/6781x21v_TheMotivAction%20Logo3.png";

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({ email: "", password: "", name: "" });
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [activePlan, setActivePlan] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [selectedDay, setSelectedDay] = useState(0);

  useEffect(() => {
    const savedToken = localStorage.getItem("motivaction_token");
    const savedUser = localStorage.getItem("motivaction_user");
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (token && user?.onboarding_complete) {
      fetchPlan();
    }
  }, [token, user]);

  const fetchPlan = async () => {
    try {
      const res = await axios.get(`${API}/workout-plans/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActivePlan(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setError("");
    try {
      const endpoint = isLogin ? "/auth/login" : "/auth/register";
      const payload = isLogin ? { email: formData.email, password: formData.password } : formData;
      const res = await axios.post(`${API}${endpoint}`, payload);
      localStorage.setItem("motivaction_token", res.data.access_token);
      localStorage.setItem("motivaction_user", JSON.stringify(res.data.user));
      setToken(res.data.access_token);
      setUser(res.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("motivaction_token");
    localStorage.removeItem("motivaction_user");
    setToken(null);
    setUser(null);
    setActivePlan(null);
  };

  const generatePlan = async () => {
    setGenerating(true);
    try {
      const res = await axios.post(`${API}/workout-plans/generate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActivePlan(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const completeOnboarding = async () => {
    try {
      await axios.put(`${API}/profile`, { onboarding_complete: true }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const updatedUser = { ...user, onboarding_complete: true };
      localStorage.setItem("motivaction_user", JSON.stringify(updatedUser));
      setUser(updatedUser);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin w-10 h-10 border-4 border-orange-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  // Auth Page
  if (!user) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <img src={LOGO_URL} alt="MotivAction" className="h-24 mx-auto mb-4" />
            <p className="text-zinc-400">Transform your fitness with AI</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <div className="flex mb-6 bg-zinc-800 rounded-xl p-1">
              <button onClick={() => setIsLogin(true)} className={`flex-1 py-3 rounded-lg font-medium ${isLogin ? 'bg-orange-500 text-white' : 'text-zinc-400'}`}>Sign In</button>
              <button onClick={() => setIsLogin(false)} className={`flex-1 py-3 rounded-lg font-medium ${!isLogin ? 'bg-orange-500 text-white' : 'text-zinc-400'}`}>Sign Up</button>
            </div>
            <form onSubmit={handleAuth} className="space-y-4">
              {!isLogin && <input type="text" placeholder="Full Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white" required />}
              <input type="email" placeholder="Email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white" required />
              <input type="password" placeholder="Password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white" required />
              {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-3 text-red-400 text-sm">{error}</div>}
              <button type="submit" disabled={authLoading} className="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-xl disabled:opacity-50">
                {authLoading ? "Loading..." : (isLogin ? "Sign In" : "Create Account")}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Onboarding
  if (!user.onboarding_complete) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <img src={LOGO_URL} alt="MotivAction" className="h-20 mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-white mb-4">Welcome, {user.name}!</h2>
          <p className="text-zinc-400 mb-8">Let's get you started with your fitness journey.</p>
          <button onClick={completeOnboarding} className="px-8 py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-xl text-lg">
            Get Started →
          </button>
        </div>
      </div>
    );
  }

  // Dashboard
  const currentWorkout = activePlan?.workout_days?.[selectedDay];

  return (
    <div className="min-h-screen bg-zinc-950">
      <header className="sticky top-0 z-40 bg-zinc-950/95 backdrop-blur border-b border-zinc-800">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <img src={LOGO_URL} alt="MotivAction" className="h-10" />
          <div className="flex items-center gap-3">
            <span className="text-zinc-300 text-sm">{user.name}</span>
            <button onClick={handleLogout} className="text-zinc-400 hover:text-white text-sm">Logout</button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Your Workout</h1>
            <p className="text-zinc-400">{activePlan ? activePlan.description : "Generate your AI workout plan"}</p>
          </div>
          <button onClick={generatePlan} disabled={generating} className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-xl disabled:opacity-50">
            {generating ? "Generating..." : (activePlan ? "New Plan" : "Generate Plan")}
          </button>
        </div>

        {!activePlan ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-12 text-center">
            <div className="text-6xl mb-4">💪</div>
            <h2 className="text-xl font-bold text-white mb-2">Ready to Transform?</h2>
            <p className="text-zinc-400 mb-6">Click the button above to generate your personalized AI workout plan.</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
              <h2 className="text-lg font-bold text-white mb-4">{activePlan.plan_name}</h2>
              <div className="flex gap-2 overflow-x-auto pb-2">
                {activePlan.workout_days?.map((day, idx) => (
                  <button key={idx} onClick={() => setSelectedDay(idx)} className={`flex-shrink-0 px-4 py-2 rounded-xl ${selectedDay === idx ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white' : 'bg-zinc-800 text-zinc-400'}`}>
                    <div className="text-xs">Day {idx + 1}</div>
                    <div className="font-semibold text-sm">{day.workout_type}</div>
                  </button>
                ))}
              </div>
            </div>

            {currentWorkout && (
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
                <h3 className="text-lg font-bold text-white mb-4">{currentWorkout.day}</h3>
                <div className="space-y-3">
                  {currentWorkout.exercises?.map((ex, idx) => (
                    <div key={idx} className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700/50">
                      {ex.image_url && <img src={ex.image_url} alt={ex.name} className="w-full h-32 object-cover rounded-lg mb-3" />}
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-white font-semibold">{ex.name}</h4>
                          <span className="text-xs text-orange-400">{ex.muscle_group}</span>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-medium">{ex.sets} × {ex.reps}</div>
                          <div className="text-zinc-500 text-sm">{ex.rest_seconds}s rest</div>
                        </div>
                      </div>
                      {ex.notes && <p className="text-zinc-400 text-sm mt-2">💡 {ex.notes}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activePlan.tips && (
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
                <h3 className="text-lg font-bold text-white mb-3">💡 Pro Tips</h3>
                <ul className="space-y-2">
                  {activePlan.tips.map((tip, idx) => (
                    <li key={idx} className="text-zinc-300 text-sm flex gap-2">
                      <span className="text-orange-500">{idx + 1}.</span> {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
