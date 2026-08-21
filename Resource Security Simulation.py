import copy

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ess_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- GAME STATE ---
INITIAL_GAME_STATE = {
    "round": 1,
    "toxic_water_visible": False,
    "is_end_game": False,
    "game_over": False,
    "market": {
        "clean_water": {"name": "Clean Water", "stock": 40, "price": 5},
        "toxic_water": {"name": "Toxic Water", "stock": 0, "price": 2},
        "food": {"name": "Food", "stock": 40, "price": 5},
        "energy": {"name": "Energy", "stock": 40, "price": 5}
    },
    "teams": {
        "High-Income": {
            "name": "High-Income Urban", "budget": 100, 
            "inventory": {"water": 0, "toxic_water": 0, "food": 0, "energy": 0}, 
            "demand_reduction": {"water": 0, "food": 0, "energy": 0},
            "multiplier": 1.0, "ecocentric_count": 0, "action_streak": 0, "score": 0, "start_score": 0, 
            "locked_in": False, "purchase_history": [], "failed_minigame": False, "unmet_units": 0
        },
        "Middle-Income": {
            "name": "Middle-Income Suburban", "budget": 50, 
            "inventory": {"water": 0, "toxic_water": 0, "food": 0, "energy": 0}, 
            "demand_reduction": {"water": 0, "food": 0, "energy": 0},
            "multiplier": 1.5, "ecocentric_count": 0, "action_streak": 0, "score": 0, "start_score": 0, 
            "locked_in": False, "purchase_history": [], "failed_minigame": False, "unmet_units": 0
        },
        "Low-Income": {
            "name": "Low-Income Rural", "budget": 20, 
            "inventory": {"water": 0, "toxic_water": 0, "food": 0, "energy": 0}, 
            "demand_reduction": {"water": 0, "food": 0, "energy": 0},
            "multiplier": 2.0, "ecocentric_count": 0, "action_streak": 0, "score": 0, "start_score": 0, 
            "locked_in": False, "purchase_history": [], "failed_minigame": False, "unmet_units": 0
        }
    },
    "loans": []
}

game_state = copy.deepcopy(INITIAL_GAME_STATE)

