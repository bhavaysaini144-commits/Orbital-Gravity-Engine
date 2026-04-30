from flask import Flask, render_template_string

app = Flask(__name__)

# --- TITAN ARCHITECT: v7 (FEATURE COMPLETE) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Titan | Architect Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* --- PROFESSIONAL UI THEME --- */
        :root { --bg: #050508; --panel: rgba(15, 18, 24, 0.9); --accent: #00f2ff; --text: #c5c6c7; --alert: #ff2e63; --gold: #ffd700; }
        body { margin: 0; background: var(--bg); overflow: hidden; font-family: 'Inter', sans-serif; color: var(--text); user-select: none; }
        canvas { display: block; width: 100vw; height: 100vh; }

        /* DASHBOARD LAYOUT */
        .ui-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; display: grid; grid-template-columns: 300px 1fr 300px; padding: 20px; box-sizing: border-box; }
        
        /* PANELS */
        .panel { 
            background: var(--panel); 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(255,255,255,0.15); 
            border-radius: 8px; 
            padding: 20px; 
            pointer-events: auto; 
            display: flex; flex-direction: column; gap: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
        }

        h2 { margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 2px; color: var(--accent); border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; font-weight: 800; }
        .stat-row { display: flex; justify-content: space-between; font-size: 12px; font-family: 'JetBrains Mono', monospace; align-items: center; }
        .stat-val { color: #fff; font-weight: 700; }
        
        /* CONTROLS */
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        button {
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); color: #fff;
            padding: 8px; border-radius: 4px; cursor: pointer; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; transition: 0.2s; text-transform: uppercase;
        }
        button:hover { background: var(--accent); color: #000; border-color: var(--accent); }
        button.danger { border-color: var(--alert); color: var(--alert); }
        button.danger:hover { background: var(--alert); color: white; }

        /* INPUTS */
        select { width: 100%; background: #111; border: 1px solid #444; color: white; padding: 8px; border-radius: 4px; cursor: pointer; }
        input[type=range] { width: 100%; accent-color: var(--accent); cursor: pointer; }

        /* ALERTS */
        #orbit-status { 
            text-align: center; padding: 10px; border-radius: 4px; font-weight: 800; font-size: 11px; letter-spacing: 1px; 
            background: #1a1d24; color: #555; margin-top: 10px;
        }
        .status-stable { background: rgba(0, 242, 255, 0.1) !important; color: var(--accent) !important; border: 1px solid var(--accent); }
        .status-escape { background: rgba(255, 46, 99, 0.1) !important; color: var(--alert) !important; border: 1px solid var(--alert); }

        .controls-hint { position: absolute; bottom: 30px; width: 100%; text-align: center; font-size: 11px; opacity: 0.4; letter-spacing: 2px; text-transform: uppercase; }
    </style>
</head>
<body>

<div class="ui-layer">
    <!-- LEFT: CELESTIAL FORGE -->
    <div class="panel">
        <h2>Celestial Forge</h2>
        
        <div class="stat-row"><span>Entity Type</span></div>
        <select id="type-select" onchange="updateBuilder()">
            <option value="planet">Standard Planet</option>
            <option value="star_yellow">Yellow Star (Sun)</option>
            <option value="star_neutron">Neutron Star (Dense)</option>
            <option value="black_hole">>> BLACK HOLE <<</option>
        </select>

        <div class="stat-row"><span>Mass Index</span> <span id="mass-display" class="stat-val">20</span></div>
        <input type="range" id="mass-slider" min="5" max="1000" value="20" oninput="updateBuilder()">

        <div class="stat-row"><span>Parameters</span></div>
        <div class="btn-group">
            <button id="lock-btn" onclick="toggleLock()">Mode: Orbit</button>
        </div>
        <div style="font-size: 10px; color: #666; margin-top: 5px;">*Locked objects do not move (Fixed Stars)</div>
    </div>

    <!-- CENTER -->
    <div></div>

    <!-- RIGHT: MISSION CONTROL -->
    <div class="panel">
        <h2>Mission Control</h2>
        <div class="btn-group">
            <button onclick="sim.loadSolar()">Load Solar</button>
            <button onclick="sim.loadBinary()">Load Binary</button>
        </div>
        <button class="danger" onclick="sim.reset()">Clear Sector</button>

        <div style="height: 10px;"></div>
        <h2>Telemetry</h2>
        <div class="stat-row"><span>Objects:</span> <span id="count" class="stat-val">0</span></div>
        <div class="stat-row"><span>Launch Vel:</span> <span id="v-launch" class="stat-val">--</span></div>
        <div class="stat-row"><span>Escape Vel:</span> <span id="v-esc" class="stat-val">--</span></div>
        
        <div id="orbit-status">SYSTEM IDLE</div>
    </div>
</div>

<div class="controls-hint">Left Drag: Launch • Right Drag: Pan • Scroll: Zoom</div>
<canvas id="canvas"></canvas>

<script>
/**
 * TITAN ENGINE v7
 * Optimized N-Body Core with Celestial Forge
 */

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d', { alpha: false });

// --- ENGINE STATE ---
const sim = {
    width: 0, height: 0,
    bodies: [],
    camera: { x: 0, y: 0, zoom: 0.5 }, 
    input: { 
        dragStart: null, current: null, 
        panning: false, panStart: {x:0, y:0} 
    },
    params: { G: 1.5, timeScale: 1.0 },
    cache: { trajectory: [] },
    // New Builder State
    builder: { type: 'planet', mass: 20, color: '#00f2ff', locked: false }
};

// --- PHYSICS KERNEL ---
class Body {
    constructor(x, y, mass, vx, vy, color, type, locked) {
        this.x = x; this.y = y;
        this.mass = mass;
        this.vx = vx; this.vy = vy;
        this.color = color;
        this.type = type; 
        this.locked = locked;
        this.trail = [];
        
        // Density Physics: R = sqrt(M) * DensityFactor
        if (type === 'black_hole') this.radius = Math.sqrt(mass) * 0.2; // Super dense
        else if (type.includes('star')) this.radius = Math.sqrt(mass) * 0.6;
        else this.radius = Math.sqrt(mass);
    }

    update(dt) {
        if (this.locked) return; 

        let fx = 0, fy = 0;
        
        // Symplectic Integration
        for (let other of sim.bodies) {
            if (other === this) continue;
            
            let dx = other.x - this.x;
            let dy = other.y - this.y;
            let distSq = dx*dx + dy*dy;
            let dist = Math.sqrt(distSq);

            // Collision / Event Horizon
            if (dist < this.radius + other.radius) {
                // Absorption Logic: Bigger eats smaller
                if (other.mass >= this.mass) { this.dead = true; other.mass += this.mass * 0.5; }
                continue;
            }

            // Gravity
            let f = (sim.params.G * other.mass) / distSq;
            fx += f * (dx / dist);
            fy += f * (dy / dist);
        }

        this.vx += fx * dt;
        this.vy += fy * dt;
        this.x += this.vx * dt;
        this.y += this.vy * dt;

        // Optimized Trail: Only update every 2nd frame
        if (sim.bodies.length < 300 && Math.random() > 0.5) {
            this.trail.push({x: this.x, y: this.y});
            if (this.trail.length > 100) this.trail.shift();
        }
    }

    draw() {
        let sx = w2s_x(this.x);
        let sy = w2s_y(this.y);
        let sr = this.radius * sim.camera.zoom;
        if (sr < 0.5) return; 

        // Trail
        if (this.trail.length > 2) {
            ctx.beginPath();
            ctx.strokeStyle = this.color;
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.4;
            ctx.moveTo(w2s_x(this.trail[0].x), w2s_y(this.trail[0].y));
            for(let i=2; i<this.trail.length; i+=2) {
                ctx.lineTo(w2s_x(this.trail[i].x), w2s_y(this.trail[i].y));
            }
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }

        // Body Render
        ctx.beginPath();
        ctx.arc(sx, sy, sr, 0, Math.PI*2);
        ctx.fillStyle = this.color;
        
        // Special Effects
        if (this.type === 'star_yellow') {
            ctx.shadowBlur = 30; ctx.shadowColor = this.color;
        } else if (this.type === 'black_hole') {
            ctx.fillStyle = '#000';
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.shadowBlur = 20; ctx.shadowColor = '#ff0000'; // Accretion Disk
        }
        ctx.fill();
        ctx.shadowBlur = 0;
    }
}

// --- TRANSFORM MATH ---
function w2s_x(wx) { return (wx - sim.camera.x) * sim.camera.zoom + sim.width/2; }
function w2s_y(wy) { return (wy - sim.camera.y) * sim.camera.zoom + sim.height/2; }
function s2w_x(sx) { return (sx - sim.width/2) / sim.camera.zoom + sim.camera.x; }
function s2w_y(sy) { return (sy - sim.height/2) / sim.camera.zoom + sim.camera.y; }

// --- UI LOGIC ---
function updateBuilder() {
    const type = document.getElementById('type-select').value;
    const mass = parseInt(document.getElementById('mass-slider').value);
    document.getElementById('mass-display').innerText = mass;

    sim.builder.type = type;
    sim.builder.mass = mass;
    
    // Preset Colors & Locks
    if (type === 'planet') { sim.builder.color = '#00f2ff'; sim.builder.locked = false; }
    if (type === 'star_yellow') { sim.builder.color = '#ffaa00'; sim.builder.locked = true; }
    if (type === 'star_neutron') { sim.builder.color = '#0088ff'; sim.builder.locked = true; }
    if (type === 'black_hole') { sim.builder.color = '#000'; sim.builder.locked = true; }
    
    // Update Button Text
    updateLockBtn();
}

function toggleLock() {
    sim.builder.locked = !sim.builder.locked;
    updateLockBtn();
}

function updateLockBtn() {
    const btn = document.getElementById('lock-btn');
    btn.innerText = sim.builder.locked ? "MODE: FIXED (STAR)" : "MODE: ORBIT (PLANET)";
    btn.style.borderColor = sim.builder.locked ? "#ffaa00" : "#00f2ff";
    btn.style.color = sim.builder.locked ? "#ffaa00" : "#00f2ff";
}

// --- INPUT & TRAJECTORY ---
window.addEventListener('resize', () => { sim.width = canvas.width = window.innerWidth; sim.height = canvas.height = window.innerHeight; });
canvas.addEventListener('contextmenu', e => e.preventDefault());

canvas.addEventListener('wheel', e => {
    e.preventDefault();
    sim.camera.zoom += e.deltaY < 0 ? 0.05 : -0.05;
    if (sim.camera.zoom < 0.05) sim.camera.zoom = 0.05;
}, { passive: false });

canvas.addEventListener('mousedown', e => {
    if (e.button === 2) {
        sim.input.panning = true;
        sim.input.panStart = { x: e.clientX, y: e.clientY };
    } else {
        sim.input.dragStart = { x: s2w_x(e.clientX), y: s2w_y(e.clientY) };
        sim.input.current = sim.input.dragStart;
        calculateTrajectory();
    }
});

canvas.addEventListener('mousemove', e => {
    if (sim.input.panning) {
        let dx = (e.clientX - sim.input.panStart.x) / sim.camera.zoom;
        let dy = (e.clientY - sim.input.panStart.y) / sim.camera.zoom;
        sim.camera.x -= dx; sim.camera.y -= dy;
        sim.input.panStart = { x: e.clientX, y: e.clientY };
        return;
    }
    if (sim.input.dragStart) {
        sim.input.current = { x: s2w_x(e.clientX), y: s2w_y(e.clientY) };
        calculateTrajectory();
    }
});

canvas.addEventListener('mouseup', e => {
    if (sim.input.panning) { sim.input.panning = false; return; }
    if (sim.input.dragStart) {
        let vx = (sim.input.dragStart.x - sim.input.current.x) * 0.02;
        let vy = (sim.input.dragStart.y - sim.input.current.y) * 0.02;
        
        sim.bodies.push(new Body(
            sim.input.dragStart.x, sim.input.dragStart.y, 
            sim.builder.mass, vx, vy, 
            sim.builder.color, sim.builder.type, sim.builder.locked
        ));
        
        sim.input.dragStart = null;
        sim.cache.trajectory = [];
        resetUI();
    }
});

function calculateTrajectory() {
    if (!sim.input.dragStart) return;
    let points = [];
    // Create Ghost Particle
    let ghost = { 
        x: sim.input.dragStart.x, y: sim.input.dragStart.y, 
        vx: (sim.input.dragStart.x - sim.input.current.x) * 0.02, 
        vy: (sim.input.dragStart.y - sim.input.current.y) * 0.02 
    };

    let v_curr = Math.sqrt(ghost.vx*ghost.vx + ghost.vy*ghost.vy);
    let sun = sim.bodies.find(b => b.type.includes('star') || b.type === 'black_hole');
    let v_esc = 0;
    
    if (sun) {
        let dist = Math.hypot(sun.x - ghost.x, sun.y - ghost.y);
        v_esc = Math.sqrt(2 * sim.params.G * sun.mass / dist);
    }

    updateTelemetry(v_curr, v_esc);

    for(let i=0; i<150; i++) { // 150 steps prediction
        let fx = 0, fy = 0;
        for(let b of sim.bodies) {
            if(!b.locked) continue; // Only static gravity wells affect prediction (Optimization)
            let dx = b.x - ghost.x;
            let dy = b.y - ghost.y;
            let dSq = dx*dx + dy*dy;
            let d = Math.sqrt(dSq);
            if(d < 20) break;
            let f = (sim.params.G * b.mass) / dSq;
            fx += f * (dx/d);
            fy += f * (dy/d);
        }
        ghost.vx += fx; ghost.vy += fy;
        ghost.x += ghost.vx; ghost.y += ghost.vy;
        points.push({x: ghost.x, y: ghost.y});
    }
    sim.cache.trajectory = points;
}

function updateTelemetry(v, esc) {
    document.getElementById('v-launch').innerText = v.toFixed(2) + " km/s";
    document.getElementById('v-esc').innerText = esc.toFixed(2) + " km/s";
    const stat = document.getElementById('orbit-status');
    
    if (v < esc) {
        stat.innerText = "ORBIT: STABLE"; stat.className = "status-stable";
    } else {
        stat.innerText = "ORBIT: ESCAPE"; stat.className = "status-escape";
    }
}

function resetUI() {
    document.getElementById('orbit-status').innerText = "SYSTEM IDLE";
    document.getElementById('orbit-status').className = "";
}

// --- SCENES ---
sim.loadSolar = () => {
    sim.bodies = [];
    sim.bodies.push(new Body(0, 0, 40000, 0, 0, '#ffaa00', 'star_yellow', true));
    let r = 600;
    let v = Math.sqrt((sim.params.G * 40000) / r);
    sim.bodies.push(new Body(r, 0, 100, 0, v, '#00f2ff', 'planet', false));
    sim.camera = {x:0, y:0, zoom:0.5};
};

sim.loadBinary = () => {
    sim.bodies = [];
    let m = 15000, r = 400;
    let v = Math.sqrt((sim.params.G * m) / (4*r));
    sim.bodies.push(new Body(-r, 0, m, 0, v, '#ff2e63', 'star_neutron', false)); // Unlocked Binary
    sim.bodies.push(new Body(r, 0, m, 0, -v, '#00f2ff', 'star_neutron', false));
    sim.camera = {x:0, y:0, zoom:0.4};
};

sim.reset = () => { sim.bodies = []; };

// --- LOOP ---
function loop() {
    ctx.fillStyle = '#050508';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = sim.bodies.length - 1; i >= 0; i--) {
        let b = sim.bodies[i];
        if (b.dead) { sim.bodies.splice(i, 1); continue; }
        b.update(1.0);
        b.draw();
    }
    
    document.getElementById('count').innerText = sim.bodies.length;

    if (sim.input.dragStart && sim.cache.trajectory.length > 0) {
        ctx.beginPath();
        let start = sim.cache.trajectory[0];
        ctx.moveTo(w2s_x(start.x), w2s_y(start.y));
        for(let p of sim.cache.trajectory) ctx.lineTo(w2s_x(p.x), w2s_y(p.y));
        ctx.strokeStyle = '#fff'; ctx.setLineDash([5,5]); ctx.stroke(); ctx.setLineDash([]);
        
        ctx.beginPath();
        ctx.moveTo(w2s_x(sim.input.dragStart.x), w2s_y(sim.input.dragStart.y));
        ctx.lineTo(w2s_x(sim.input.current.x), w2s_y(sim.input.current.y));
        ctx.strokeStyle = sim.builder.color; ctx.stroke();
    }
    requestAnimationFrame(loop);
}

window.dispatchEvent(new Event('resize'));
updateBuilder();
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

