from flask import Flask, render_template_string

app = Flask(__name__)

# --- TITAN VIII: FINAL + VELOCITY ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Titan VIII | Velocity Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* --- UI THEME --- */
        :root { --bg: #000000; --panel: rgba(10, 12, 16, 0.95); --accent: #00f2ff; --danger: #ff2e63; --gold: #ffd700; --void: #b12eff; }
        body { margin: 0; background: var(--bg); overflow: hidden; font-family: 'Inter', sans-serif; color: #ccc; user-select: none; }
        canvas { display: block; width: 100vw; height: 100vh; }

        /* LAYOUT */
        .ui-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; display: flex; justify-content: space-between; padding: 20px; box-sizing: border-box; }
        
        /* PANELS */
        .panel { 
            background: var(--panel); 
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 8px; 
            padding: 15px; 
            pointer-events: auto; 
            width: 280px;
            display: flex; flex-direction: column; gap: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        }

        h2 { margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; color: #666; border-bottom: 1px solid #333; padding-bottom: 5px; }
        .active-mode { color: var(--accent); border-color: var(--accent); }

        /* TAB SELECTOR */
        .mode-switch { display: flex; gap: 5px; margin-bottom: 10px; background: #111; padding: 4px; border-radius: 6px; }
        .mode-btn { 
            flex: 1; border: none; background: transparent; color: #666; padding: 8px; 
            font-size: 10px; font-weight: 800; cursor: pointer; text-transform: uppercase; border-radius: 4px;
        }
        .mode-btn.selected { background: #222; color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.5); }

        /* CONTROLS */
        button.action-btn {
            width: 100%; background: rgba(255,255,255,0.05); border: 1px solid #333; color: #fff;
            padding: 10px; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 11px; transition: 0.2s;
        }
        button.action-btn:hover { border-color: var(--accent); color: var(--accent); }
        
        /* ENTITY SELECTOR (GOD MODE) */
        .entity-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        .entity-card {
            border: 1px solid #333; background: #080808; padding: 10px; text-align: center; cursor: pointer; border-radius: 4px; transition: 0.2s;
        }
        .entity-card:hover { border-color: var(--gold); }
        .entity-card.selected { border-color: var(--gold); background: rgba(255, 215, 0, 0.1); }
        .entity-card.bh { border-color: #444; }
        .entity-card.bh:hover { border-color: var(--danger); }
        .entity-card.bh.selected { border-color: var(--danger); background: rgba(255, 46, 99, 0.1); }
        
        /* TELEMETRY */
        .stat-row { display: flex; justify-content: space-between; font-size: 11px; font-family: 'JetBrains Mono', monospace; }
        .val { color: #fff; font-weight: 700; }

        /* HINT */
        .hud-hint { position: absolute; bottom: 30px; width: 100%; text-align: center; font-size: 11px; letter-spacing: 2px; opacity: 0.5; text-transform: uppercase; }
    </style>
</head>
<body>

<div class="ui-layer">
    
    <!-- LEFT: INTERACTION MODE -->
    <div class="panel">
        <h2>Control System</h2>
        
        <!-- MODE SWITCHER -->
        <div class="mode-switch">
            <button class="mode-btn selected" onclick="setMode('launch')" id="btn-launch">Launch Mode</button>
            <button class="mode-btn" onclick="setMode('god')" id="btn-god">God Mode</button>
        </div>

        <!-- DYNAMIC CONTENT: LAUNCHER -->
        <div id="panel-launch">
            <div class="stat-row" style="color: var(--accent); margin-bottom: 5px;">> PROJECTILE CONFIG</div>
            <div class="stat-row"><span>Mass</span> <span class="val" id="mass-val">20</span></div>
            <input type="range" min="5" max="200" value="20" oninput="sim.launchMass=parseInt(this.value); document.getElementById('mass-val').innerText=this.value" style="width:100%; accent-color: var(--accent);">
            <div style="font-size: 10px; color: #555; margin-top: 5px;">Drag on screen to slingshot planets.</div>
        </div>

        <!-- DYNAMIC CONTENT: GOD MODE -->
        <div id="panel-god" style="display: none;">
            <div class="stat-row" style="color: var(--gold); margin-bottom: 5px;">> CELESTIAL PLACEMENT</div>
            <div class="entity-grid">
                <div class="entity-card selected" onclick="selectEntity('star_yellow', this)">
                    <div style="color: var(--gold); font-weight:800;">SUN</div>
                    <div style="font-size:9px; color:#666;">Mass: 50k</div>
                </div>
                <div class="entity-card" onclick="selectEntity('star_neutron', this)">
                    <div style="color: var(--accent); font-weight:800;">NEUTRON</div>
                    <div style="font-size:9px; color:#666;">Mass: 80k</div>
                </div>
                <div class="entity-card bh" onclick="selectEntity('black_hole', this)" style="grid-column: span 2;">
                    <div style="color: var(--danger); font-weight:800;">>> BLACK HOLE <<</div>
                    <div style="font-size:9px; color:#666;">Mass: 5,000,000 (INFINITE)</div>
                </div>
            </div>
            <div style="font-size: 10px; color: #555; margin-top: 10px;">Click anywhere to SPAWN INSTANTLY.</div>
        </div>
    </div>

    <!-- RIGHT: SYSTEM -->
    <div class="panel">
        <h2>Simulation State</h2>
        <button class="action-btn" onclick="sim.loadSolar()">Reset: Solar System</button>
        <button class="action-btn" onclick="sim.reset()" style="border-color: #552222; color: #ff5555;">Clear Vacuum</button>
        
        <div style="border-top: 1px solid #333; margin: 10px 0;"></div>
        
        <div class="stat-row"><span>Entities:</span> <span class="val" id="count">0</span></div>
        <div class="stat-row"><span>Physics Load:</span> <span class="val" id="fps">OPTIMAL</span></div>
        <div class="stat-row"><span>Event Horizon:</span> <span class="val" id="bh-status" style="color: #444;">NONE</span></div>
    </div>

</div>

<div class="hud-hint" id="hint-text">MODE: LAUNCHER (DRAG TO SHOOT)</div>
<canvas id="canvas"></canvas>

<script>
/**
 * TITAN VIII ENGINE
 * Features: Dual-Mode UI, Realistic N-Body, Black Hole Physics
 */

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d', { alpha: false });

// --- CONFIGURATION ---
const COLORS = {
    bg: '#000000',
    planet: '#00f2ff',
    sun: '#ffaa00',
    neutron: '#ffffff',
    bh: '#000000',
    bh_glow: '#ff2e63'
};

// --- ENGINE STATE ---
const sim = {
    width: 0, height: 0,
    bodies: [],
    mode: 'launch', // 'launch' or 'god'
    godSelection: 'star_yellow',
    launchMass: 20,
    camera: { x: 0, y: 0, zoom: 0.4 }, // Start zoomed out further
    input: { dragStart: null, current: null, panning: false, panStart: {x:0, y:0} },
    params: { G: 1.0 }, // Tuned Gravity
    cache: { trajectory: [] }
};

// --- PHYSICS CORE ---
class Body {
    constructor(x, y, mass, vx, vy, type) {
        this.x = x; this.y = y;
        this.mass = mass;
        this.vx = vx; this.vy = vy;
        this.type = type;
        this.trail = [];
        this.dead = false;
        
        // Visual Properties
        if (type === 'planet') { this.radius = Math.max(2, Math.sqrt(mass)); this.color = COLORS.planet; }
        if (type === 'star_yellow') { this.radius = Math.sqrt(mass)*0.5; this.color = COLORS.sun; }
        if (type === 'star_neutron') { this.radius = Math.sqrt(mass)*0.3; this.color = COLORS.neutron; }
        if (type === 'black_hole') { this.radius = Math.sqrt(mass)*0.05; this.color = COLORS.bh; } // Ultra dense
    }

    update(dt) {
        // PHYSICS: Symplectic Euler Integration
        let fx = 0, fy = 0;

        for (let other of sim.bodies) {
            if (other === this) continue;

            let dx = other.x - this.x;
            let dy = other.y - this.y;
            let distSq = dx*dx + dy*dy;
            let dist = Math.sqrt(distSq);

            // COLLISION LOGIC
            // If Black Hole: Eats everything.
            // If Star: Eats planets.
            if (dist < this.radius + other.radius) {
                this.resolveCollision(other);
                continue;
            }

            // GRAVITY: F = G * M * m / r^2
            // Optimization: Softening parameter to prevent infinity
            let f = (sim.params.G * other.mass) / (distSq + 100); 
            fx += f * (dx / dist);
            fy += f * (dy / dist);
        }

        // Apply Forces
        this.vx += fx * dt;
        this.vy += fy * dt;
        this.x += this.vx * dt;
        this.y += this.vy * dt;

        // Trail Buffer
        if (this.type === 'planet' && Math.random() > 0.5) {
            this.trail.push({x: this.x, y: this.y});
            if (this.trail.length > 50) this.trail.shift();
        }
    }

    resolveCollision(other) {
        // HIERARCHY: Black Hole > Neutron > Star > Planet
        const rank = { 'black_hole': 4, 'star_neutron': 3, 'star_yellow': 2, 'planet': 1 };
        
        if (rank[this.type] >= rank[other.type]) {
            // "This" eats "Other"
            // Conservation of Momentum (Optional, but let's keep BH static-ish for stability unless huge)
            if (this.type !== 'black_hole') {
                this.vx = (this.mass*this.vx + other.mass*other.vx)/(this.mass+other.mass);
                this.vy = (this.mass*this.vy + other.mass*other.vy)/(this.mass+other.mass);
            }
            this.mass += other.mass * 0.5; // Gain mass
            other.dead = true;
        }
    }

    draw() {
        let sx = w2s_x(this.x);
        let sy = w2s_y(this.y);
        let sr = this.radius * sim.camera.zoom;
        if (sr < 0.5 && this.type === 'planet') return;

        // Trail
        if (this.trail.length > 2) {
            ctx.beginPath();
            ctx.strokeStyle = this.color;
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.4;
            ctx.moveTo(w2s_x(this.trail[0].x), w2s_y(this.trail[0].y));
            for(let i=2; i<this.trail.length; i+=2) ctx.lineTo(w2s_x(this.trail[i].x), w2s_y(this.trail[i].y));
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }

        // Draw Body
        ctx.beginPath();
        ctx.arc(sx, sy, sr, 0, Math.PI*2);
        ctx.fillStyle = this.color;
        
        // EFFECTS
        if (this.type === 'black_hole') {
            // Event Horizon Glow
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
            ctx.shadowBlur = 30; ctx.shadowColor = COLORS.bh_glow;
        } else if (this.type.includes('star')) {
            ctx.shadowBlur = 40; ctx.shadowColor = this.color;
        }
        
        ctx.fill();
        ctx.shadowBlur = 0;

        // --- VELOCITY LABEL (NEW) ---
        // Only show if moving faster than a crawl
        let speed = Math.sqrt(this.vx*this.vx + this.vy*this.vy);
        if (speed > 0.1) {
            ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
            ctx.font = "10px JetBrains Mono";
            // Offset text to right of object
            ctx.fillText(speed.toFixed(1) + " km/s", sx + sr + 5, sy + 4);
        }
    }
}

// --- UI LOGIC ---
function setMode(m) {
    sim.mode = m;
    // Toggle Panels
    document.getElementById('panel-launch').style.display = m==='launch'?'block':'none';
    document.getElementById('panel-god').style.display = m==='god'?'block':'none';
    // Toggle Buttons
    document.getElementById('btn-launch').className = m==='launch'?'mode-btn selected':'mode-btn';
    document.getElementById('btn-god').className = m==='god'?'mode-btn selected':'mode-btn';
    // Hint
    const hint = m==='launch' ? "MODE: LAUNCHER (DRAG TO SHOOT PLANETS)" : "MODE: GOD (CLICK TO PLACE STARS)";
    document.getElementById('hint-text').innerText = hint;
    
    // Reset Interaction
    sim.input.dragStart = null;
    sim.cache.trajectory = [];
}

function selectEntity(type, el) {
    sim.godSelection = type;
    // Update UI visual selection
    document.querySelectorAll('.entity-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
}

// --- INPUT HANDLING ---
function getMouseWorld(e) { return { x: s2w_x(e.clientX), y: s2w_y(e.clientY) }; }

canvas.addEventListener('mousedown', e => {
    if (e.button === 2) { // Right Click Pan
        sim.input.panning = true; sim.input.panStart = { x: e.clientX, y: e.clientY };
        return;
    }

    if (sim.mode === 'launch') {
        let pos = getMouseWorld(e);
        sim.input.dragStart = pos;
        sim.input.current = pos;
        calculateTrajectory();
    } else {
        // GOD MODE: INSTANT SPAWN
        spawnEntity(e);
    }
});

canvas.addEventListener('mousemove', e => {
    if (sim.input.panning) {
        sim.camera.x -= (e.clientX - sim.input.panStart.x) / sim.camera.zoom;
        sim.camera.y -= (e.clientY - sim.input.panStart.y) / sim.camera.zoom;
        sim.input.panStart = { x: e.clientX, y: e.clientY };
        return;
    }

    if (sim.mode === 'launch' && sim.input.dragStart) {
        sim.input.current = getMouseWorld(e);
        calculateTrajectory();
    }
});

canvas.addEventListener('mouseup', () => {
    sim.input.panning = false;
    if (sim.mode === 'launch' && sim.input.dragStart) {
        // FIRE PLANET
        let vx = (sim.input.dragStart.x - sim.input.current.x) * 0.03;
        let vy = (sim.input.dragStart.y - sim.input.current.y) * 0.03;
        sim.bodies.push(new Body(sim.input.dragStart.x, sim.input.dragStart.y, sim.launchMass, vx, vy, 'planet'));
        sim.input.dragStart = null;
        sim.cache.trajectory = [];
    }
});

// --- SPAWNER ---
function spawnEntity(e) {
    let pos = getMouseWorld(e);
    let type = sim.godSelection;
    let mass = 0;
    
    if (type === 'star_yellow') mass = 50000;
    if (type === 'star_neutron') mass = 80000;
    if (type === 'black_hole') mass = 5000000; // INSANE MASS

    sim.bodies.push(new Body(pos.x, pos.y, mass, 0, 0, type));
    
    // Check for BH presence to update UI
    if (type === 'black_hole') document.getElementById('bh-status').innerText = "ACTIVE (DANGER)";
}

// --- TRAJECTORY ---
function calculateTrajectory() {
    if (!sim.input.dragStart) return;
    let points = [];
    let ghost = { 
        x: sim.input.dragStart.x, y: sim.input.dragStart.y, 
        vx: (sim.input.dragStart.x - sim.input.current.x) * 0.03, 
        vy: (sim.input.dragStart.y - sim.input.current.y) * 0.03 
    };

    for(let i=0; i<100; i++) {
        let fx = 0, fy = 0;
        for(let b of sim.bodies) {
            if (b.type === 'planet') continue; // Planets don't affect prediction much
            let dx = b.x - ghost.x;
            let dy = b.y - ghost.y;
            let dSq = dx*dx + dy*dy;
            let d = Math.sqrt(dSq);
            if (d < 50) break;
            let f = (sim.params.G * b.mass) / dSq;
            fx += f * (dx/d); fy += f * (dy/d);
        }
        ghost.vx += fx; ghost.vy += fy;
        ghost.x += ghost.vx; ghost.y += ghost.vy;
        points.push({x: ghost.x, y: ghost.y});
    }
    sim.cache.trajectory = points;
}

// --- UTILS ---
function w2s_x(wx) { return (wx - sim.camera.x) * sim.camera.zoom + sim.width/2; }
function w2s_y(wy) { return (wy - sim.camera.y) * sim.camera.zoom + sim.height/2; }
function s2w_x(sx) { return (sx - sim.width/2) / sim.camera.zoom + sim.camera.x; }
function s2w_y(sy) { return (sy - sim.height/2) / sim.camera.zoom + sim.camera.y; }
window.addEventListener('wheel', e => { e.preventDefault(); sim.camera.zoom = Math.max(0.05, sim.camera.zoom - Math.sign(e.deltaY)*0.05); }, {passive:false});
window.addEventListener('resize', () => { sim.width = canvas.width = window.innerWidth; sim.height = canvas.height = window.innerHeight; });
window.dispatchEvent(new Event('resize'));

// --- SCENES ---
sim.loadSolar = () => {
    sim.bodies = [];
    // Sun is just a body now. It can move!
    sim.bodies.push(new Body(0, 0, 50000, 0, 0, 'star_yellow'));
    
    // Earth
    let r = 600;
    let v = Math.sqrt((sim.params.G * 50000) / r);
    sim.bodies.push(new Body(r, 0, 20, 0, v, 'planet'));
    
    sim.camera = {x:0, y:0, zoom:0.4};
    document.getElementById('bh-status').innerText = "NONE";
};
sim.reset = () => { sim.bodies = []; document.getElementById('bh-status').innerText = "NONE"; };

// --- LOOP ---
function loop() {
    // Clear
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Render Bodies
    for (let i = sim.bodies.length - 1; i >= 0; i--) {
        let b = sim.bodies[i];
        if (b.dead) { sim.bodies.splice(i, 1); continue; }
        b.update(1.0);
        b.draw();
    }

    // Render Trajectory
    if (sim.mode === 'launch' && sim.input.dragStart && sim.cache.trajectory.length) {
        ctx.beginPath();
        let t = sim.cache.trajectory;
        ctx.moveTo(w2s_x(t[0].x), w2s_y(t[0].y));
        for(let p of t) ctx.lineTo(w2s_x(p.x), w2s_y(p.y));
        ctx.strokeStyle = '#fff'; ctx.setLineDash([5,5]); ctx.stroke(); ctx.setLineDash([]);
        
        // Pull Line
        ctx.beginPath();
        ctx.moveTo(w2s_x(sim.input.dragStart.x), w2s_y(sim.input.dragStart.y));
        ctx.lineTo(w2s_x(sim.input.current.x), w2s_y(sim.input.current.y));
        ctx.strokeStyle = sim.mode === 'launch' ? '#00f2ff' : '#ffd700'; ctx.stroke();
    }

    document.getElementById('count').innerText = sim.bodies.length;
    requestAnimationFrame(loop);
}

sim.loadSolar();
loop();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(debug=True, port=8080)

