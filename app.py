from flask import Flask, render_template_string

app = Flask(__name__)

# --- TITAN ENGINE: v6 (OPTIMIZED & PROFESSIONAL) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Titan | Orbital Dynamics Lab</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* --- PROFESSIONAL UI THEME --- */
        :root { --bg: #0b0c10; --panel: rgba(20, 24, 30, 0.85); --accent: #00f2ff; --text: #c5c6c7; --alert: #ff2e63; }
        body { margin: 0; background: var(--bg); overflow: hidden; font-family: 'Inter', sans-serif; color: var(--text); user-select: none; }
        canvas { display: block; width: 100vw; height: 100vh; }

        /* DASHBOARD LAYOUT */
        .ui-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; display: grid; grid-template-columns: 320px 1fr 320px; padding: 20px; box-sizing: border-box; }
        
        /* PANELS */
        .panel { 
            background: var(--panel); 
            backdrop-filter: blur(12px); 
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 6px; 
            padding: 20px; 
            pointer-events: auto; 
            display: flex; flex-direction: column; gap: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        }

        /* TYPOGRAPHY */
        h2 { margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; color: var(--accent); border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
        .stat-row { display: flex; justify-content: space-between; font-size: 13px; font-family: 'JetBrains Mono', monospace; }
        .stat-val { color: #fff; font-weight: 700; }
        
        /* CONTROLS */
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button {
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); color: #fff;
            padding: 10px; border-radius: 4px; cursor: pointer; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; transition: 0.2s;
        }
        button:hover { background: var(--accent); color: #000; border-color: var(--accent); }
        button.danger { border-color: var(--alert); color: var(--alert); }
        button.danger:hover { background: var(--alert); color: white; }

        /* ORBIT STATUS INDICATOR */
        #orbit-status { 
            text-align: center; padding: 8px; border-radius: 4px; font-weight: 800; font-size: 12px; letter-spacing: 1px; 
            background: #1a1d24; color: #555; 
        }
        .status-stable { background: rgba(0, 242, 255, 0.15) !important; color: var(--accent) !important; box-shadow: 0 0 15px var(--accent); }
        .status-escape { background: rgba(255, 46, 99, 0.15) !important; color: var(--alert) !important; }

        /* TOOLTIP INSTRUCTIONS */
        .controls-hint { position: absolute; bottom: 30px; width: 100%; text-align: center; font-size: 12px; opacity: 0.5; letter-spacing: 1px; }
    </style>
</head>
<body>

<div class="ui-layer">
    <!-- LEFT: MISSION CONTROL -->
    <div class="panel">
        <h2>Mission Configuration</h2>
        <div class="btn-group">
            <button onclick="sim.loadSolar()">Load Solar</button>
            <button onclick="sim.loadBinary()">Load Binary</button>
        </div>
        <button class="danger" onclick="sim.reset()">Clear Vacuum</button>
        
        <div style="height: 10px;"></div>
        <h2>Physics Parameters</h2>
        <div class="stat-row"><span>Time Scale</span> <span id="t-val" class="stat-val">1.0x</span></div>
        <input type="range" min="0" max="3" step="0.1" value="1" oninput="sim.params.timeScale=parseFloat(this.value); updateUI();">
    </div>

    <!-- CENTER spacer -->
    <div></div>

    <!-- RIGHT: TELEMETRY -->
    <div class="panel">
        <h2>Flight Computer</h2>
        <div class="stat-row"><span>Active Bodies:</span> <span id="count" class="stat-val">0</span></div>
        <div class="stat-row"><span>Zoom Level:</span> <span id="zoom-display" class="stat-val">1.00x</span></div>
        
        <div style="border-top: 1px solid rgba(255,255,255,0.1); margin: 5px 0;"></div>
        
        <!-- DYNAMIC TRAJECTORY DATA -->
        <div class="stat-row"><span>Launch Vel:</span> <span id="v-launch" class="stat-val">--</span></div>
        <div class="stat-row"><span>Escape Vel:</span> <span id="v-esc" class="stat-val">--</span></div>
        <div id="orbit-status">AWAITING INPUT</div>
    </div>
</div>

<div class="controls-hint">LEFT DRAG: LAUNCH • RIGHT DRAG: PAN CAMERA • SCROLL: ZOOM</div>
<canvas id="canvas"></canvas>

<script>
/**
 * TITAN ENGINE v6
 * A High-Performance N-Body Physics Kernel
 */

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d', { alpha: false }); // Optimize rendering

// --- ENGINE STATE ---
const sim = {
    width: 0, height: 0,
    bodies: [],
    camera: { x: 0, y: 0, zoom: 0.5 }, // Start zoomed out
    input: { 
        dragStart: null, // World coords
        current: null,   // World coords
        panning: false, 
        panStart: {x:0, y:0} 
    },
    params: { G: 1.5, timeScale: 1.0 }, // Tuned Gravity
    cache: { trajectory: [] } // Optimization: Cache prediction
};

// --- THE PHYSICS KERNEL ---
class Body {
    constructor(x, y, mass, vx, vy, color, type) {
        this.x = x; this.y = y;
        this.mass = mass;
        this.vx = vx; this.vy = vy;
        this.color = color;
        this.type = type; // 'star' | 'planet'
        this.radius = type === 'star' ? Math.sqrt(mass)*0.4 : Math.max(2, Math.sqrt(mass));
        this.trail = [];
    }

    update(dt) {
        if (this.type === 'star') return; // Optimization: Stars don't move in this mode

        let fx = 0, fy = 0;
        
        // Semi-Implicit Euler Integration (Symplectic)
        for (let other of sim.bodies) {
            if (other === this) continue;
            
            let dx = other.x - this.x;
            let dy = other.y - this.y;
            let distSq = dx*dx + dy*dy;
            let dist = Math.sqrt(distSq);

            // Collision (Absorption Logic)
            if (dist < this.radius + other.radius) {
                if (other.mass > this.mass) { this.dead = true; other.mass += this.mass * 0.1; }
                continue;
            }

            // Gravity: F = G * M * m / r^2
            let f = (sim.params.G * other.mass) / distSq;
            fx += f * (dx / dist);
            fy += f * (dy / dist);
        }

        this.vx += fx * dt;
        this.vy += fy * dt;
        this.x += this.vx * dt;
        this.y += this.vy * dt;

        // Trail Buffer (Optimized: Skip frames if slow)
        if (sim.bodies.length < 300) {
            this.trail.push({x: this.x, y: this.y});
            if (this.trail.length > 100) this.trail.shift();
        }
    }

    draw() {
        let sx = w2s_x(this.x);
        let sy = w2s_y(this.y);
        let sr = this.radius * sim.camera.zoom;

        if (sr < 0.5) return; // Don't draw sub-pixel dots

        // Draw Trail
        if (this.trail.length > 2) {
            ctx.beginPath();
            ctx.strokeStyle = this.color;
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.3;
            // Draw only every 3rd point for performance
            ctx.moveTo(w2s_x(this.trail[0].x), w2s_y(this.trail[0].y));
            for(let i=2; i<this.trail.length; i+=2) {
                ctx.lineTo(w2s_x(this.trail[i].x), w2s_y(this.trail[i].y));
            }
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }

        // Draw Body
        ctx.beginPath();
        ctx.arc(sx, sy, sr, 0, Math.PI*2);
        ctx.fillStyle = this.color;
        
        // Star Glow
        if (this.type === 'star') {
            ctx.shadowBlur = 40;
            ctx.shadowColor = this.color;
        }
        ctx.fill();
        ctx.shadowBlur = 0;
    }
}

// --- COORDINATE SYSTEMS (CRITICAL FOR ZOOM) ---
// World to Screen
function w2s_x(wx) { return (wx - sim.camera.x) * sim.camera.zoom + sim.width/2; }
function w2s_y(wy) { return (wy - sim.camera.y) * sim.camera.zoom + sim.height/2; }
// Screen to World
function s2w_x(sx) { return (sx - sim.width/2) / sim.camera.zoom + sim.camera.x; }
function s2w_y(sy) { return (sy - sim.height/2) / sim.camera.zoom + sim.camera.y; }

// --- INPUT HANDLING (PAN & ZOOM) ---
window.addEventListener('resize', () => {
    sim.width = canvas.width = window.innerWidth;
    sim.height = canvas.height = window.innerHeight;
});

canvas.addEventListener('wheel', e => {
    e.preventDefault(); // STOP PAGE SCROLLING
    let zoomIntensity = 0.1;
    sim.camera.zoom += e.deltaY < 0 ? zoomIntensity : -zoomIntensity;
    if (sim.camera.zoom < 0.1) sim.camera.zoom = 0.1;
    updateUI();
}, { passive: false });

canvas.addEventListener('mousedown', e => {
    if (e.button === 2) { // Right Click (Pan)
        sim.input.panning = true;
        sim.input.panStart = { x: e.clientX, y: e.clientY };
    } else { // Left Click (Launch)
        let wx = s2w_x(e.clientX);
        let wy = s2w_y(e.clientY);
        sim.input.dragStart = { x: wx, y: wy };
        sim.input.current = { x: wx, y: wy };
        calculateTrajectory(); // Calc once on click
    }
});

canvas.addEventListener('mousemove', e => {
    // Panning Logic
    if (sim.input.panning) {
        let dx = (e.clientX - sim.input.panStart.x) / sim.camera.zoom;
        let dy = (e.clientY - sim.input.panStart.y) / sim.camera.zoom;
        sim.camera.x -= dx;
        sim.camera.y -= dy;
        sim.input.panStart = { x: e.clientX, y: e.clientY };
        return;
    }

    // Launching Logic
    if (sim.input.dragStart) {
        let wx = s2w_x(e.clientX);
        let wy = s2w_y(e.clientY);
        sim.input.current = { x: wx, y: wy };
        
        // OPTIMIZATION: Recalculate trajectory ONLY when mouse moves
        calculateTrajectory();
    }
});

canvas.addEventListener('mouseup', e => {
    if (sim.input.panning) { sim.input.panning = false; return; }
    
    if (sim.input.dragStart) {
        // Launch!
        let vx = (sim.input.dragStart.x - sim.input.current.x) * 0.02;
        let vy = (sim.input.dragStart.y - sim.input.current.y) * 0.02;
        
        sim.bodies.push(new Body(
            sim.input.dragStart.x, sim.input.dragStart.y, 
            20, vx, vy, '#00f2ff', 'planet'
        ));
        
        sim.input.dragStart = null;
        sim.cache.trajectory = []; // Clear cache
        resetUI();
        updateUI();
    }
});
// Disable context menu for right-click pan
canvas.addEventListener('contextmenu', e => e.preventDefault());

// --- TRAJECTORY PREDICTOR (THE MATH CORE) ---
function calculateTrajectory() {
    if (!sim.input.dragStart) return;
    
    let points = [];
    let ghost = { 
        x: sim.input.dragStart.x, 
        y: sim.input.dragStart.y, 
        vx: (sim.input.dragStart.x - sim.input.current.x) * 0.02, 
        vy: (sim.input.dragStart.y - sim.input.current.y) * 0.02 
    };

    // Calculate Velocity & Escape Velocity
    let v_curr = Math.sqrt(ghost.vx*ghost.vx + ghost.vy*ghost.vy);
    let sun = sim.bodies.find(b => b.type === 'star');
    let v_esc = 0;
    let isStable = false;

    if (sun) {
        let dx = sun.x - ghost.x;
        let dy = sun.y - ghost.y;
        let dist = Math.sqrt(dx*dx + dy*dy);
        v_esc = Math.sqrt(2 * sim.params.G * sun.mass / dist); // Physics Formula
        isStable = v_curr < v_esc;
    }

    // Simulate 200 steps
    for(let i=0; i<200; i++) {
        let fx = 0, fy = 0;
        for(let b of sim.bodies) {
            if(b.type !== 'star') continue; // Only gravity from stars matters for prediction
            let dx = b.x - ghost.x;
            let dy = b.y - ghost.y;
            let dSq = dx*dx + dy*dy;
            let d = Math.sqrt(dSq);
            if(d < 20) break; // Crash
            let f = (sim.params.G * b.mass) / dSq;
            fx += f * (dx/d);
            fy += f * (dy/d);
        }
        ghost.vx += fx; ghost.vy += fy;
        ghost.x += ghost.vx; ghost.y += ghost.vy;
        points.push({x: ghost.x, y: ghost.y});
    }
    
    sim.cache.trajectory = points;
    updateTelemetry(v_curr, v_esc, isStable);
}

// --- UI UPDATES ---
function updateUI() {
    document.getElementById('count').innerText = sim.bodies.length;
    document.getElementById('zoom-display').innerText = sim.camera.zoom.toFixed(2) + "x";
    document.getElementById('t-val').innerText = sim.params.timeScale.toFixed(1) + "x";
}

function updateTelemetry(v, esc, stable) {
    document.getElementById('v-launch').innerText = v.toFixed(3) + " km/s";
    document.getElementById('v-esc').innerText = esc.toFixed(3) + " km/s";
    
    const statBox = document.getElementById('orbit-status');
    if(stable) {
        statBox.innerText = "ORBIT: STABLE (CAPTURE)";
        statBox.className = "status-stable";
    } else {
        statBox.innerText = "ORBIT: ESCAPE TRAJECTORY";
        statBox.className = "status-escape";
    }
}

function resetUI() {
    const statBox = document.getElementById('orbit-status');
    statBox.innerText = "AWAITING INPUT";
    statBox.className = "";
    document.getElementById('v-launch').innerText = "--";
    document.getElementById('v-esc').innerText = "--";
}

// --- SCENES ---
sim.loadSolar = () => {
    sim.bodies = [];
    let cx = 0, cy = 0;
    
    // 1. Sun (Massive, Static)
    sim.bodies.push(new Body(cx, cy, 40000, 0, 0, '#ffaa00', 'star'));
    
    // 2. Earth (Stable Circular Orbit)
    // v = sqrt(G * M / r)
    let r = 600;
    let v = Math.sqrt((sim.params.G * 40000) / r);
    sim.bodies.push(new Body(cx + r, cy, 100, 0, v, '#00f2ff', 'planet'));
    
    sim.camera.x = 0; sim.camera.y = 0; sim.camera.zoom = 0.5;
    updateUI();
};

sim.loadBinary = () => {
    sim.bodies = [];
    let m = 15000, r = 400;
    let v = Math.sqrt((sim.params.G * m) / (4*r)); // Binary Stability Formula

    sim.bodies.push(new Body(-r, 0, m, 0, v, '#ff2e63', 'star'));
    sim.bodies.push(new Body(r, 0, m, 0, -v, '#00f2ff', 'star'));
    
    sim.camera.x = 0; sim.camera.y = 0; sim.camera.zoom = 0.4;
    updateUI();
};

sim.reset = () => { sim.bodies = []; updateUI(); };

// --- MAIN LOOP ---
function loop() {
    // 1. Clear
    ctx.fillStyle = '#0b0c10';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Draw Grid (Optional: Helps perception of movement)
    // (Skipped for minimalism, but stars would go here)

    // 3. Physics & Draw
    for (let i = sim.bodies.length - 1; i >= 0; i--) {
        let b = sim.bodies[i];
        if (b.dead) { sim.bodies.splice(i, 1); continue; }
        b.update(sim.params.timeScale);
        b.draw();
    }

    // 4. Draw Prediction Line (From Cache)
    if (sim.input.dragStart && sim.cache.trajectory.length > 0) {
        ctx.beginPath();
        let start = sim.cache.trajectory[0];
        ctx.moveTo(w2s_x(start.x), w2s_y(start.y));
        for(let p of sim.cache.trajectory) {
            ctx.lineTo(w2s_x(p.x), w2s_y(p.y));
        }
        ctx.strokeStyle = '#ffffff';
        ctx.setLineDash([5, 5]);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Draw Drag Line
        ctx.beginPath();
        ctx.moveTo(w2s_x(sim.input.dragStart.x), w2s_y(sim.input.dragStart.y));
        ctx.lineTo(w2s_x(sim.input.current.x), w2s_y(sim.input.current.y));
        ctx.strokeStyle = '#00f2ff';
        ctx.stroke();
    }

    requestAnimationFrame(loop);
}

// Init
window.dispatchEvent(new Event('resize')); // Force size calc
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