# --- REAL-TIME SCORING LOGIC ---
def calculate_scores():
    if game_state.get("is_end_game", False):
        base_target = game_state["round"] * 4
        unmet_penalty_rate = 20
    else:
        base_target = game_state["round"] * 2 
        unmet_penalty_rate = 10
    
    for team_key, team in game_state["teams"].items():
        raw_score = 0
        unmet_units = 0
        
        # Availability & Demand Reduction Check
        for item in ["water", "food", "energy"]:
            target = max(0, base_target - team["demand_reduction"][item])
            count = team["inventory"][item]
            if count >= target:
                raw_score += 10 
            else:
                deficit = target - count
                unmet_units += deficit
                raw_score -= deficit * unmet_penalty_rate 

        team["unmet_units"] = unmet_units
        
        # Safety Penalty
        raw_score -= (team["inventory"]["toxic_water"] * 15)
        
        # Affordability Bonus
        raw_score += int(team["budget"] // 5)
        
        # Adaptation Bonus with Compounding Action Streak
        base_adaptation = team["ecocentric_count"] * 20
        streak_bonus = max(0, team["action_streak"] - 1) * 10 if team["action_streak"] > 0 else 0
        
        raw_score += (base_adaptation + streak_bonus)
        
        # Apply Equity Multiplier
        team["score"] = int(raw_score * team["multiplier"])


def reset_game_state():
    global game_state
    game_state = copy.deepcopy(INITIAL_GAME_STATE)
    calculate_scores()
    for team in game_state["teams"].values():
        team["start_score"] = team["score"]

# --- FRONTEND HTML/JS ---
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>ESS Resource Security Simulation</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f9; color: #333; line-height: 1.6; }
        h1, h2, h3, h4 { text-align: center; margin-bottom: 5px; }
        .grid { display: flex; gap: 15px; margin-bottom: 20px; justify-content: center; flex-wrap: wrap; }
        .box { background: white; border: 2px solid #333; padding: 15px; border-radius: 8px; flex: 1; min-width: 320px; position: relative; overflow: visible;}
        .market-box { background: #e3f2fd; border: 2px solid #1565c0; text-align: center; font-size: 1.2em; }
        .controls { text-align: center; margin-top: 20px; padding: 15px; background: #fff3e0; border: 2px solid #ff9800; border-radius: 8px;}
        .bank-controls { background: #e8f5e9; border: 2px solid #4caf50; border-radius: 8px; padding: 15px; margin-top: 20px; text-align: center; }
        button { padding: 8px 12px; margin: 3px; cursor: pointer; border-radius: 4px; border: 1px solid #ccc; background: #eee; font-size: 0.9em; }
        button:hover { background: #ddd; }
        .buy-btn { background: #4caf50; color: white; border: none; font-weight: bold; width: 100%; margin-bottom: 4px; }
        .buy-btn:hover { background: #45a049; }
        .buy-btn:disabled { background: #ccc; cursor: not-allowed; opacity: 0.6; }
        .submit-btn { background: #2196F3; color: white; font-weight: bold; width: 100%; border: none; padding: 10px; font-size: 1em; }
        .submit-btn:hover { background: #1976D2; }
        .undo-btn { background: #ffc107; color: #333; font-weight: bold; border: none; width: 100%; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .undo-btn:hover { background: #ffb300; }
        
        .strategy-container { display: flex; gap: 8px; margin-top: 10px; }
        .strategy-col { flex: 1; background: #f8f9fa; border: 1px solid #ddd; padding: 8px 4px; border-radius: 6px; text-align: center; }
        .strategy-col h4 { font-size: 0.82em; white-space: nowrap; margin: 4px 0 8px 0; text-align: center; letter-spacing: -0.2px; }
        .supply-btn { background: #8e44ad; color: white; font-weight: bold; width: 100%; border: none; font-size: 0.85em; padding: 8px 4px; }
        .supply-btn:hover { background: #9b59b6; }
        .demand-btn { background: #16a085; color: white; font-weight: bold; width: 100%; border: none; font-size: 0.85em; padding: 8px 4px; }
        .demand-btn:hover { background: #1abc9c; }
        button:disabled { background: #7f8c8d !important; cursor: not-allowed; opacity: 0.7; }

        .score-badge { background: #ffd700; color: #333; padding: 8px 12px; border-radius: 20px; font-weight: bold; font-size: 1.3em; display: inline-block; margin-bottom: 10px; border: 2px solid #daa520; }
        .streak-badge { background: #e67e22; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.85em; display: inline-block; margin-bottom: 15px; }

        .inventory-panel { display: flex; gap: 10px; margin-bottom: 15px; }
        .inv-section { flex: 1; padding: 10px; border-radius: 5px; font-size: 0.85em; }
        .inv-need { background: #f9f9f9; border: 1px solid #ddd; }
        .inv-bank { background: #e8f5e9; border: 1px solid #c8e6c9; }
        .inv-section h4 { margin: 0 0 8px 0; font-size: 1em; border-bottom: 1px solid #ccc; padding-bottom: 4px;}
        .inv-item { margin-bottom: 4px; font-weight: bold; }
        
        .loan-form { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; align-items: center; margin-top: 10px; }
        .loan-form label { font-weight: bold; font-size: 0.9em; }
        .loan-form input, .loan-form select { padding: 6px; border: 1px solid #ccc; border-radius: 4px; }
        .repayment-box { background: #fff3cd; border: 2px solid #ffeba2; padding: 10px; border-radius: 6px; margin-top: 10px; text-align: left; }

        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.7); }
        .modal-content { background-color: #fff; margin: 4% auto; padding: 25px; border: 3px solid #333; width: 65%; max-width: 600px; border-radius: 10px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
        .modal-btn { background: #ff9800; color: white; font-weight: bold; font-size: 1.1em; padding: 10px 20px; border: none; margin-top: 15px; border-radius: 5px; }
        
        #intro-screen { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .start-btn { display: block; width: 100%; background: #1565c0; color: white; font-size: 1.2em; font-weight: bold; padding: 15px; margin-top: 20px; border: none; border-radius: 5px;}

        /* Minigame Styles */
        #scrambled-word { font-size: 2.3em; letter-spacing: 5px; margin: 15px 0; font-weight: bold; color: #2c3e50; }
        #minigame-timer { font-size: 1.4em; color: #e74c3c; font-weight: bold; }
        #minigame-input { font-size: 1.4em; text-align: center; width: 80%; text-transform: uppercase; margin-bottom: 15px;}
        #minigame-hint { font-size: 1.1em; color: #2c3e50; background: #eef2f7; border-left: 4px solid #3498db; padding: 12px; border-radius: 4px; margin: 12px 0; text-align: left; line-height: 1.4; }

        /* --- SVG VECTOR ANIMATION STYLES & KEYFRAMES --- */
        .svg-anim-canvas {
            width: 100%;
            height: 180px;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            margin-bottom: 12px;
            overflow: hidden;
        }

        /* Rainwater Harvesting Keyframes */
        @keyframes rainDrop {
            0% { transform: translateY(-10px); opacity: 0; }
            30% { opacity: 1; }
            100% { transform: translateY(45px); opacity: 0; }
        }
        @keyframes wellFill {
            0% { height: 5px; y: 155px; }
            100% { height: 35px; y: 125px; }
        }
        @keyframes pipeFlow {
            0% { stroke-dashoffset: 40; }
            100% { stroke-dashoffset: 0; }
        }
        .rain-drop { animation: rainDrop 1s infinite linear; }
        .well-water { animation: wellFill 2.5s forwards ease-out; }
        .pipe-stream { stroke-dasharray: 6; animation: pipeFlow 0.8s infinite linear; }

        /* Polyculture Farming Keyframes */
        @keyframes cropSprout {
            0% { transform: scaleY(0); }
            100% { transform: scaleY(1); }
        }
        @keyframes fruitPop {
            0% { transform: scale(0); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        .crop-stalk { transform-origin: bottom center; animation: cropSprout 1.5s forwards ease-out; }
        .crop-produce { transform-origin: center; animation: fruitPop 0.5s 1.2s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275); opacity: 0; }

        /* Energy Storage Keyframes */
        @keyframes batteryCharge {
            0% { width: 0px; }
            100% { width: 110px; }
        }
        @keyframes currentFlow {
            0% { stroke-dashoffset: 30; }
            100% { stroke-dashoffset: 0; }
        }
        .battery-fill { animation: batteryCharge 2s forwards ease-in-out; }
        .power-line { stroke-dasharray: 6; animation: currentFlow 0.8s infinite linear; }

        /* Greywater Recycling Keyframes */
        @keyframes dropFilter {
            0% { transform: translateY(0); fill: #94a3b8; }
            50% { fill: #38bdf8; }
            100% { transform: translateY(50px); fill: #0284c7; }
        }
        .filter-drop { animation: dropFilter 1.5s infinite ease-in; }

        /* Plant-Based Diets Keyframes */
        @keyframes meterDrop {
            0% { height: 70px; y: 40px; }
            100% { height: 20px; y: 90px; }
        }
        .resource-meter { animation: meterDrop 1.8s forwards cubic-bezier(0.4, 0, 0.2, 1); }

        /* Public Transport Keyframes */
        @keyframes trainArrival {
            0% { transform: translateX(-180px); }
            60% { transform: translateX(0px); }
            100% { transform: translateX(0px); }
        }
        @keyframes commuterBoard {
            0% { transform: translateY(0); opacity: 1; }
            100% { transform: translateY(-15px); opacity: 0; }
        }
        @keyframes carFade {
            0% { opacity: 1; }
            100% { opacity: 0.15; }
        }
        .subway-train { animation: trainArrival 2s ease-out forwards; }
        .passengers { animation: commuterBoard 1.2s 1.8s forwards ease-in; }
        .fading-car { animation: carFade 1.5s 1s forwards ease-out; }

        /* Strategy Modal Entrance Animation */
        @keyframes scaleIn {
            0% { transform: scale(0.6); opacity: 0; }
            70% { transform: scale(1.05); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
        .anim-feedback { animation: scaleIn 0.4s ease-out forwards; }
        .strategy-commentary { background: #f0f9ff; border-left: 5px solid #0284c7; padding: 12px; border-radius: 6px; text-align: left; font-size: 0.95em; margin-top: 10px; line-height: 1.4; color: #0c4a6e; }

        /* Floating Income Animation */
        @keyframes floatUp {
            0% { opacity: 0; transform: translate(-50%, 0) scale(0.8); }
            15% { opacity: 1; transform: translate(-50%, -10px) scale(1.1); }
            80% { opacity: 1; transform: translate(-50%, -40px) scale(1); }
            100% { opacity: 0; transform: translate(-50%, -50px) scale(1); }
        }
        .income-anim { position: absolute; top: 100px; left: 50%; transform: translateX(-50%); color: #4caf50; font-weight: bold; font-size: 2.2em; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); animation: floatUp 2.5s ease-out forwards; pointer-events: none; z-index: 100; }

        /* Shock Disturbance Modal */
        .shock-caption {
            font-size: 1.02em;
            line-height: 1.5;
            color: #374151;
            text-align: left;
            background: #f8fafc;
            border-left: 4px solid #ef4444;
            padding: 12px;
            border-radius: 6px;
            margin: 12px 0 16px;
        }
        .shock-anim {
            width: 100%;
            height: 170px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            background: linear-gradient(180deg, #fff7ed 0%, #fef2f2 100%);
            position: relative;
            overflow: hidden;
            margin-bottom: 12px;
        }
        .shock-sun {
            position: absolute;
            top: 16px;
            left: 18px;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: #f59e0b;
            box-shadow: 0 0 0 rgba(245, 158, 11, 0.45);
            animation: heatPulse 1.6s infinite ease-in-out;
        }
        .shock-drop {
            position: absolute;
            top: 12px;
            right: 28px;
            width: 14px;
            height: 22px;
            background: #2563eb;
            border-radius: 50% 50% 60% 60%;
            transform: rotate(15deg);
            animation: spillDrop 1.4s infinite ease-in;
        }
        .shock-bars {
            position: absolute;
            bottom: 18px;
            left: 14px;
            right: 14px;
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        .shock-bar {
            flex: 1;
            border-radius: 5px 5px 0 0;
            transform-origin: bottom center;
        }
        .shock-bar.food { height: 36px; background: #f59e0b; animation: priceRise 1.2s infinite alternate; }
        .shock-bar.water { height: 48px; background: #0ea5e9; animation: priceRise 1.2s 0.2s infinite alternate; }
        .shock-bar.clean { height: 58px; background: #1d4ed8; animation: priceRise 1.2s 0.4s infinite alternate; }
        .shock-labels {
            display: flex;
            gap: 12px;
            font-size: 0.82em;
            color: #475569;
            margin-top: 4px;
        }
        .shock-labels span { flex: 1; text-align: center; }

        @keyframes heatPulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.45); }
            100% { transform: scale(1.08); box-shadow: 0 0 0 16px rgba(245, 158, 11, 0); }
        }
        @keyframes spillDrop {
            0% { transform: translateY(0) rotate(15deg); opacity: 0.8; }
            100% { transform: translateY(110px) rotate(15deg); opacity: 0.2; }
        }
        @keyframes priceRise {
            0% { transform: scaleY(0.82); filter: saturate(0.95); }
            100% { transform: scaleY(1.14); filter: saturate(1.2); }
        }

        /* Hyperinflation Crisis Modal */
        .crisis-caption {
            font-size: 1.02em;
            line-height: 1.5;
            color: #3f2b1b;
            text-align: left;
            background: #fff7ed;
            border-left: 4px solid #d97706;
            padding: 12px;
            border-radius: 6px;
            margin: 12px 0 16px;
        }
        .crisis-anim {
            width: 100%;
            height: 170px;
            border-radius: 8px;
            border: 1px solid #f5d0a6;
            background: linear-gradient(180deg, #fffbeb 0%, #fff1e6 100%);
            position: relative;
            overflow: hidden;
            margin-bottom: 12px;
        }
        .crisis-arrow {
            position: absolute;
            left: 18px;
            top: 18px;
            color: #dc2626;
            font-size: 36px;
            font-weight: bold;
            animation: crisisRise 1.1s infinite alternate ease-in-out;
        }
        .crisis-bars {
            position: absolute;
            bottom: 18px;
            left: 72px;
            right: 14px;
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        .crisis-bar {
            flex: 1;
            border-radius: 5px 5px 0 0;
            transform-origin: bottom center;
            animation: crisisPulse 1.2s infinite alternate;
        }
        .crisis-bar.water { height: 40px; background: #0ea5e9; }
        .crisis-bar.food { height: 52px; background: #f59e0b; animation-delay: 0.15s; }
        .crisis-bar.energy { height: 64px; background: #ef4444; animation-delay: 0.3s; }
        .crisis-labels {
            display: flex;
            gap: 12px;
            font-size: 0.82em;
            color: #7c2d12;
            margin-top: 4px;
        }
        .crisis-labels span { flex: 1; text-align: center; }

        @keyframes crisisRise {
            0% { transform: translateY(0) scale(1); opacity: 0.85; }
            100% { transform: translateY(-10px) scale(1.08); opacity: 1; }
        }
        @keyframes crisisPulse {
            0% { transform: scaleY(0.84); filter: saturate(0.9); }
            100% { transform: scaleY(1.18); filter: saturate(1.25); }
        }
    </style>
</head>
<body>

    <!-- ROUND SUMMARY MODAL -->
    <div id="summary-modal" class="modal">
        <div class="modal-content">
            <h1 id="modal-title">Round Complete</h1>
            <p id="modal-event" style="font-size: 1.2em; font-style: italic; color: #555;"></p>
            <div id="modal-repayments"></div>
            <div id="modal-scores" style="font-size: 1.1em; margin: 15px 0; text-align: left; display: inline-block;"></div>
            <br>
            <button class="modal-btn" onclick="closeModal()">Acknowledge & Begin Next Round</button>
        </div>
    </div>

    <!-- END GAME CLIMATE TIPPING POINT MODAL -->
    <div id="endgame-modal" class="modal">
        <div class="modal-content" style="max-width: 750px; border-color: #b71c1c;">
            <h1 style="color: #b71c1c; margin-bottom: 5px;">CLIMATE TIPPING POINT: END GAME</h1>
            <h2 id="endgame-winner-banner" style="color: #2e7d32; background: #e8f5e9; padding: 12px; border-radius: 6px; margin: 10px 0;"></h2>
            <p style="font-size: 1em; color: #444; margin-bottom: 8px;">Climate Disturbance has halted the market economy. No new buying is possible, so each community must use what it already has in inventory to meet the full end-game quotas.</p>
            <p style="font-size: 0.95em; color: #666; margin-bottom: 15px;"><strong>Resource Gap</strong> shows missing units of water, food, or energy, and <strong>Safety Loss</strong> shows the CRS cost of toxic water consumed.</p>
            <div id="endgame-table-container"></div>
            <button class="modal-btn" style="background: #b71c1c; width: 100%; margin-top: 20px;" onclick="closeEndgameModal()">Close Final Audit</button>
        </div>
    </div>

    <!-- PRE-SHOCK DISTURBANCE MODAL -->
    <div id="shock-modal" class="modal">
        <div class="modal-content" style="max-width: 620px; border-color: #dc2626;">
            <h2 style="color: #b91c1c; margin-top: 0;">Climate Disturbance Incoming</h2>
            <div class="shock-anim">
                <div class="shock-sun"></div>
                <div class="shock-drop"></div>
                <div class="shock-bars">
                    <div class="shock-bar food"></div>
                    <div class="shock-bar water"></div>
                    <div class="shock-bar clean"></div>
                </div>
            </div>
            <div class="shock-labels">
                <span>Food Price</span>
                <span>Water Price</span>
                <span>Purified Water Cost</span>
            </div>
            <p class="shock-caption">
                A severe drought is raising food and water prices, while a chemical spill is increasing the cost of purified clean water.
                Confirm to trigger the disturbance and continue to the next round.
            </p>
            <button class="modal-btn" style="background:#dc2626; width:100%; margin-top: 6px;" onclick="confirmShockAdvance()">Trigger Disturbance</button>
            <button class="modal-btn" style="background:#cbd5e1; color:#111827; width:100%;" onclick="closeShockModal()">Cancel</button>
        </div>
    </div>

    <!-- PRE-CRISIS HYPERINFLATION MODAL -->
    <div id="crisis-modal" class="modal">
        <div class="modal-content" style="max-width: 620px; border-color: #d97706;">
            <h2 style="color: #b45309; margin-top: 0;">Hyperinflation Warning</h2>
            <div class="crisis-anim">
                <div class="crisis-arrow">↑↑</div>
                <div class="crisis-bars">
                    <div class="crisis-bar water"></div>
                    <div class="crisis-bar food"></div>
                    <div class="crisis-bar energy"></div>
                </div>
            </div>
            <div class="crisis-labels">
                <span>Water Price</span>
                <span>Food Price</span>
                <span>Energy Price</span>
            </div>
            <p class="crisis-caption">
                A hyperinflation surge is destabilizing the economy. The cost of bare essentials spike sharply, and each team will face much higher costs for clean water, food, and energy. Confirm to trigger the crisis and continue to the next round.
            </p>
            <button class="modal-btn" style="background:#d97706; width:100%; margin-top: 6px;" onclick="confirmCrisisAdvance()">Trigger Hyperinflation</button>
            <button class="modal-btn" style="background:#cbd5e1; color:#111827; width:100%;" onclick="closeCrisisModal()">Cancel</button>
        </div>
    </div>

    <!-- MINIGAME MODAL -->
    <div id="minigame-modal" class="modal">
        <div class="modal-content" id="minigame-card">
            <h1 id="minigame-title">Action Challenge</h1>
            <p id="minigame-desc">Unscramble the DP ESS term to complete this adaptation project!</p>
            <div id="minigame-hint"></div>
            <div id="minigame-timer">Time Left: 20s</div>
            <div id="scrambled-word"></div>
            <input type="text" id="minigame-input" placeholder="Type your answer..." autocomplete="off">
            <br>
            <button class="modal-btn" id="minigame-submit-btn" onclick="submitMinigame()">Submit Answer</button>
            <button class="modal-btn" style="background: #ccc; color: #333;" onclick="failMinigame()">Cancel / Give Up</button>
        </div>
    </div>

    <!-- STRATEGY ANIMATION FEEDBACK MODAL -->
    <div id="strategy-modal" class="modal">
        <div class="modal-content anim-feedback" style="border-color: #2ecc71; max-width: 550px;">
            <h2 id="strategy-feedback-title" style="color: #27ae60; margin-top: 0; margin-bottom: 2px;">Strategy Executed!</h2>
            <p id="strategy-term-tag" style="font-weight: bold; color: #8e44ad; font-size: 0.95em; margin-top: 0; margin-bottom: 10px;"></p>
            
            <div id="strategy-commentary-text" style="text-align: left;"></div>

            <button class="modal-btn" style="background: #2ecc71; width: 100%; margin-top: 10px;" onclick="closeStrategyModal()">Continue Simulation 🚀</button>
        </div>
    </div>

    <!-- INTRO SCREEN -->
    <div id="intro-screen">
        <h1>🌍 Resource Security Simulation</h1>
        <h2>Strategic Pathways:</h2>
        <ul>
            <li><strong>The Quota (Survival Baseline):</strong> Secure Water, Food, and Energy every round.</li>
            <li><strong>Market Purchasing:</strong> Buy resources directly from the global market economy, using available funds.</li>
            <li><strong>ESS Minigames:</strong> Features 105 DP ESS syllabus terms across Topics 1, 2, 3, and 7.1.</li>
            <li><strong>Inter-Team Loans:</strong> Negotiate loans between teams, including repayment amounts & timeframe.</li>
        </ul>
        
        <h2 style="margin-top: 25px; color: #1565c0;">🏆 How to Earn Community Resilience (CRS) Points:</h2>
        <ul style="background: #f8f9fa; padding: 15px 35px; border-radius: 8px; border-left: 5px solid #2196F3; font-size: 1.05em;">
            <li style="margin-bottom: 8px;"><strong>Availability:</strong> <b>+10 points</b> for meeting each resource target. <em>Penalty: -10 pts per missing unit!</em></li>
            <li style="margin-bottom: 8px;"><strong>Adaptation:</strong> <b>+20 points</b> for each successful ESS action (minigame), plus compounding streak bonuses.</li>
            <li style="margin-bottom: 8px;"><strong>Affordability:</strong> <b>+1 point</b> for every $5 of budget saved.</li>
            <li style="margin-bottom: 8px; color: #d32f2f;"><strong>Toxic Penalty:</strong> <b>-15 points</b> for every unit of Toxic Water consumed.</li>
            <li><strong>Equity Multiplier:</strong> High-Income <b>(1.0x)</b>, Middle-Income <b>(1.5x)</b>, Low-Income <b>(2.0x)</b>.</li>
        </ul>

        <button class="start-btn" onclick="startDashboard()">Launch Teacher Dashboard 🚀</button>
    </div>

    <!-- MAIN DASHBOARD -->
    <div id="game-dashboard" style="display: none;">
        <h1>🌍 Resource Security - Class Dashboard</h1>
        
        <div class="box market-box">
            <h2>Global Market (Round <span id="round">1</span>)</h2>
            <div class="grid" id="market-display"></div>
        </div>

        <div class="grid">
            <div class="box" id="panel-High-Income"></div>
            <div class="box" id="panel-Middle-Income"></div>
            <div class="box" id="panel-Low-Income"></div>
        </div>

        <div class="bank-controls">
            <h2>🏦 Bank & Contractual Inter-Team Loans</h2>
            <div class="loan-form">
                <div>
                    <label>Lender:</label>
                    <select id="transfer-from">
                        <option value="High-Income">High-Income</option>
                        <option value="Middle-Income">Middle-Income</option>
                        <option value="Low-Income">Low-Income</option>
                    </select>
                </div>
                <div>
                    <label>Borrower:</label>
                    <select id="transfer-to">
                        <option value="High-Income">High-Income</option>
                        <option value="Middle-Income">Middle-Income</option>
                        <option value="Low-Income" selected>Low-Income</option>
                    </select>
                </div>
                <div>
                    <label>Loan Amount ($):</label>
                    <input type="number" id="transfer-amount" value="10" min="1" style="width: 60px;">
                </div>
                <div>
                    <label>Repayment Amount ($):</label>
                    <input type="number" id="repayment-amount" value="15" min="1" style="width: 60px;">
                </div>
                <div>
                    <label>Due In (Rounds):</label>
                    <input type="number" id="due-in-rounds" value="1" min="1" max="5" style="width: 50px;">
                </div>
                <div>
                    <button onclick="transferFunds()" style="background: #4caf50; color: white; border: none; font-weight:bold; padding: 8px 15px;">💸 Issue Loan Contract</button>
                </div>
            </div>
            <div id="active-loans-display" style="margin-top: 10px; font-size: 0.9em;"></div>
        </div>

        <div class="controls">
            <h2>⚙️ Advance Round Controls</h2>
            <button onclick="advanceRound('normal')">✅ Advance to Next Round (Normal Setting)</button>
            <button onclick="advanceRound('shock')">🚨 Advance & Trigger Shock (Drought & Spill)</button>
            <button onclick="advanceRound('crisis')">🔥 Advance & Trigger Crisis (Hyperinflation)</button>
            <br><br>
            <button onclick="triggerEndGame()" style="background: #b71c1c; color: white; font-weight: bold; border: none; padding: 10px 20px; font-size: 1.05em;">🔥 TRIGGER END GAME (Climate Tipping Point)</button>
        </div>
    </div>

    <script>
        const socket = io();
        const teams = ["High-Income", "Middle-Income", "Low-Income"];
        const stipends = {"High-Income": 30, "Middle-Income": 20, "Low-Income": 10};
        
        let currentState = null;
        let streakAlertsShown = {"High-Income": false, "Middle-Income": false, "Low-Income": false};
        
        // --- 105 DP ESS SL VOCABULARY WORDS ---
        const essVocab = [
            "ECOCENTRIC", "TECHNOCENTRIC", "ANTHROPOCENTRIC", "SUSTAINABILITY", "EQUILIBRIUM", 
            "FOOTPRINT", "POLLUTION", "BIODEGRADABLE", "PERSISTENT", "FEEDBACK", 
            "SYSTEM", "CHRONIC", "STORAGE", "CAPACITY", "STEWARDSHIP", 
            "TRANSFORMATION", "TRANSITION", "MODEL", "INPUT",
            "ECOSYSTEM", "COMMUNITY", "POPULATION", "HABITAT", "PHOTOSYNTHESIS", 
            "RESPIRATION", "PRODUCTIVITY", "HERBIVORE", "CARNIVORE", "OMNIVORE", 
            "DECOMPOSER", "PRODUCER", "CONSUMER", "BIOACCUMULATION", "BIOMAGNIFICATION", 
            "BIOMASS", "MUTUALISM", "PARASITISM", "PREDATION", "COMPETITION", 
            "SUCCESSION", "ZONATION", "CLIMAX", "PIONEER", "TRANSECT", 
            "QUADRAT", "INSOLATION", "BIOME", "NITROGEN", "TROPHIC", 
            "FLOW", "PYRAMID", "ABIOTIC", "BIOTIC", "TUNDRA",
            "BIODIVERSITY", "SPECIATION", "EVOLUTION", "EXTINCTION", "HOTSPOT", 
            "ENDEMIC", "KEYSTONE", "FLAGSHIP", "UMBRELLA", "CONSERVATION", 
            "ISOLATION", "GENETIC", "RESERVE", "CORRIDOR", "CITES", 
            "SEEDBANK", "ENDANGERED", "VULNERABLE", "RESTORATION", "INVASIVE", 
            "DIVERSITY", "MUTATION", "TAXONOMY",
            "CAPITAL", "INCOME", "RESOURCE", "GOODS", "SERVICES", 
            "DEMAND", "SEQUESTRATION", "RENEWABLE", "NONRENEWABLE", "INTRINSIC", 
            "AESTHETIC", "CULTURAL", "DYNAMIC", "SECURITY", "EXPLOITATION", 
            "REGENERATION", "HARVESTING", "VALUE", "SOCIOCULTURAL", "PERSPECTIVE", 
            "TIMBER", "FRESHWATER", "FINITE", "SPIRITUAL", "CORK", 
            "HEALTH", "PROTECTION"
        ];

        // --- RELATED WORDS DICTIONARY ---
        const essRelatedWords = {
            "PYRAMID": ["numbers", "biomass", "productivity"],
            "ECOCENTRIC": ["deep ecology", "biorights", "nature-centered"],
            "TECHNOCENTRIC": ["technology", "cornucopian", "geoengineering"],
            "ANTHROPOCENTRIC": ["human-centered", "managerial", "resource use"],
            "SUSTAINABILITY": ["replenishment", "yield", "future generations"],
            "EQUILIBRIUM": ["steady-state", "balance", "feedback"],
            "FOOTPRINT": ["area", "consumption", "carrying capacity"],
            "POLLUTION": ["contamination", "point source", "effluent"],
            "BIODEGRADABLE": ["decomposers", "organic matter", "breakdown"],
            "PERSISTENT": ["DDT", "accumulation", "non-degradable"],
            "FEEDBACK": ["loops", "amplification", "stabilization"],
            "SYSTEM": ["inputs", "outputs", "storages"],
            "CHRONIC": ["long-term", "persistent", "exposure"],
            "STORAGE": ["stock", "accumulation", "reservoir"],
            "CAPACITY": ["carrying", "limit", "threshold"],
            "STEWARDSHIP": ["responsibility", "conservation", "management"],
            "TRANSFORMATION": ["state change", "energy flow", "chemical process"],
            "TRANSITION": ["shift", "change", "energy mix"],
            "MODEL": ["simplified", "simulation", "prediction"],
            "INPUT": ["energy inflow", "matter inflow", "entry"],
            "ECOSYSTEM": ["community", "abiotic environment", "interactions"],
            "COMMUNITY": ["populations", "biotic", "coexisting species"],
            "POPULATION": ["same species", "group", "interbreeding"],
            "HABITAT": ["environment", "living area", "niche"],
            "PHOTOSYNTHESIS": ["producers", "chlorophyll", "glucose"],
            "RESPIRATION": ["cellular", "ATP", "carbon dioxide"],
            "PRODUCTIVITY": ["gross", "net", "biomass accumulation"],
            "HERBIVORE": ["primary consumer", "plant-eater", "trophic level 2"],
            "CARNIVORE": ["secondary consumer", "meat-eater", "predator"],
            "OMNIVORE": ["plants and meat", "flexible diet", "consumer"],
            "DECOMPOSER": ["fungi", "bacteria", "nutrient recycling"],
            "PRODUCER": ["autotroph", "plants", "photosynthesis"],
            "CONSUMER": ["heterotroph", "ingestion", "trophic levels"],
            "BIOACCUMULATION": ["individual organism", "fat tissue", "toxin buildup"],
            "BIOMAGNIFICATION": ["apex predators", "food chain", "increasing concentration"],
            "BIOMASS": ["dry weight", "organic matter", "stored energy"],
            "MUTUALISM": ["symbiosis", "win-win", "both benefit"],
            "PARASITISM": ["host", "harmful", "symbiosis"],
            "PREDATION": ["predator", "prey", "hunting"],
            "COMPETITION": ["limited resources", "niche overlap", "survival"],
            "SUCCESSION": ["pioneer species", "climax community", "seral stages"],
            "ZONATION": ["spatial gradient", "altitudinal", "tidal bands"],
            "CLIMAX": ["stable community", "mature ecosystem", "equilibrium"],
            "PIONEER": ["colonizers", "lichens", "early succession"],
            "TRANSECT": ["line sampling", "belt", "gradient measurement"],
            "QUADRAT": ["sampling frame", "density", "percentage cover"],
            "INSOLATION": ["solar radiation", "sunlight", "incoming energy"],
            "BIOME": ["climate", "vegetation zones", "latitude"],
            "NITROGEN": ["cycle", "fixation", "macronutrient"],
            "TROPHIC": ["food chain", "energy transfer", "levels"],
            "FLOW": ["movement", "energy transfer", "matter transport"],
            "ABIOTIC": ["non-living", "temperature", "pH"],
            "BIOTIC": ["living components", "organisms", "biological factors"],
            "TUNDRA": ["permafrost", "cold climate", "low vegetation"],
            "BIODIVERSITY": ["richness", "genetic", "species diversity"],
            "SPECIATION": ["evolution", "isolation", "new species"],
            "EVOLUTION": ["natural selection", "adaptation", "descent with modification"],
            "EXTINCTION": ["loss of species", "biodiversity crisis", "mass die-off"],
            "HOTSPOT": ["high endemicity", "threatened habitat", "conservation priority"],
            "ENDEMIC": ["native", "restricted geography", "unique species"],
            "KEYSTONE": ["disproportionate impact", "top predator", "ecosystem stability"],
            "FLAGSHIP": ["charismatic species", "public appeal", "awareness campaign"],
            "UMBRELLA": ["broad habitat protection", "large range", "co-benefits"],
            "CONSERVATION": ["protection", "preservation", "sustainable management"],
            "ISOLATION": ["geographic", "reproductive", "barriers"],
            "GENETIC": ["DNA diversity", "gene pool", "variation"],
            "RESERVE": ["protected area", "national park", "sanctuary"],
            "CORRIDOR": ["habitat link", "migration route", "fragmentation solution"],
            "CITES": ["endangered species", "trade regulation", "international treaty"],
            "SEEDBANK": ["ex-situ conservation", "gene storage", "future restoration"],
            "ENDANGERED": ["high extinction risk", "red list", "threatened"],
            "VULNERABLE": ["at risk", "declining population", "threatened category"],
            "RESTORATION": ["rehabilitation", "ecosystem recovery", "rewilding"],
            "INVASIVE": ["non-native", "disruptive", "outcompeting"],
            "DIVERSITY": ["variety", "heterogeneity", "index"],
            "MUTATION": ["genetic change", "DNA alteration", "variation source"],
            "TAXONOMY": ["classification", "naming", "hierarchy"],
            "CAPITAL": ["natural stock", "wealth", "resource storage"],
            "INCOME": ["sustainable yield", "annual harvest", "natural growth"],
            "RESOURCE": ["valuable goods", "materials", "supplies"],
            "GOODS": ["physical products", "timber", "crops"],
            "SERVICES": ["ecosystem functions", "water filtration", "pollination"],
            "DEMAND": ["consumption rate", "human usage", "market force"],
            "SEQUESTRATION": ["carbon storage", "sinks", "locking away"],
            "RENEWABLE": ["replenishable", "solar", "infinite supply"],
            "NONRENEWABLE": ["fossil fuels", "finite", "depletion"],
            "INTRINSIC": ["inherent value", "biorights", "non-monetary"],
            "AESTHETIC": ["beauty", "landscape appreciation", "non-material value"],
            "CULTURAL": ["tradition", "heritage", "societal value"],
            "DYNAMIC": ["changing", "active balance", "flux"],
            "SECURITY": ["guaranteed access", "safety", "resilience"],
            "EXPLOITATION": ["over-use", "extraction", "resource harvesting"],
            "REGENERATION": ["recovery", "regrowth", "renewal"],
            "HARVESTING": ["extraction", "yielding", "collection"],
            "VALUE": ["economic", "intrinsic", "cultural worth"],
            "SOCIOCULTURAL": ["society", "tradition", "human perception"],
            "PERSPECTIVE": ["worldview", "viewpoint", "lens"],
            "TIMBER": ["wood", "forestry", "building resource"],
            "FRESHWATER": ["clean water", "rivers", "lakes"],
            "FINITE": ["limited supply", "non-renewable", "depletable"],
            "SPIRITUAL": ["sacred spaces", "connection to nature", "reverence"],
            "CORK": ["renewable material", "bark harvest", "sustainable forestry"],
            "HEALTH": ["well-being", "ecosystem vitality", "clean environment"],
            "PROTECTION": ["safeguarding", "conservation", "legislation"]
        };

        // --- UPDATED ANIMATED VECTOR STRATEGY DETAILS & CAPTIONS ---
        const strategyDetails = {
            "Rainwater Harvesting": {
                svg: `
                <svg class="svg-anim-canvas" viewBox="0 0 300 170">
                    <!-- Roof Line -->
                    <path d="M 30 70 L 120 20 L 210 70" fill="none" stroke="#475569" stroke-width="6" stroke-linecap="round"/>
                    <path d="M 205 70 L 215 70 L 215 130 L 250 130 L 250 145" fill="none" stroke="#64748b" stroke-width="4" class="pipe-stream"/>
                    <!-- Rain Drops -->
                    <circle cx="70" cy="30" r="3" fill="#38bdf8" class="rain-drop" style="animation-delay: 0.1s;"/>
                    <circle cx="120" cy="10" r="3" fill="#38bdf8" class="rain-drop" style="animation-delay: 0.4s;"/>
                    <circle cx="160" cy="35" r="3" fill="#38bdf8" class="rain-drop" style="animation-delay: 0.2s;"/>
                    <!-- Underground Well/Cistern -->
                    <rect x="230" y="110" width="50" height="50" rx="4" fill="#cbd5e1" stroke="#475569" stroke-width="3"/>
                    <rect x="233" y="125" width="44" height="32" rx="2" fill="#0284c7" class="well-water"/>
                    <text x="255" y="102" font-size="10" font-weight="bold" fill="#334155" text-anchor="middle">Cistern Well</text>
                </svg>`,
                comment: "<div class='strategy-commentary'>Capturing precipitation directly increases local water storage. This builds water security without over-extracting groundwater aquifers.</div>"
            },
            "Polyculture Farming": {
                svg: `
                <svg class="svg-anim-canvas" viewBox="0 0 300 170">
                    <path d="M 20 140 Q 150 135 280 140 L 280 160 L 20 160 Z" fill="#78350f"/>
                    
                    <!-- Crop 1: Tall Corn Stalk -->
                    <g transform="translate(60, 0)">
                        <path d="M 0 140 L 0 60" fill="none" stroke="#15803d" stroke-width="4" stroke-linecap="round" class="crop-stalk"/>
                        <path d="M 0 90 Q -15 80 -20 65 Q -5 75 0 90" fill="#22c55e" class="crop-produce"/>
                        <path d="M 0 80 Q 15 70 20 55 Q 5 65 0 80" fill="#22c55e" class="crop-produce"/>
                        <circle cx="0" cy="55" r="5" fill="#facc15" class="crop-produce"/>
                    </g>

                    <!-- Crop 2: Leafy Greens -->
                    <g transform="translate(150, 0)">
                        <path d="M 0 140 L 0 95" fill="none" stroke="#16a34a" stroke-width="5" stroke-linecap="round" class="crop-stalk"/>
                        <circle cx="-10" cy="90" r="12" fill="#4ade80" class="crop-produce"/>
                        <circle cx="10" cy="90" r="12" fill="#22c55e" class="crop-produce"/>
                        <circle cx="0" cy="80" r="14" fill="#16a34a" class="crop-produce"/>
                    </g>

                    <!-- Crop 3: Root Vegetables (Carrots) -->
                    <g transform="translate(240, 0)">
                        <path d="M 0 140 L 0 110" fill="none" stroke="#65a30d" stroke-width="3" class="crop-stalk"/>
                        <polygon points="0,140 -8,160 8,160" fill="#ea580c" class="crop-produce"/>
                        <path d="M 0 110 Q -10 100 -5 90" fill="none" stroke="#84cc16" stroke-width="2" class="crop-produce"/>
                        <path d="M 0 110 Q 10 100 5 90" fill="none" stroke="#84cc16" stroke-width="2" class="crop-produce"/>
                    </g>
                    
                    <text x="150" y="25" font-size="11" font-weight="bold" fill="#15803d" text-anchor="middle">Diverse Crop Guilds</text>
                </svg>`,
                comment: "<div class='strategy-commentary'>Cultivating a diverse range of crops together mimics natural ecosystem biodiversity, optimizing soil nutrient cycling, reducing pests, and increasing total long-term yield.</div>"
            },
            "Energy Storage": {
                svg: `
                <svg class="svg-anim-canvas" viewBox="0 0 300 170">
                    <!-- Electricity Stream -->
                    <path d="M 20 85 L 80 85" fill="none" stroke="#eab308" stroke-width="4" class="power-line"/>
                    <text x="50" y="70" font-size="10" font-weight="bold" fill="#ca8a04" text-anchor="middle">⚡ Grid Input</text>

                    <!-- Lithium Battery Module Outer Cabinet -->
                    <rect x="80" y="45" width="140" height="80" rx="6" fill="#1e293b" stroke="#475569" stroke-width="3"/>
                    <rect x="220" y="72" width="8" height="26" rx="2" fill="#94a3b8"/>
                    
                    <!-- Internal Charging Level Bars -->
                    <rect x="95" y="60" width="0" height="50" rx="3" fill="#22c55e" class="battery-fill"/>

                    <!-- Grid Output -->
                    <path d="M 228 85 L 280 85" fill="none" stroke="#22c55e" stroke-width="4" class="power-line" style="animation-delay: 1.5s;"/>
                    <text x="250" y="70" font-size="10" font-weight="bold" fill="#16a34a" text-anchor="middle">Supply Out</text>
                </svg>`,
                comment: "<div class='strategy-commentary'>Deploying lithium-ion energy storage captures surplus grid generation and releases it during high-demand periods, effectively expanding reliable energy availability.</div>"
            },
            "Greywater Recycling": {
                svg: `
                <svg class="svg-anim-canvas" viewBox="0 0 300 170">
                    <path d="M 70 20 L 70 60 L 130 60 L 130 80" fill="none" stroke="#64748b" stroke-width="6"/>
                    <rect x="100" y="80" width="60" height="35" rx="4" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
                    <text x="130" y="101" font-size="9" font-weight="bold" fill="#ffffff" text-anchor="middle">FILTER</text>
                    <circle cx="70" cy="35" r="4" class="filter-drop"/>
                    <path d="M 130 115 L 130 145 L 220 145" fill="none" stroke="#38bdf8" stroke-width="4" stroke-dasharray="4"/>
                    <path d="M 220 140 Q 230 120 240 140" stroke="#16a34a" stroke-width="3" fill="none"/>
                </svg>`,
                comment: "<div class='strategy-commentary'>Treating and reusing wastewater from household sinks and laundry for crop irrigation reduces overall freshwater withdrawals.</div>"
            },
            "Plant-Based Diets": {
                svg: `
                <svg class="svg-anim-canvas" viewBox="0 0 300 170">
                    <!-- Plate Illustration -->
                    <ellipse cx="90" cy="85" rx="55" ry="35" fill="#e2e8f0" stroke="#94a3b8" stroke-width="3"/>
                    <ellipse cx="90" cy="85" rx="42" ry="25" fill="#ffffff"/>
                    <!-- Plant Foods on Plate -->
                    <circle cx="80" cy="80" r="8" fill="#16a34a"/>
                    <circle cx="95" cy="88" r="10" fill="#eab308"/>
                    <circle cx="102" cy="78" r="7" fill="#ea580c"/>

                    <!-- Resource Demand Meters -->
                    <g transform="translate(170, 20)">
                        <!-- Land Meter -->
                        <text x="12" y="30" font-size="9" font-weight="bold" fill="#475569">Land</text>
                        <rect x="10" y="35" width="16" height="80" rx="3" fill="#cbd5e1"/>
                        <rect x="10" y="40" width="16" height="75" rx="3" fill="#ef4444" class="resource-meter"/>

                        <!-- Water Meter -->
                        <text x="42" y="30" font-size="9" font-weight="bold" fill="#475569">Water</text>
                        <rect x="42" y="35" width="16" height="80" rx="3" fill="#cbd5e1"/>
                        <rect x="42" y="40" width="16" height="75" rx="3" fill="#38bdf8" class="resource-meter"/>

                        <!-- Energy Meter -->
                        <text x="75" y="30" font-size="9" font-weight="bold" fill="#475569">Energy</text>
                        <rect x="75" y="35" width="16" height="80" rx="3" fill="#cbd5e1"/>
                        <rect x="75" y="40" width="16" height="75" rx="3" fill="#facc15" class="resource-meter"/>
                    </g>
                    <text x="220" y="150" font-size="11" font-weight="bold" fill="#16a34a" text-anchor="middle">📉 Quotas Dropped</text>
                </svg>`,
                comment: "<div class='strategy-commentary'>Shifting diets toward plant-based foods bypasses resource-intensive livestock feed, drastically lowering land, water, and energy requirements per calorie of food produced.</div>"
            },
            "Use Public Transport": {
                svg: `
                <svg class="svg-anim-canvas" viewBox="0 0 300 170">
                    <!-- Platform & Track -->
                    <rect x="0" y="120" width="300" height="40" fill="#94a3b8"/>
                    <line x1="0" y1="120" x2="300" y2="120" stroke="#475569" stroke-width="4"/>

                    <!-- Individual Cars Fading in Background -->
                    <g class="fading-car">
                        <rect x="220" y="95" width="55" height="20" rx="4" fill="#ef4444"/>
                        <circle cx="232" cy="115" r="5" fill="#1e293b"/>
                        <circle cx="263" cy="115" r="5" fill="#1e293b"/>
                    </g>

                    <!-- Subway Station Commuters Boarding -->
                    <g class="passengers">
                        <circle cx="150" cy="100" r="4" fill="#1e293b"/>
                        <line x1="150" y1="104" x2="150" y2="118" stroke="#1e293b" stroke-width="2"/>
                        <circle cx="165" cy="100" r="4" fill="#1e293b"/>
                        <line x1="165" y1="104" x2="165" y2="118" stroke="#1e293b" stroke-width="2"/>
                    </g>

                    <!-- Electric Subway Train Car -->
                    <g class="subway-train">
                        <rect x="10" y="60" width="180" height="55" rx="8" fill="#2563eb" stroke="#1d4ed8" stroke-width="2"/>
                        <rect x="25" y="70" width="30" height="20" rx="2" fill="#93c5fd"/>
                        <rect x="65" y="70" width="30" height="20" rx="2" fill="#93c5fd"/>
                        <rect x="105" y="70" width="30" height="20" rx="2" fill="#93c5fd"/>
                        <rect x="145" y="70" width="30" height="20" rx="2" fill="#93c5fd"/>
                        <circle cx="45" cy="115" r="4" fill="#0f172a"/>
                        <circle cx="155" cy="115" r="4" fill="#0f172a"/>
                    </g>
                </svg>`,
                comment: "<div class='strategy-commentary'>Transitioning commuters from private motor vehicles to high-capacity electric mass transit dramatically lowers per-capita fuel consumption and overall energy demand.</div>"
            }
        };

        let minigameTimerInterval = null;
        let minigameTimeLeft = 20;
        let currentTargetWord = "";
        let activeMinigameTeam = "";
        let activeActionType = "";
        let activeResource = "";
        let activeStrategyTitle = "";

        function startDashboard() {
            socket.emit('start_game');
            document.getElementById('intro-screen').style.display = 'none';
            document.getElementById('game-dashboard').style.display = 'block';
        }

        function closeModal() {
            document.getElementById('summary-modal').style.display = 'none';
            playIncomeAnimation(); 
        }

        function closeEndgameModal() {
            document.getElementById('endgame-modal').style.display = 'none';
        }

        function openShockModal() {
            document.getElementById('shock-modal').style.display = 'block';
        }

        function closeShockModal() {
            document.getElementById('shock-modal').style.display = 'none';
        }

        function confirmShockAdvance() {
            closeShockModal();
            socket.emit('advance_round', {type: 'shock'});
        }

        function openCrisisModal() {
            document.getElementById('crisis-modal').style.display = 'block';
        }

        function closeCrisisModal() {
            document.getElementById('crisis-modal').style.display = 'none';
        }

        function confirmCrisisAdvance() {
            closeCrisisModal();
            socket.emit('advance_round', {type: 'crisis'});
        }

        function playIncomeAnimation() {
            teams.forEach(team => {
                let box = document.getElementById(`panel-${team}`);
                if (box) {
                    let anim = document.createElement('div');
                    anim.className = 'income-anim';
                    anim.innerText = `+$${stipends[team]}`;
                    box.appendChild(anim);
                    setTimeout(() => { if(box.contains(anim)) box.removeChild(anim); }, 2600);
                }
            });
        }

        function shuffleWord(word) {
            let letters = word.split('');
            for (let i = letters.length - 1; i > 0; i--) {
                let j = Math.floor(Math.random() * (i + 1));
                let temp = letters[i];
                letters[i] = letters[j];
                letters[j] = temp;
            }
            let scrambled = letters.join('');
            if (scrambled === word && word.length > 1) {
                return word.split('').reverse().join('');
            }
            return scrambled;
        }

        function openMinigame(team, actionType, resource, titleText) {
            activeMinigameTeam = team;
            activeActionType = actionType;
            activeResource = resource;
            activeStrategyTitle = titleText;

            currentTargetWord = essVocab[Math.floor(Math.random() * essVocab.length)];
            let scrambled = shuffleWord(currentTargetWord);

            let related = essRelatedWords[currentTargetWord] || ["environmental systems", "syllabus term", "ecology"];
            let relatedText = related.join(", ");

            document.getElementById('minigame-hint').innerHTML = `💡 <b>Related terms:</b> ${relatedText} <span style="color:#7f8c8d; font-size:0.9em;">(${currentTargetWord.length} letters)</span>`;
            document.getElementById('scrambled-word').innerText = scrambled;

            document.getElementById('minigame-title').innerText = titleText;
            document.getElementById('minigame-desc').innerText = actionType === 'supply' 
                ? `Unscramble the DP ESS term to generate +1 ${resource.toUpperCase()}!`
                : `Unscramble the DP ESS term to REDUCE ${resource.toUpperCase()} quota baseline!`;
            
            let card = document.getElementById('minigame-card');
            let submitBtn = document.getElementById('minigame-submit-btn');
            if (actionType === 'supply') {
                card.style.borderColor = "#8e44ad";
                submitBtn.style.background = "#8e44ad";
            } else {
                card.style.borderColor = "#16a085";
                submitBtn.style.background = "#16a085";
            }

            document.getElementById('minigame-input').value = "";
            document.getElementById('minigame-modal').style.display = 'block';
            document.getElementById('minigame-input').focus();
            
            minigameTimeLeft = 20;
            document.getElementById('minigame-timer').innerText = `Time Left: ${minigameTimeLeft}s`;

            clearInterval(minigameTimerInterval);
            minigameTimerInterval = setInterval(() => {
                minigameTimeLeft--;
                document.getElementById('minigame-timer').innerText = `Time Left: ${minigameTimeLeft}s`;
                
                if (minigameTimeLeft <= 0) {
                    clearInterval(minigameTimerInterval);
                    alert(`⏳ Time's up! The correct word was "${currentTargetWord}". Action failed and streak reset!`);
                    failMinigame();
                }
            }, 1000);
        }

        function submitMinigame() {
            let guess = document.getElementById('minigame-input').value.toUpperCase().trim();
            if (guess === currentTargetWord) {
                socket.emit('execute_action', {
                    team: activeMinigameTeam, 
                    action_type: activeActionType, 
                    resource: activeResource
                });

                closeMinigameModal(); 
                showStrategyFeedback(activeStrategyTitle, currentTargetWord);
            } else {
                let input = document.getElementById('minigame-input');
                input.style.backgroundColor = "#ffcccc";
                setTimeout(() => { input.style.backgroundColor = "white"; }, 300);
            }
        }

        function showStrategyFeedback(strategyTitle, solvedWord) {
            let info = strategyDetails[strategyTitle] || {
                svg: ``, 
                comment: "<div class='strategy-commentary'><b>Adaptation Action Complete:</b> Implementing sustainable resource stewardship increases resilience.</div>"
            };
            
            document.getElementById('strategy-feedback-title').innerText = `${strategyTitle} Deployed!`;
            document.getElementById('strategy-term-tag').innerText = `🧩 ESS Term Solved: ${solvedWord}`;
            document.getElementById('strategy-commentary-text').innerHTML = info.svg + info.comment;
            
            document.getElementById('strategy-modal').style.display = 'block';
        }

        function closeStrategyModal() {
            document.getElementById('strategy-modal').style.display = 'none';
        }

        function failMinigame() {
            if (activeMinigameTeam) {
                socket.emit('minigame_failed', {team: activeMinigameTeam});
            }
            closeMinigameModal();
        }

        function closeMinigameModal() {
            clearInterval(minigameTimerInterval);
            document.getElementById('minigame-modal').style.display = 'none';
        }

        document.getElementById("minigame-input").addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                submitMinigame();
            }
        });

        // --- DASHBOARD RENDER ---
        socket.on('update_state', function(state) {
            currentState = state; 
            document.getElementById('round').innerText = state.round;
            
            let marketHtml = "";
            for (let item in state.market) {
                if (item === 'toxic_water' && !state.toxic_water_visible) {
                    continue;
                }
                let m = state.market[item];
                marketHtml += `<div><strong>${m.name}</strong><br>Stock: ${m.stock} <br>Price: $${m.price}</div>`;
            }
            document.getElementById('market-display').innerHTML = marketHtml;

            let loansHtml = "<strong>📋 Active Loan Contracts:</strong> ";
            let activeLoans = state.loans ? state.loans.filter(l => l.status === 'active') : [];
            if (activeLoans.length === 0) {
                loansHtml += "<em>None</em>";
            } else {
                loansHtml += "<ul>";
                activeLoans.forEach(l => {
                    loansHtml += `<li><strong>${l.borrower}</strong> owes <strong>${l.lender}</strong> $${l.repayment_amount} (Due in Round ${l.due_round})</li>`;
                });
                loansHtml += "</ul>";
            }
            document.getElementById('active-loans-display').innerHTML = loansHtml;

            teams.forEach(team => {
                let tData = state.teams[team];
                
                if (tData.action_streak >= 2 && !streakAlertsShown[team]) {
                    streakAlertsShown[team] = true;
                    setTimeout(() => {
                        alert(`🔥 STREAK BONUS UNLOCKED for ${team}! 🔥\n\nYour community is building momentum! Every consecutive ESS Action you complete now adds compounding bonus points to your CRS.`);
                    }, 500);
                }
                
                if (tData.action_streak === 0) {
                    streakAlertsShown[team] = false;
                }

                let baseTarget = state.round * 2;
                
                let splits = {};
                ['water', 'food', 'energy'].forEach(i => {
                    let teamRed = tData.demand_reduction[i];
                    let currentTarget = Math.max(0, baseTarget - teamRed);
                    let totalInv = tData.inventory[i];
                    
                    splits[i] = {
                        need: Math.min(currentTarget, totalInv),
                        quota: currentTarget,
                        bank: Math.max(0, totalInv - currentTarget)
                    };
                });

                let panelHtml = `
                    <h2>${team === 'High-Income' ? '🏙️' : (team === 'Middle-Income' ? '🏡' : '🌾')} ${team}</h2>
                    <div style="text-align: center;">
                        <div class="score-badge">⭐ CRS: <span>${tData.score}</span></div><br>
                        <div class="streak-badge">🔥 Action Streak: <span>${tData.action_streak}x</span></div>
                    </div>
                    <h3 style="color: green; margin-top: 0;">Budget: $<span>${tData.budget}</span></h3>
                    ${state.toxic_water_visible ? `<p style="color: red; font-weight: bold; margin-bottom: 5px; text-align: center;">⚠️ Toxic Water Consumed: <span>${tData.inventory.toxic_water}</span></p>` : ''}
                    
                    <div class="inventory-panel">
                        <div class="inv-section inv-need">
                            <h4>🎯 Target Quotas</h4>
                            <div class="inv-item">💧 Water: <span style="color: ${splits.water.need >= splits.water.quota ? 'green' : 'red'};">${splits.water.need}/${splits.water.quota}</span></div>
                            <div class="inv-item">🍞 Food: <span style="color: ${splits.food.need >= splits.food.quota ? 'green' : 'red'};">${splits.food.need}/${splits.food.quota}</span></div>
                            <div class="inv-item">⚡ Energy: <span style="color: ${splits.energy.need >= splits.energy.quota ? 'green' : 'red'};">${splits.energy.need}/${splits.energy.quota}</span></div>
                        </div>
                        <div class="inv-section inv-bank">
                            <h4>🏦 Resource Bank</h4>
                            <div class="inv-item">💧 Water: <span>${splits.water.bank}</span></div>
                            <div class="inv-item">🍞 Food: <span>${splits.food.bank}</span></div>
                            <div class="inv-item">⚡ Energy: <span>${splits.energy.bank}</span></div>
                        </div>
                    </div>
                    <hr>
                `;

                let actionsHtml = "";
                if (tData.locked_in) {
                    actionsHtml = `<button class="submit-btn" disabled style="background:#888;">🔒 Turn Ended</button><br>`;
                } else {
                    actionsHtml = `<button class="submit-btn" onclick="submitOrder('${team}')">✅ End Turn</button><br><br>`;
                    
                    if (tData.purchase_history && tData.purchase_history.length > 0) {
                        actionsHtml += `<button class="undo-btn" onclick="undoPurchase('${team}')">↩️ Undo Last Purchase</button><br>`;
                    }

                    actionsHtml += `<h4>🛒 Market Purchases</h4>`;
                    for (let item in state.market) {
                        if (item === 'toxic_water' && !state.toxic_water_visible) {
                            continue;
                        }
                        let price = state.market[item].price;
                        let stock = state.market[item].stock;
                        let canAfford = tData.budget >= price && stock > 0;
                        actionsHtml += `<button class="buy-btn" ${canAfford ? "" : "disabled"} 
                            onclick="buy('${team}', '${item}')">Buy ${state.market[item].name} ($${price})</button>`;
                    }

                    actionsHtml += `<hr><div class="strategy-container">
                        <div class="strategy-col">
                            <h4>📈 Increase Supply (+1)</h4>
                            <button class="supply-btn" ${tData.failed_minigame ? 'disabled' : ''} onclick="openMinigame('${team}', 'supply', 'water', 'Rainwater Harvesting')">💧 Harvest Water</button>
                            <button class="supply-btn" ${tData.failed_minigame ? 'disabled' : ''} onclick="openMinigame('${team}', 'supply', 'food', 'Polyculture Farming')">🌱 Polyculture</button>
                            <button class="supply-btn" ${tData.failed_minigame ? 'disabled' : ''} onclick="openMinigame('${team}', 'supply', 'energy', 'Energy Storage')">⚡ Battery Storage</button>
                        </div>
                        <div class="strategy-col">
                            <h4>📉 Reduce Demand (-1 Quota)</h4>
                            <button class="demand-btn" ${tData.failed_minigame ? 'disabled' : ''} onclick="openMinigame('${team}', 'demand', 'water', 'Greywater Recycling')">💧 Recycle Water</button>
                            <button class="demand-btn" ${tData.failed_minigame ? 'disabled' : ''} onclick="openMinigame('${team}', 'demand', 'food', 'Plant-Based Diets')">🥗 Plant Diets</button>
                            <button class="demand-btn" ${tData.failed_minigame ? 'disabled' : ''} onclick="openMinigame('${team}', 'demand', 'energy', 'Use Public Transport')">🚆 Public Transit</button>
                        </div>
                    </div>`;

                    if (tData.failed_minigame) {
                        actionsHtml += `<p style="color:red; font-size:0.8em; text-align:center; margin-top:5px;">⚠️ Action failed. Action streak reset to 0!</p>`;
                    }
                }
                
                document.getElementById(`panel-${team}`).innerHTML = panelHtml + actionsHtml;
            });
        });

        socket.on('round_summary', function(summary) {
            document.getElementById('modal-title').innerText = `Round ${summary.round} Beginning!`;
            
            let eventText = "The market remained stable.";
            if (summary.type === 'shock') eventText = "🚨 A Drought & Chemical Spill occurred! Clean water supply plummeted and toxic sources emerged.";
            if (summary.type === 'crisis') eventText = "🔥 Hyperinflation struck the market! Prices have skyrocketed.";
            document.getElementById('modal-event').innerText = eventText;

            let repayContainer = document.getElementById('modal-repayments');
            if (summary.repayments && summary.repayments.length > 0) {
                let html = `<div class="repayment-box">
                    <h3 style="margin: 0 0 5px 0; color: #856404;">💳 AUTOMATED LOAN REPAYMENTS PROCESSED</h3>`;
                summary.repayments.forEach(r => {
                    html += `<p style="margin: 3px 0;"><strong>${r.borrower}</strong> automatically repaid <strong>$${r.amount}</strong> to <strong>${r.lender}</strong> (Loan issued in Round ${r.issue_round}).</p>`;
                });
                html += `</div>`;
                repayContainer.innerHTML = html;
            } else {
                repayContainer.innerHTML = "";
            }

            let scoresHtml = "<h3>Round Scores & CRS Progression:</h3><ul>";
            for (let team in summary.teams) {
                let delta = summary.teams[team].delta;
                let color = delta >= 0 ? "green" : "red";
                let sign = delta >= 0 ? "+" : "";
                scoresHtml += `<li><strong>${team}:</strong> Ended Round ${summary.round - 1} with ${summary.teams[team].score} CRS (<span style="color:${color}">${sign}${delta} pts</span>)</li>`;
            }
            scoresHtml += "</ul>";
            
            document.getElementById('modal-scores').innerHTML = scoresHtml;
            document.getElementById('summary-modal').style.display = 'block';
        });

        socket.on('endgame_triggered', function(data) {
            document.getElementById('endgame-winner-banner').innerText = `🏆 WINNER: ${data.winner.toUpperCase()} COMMUNITY!`;

            let tableHtml = `<table style="width:100%; border-collapse: collapse; margin-top:10px; font-size: 0.9em;">
                <thead>
                    <tr style="background:#f2f2f2; border-bottom:2px solid #ccc;">
                        <th style="padding:8px; text-align:left;">Community</th>
                        <th style="padding:8px; text-align:center;">Secured Progress</th>
                        <th style="padding:8px; text-align:center;">Resource Gap</th>
                        <th style="padding:8px; text-align:center;">Safety Loss</th>
                        <th style="padding:8px; text-align:center;">Final CRS</th>
                        <th style="padding:8px; text-align:left;">Survival Status</th>
                    </tr>
                </thead>
                <tbody>`;

            for (let team in data.results) {
                let result = data.results[team];
                let statusColor = result.status.includes('Winner') ? '#2e7d32' : (result.status.includes('Vulnerable') ? '#f57c00' : '#c62828');
                tableHtml += `<tr style="border-bottom:1px solid #eee;">
                    <td style="padding:8px; font-weight:bold;">${team}</td>
                    <td style="padding:8px; text-align:center; color:#1565c0; font-weight:bold;">Secured ${result.secured_units} of ${result.required_units} required</td>
                    <td style="padding:8px; text-align:center; color:#c62828;">-${result.unmet_units * 20} pts (${result.unmet_units} units)</td>
                    <td style="padding:8px; text-align:center; color:#c62828;">-${result.toxic_count * 15} pts (${result.toxic_count} units)</td>
                    <td style="padding:8px; text-align:center; font-weight:bold; font-size:1.1em;">${result.final_crs}</td>
                    <td style="padding:8px; font-weight:bold; color:${statusColor};">${result.status}</td>
                </tr>`;
            }

            tableHtml += `</tbody></table>`;
            document.getElementById('endgame-table-container').innerHTML = tableHtml;
            document.getElementById('endgame-modal').style.display = 'block';
        });

        function buy(team, item) { 
            if (item === 'toxic_water') {
                let msg = `⚠️ WARNING: TOXIC WATER ⚠️\n\nPurchasing Toxic Water will count towards your Water Quota / Bank, BUT it will inflict a massive -15 CRS penalty per unit consumed at the end of every round!\n\nAre you sure you want to proceed?`;
                if (!confirm(msg)) {
                    return; 
                }
            }
            socket.emit('buy_item', {team: team, item: item}); 
        }

        function undoPurchase(team) { socket.emit('undo_purchase', {team: team}); }
        
        function submitOrder(team) { 
            if (!currentState) return;
            
            let tData = currentState.teams[team];
            let baseTarget = currentState.round * 2;
            let inv = tData.inventory;
            
            let missingWater = Math.max(0, (baseTarget - tData.demand_reduction.water) - inv.water);
            let missingFood = Math.max(0, (baseTarget - tData.demand_reduction.food) - inv.food);
            let missingEnergy = Math.max(0, (baseTarget - tData.demand_reduction.energy) - inv.energy);
            
            let totalMissing = missingWater + missingFood + missingEnergy;
            
            if (totalMissing > 0) {
                let penalty = totalMissing * 10;
                let message = `⚠️ INSUFFICIENT AVAILABILITY ⚠️\n\nYour community has not secured enough resources to meet target quotas.\n\nPenalty: -${penalty} CRS points.\n\nLock in this order anyway?`;
                
                if (confirm(message)) {
                    socket.emit('submit_order', {team: team});
                }
            } else {
                socket.emit('submit_order', {team: team});
            }
        }
        
        function advanceRound(type) {
            if (type === 'shock') {
                openShockModal();
                return;
            }
            if (type === 'crisis') {
                openCrisisModal();
                return;
            }
            socket.emit('advance_round', {type: type});
        }
        function triggerEndGame() { socket.emit('advance_round', {type: 'endgame'}); }
        
        function transferFunds() {
            let fromTeam = document.getElementById('transfer-from').value;
            let toTeam = document.getElementById('transfer-to').value;
            let amount = parseInt(document.getElementById('transfer-amount').value);
            let repaymentAmount = parseInt(document.getElementById('repayment-amount').value);
            let dueInRounds = parseInt(document.getElementById('due-in-rounds').value);
            
            if (fromTeam === toTeam) {
                alert("Lender and Borrower must be different teams!");
                return;
            }
            
            if (amount > 0 && repaymentAmount > 0 && dueInRounds >= 1) {
                let dueRound = currentState.round + dueInRounds;
                let message = `⚠️ LOAN CONTRACT CONFIRMATION ⚠️\n\nLender: ${fromTeam}\nBorrower: ${toTeam}\nPrincipal Transfer: $${amount}\nRepayment Amount: $${repaymentAmount}\nDue In: ${dueInRounds} Round(s) (Round ${dueRound})\n\n$${repaymentAmount} will be automatically deducted from ${toTeam}'s budget at the start of Round ${dueRound}.\n\nFinalize loan contract?`;
                if (confirm(message)) {
                    socket.emit('transfer_funds', {
                        from_team: fromTeam, 
                        to_team: toTeam, 
                        amount: amount,
                        repayment_amount: repaymentAmount,
                        due_in_rounds: dueInRounds
                    });
                }
            } else {
                alert("Please enter valid loan values.");
            }
        }
    </script>
</body>
</html>
"""

# --- ROUTES & SOCKET EVENTS ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    calculate_scores()
    for t, team in game_state["teams"].items():
        team['start_score'] = team['score']
    emit('update_state', game_state)


@socketio.on('start_game')
def handle_start_game():
    reset_game_state()
    emit('update_state', game_state, broadcast=True)

@socketio.on('buy_item')
def handle_buy(data):
    team_name = data['team']
    item = data['item']
    team = game_state['teams'][team_name]
    market_item = game_state['market'][item]

    if not team['locked_in'] and market_item['stock'] > 0 and team['budget'] >= market_item['price']:
        team['purchase_history'].append({"item": item, "price": market_item['price']})
        
        team['budget'] -= market_item['price']
        market_item['stock'] -= 1
        
        if item == "clean_water":
            team['inventory']['water'] += 1
        elif item == "toxic_water":
            team['inventory']['toxic_water'] += 1
            team['inventory']['water'] += 1
        else:
            team['inventory'][item] += 1
        
        calculate_scores()
        emit('update_state', game_state, broadcast=True)

@socketio.on('undo_purchase')
def handle_undo(data):
    team_name = data['team']
    team = game_state['teams'][team_name]
    
    if not team['locked_in'] and len(team.get('purchase_history', [])) > 0:
        last_purchase = team['purchase_history'].pop()
        item_to_undo = last_purchase['item']
        price_paid = last_purchase['price']
        
        team['budget'] += price_paid
        game_state['market'][item_to_undo]['stock'] += 1
        
        if item_to_undo == "clean_water":
            if team['inventory']['water'] > 0:
                team['inventory']['water'] -= 1
        elif item_to_undo == "toxic_water":
            if team['inventory']['toxic_water'] > 0:
                team['inventory']['toxic_water'] -= 1
            if team['inventory']['water'] > 0:
                team['inventory']['water'] -= 1
        else:
            if team['inventory'][item_to_undo] > 0:
                team['inventory'][item_to_undo] -= 1
            
        calculate_scores()
        emit('update_state', game_state, broadcast=True)

@socketio.on('transfer_funds')
def handle_transfer(data):
    from_team = data['from_team']
    to_team = data['to_team']
    amount = int(data['amount'])
    repayment_amount = int(data.get('repayment_amount', amount))
    due_in_rounds = int(data.get('due_in_rounds', 1))
    
    if game_state['teams'][from_team]['budget'] >= amount and from_team != to_team:
        game_state['teams'][from_team]['budget'] -= amount
        game_state['teams'][to_team]['budget'] += amount
        
        loan_contract = {
            "lender": from_team,
            "borrower": to_team,
            "principal": amount,
            "repayment_amount": repayment_amount,
            "issue_round": game_state['round'],
            "due_round": game_state['round'] + due_in_rounds,
            "status": "active"
        }
        game_state['loans'].append(loan_contract)
        
        calculate_scores()
        emit('update_state', game_state, broadcast=True)

@socketio.on('execute_action')
def handle_execute_action(data):
    team = game_state['teams'][data['team']]
    action_type = data['action_type']
    resource = data['resource']
    
    if not team['locked_in']:
        if action_type == 'supply':
            team['inventory'][resource] += 1
        elif action_type == 'demand':
            team['demand_reduction'][resource] += 1
            
        team['ecocentric_count'] += 1
        team['action_streak'] += 1
        calculate_scores()
        emit('update_state', game_state, broadcast=True)

@socketio.on('minigame_failed')
def handle_minigame_failed(data):
    team = game_state['teams'][data['team']]
    if not team['locked_in']:
        team['failed_minigame'] = True
        team['action_streak'] = 0
        calculate_scores()
        emit('update_state', game_state, broadcast=True)

@socketio.on('submit_order')
def handle_submit(data):
    team = game_state['teams'][data['team']]
    team['locked_in'] = True
    team['purchase_history'] = [] 
    emit('update_state', game_state, broadcast=True)

@socketio.on('advance_round')
def handle_advance(data):
    event_type = data['type']

    if event_type == 'endgame':
        game_state['is_end_game'] = True
        game_state['game_over'] = True

        for item in game_state['market']:
            game_state['market'][item]['stock'] = 0

        calculate_scores()

        endgame_results = {}
        winner = None
        max_score = -999999

        for team_key, team in game_state["teams"].items():
            final_crs = team['score']
            endgame_base_target = game_state['round'] * 4
            required_units = 0
            secured_units = 0

            for item in ["water", "food", "energy"]:
                target = max(0, endgame_base_target - team["demand_reduction"][item])
                required_units += target
                secured_units += min(team['inventory'][item], target)

            if final_crs > max_score:
                max_score = final_crs
                winner = team_key

            if final_crs >= 150:
                status = "Ecosystem Winner (Thriving)"
            elif final_crs >= 0:
                status = "Vulnerable / Chronic Failure"
            else:
                status = "Total System Collapse"

            endgame_results[team_key] = {
                "final_crs": final_crs,
                "unmet_units": team.get("unmet_units", 0),
                "toxic_count": team['inventory']['toxic_water'],
                "required_units": required_units,
                "secured_units": secured_units,
                "status": status,
                "multiplier": team['multiplier']
            }

        emit('endgame_triggered', {
            "winner": winner,
            "round": game_state['round'],
            "results": endgame_results
        }, broadcast=True)
        emit('update_state', game_state, broadcast=True)
        return
    
    summary = {
        "round": game_state['round'] + 1,
        "type": event_type,
        "teams": {},
        "repayments": []
    }
    
    for t, team in game_state["teams"].items():
        delta = team['score'] - team['start_score']
        summary["teams"][t] = {"score": team['score'], "delta": delta}
        
        team['locked_in'] = False
        team['failed_minigame'] = False
        team['purchase_history'] = [] 
        
        if t == 'High-Income': team['budget'] += 30
        elif t == 'Middle-Income': team['budget'] += 20
        elif t == 'Low-Income': team['budget'] += 10

    game_state['round'] += 1
    
    # Auto Repayment for Maturing Loans
    for loan in game_state['loans']:
        if loan['status'] == 'active' and loan['due_round'] == game_state['round']:
            borrower = loan['borrower']
            lender = loan['lender']
            repay_amt = loan['repayment_amount']
            
            game_state['teams'][borrower]['budget'] -= repay_amt
            game_state['teams'][lender]['budget'] += repay_amt
            loan['status'] = 'paid'
            
            summary['repayments'].append({
                "borrower": borrower,
                "lender": lender,
                "amount": repay_amt,
                "issue_round": loan['issue_round']
            })

    if event_type == 'shock':
        game_state['toxic_water_visible'] = True
        game_state['market']['clean_water']['stock'] = int(game_state['market']['clean_water']['stock'] / 2)
        game_state['market']['clean_water']['price'] = 10
        game_state['market']['toxic_water']['stock'] = 10
        game_state['market']['food']['price'] = 8
    elif event_type == 'crisis':
        game_state['market']['clean_water']['price'] = 15
        game_state['market']['food']['price'] = 15
        game_state['market']['energy']['price'] = 15

    calculate_scores()
    
    for t, team in game_state["teams"].items():
        team['start_score'] = team['score']

    emit('round_summary', summary, broadcast=True)
    emit('update_state', game_state, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False, port=5001)
