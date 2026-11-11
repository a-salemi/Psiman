from flask import Flask, render_template_string, jsonify, request, redirect, url_for, session
from functools import wraps
import os, time, json, subprocess, threading

# --- Try to load Waitress for Production Server ---
try:
    from waitress import serve
    HAS_WAITRESS = True
except ImportError:
    HAS_WAITRESS = False

app = Flask(__name__)
app.secret_key = 'psi_super_secret_enterprise_key_2026!@#'

# --- Persistent Config (For Changing Passwords) ---
CONFIG_FILE = '/opt/psi_config.json'
DEFAULT_CONFIG = {"username": "admin", "password": "asdf1234!!@@"}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(new_config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(new_config, f)

# --- Authentication Logic ---
def check_auth(username, password):
    cfg = load_config()
    return username == cfg['username'] and password == cfg['password']

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- Routes for Login/Logout ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if check_auth(username, password):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password!"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- Database ---
PORTS = {"US": 4050, "DE": 4051, "GB": 4052, "FR": 4053, "CA": 4054, "NL": 4055, "AT": 4056, "BE": 4057, "BG": 4058, "CH": 4059, "CZ": 4060, "DK": 4061, "EE": 4062, "ES": 4063, "FI": 4064, "HR": 4065, "HU": 4066, "IN": 4067, "IT": 4068, "JP": 4069, "LV": 4070, "NO": 4071, "PL": 4072, "PT": 4073, "RO": 4074, "RS": 4075, "SE": 4076, "SG": 4077, "SK": 4078, "UA": 4079, "AU": 4080, "ID": 4081, "IE": 4082, "LT": 4083, "BR": 4084}
NAMES = {"US": "United States", "DE": "Germany", "GB": "United Kingdom", "FR": "France", "CA": "Canada", "NL": "Netherlands", "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CH": "Switzerland", "CZ": "Czech Republic", "DK": "Denmark", "EE": "Estonia", "ES": "Spain", "FI": "Finland", "HR": "Croatia", "HU": "Hungary", "IN": "India", "IT": "Italy", "JP": "Japan", "LV": "Latvia", "NO": "Norway", "PL": "Poland", "PT": "Portugal", "RO": "Romania", "RS": "Serbia", "SE": "Sweden", "SG": "Singapore", "SK": "Slovakia", "UA": "Ukraine", "AU": "Australia", "ID": "Indonesia", "IE": "Ireland", "LT": "Lithuania", "BR": "Brazil"}

CONTINENTS = {
    "Americas": ["US", "CA", "BR"],
    "Europe": ["GB", "DE", "FR", "NL", "IE", "CH", "AT", "BE", "BG", "CZ", "DK", "EE", "ES", "FI", "HR", "HU", "IT", "LT", "LV", "NO", "PL", "PT", "RO", "RS", "SE", "SK", "UA"],
    "Asia-Pacific": ["AU", "IN", "ID", "JP", "SG"]
}

def get_psiphon_config(socks, http, region):
    return f'''{{
    "LocalSocksProxyPort": {socks},
    "LocalHttpProxyPort": {http},
    "EgressRegion": "{region}",
    "PropagationChannelId": "FFFFFFFFFFFFFFFF",
    "SponsorId": "FFFFFFFFFFFFFFFF",
    "RemoteServerListUrl": "https://s3.amazonaws.com//psiphon/web/mjr4-p23r-puwl/server_list_compressed",
    "RemoteServerListSignaturePublicKey": "MIICIDANBgkqhkiG9w0BAQEFAAOCAg0AMIICCAKCAgEAt7Ls+/39r+T6zNW7GiVpJfzq/xvL9SBH5rIFnk0RXYEYavax3WS6HOD35eTAqn8AniOwiH+DOkvgSKF2caqk/y1dfq47Pdymtwzp9ikpB1C5OfAysXzBiwVJlCdajBKvBZDerV1cMvRzCKvKwRmvDmHgphQQ7WfXIGbRbmmk6opMBh3roE42KcotLFtqp0RRwLtcBRNtCdsrVsjiI1Lqz/lH+T61sGjSjQ3CHMuZYSQJZo/KrvzgQXpkaCTdbObxHqb6/+i1qaVOfEsvjoiyzTxJADvSytVtcTjijhPEV6XskJVHE1Zgl+7rATr/pDQkw6DPCNBS1+Y6fy7GstZALQXwEDN/qhQI9kWkHijT8ns+i1vGg00Mk/6J75arLhqcodWsdeG/M/moWgqQAnlZAGVtJI1OgeF5fsPpXu4kctOfuZlGjVZXQNW34aOzm8r8S0eVZitPlbhcPiR4gT/aSMz/wd8lZlzZYsje/Jr8u/YtlwjjreZrGRmG8KMOzukV3lLmMppXFMvl4bxv6YFEmIuTsOhbLTwFgh7KYNjodLj/LsqRVfwz31PgWQFTEPICV7GCvgVlPRxnofqKSjgTWI4mxDhBpVcATvaoBl1L/6WLbFvBsoAUBItWwctO2xalKxF5szhGm8lccoc5MZr8kfE0uxMgsxz4er68iCID+rsCAQM=",
    "RemoteServerListDownloadFilename": "remote_server_list",
    "FetchRemoteServerListRetryIntervalMilliseconds": 1000
}}'''

# --- Accurate CPU/RAM Stats (Global variables for CPU delta calculation) ---
last_cpu_total = 0
last_cpu_idle = 0

def get_sys_stats():
    global last_cpu_total, last_cpu_idle
    
    # 1. RAM Calculation
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        total = int(lines[0].split()[1])
        free = int(lines[1].split()[1])
        buffers = int(lines[3].split()[1])
        cached = int(lines[4].split()[1])
        used = total - free - buffers - cached
        ram = int((used / total) * 100)
    except:
        ram = 0

    # 2. True CPU Calculation (using /proc/stat deltas)
    cpu = 0
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline().split()[1:]
        cpu_stats = [int(i) for i in line]
        
        idle = cpu_stats[3] + cpu_stats[4] # idle + iowait
        non_idle = sum(cpu_stats[:3]) + sum(cpu_stats[5:8]) # user + nice + system + irq + softirq + steal
        total = idle + non_idle

        total_diff = total - last_cpu_total
        idle_diff = idle - last_cpu_idle

        if last_cpu_total > 0 and total_diff > 0:
            cpu = int(100 * (total_diff - idle_diff) / total_diff)
        
        # Save current stats for next tick
        last_cpu_total = total
        last_cpu_idle = idle
        
        cpu = max(0, min(100, cpu)) # Keep between 0 and 100
    except:
        cpu = 0

    return {"cpu": cpu, "ram": ram}

# --- Frontend Templates ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Login - PsiMan Quantum</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { 
            background: linear-gradient(-45deg, #020617, #0f172a, #082f49, #020617);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; overflow: hidden; 
        }
        @keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .glass-panel { background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(40px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .ambient-glow { position: absolute; width: 60vw; height: 60vw; background: radial-gradient(circle, rgba(14,165,233,0.15) 0%, rgba(0,0,0,0) 70%); top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: -1; animation: pulse 6s infinite alternate; }
        @keyframes pulse { 0% { transform: translate(-50%, -50%) scale(1); } 100% { transform: translate(-50%, -50%) scale(1.1); } }
        input:-webkit-autofill { -webkit-box-shadow: 0 0 0 30px #0f172a inset !important; -webkit-text-fill-color: white !important; }
        .fade-in { animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; transform: translateY(30px); }
        @keyframes fadeIn { to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center relative">
    <div class="ambient-glow"></div>
    <div class="glass-panel p-10 rounded-[32px] w-full max-w-[380px] shadow-2xl relative z-10 mx-4 fade-in">
        
        <div class="flex justify-center mb-6">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-400 to-indigo-500 flex items-center justify-center shadow-lg shadow-sky-500/40">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"></path></svg>
            </div>
        </div>
        
        <h2 class="text-2xl font-bold text-center mb-1.5 tracking-tight">PsiMan Quantum</h2>
        <p class="text-gray-400 text-center text-[13px] font-medium mb-8">v10.0 Enterprise UI</p>
        
        {% if error %}
        <div class="bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium p-3 rounded-xl mb-6 text-center backdrop-blur-sm">
            {{ error }}
        </div>
        {% endif %}

        <form method="POST" class="space-y-4">
            <div>
                <input type="text" name="username" placeholder="Username" required class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-gray-500 focus:outline-none focus:border-sky-500 focus:bg-white/10 transition-all text-[15px]">
            </div>
            <div>
                <input type="password" name="password" placeholder="Password" required class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-gray-500 focus:outline-none focus:border-sky-500 focus:bg-white/10 transition-all text-[15px]">
            </div>
            <button type="submit" class="w-full bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold py-3.5 rounded-xl transition-all shadow-[0_0_20px_rgba(14,165,233,0.3)] mt-4 text-[15px]">
                Authenticate
            </button>
        </form>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PsiMan Quantum Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;600&display=swap');
        body { 
            background: linear-gradient(-45deg, #020617, #0f172a, #082f49, #020617);
            background-size: 400% 400%;
            animation: gradientBG 20s ease infinite;
            color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; -webkit-font-smoothing: antialiased; overflow-x: hidden; 
        }
        @keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        
        .ios-card { 
            background: rgba(15, 23, 42, 0.4); 
            backdrop-filter: blur(20px); 
            border-radius: 20px; 
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); 
            border: 1px solid rgba(255, 255, 255, 0.05); 
        }
        .ios-card:hover { transform: translateY(-4px) scale(1.01); border-color: rgba(255, 255, 255, 0.15); box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
        .ios-search { background: rgba(30, 41, 59, 0.6); caret-color: #38bdf8; }
        .ios-search:focus { outline: none; box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.4); }
        .active-card { background: rgba(15, 23, 42, 0.7); border-color: rgba(16, 185, 129, 0.4) !important; box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.4), 0 4px 20px rgba(16, 185, 129, 0.15) !important; }
        
        .stagger-item { opacity: 0; transform: translateY(20px); animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        @keyframes fadeInUp { to { opacity: 1; transform: translateY(0); } }

        .spinner { animation: spin 1s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        ::-webkit-scrollbar { width: 4px; background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
        .modal-bg { background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(15px); }
        
        #toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; }
        .toast { padding: 12px 20px; border-radius: 12px; font-weight: 500; font-size: 14px; display: flex; align-items: center; gap: 8px; backdrop-filter: blur(15px); animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .toast.success { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34D399; }
        .toast.error { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #F87171; }
        .toast.info { background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #7DD3FC; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .toast-fade-out { animation: fadeOut 0.3s forwards; }
        @keyframes fadeOut { to { transform: translateX(100%); opacity: 0; } }

        .terminal-text { font-family: 'Fira Code', monospace; font-size: 12px; line-height: 1.6; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div id="toast-container"></div>

    <div class="max-w-7xl mx-auto">
        
        <!-- Live System Stats Bar with Progress Bars -->
        <div class="mb-6 flex flex-wrap gap-4 items-center justify-between bg-white/5 border border-white/10 p-3.5 rounded-2xl backdrop-blur-md stagger-item">
            <div class="flex items-center gap-8 px-2 w-full md:w-auto">
                <div class="flex-1 min-w-[120px]">
                    <div class="flex justify-between items-center mb-1.5">
                        <div class="flex items-center gap-1.5">
                            <svg class="w-3.5 h-3.5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
                            <span class="text-[10px] text-sky-200/70 font-bold uppercase tracking-widest">CPU LOAD</span>
                        </div>
                        <span id="stat-cpu-text" class="text-xs font-mono font-bold text-white">--%</span>
                    </div>
                    <div class="w-full bg-black/40 rounded-full h-1.5 border border-white/5 overflow-hidden">
                        <div id="stat-cpu-bar" class="bg-sky-400 h-1.5 rounded-full transition-all duration-700 w-0 shadow-[0_0_10px_rgba(56,189,248,0.5)]"></div>
                    </div>
                </div>
                
                <div class="flex-1 min-w-[120px]">
                    <div class="flex justify-between items-center mb-1.5">
                        <div class="flex items-center gap-1.5">
                            <svg class="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
                            <span class="text-[10px] text-indigo-200/70 font-bold uppercase tracking-widest">MEM USAGE</span>
                        </div>
                        <span id="stat-ram-text" class="text-xs font-mono font-bold text-white">--%</span>
                    </div>
                    <div class="w-full bg-black/40 rounded-full h-1.5 border border-white/5 overflow-hidden">
                        <div id="stat-ram-bar" class="bg-indigo-400 h-1.5 rounded-full transition-all duration-700 w-0 shadow-[0_0_10px_rgba(99,102,241,0.5)]"></div>
                    </div>
                </div>
            </div>
            
            <button onclick="toggleModal('bulkModal')" class="bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-orange-500/30 text-orange-400 text-xs font-bold px-4 py-2 rounded-xl hover:bg-orange-500/30 transition-all flex items-center gap-1.5 ml-auto">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> Bulk Actions
            </button>
        </div>

        <!-- Header & Search -->
        <div class="mb-10 sticky top-4 z-40 bg-slate-900/60 backdrop-blur-xl pt-4 pb-4 px-5 rounded-3xl border border-white/10 shadow-2xl stagger-item">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-sky-400 to-indigo-500 flex items-center justify-center shadow-lg shadow-sky-500/30">
                        <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path></svg>
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">PsiMan Quantum</h1>
                        <p class="text-emerald-400/80 text-[10px] font-bold uppercase tracking-widest mt-1 flex items-center gap-1.5">
                            <span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span></span> 
                            System Online
                        </p>
                    </div>
                </div>
                
                <div class="flex items-center gap-3 w-full md:w-auto">
                    <div class="relative flex-1 md:w-64">
                        <svg class="absolute left-3 top-3 w-5 h-5 text-sky-200/50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        <input type="text" id="searchBox" onkeyup="filterNodes()" placeholder="Search location..." class="ios-search w-full pl-10 pr-4 py-2.5 rounded-xl text-[15px] font-medium placeholder-sky-200/40 transition-all text-white border border-white/5">
                    </div>
                    <button onclick="toggleModal('toolsModal')" class="bg-white/5 border border-white/10 p-2.5 rounded-xl hover:bg-white/10 transition-colors shadow-lg" title="Tools & Diagnostics">
                        <svg class="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                    </button>
                    <button onclick="toggleModal('settingsModal')" class="bg-white/5 border border-white/10 p-2.5 rounded-xl hover:bg-white/10 transition-colors shadow-lg" title="Settings">
                        <svg class="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                    </button>
                    <a href="/logout" class="bg-red-500/10 border border-red-500/20 p-2.5 rounded-xl hover:bg-red-500/20 transition-colors text-red-400 flex items-center justify-center shadow-lg" title="Sign Out">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                    </a>
                </div>
            </div>
        </div>

        <!-- Sections by Continent -->
        {% for continent, codes in continents.items() %}
        <div class="mb-14 continent-section stagger-item">
            <div class="flex items-center gap-4 mb-6 px-2">
                <h2 class="text-xl font-bold text-white tracking-tight">{{ continent }}</h2>
                <div class="h-[1px] flex-1 bg-gradient-to-r from-white/20 to-transparent"></div>
            </div>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {% for code in codes %}
                <div id="card-{{code}}" data-name="{{ names[code] }}" data-code="{{ code }}" class="node-card ios-card p-5 relative overflow-hidden group {% if active_nodes[code] %}active-card{% endif %}">
                    <div id="loading-{{code}}" class="absolute inset-0 bg-[#0f172a]/90 hidden flex justify-center items-center backdrop-blur-md z-20 rounded-[20px]">
                        <div class="w-6 h-6 border-[3px] border-[#10B981] border-t-transparent rounded-full spinner"></div>
                    </div>

                    <div class="flex justify-between items-center h-full">
                        <div class="flex items-center gap-4">
                            <div class="relative">
                                <img src="https://hatscripts.github.io/circle-flags/flags/{{ code | lower }}.svg" class="w-11 h-11 rounded-full shadow-[0_2px_15px_rgba(0,0,0,0.4)] border border-white/5" alt="Flag">
                            </div>
                            <div class="flex flex-col">
                                <h3 class="font-semibold text-[16px] tracking-tight leading-tight">{{ names[code] }}</h3>
                                <div class="flex items-center gap-1.5 mt-1">
                                    <span class="text-sky-100/60 text-[12px] font-mono font-medium">{{ code }} : {{ ports[code] }}</span>
                                    <span class="text-gray-600 text-[10px]">&bull;</span>
                                    <span id="status-text-{{code}}" class="text-[11px] font-bold uppercase tracking-wider transition-colors {% if active_nodes[code] %}text-[#10B981]{% else %}text-gray-500{% endif %}">
                                        {% if active_nodes[code] %}Active{% else %}Off{% endif %}
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="flex items-center gap-3">
                            <button onclick="openLogs('{{code}}')" class="text-sky-200/50 hover:text-sky-400 transition-colors focus:outline-none" title="Live Terminal Logs">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                            </button>
                            
                            <button id="toggle-btn-{{code}}" onclick="toggleNode('{{code}}')" class="relative inline-flex h-[31px] w-[51px] shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-300 ease-in-out focus:outline-none {% if active_nodes[code] %}bg-[#10B981] shadow-[0_0_15px_rgba(16,185,129,0.4)]{% else %}bg-white/10{% endif %}">
                                <span id="toggle-knob-{{code}}" class="pointer-events-none inline-block h-[27px] w-[27px] transform rounded-full bg-white shadow-md ring-0 transition duration-300 ease-in-out {% if active_nodes[code] %}translate-x-[20px]{% else %}translate-x-0{% endif %}"></span>
                            </button>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Terminal Modal -->
    <div id="termModal" class="fixed inset-0 modal-bg hidden z-[60] flex items-center justify-center p-4 opacity-0 transition-opacity duration-300">
        <div class="bg-[#0D1117] border border-gray-700 w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden transform scale-95 transition-transform duration-300 relative flex flex-col h-[70vh]" id="termContentWrapper">
            <div class="bg-black/40 border-b border-white/5 px-4 py-3 flex justify-between items-center backdrop-blur-md">
                <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    <span class="text-sm font-semibold text-gray-200 font-mono tracking-wide">psiphon-<span id="termNodeCode"></span>.service</span>
                </div>
                <button onclick="toggleModal('termModal')" class="text-gray-500 hover:text-red-400 transition-colors bg-white/5 p-1 rounded-lg">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            <div class="p-4 overflow-auto flex-1 relative bg-black/60">
                <div id="termLoader" class="absolute inset-0 flex justify-center items-center bg-[#0D1117]/80 z-10"><div class="w-8 h-8 border-4 border-gray-600 border-t-emerald-500 rounded-full spinner"></div></div>
                <pre id="termText" class="terminal-text text-emerald-400 whitespace-pre-wrap break-all"></pre>
            </div>
            <div class="bg-black/40 border-t border-white/5 px-4 py-2 text-xs font-mono text-gray-500 flex justify-between items-center backdrop-blur-md">
                <span>> Live journalctl feed (last 50 lines)</span>
                <button onclick="fetchLogs()" class="hover:text-white flex items-center gap-1 bg-white/5 px-2 py-1 rounded border border-white/10"><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg> Refresh</button>
            </div>
        </div>
    </div>

    <!-- Bulk Actions Modal -->
    <div id="bulkModal" class="fixed inset-0 modal-bg hidden z-50 flex items-center justify-center p-4 opacity-0 transition-opacity duration-300">
        <div class="ios-card w-full max-w-sm p-6 transform scale-95 transition-transform duration-300 relative" id="bulkContent">
            <button onclick="toggleModal('bulkModal')" class="absolute top-4 right-4 text-gray-400 hover:text-white bg-white/5 rounded-full p-1 transition-colors"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
            <h2 class="text-xl font-bold mb-6 flex items-center gap-2 text-orange-400"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> Bulk Actions</h2>
            <div class="space-y-3">
                <button onclick="executeBulk('start_eu')" class="w-full bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 font-medium py-3 rounded-xl transition-all">Start Entire Europe</button>
                <button onclick="executeBulk('start_all')" class="w-full bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-400 font-medium py-3 rounded-xl transition-all">Start All Continents</button>
                <div class="h-px bg-white/10 my-3"></div>
                <button onclick="executeBulk('stop_all')" class="w-full bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 font-medium py-3 rounded-xl transition-all">Kill All (Stop Everything)</button>
            </div>
        </div>
    </div>

    <!-- Settings Modal -->
    <div id="settingsModal" class="fixed inset-0 modal-bg hidden z-50 flex items-center justify-center p-4 opacity-0 transition-opacity duration-300">
        <div class="ios-card w-full max-w-sm p-6 transform scale-95 transition-transform duration-300 relative" id="settingsContent">
            <button onclick="toggleModal('settingsModal')" class="absolute top-4 right-4 text-gray-400 hover:text-white bg-white/5 rounded-full p-1 transition-colors"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
            <h2 class="text-xl font-bold mb-6 text-gray-200 flex items-center gap-2"><svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg> Security Settings</h2>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">New Username</label>
                    <input type="text" id="set_user" placeholder="admin" class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-sky-500 focus:outline-none transition-colors">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">New Password</label>
                    <input type="password" id="set_pass" placeholder="Enter new password" class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-sky-500 focus:outline-none transition-colors">
                </div>
                <button onclick="saveSettings()" class="w-full bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold py-3 rounded-xl transition-all shadow-[0_0_15px_rgba(56,189,248,0.3)] mt-2">Save Credentials</button>
            </div>
        </div>
    </div>

    <!-- Tools Modal -->
    <div id="toolsModal" class="fixed inset-0 modal-bg hidden z-50 flex items-center justify-center p-4 opacity-0 transition-opacity duration-300">
        <div class="ios-card w-full max-w-lg p-6 transform scale-95 transition-transform duration-300 relative" id="modalContent">
            
            <button onclick="toggleModal('toolsModal')" class="absolute top-4 right-4 text-gray-400 hover:text-white bg-white/5 rounded-full p-1 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            
            <h2 class="text-2xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-400">Diagnostics & Tools</h2>
            
            <div class="mb-6 bg-black/30 rounded-2xl p-5 border border-white/5">
                <h3 class="font-semibold text-lg mb-2 flex items-center gap-2 text-sky-300"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg> Live Network Radar</h3>
                <p class="text-sm text-sky-100/60 mb-4">Scan Psiphon's global network in real-time to find new or active regions.</p>
                <button onclick="runRadar()" id="btn-radar" class="w-full bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-400 font-medium py-3 rounded-xl transition-all flex justify-center items-center gap-2">
                    Start Global Scan
                </button>
                <div id="radar-results" class="mt-4 hidden max-h-48 overflow-y-auto bg-black/50 p-4 rounded-xl border border-white/5 text-sm space-y-2"></div>
            </div>

            <div class="bg-black/30 rounded-2xl p-5 border border-white/5">
                <h3 class="font-semibold text-lg mb-2 flex items-center gap-2 text-purple-400"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg> Isolated Node Tester</h3>
                <p class="text-sm text-purple-100/60 mb-4">Test any country code (e.g., DE) in a secure sandbox without affecting active services.</p>
                <div class="flex gap-3">
                    <input type="text" id="testCode" placeholder="Code (e.g. US)" class="ios-search w-24 px-4 py-3 rounded-xl text-center font-bold uppercase placeholder-white/20 border border-white/5 text-white">
                    <button onclick="runTest()" id="btn-test" class="flex-1 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-400 font-medium py-3 rounded-xl transition-all flex justify-center items-center gap-2">
                        Run Test Probe
                    </button>
                </div>
                <div id="test-results" class="mt-4 hidden bg-black/50 p-4 rounded-xl border border-white/5 text-sm"></div>
            </div>

        </div>
    </div>

    <script>
        // Set staggered animation delays for cards
        document.addEventListener("DOMContentLoaded", () => {
            document.querySelectorAll('.stagger-item').forEach((el, i) => {
                el.style.animationDelay = `${i * 0.08}s`;
            });
        });

        // --- Custom Toast System ---
        function showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            let icon = type === 'success' ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>' : 
                       type === 'error' ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>' :
                       '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
            
            toast.innerHTML = `${icon} <span>${message}</span>`;
            container.appendChild(toast);
            
            // Subtle Audio Feedback
            try {
                let ctx = new (window.AudioContext || window.webkitAudioContext)();
                let osc = ctx.createOscillator();
                let gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                if (type === 'success') { osc.frequency.setValueAtTime(600, ctx.currentTime); osc.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 0.1); }
                else { osc.frequency.setValueAtTime(300, ctx.currentTime); osc.frequency.exponentialRampToValueAtTime(150, ctx.currentTime + 0.1); }
                gain.gain.setValueAtTime(0.05, ctx.currentTime); gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
                osc.start(); osc.stop(ctx.currentTime + 0.1);
            } catch(e) {}

            setTimeout(() => {
                toast.classList.add('toast-fade-out');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        // --- Live Stats Polling with Smooth Bars ---
        setInterval(async () => {
            try {
                let res = await fetch('/api/stats');
                let data = await res.json();
                
                document.getElementById('stat-cpu-text').innerText = data.cpu + '%';
                document.getElementById('stat-cpu-bar').style.width = data.cpu + '%';
                
                document.getElementById('stat-ram-text').innerText = data.ram + '%';
                document.getElementById('stat-ram-bar').style.width = data.ram + '%';
                
                // Color warnings
                document.getElementById('stat-cpu-bar').className = `h-1.5 rounded-full transition-all duration-700 w-full ${data.cpu > 80 ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-sky-400 shadow-[0_0_10px_rgba(56,189,248,0.5)]'}`;
                document.getElementById('stat-ram-bar').className = `h-1.5 rounded-full transition-all duration-700 w-full ${data.ram > 80 ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.5)]'}`;
            } catch(e) {}
        }, 3000);

        // --- UI Logic ---
        function filterNodes() {
            let input = document.getElementById('searchBox').value.toLowerCase();
            let sections = document.querySelectorAll('.continent-section');
            sections.forEach(section => {
                let cards = section.querySelectorAll('.node-card');
                let visibleCount = 0;
                cards.forEach(card => {
                    let name = card.getAttribute('data-name').toLowerCase();
                    let code = card.getAttribute('data-code').toLowerCase();
                    if (name.includes(input) || code.includes(input)) {
                        card.style.display = "block"; visibleCount++;
                    } else {
                        card.style.display = "none";
                    }
                });
                section.style.display = visibleCount > 0 ? "block" : "none";
            });
        }

        async function toggleNode(code) {
            const btn = document.getElementById('toggle-btn-' + code);
            const knob = document.getElementById('toggle-knob-' + code);
            const statusText = document.getElementById('status-text-' + code);
            const card = document.getElementById('card-' + code);
            const loader = document.getElementById('loading-' + code);

            const isActive = btn.classList.contains('bg-[#10B981]');
            const action = isActive ? 'stop' : 'start';

            loader.classList.remove('hidden');

            try {
                let res = await fetch(`/api/${action}/${code}`);
                let data = await res.json();
                if(data.success) {
                    if(action === 'start') {
                        btn.classList.replace('bg-white/10', 'bg-[#10B981]');
                        btn.classList.add('shadow-[0_0_15px_rgba(16,185,129,0.4)]');
                        knob.classList.replace('translate-x-0', 'translate-x-[20px]');
                        statusText.innerText = "Active";
                        statusText.className = "text-[11px] font-bold uppercase tracking-wider text-[#10B981] transition-colors";
                        card.classList.add('active-card');
                        showToast(`${code} Node Started Successfully`, 'success');
                    } else {
                        btn.classList.replace('bg-[#10B981]', 'bg-white/10');
                        btn.classList.remove('shadow-[0_0_15px_rgba(16,185,129,0.4)]');
                        knob.classList.replace('translate-x-[20px]', 'translate-x-0');
                        statusText.innerText = "Off";
                        statusText.className = "text-[11px] font-bold uppercase tracking-wider text-gray-500 transition-colors";
                        card.classList.remove('active-card');
                        showToast(`${code} Node Stopped`, 'info');
                    }
                } else if(data.error) {
                    showToast(data.error, 'error');
                }
            } catch(e) { showToast("Connection error.", 'error'); }
            setTimeout(() => { loader.classList.add('hidden'); }, 300);
        }

        function toggleModal(modalID) {
            const modal = document.getElementById(modalID);
            const content = modal.children[0];
            if(modal.classList.contains('hidden')) {
                modal.classList.remove('hidden');
                setTimeout(() => {
                    modal.classList.replace('opacity-0', 'opacity-100');
                    content.classList.replace('scale-95', 'scale-100');
                }, 10);
            } else {
                modal.classList.replace('opacity-100', 'opacity-0');
                content.classList.replace('scale-100', 'scale-95');
                setTimeout(() => { modal.classList.add('hidden'); }, 300);
            }
        }

        // --- Terminal Logs ---
        let currentTermCode = "";
        function openLogs(code) {
            currentTermCode = code;
            document.getElementById('termNodeCode').innerText = code;
            document.getElementById('termText').innerText = "";
            toggleModal('termModal');
            fetchLogs();
        }
        async function fetchLogs() {
            if(!currentTermCode) return;
            document.getElementById('termLoader').classList.remove('hidden');
            try {
                let res = await fetch('/api/logs/' + currentTermCode);
                let data = await res.json();
                document.getElementById('termText').innerText = data.logs || "No logs available. Is the service running?";
            } catch(e) {
                document.getElementById('termText').innerText = "Error fetching logs.";
            }
            document.getElementById('termLoader').classList.add('hidden');
        }

        // --- Bulk Actions ---
        async function executeBulk(action) {
            toggleModal('bulkModal');
            showToast('Executing bulk action... This may take a moment.', 'info');
            try {
                let res = await fetch('/api/bulk/' + action);
                let data = await res.json();
                if(data.success) {
                    showToast('Bulk Action Complete! Refreshing...', 'success');
                    setTimeout(() => location.reload(), 1500);
                }
            } catch(e) { showToast('Bulk action failed.', 'error'); }
        }

        // --- Settings ---
        async function saveSettings() {
            let u = document.getElementById('set_user').value.trim();
            let p = document.getElementById('set_pass').value.trim();
            if(!u || !p) { showToast('Fields cannot be empty!', 'error'); return; }
            
            try {
                let res = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({u: u, p: p})
                });
                let data = await res.json();
                if(data.success) {
                    showToast('Credentials Saved! Please login again.', 'success');
                    setTimeout(() => window.location.href='/logout', 2000);
                }
            } catch(e) { showToast('Error saving settings.', 'error'); }
        }

        // --- Tools (Radar & Test) ---
        async function runRadar() {
            const btn = document.getElementById('btn-radar');
            const resDiv = document.getElementById('radar-results');
            btn.innerHTML = '<div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full spinner"></div> Scanning Network...';
            btn.disabled = true; resDiv.classList.add('hidden');
            try {
                let res = await fetch('/api/tools/radar');
                let data = await res.json();
                resDiv.classList.remove('hidden');
                if(data.success && data.regions.length > 0) {
                    let html = `<div class="text-[#10B981] font-bold mb-3 flex items-center gap-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Found ${data.regions.length} Online Regions:</div><div class="flex flex-wrap gap-2">`;
                    data.regions.forEach(r => {
                        let isNew = !data.known_codes.includes(r);
                        let badgeClass = isNew ? "bg-purple-500/20 text-purple-400 border-purple-500/30" : "bg-sky-500/10 text-sky-400 border-sky-500/20";
                        html += `<span class="px-2.5 py-1 rounded-md border font-medium ${badgeClass}">${r} ${isNew ? '✨NEW' : ''}</span>`;
                    });
                    html += `</div>`;
                    resDiv.innerHTML = html;
                    showToast('Radar scan complete', 'success');
                } else {
                    resDiv.innerHTML = `<span class="text-red-400 flex items-center gap-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> ${data.error || 'Scan timed out or network is busy.'}</span>`;
                    showToast('Radar scan failed', 'error');
                }
            } catch(e) { resDiv.classList.remove('hidden'); resDiv.innerHTML = `<span class="text-red-400">❌ Error executing scan.</span>`; }
            btn.innerHTML = 'Start Global Scan'; btn.disabled = false;
        }

        async function runTest() {
            const btn = document.getElementById('btn-test');
            const resDiv = document.getElementById('test-results');
            let code = document.getElementById('testCode').value.toUpperCase().trim();
            if(!code || code.length !== 2) { showToast("Invalid country code.", 'error'); return; }
            btn.innerHTML = '<div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full spinner"></div> Probing...';
            btn.disabled = true; resDiv.classList.add('hidden');
            try {
                let res = await fetch('/api/tools/test/' + code);
                let data = await res.json();
                resDiv.classList.remove('hidden');
                if(data.success) {
                    resDiv.innerHTML = `
                        <div class="flex items-center gap-2 text-[#10B981] font-bold mb-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Connection Successful!</div>
                        <div class="text-sky-100/70 mb-1">Target Region: <span class="font-mono text-white font-bold bg-white/10 px-2 py-0.5 rounded">${data.code}</span></div>
                        <div class="text-sky-100/70">Assigned IP: <span class="font-mono text-cyan-400 font-bold bg-cyan-400/10 border border-cyan-400/20 px-2 py-0.5 rounded">${data.ip}</span></div>
                    `;
                    showToast(`Successfully tested ${code}`, 'success');
                } else {
                    resDiv.innerHTML = `<div class="text-red-400 font-bold flex items-center gap-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> ${data.error || 'Connection Failed (Timeout)'}</div>`;
                    showToast(`Test failed for ${code}`, 'error');
                }
            } catch(e) { resDiv.classList.remove('hidden'); resDiv.innerHTML = `<span class="text-red-400">❌ Error executing test.</span>`; }
            btn.innerHTML = 'Run Test Probe'; btn.disabled = false;
        }
    </script>
</body>
</html>
"""

# --- API Routes ---
@app.route('/')
@requires_auth
def dashboard():
    active_nodes = {code: is_active(code) for code in PORTS.keys()}
    return render_template_string(HTML_TEMPLATE, continents=CONTINENTS, ports=PORTS, names=NAMES, active_nodes=active_nodes)

def is_active(code):
    return os.system(f"systemctl is-active --quiet psiphon-{code}") == 0

@app.route('/api/stats')
@requires_auth
def api_stats():
    return jsonify(get_sys_stats())

@app.route('/api/settings', methods=['POST'])
@requires_auth
def api_settings():
    data = request.json
    save_config({"username": data['u'], "password": data['p']})
    return jsonify({"success": True})

@app.route('/api/logs/<code>')
@requires_auth
def api_logs(code):
    try:
        logs = os.popen(f"journalctl -u psiphon-{code} -n 50 --no-pager").read()
        if not logs.strip(): logs = f"No logs found for {code}. Service might be inactive or starting."
        return jsonify({"logs": logs})
    except:
        return jsonify({"logs": "Error reading logs from systemd."})

@app.route('/api/bulk/<action>')
@requires_auth
def api_bulk(action):
    if action == "stop_all":
        os.system("systemctl stop psiphon-* 2>/dev/null")
        os.system("systemctl disable psiphon-* 2>/dev/null")
        os.system("rm -f /etc/systemd/system/psiphon-*.service")
        os.system("rm -rf /etc/psiphon-*")
        os.system("systemctl daemon-reload")
        return jsonify({"success": True})
        
    elif action == "start_eu" or action == "start_all":
        targets = CONTINENTS["Europe"] if action == "start_eu" else PORTS.keys()
        for code in targets:
            if not is_active(code):
                os.makedirs(f"/etc/psiphon-{code}", exist_ok=True)
                conf = get_psiphon_config(PORTS[code], PORTS[code]-1000, code)
                svc = f'''[Unit]
Description=Psiphon Service - {NAMES[code]} ({code})
After=network.target\n\n[Service]
Type=simple\nUser=root\nWorkingDirectory=/etc/psiphon-{code}
ExecStart=/usr/local/bin/psiphon -config /etc/psiphon-{code}/config.json
Restart=always\nRestartSec=3\n\n[Install]\nWantedBy=multi-user.target'''
                with open(f"/etc/psiphon-{code}/config.json", "w") as f: f.write(conf)
                with open(f"/etc/systemd/system/psiphon-{code}.service", "w") as f: f.write(svc)
                os.system(f"systemctl enable psiphon-{code} > /dev/null 2>&1")
                os.system(f"systemctl start psiphon-{code}")
        os.system("systemctl daemon-reload")
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/start/<code>')
@requires_auth
def start_node(code):
    try:
        if code not in PORTS: return jsonify({"success": False, "error": "Invalid code"})
        os.makedirs(f"/etc/psiphon-{code}", exist_ok=True)
        conf = get_psiphon_config(PORTS[code], PORTS[code]-1000, code)
        svc = f'''[Unit]\nDescription=Psiphon Service - {NAMES[code]} ({code})\nAfter=network.target\n\n[Service]\nType=simple\nUser=root\nWorkingDirectory=/etc/psiphon-{code}\nExecStart=/usr/local/bin/psiphon -config /etc/psiphon-{code}/config.json\nRestart=always\nRestartSec=3\n\n[Install]\nWantedBy=multi-user.target'''
        with open(f"/etc/psiphon-{code}/config.json", "w") as f: f.write(conf)
        with open(f"/etc/systemd/system/psiphon-{code}.service", "w") as f: f.write(svc)
        os.system("systemctl daemon-reload")
        os.system(f"systemctl enable psiphon-{code} > /dev/null 2>&1")
        os.system(f"systemctl start psiphon-{code}")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stop/<code>')
@requires_auth
def stop_node(code):
    try:
        os.system(f"systemctl stop psiphon-{code}")
        os.system(f"systemctl disable psiphon-{code} > /dev/null 2>&1")
        os.system(f"rm -f /etc/systemd/system/psiphon-{code}.service")
        os.system(f"rm -rf /etc/psiphon-{code}")
        os.system("systemctl daemon-reload")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/tools/radar')
@requires_auth
def run_radar():
    try:
        conf_path = "/tmp/psi_radar_web.json"
        log_path = "/tmp/psi_live_web.log"
        conf = get_psiphon_config(39999, 39998, "")
        with open(conf_path, "w") as f: f.write(conf)
        os.system(f"> {log_path}")
        os.system(f"/usr/local/bin/psiphon -config {conf_path} > {log_path} 2>&1 &")
        
        live_regions = []
        start_time = time.time()
        found = False
        while time.time() - start_time < 20:
            time.sleep(1)
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as file:
                    for line in file:
                        if "AvailableEgressRegions" in line:
                            try:
                                data = json.loads(line.strip())
                                live_regions = data.get("data", {}).get("regions", [])
                                found = True
                            except: pass
                            break
            if found: break
        
        os.system(f"pkill -f {conf_path}")
        if os.path.exists(conf_path): os.remove(conf_path)
        if os.path.exists(log_path): os.remove(log_path)
        
        return jsonify({"success": len(live_regions) > 0, "regions": live_regions, "known_codes": list(PORTS.keys())})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/tools/test/<code>')
@requires_auth
def run_test(code):
    try:
        code = code.upper()
        conf_path = f"/tmp/psi_test_web_{code}.json"
        conf = get_psiphon_config(39996, 39995, code)
        with open(conf_path, "w") as f: f.write(conf)
        os.system(f"/usr/local/bin/psiphon -config {conf_path} > /dev/null 2>&1 &")
        
        start_time = time.time()
        ip_addr = ""
        while time.time() - start_time < 30:
            time.sleep(1)
            try:
                result = os.popen("curl -s -x http://127.0.0.1:39995 --connect-timeout 3 https://api.ipify.org").read().strip()
                if result and "." in result:
                    ip_addr = result
                    break
            except: pass
                
        os.system(f"pkill -f {conf_path}")
        if os.path.exists(conf_path): os.remove(conf_path)
        return jsonify({"success": bool(ip_addr), "ip": ip_addr, "code": code})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Use Waitress for production-grade speed if installed, else fallback to threaded Flask.
    # The default port 8585 is hardcoded here so install.sh can use 'sed' to change it during installation!
    if HAS_WAITRESS:
        serve(app, host='0.0.0.0', port=8585, threads=8)
    else:
        app.run(host='0.0.0.0', port=8585, threaded=True)
