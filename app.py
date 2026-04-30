from flask import Flask, render_template_string

app = Flask(__name__)

# --- ORBITAL ENGINE: FINAL VERSION ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Orbital | Gravity Sim</title>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; background: #050505; overflow: hidden; color: #aaddff; font-family: 'Rajdhani', sans-serif; user-select: none; }
        canvas { display: block; }
        
        /* UI OVERLAY */
        .hud { position: absolute; top: 0; left: 0; width: 100%; padding: 20px; box-sizing: border-box; display: flex; justify-content: space-between; pointer-events: none; }
        .panel { background: rgba(10, 15, 30, 0.8); border: 1px solid #1e3a5f; padding: 15px; border-radius: 8px; backdrop-filter: blur(4px); pointer-events: auto; min-width: 220px; }
        
        h1 { margin: 0 0 10px 0; font-size: 22px; letter-spacing: 2px; text-transform: uppercase; color: #fff; text-shadow: 0 0 10px #00d2ff; border-bottom: 1px solid #1e3a5f; padding-bottom: 5px; }
        .stat-row { display: flex; justify-content: space-between; margin: 5px 0; font-size: 14px; color: #88ccff; }
        .stat-val { font-weight: bold; color: #fff; }

        /* CONTROLS */
        .slider-box { margin-top: 15px; border-top: 1px solid #1e3a5f; padding-top: 10px; }
        label { display: block; font-size: 11px; color: #6699cc; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px; }
        input[type=range] { width: 100%; cursor: pointer; accent-color: #00d2ff; margin-bottom: 10px; }
        
        button { width: 100%; background: rgba(0, 210, 255, 0.1); border: 1px solid #00d2ff; color: #00d2ff; padding: 10px; margin-top: 8px; font-family: inherit; font-weight: bold; cursor: pointer; transition: 0.2s; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
        button:hover { background: #00d2ff; color: #000; box-shadow: 0 0 15px #00d2ff; }
        button.danger { border-color: #ff4444; color: #ff4444; background: rgba(255, 68, 68, 0.1); }
        button.danger:hover { background: #ff4444; color: white; box-shadow: 0 0 15px #ff4444; }

        .tutorial { position: absolute; bottom: 30px; width: 100%; text-align: center; color: rgba(255,255,255,0.3); font-size: 14px; pointer-events: none; letter-spacing: 2px; text-transform: uppercase; }
    </style>
</head>
<body>

<div class="hud">
    <!-- DATA PANEL -->
    <div class="panel">
        <h1>Physics Data</h1>
        <div class="stat-row"><span>Objects:</span> <span class="stat-val" id="obj-count">0</span></div>
        <div class="stat-row"><span>Gravity (G):</span> <span class="stat-val" id="g-val">0.50</span></div>
        <div class="stat-row"><span>Time Scale:</span> <span class="stat-val" id="time-val">1.0x</span></div>
        
        <div class="slider-box">
            <label>Gravitational Constant</label>
            <input type="range" min="0.1" max="2.0" step="0.1" value="0.5" oninput="updatePhysics(this.value, 'g')">
            <label>Time Dilation</label>
            <input type="range" min="0.0" max="3.0" step="0.1" value="1.0" oninput="updatePhysics(this.value, 't')">
        </div>
    </div>

    <!-- CONTROL PANEL -->
    <div class="panel">
        <h1>Simulation</h1>
        <button onclick="spawnSystem('solar')">PRESET: Solar System</button>
        <button onclick="spawnSystem('binary')">PRESET: Binary Stars</button>
        <button onclick="spawnSystem('void')">PRESET: The Void</button>
        <button class="danger" onclick="reset()">Clear All</button>
    </div>
</div>

<div class="tutorial">Click & Drag to Launch • Scroll to Zoom</div>
<canvas id="sim"></canvas>

<script>
    const canvas = document.getElementById('sim');
    const ctx = canvas.getContext('2d');
    
    // --- 1. ENGINE VARIABLES ---
    let G = 0.5;           // Gravity Strength
    let timeScale = 1.0;   // Time Speed
    let particles = [];
    let width, height;
    let stars = [];

    // --- 2. SETUP & RESIZE ---
    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        createStars();
    }
    window.addEventListener('resize', resize);

    function createStars() {
        stars = [];
        for(let i=0; i<150; i++) {
            stars.push({
                x: Math.random() * width,
                y: Math.random() * height,
                size: Math.random() * 1.5,
                alpha: Math.random()
            });
        }
    }

    // --- 3. THE PHYSICS OBJECT ---
    class Particle {
        constructor(x, y, mass, vx, vy, color, isStatic=false) {
            this.x = x;
            this.y = y;
            this.mass = mass;
            this.vx = vx;
            this.vy = vy;
            this.radius = Math.max(2, Math.sqrt(this.mass)); 
            this.color = color;
            this.trail = [];
            this.isStatic = isStatic;
        }

        update() {
            // N-Body Gravity Calculation
            for (let p of particles) {
                if (p === this) continue;
                
                let dx = p.x - this.x;
                let dy = p.y - this.y;
                let distSq = dx*dx + dy*dy;
                let dist = Math.sqrt(distSq);
                
                // Prevent divide by zero / singularity
                if (dist < (this.radius + p.radius)) continue;

                // NEWTON'S LAW: F = G * m1 * m2 / r^2
                let force = (G * this.mass * p.mass) / distSq;
                
                // Force Vectors
                let forceX = force * (dx / dist);
                let forceY = force * (dy / dist);

                // F=ma -> a=F/m -> v+=a
                if(!this.isStatic) {
                    this.vx += (forceX / this.mass) * timeScale;
                    this.vy += (forceY / this.mass) * timeScale;
                }
            }

            // Apply Velocity to Position
            this.x += this.vx * timeScale;
            this.y += this.vy * timeScale;

            // Store Trail
            if(particles.length < 80) {
                this.trail.push({x: this.x, y: this.y});
                if (this.trail.length > 30) this.trail.shift();
            }
        }

        draw() {
            // Draw Trail
            if (this.trail.length > 1) {
                ctx.beginPath();
                ctx.strokeStyle = this.color;
                ctx.lineWidth = 1;
                for(let i=0; i<this.trail.length-1; i++) {
                    ctx.globalAlpha = (i/this.trail.length) * 0.4;
                    ctx.lineTo(this.trail[i].x, this.trail[i].y);
                    ctx.stroke();
                    ctx.beginPath();
                    ctx.moveTo(this.trail[i].x, this.trail[i].y);
                }
            }
            
            // Draw Body
            ctx.globalAlpha = 1.0;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI*2);
            ctx.fillStyle = this.color;
            // Glow Effect based on Mass
            ctx.shadowBlur = this.mass > 100 ? 40 : 10;
            ctx.shadowColor = this.color;
            ctx.fill();
            ctx.shadowBlur = 0; 
        }
    }

    // --- 4. MOUSE CONTROLS (SLINGSHOT) ---
    let dragStart = null;
    let dragCurrent = null;

    canvas.addEventListener('mousedown', e => {
        dragStart = {x: e.clientX, y: e.clientY};
        dragCurrent = {x: e.clientX, y: e.clientY};
    });

    canvas.addEventListener('mousemove', e => {
        if(dragStart) dragCurrent = {x: e.clientX, y: e.clientY};
    });

    canvas.addEventListener('mouseup', e => {
        if(!dragStart) return;
        
        // Calculate Velocity Vector
        let vx = (dragStart.x - e.clientX) * 0.03;
        let vy = (dragStart.y - e.clientY) * 0.03;
        
        // Create New Planet
        let h = Math.floor(Math.random() * 360);
        let color = `hsl(${h}, 90%, 60%)`;
        let mass = Math.random() * 40 + 10;

        particles.push(new Particle(dragStart.x, dragStart.y, mass, vx, vy, color));
        
        dragStart = null;
        dragCurrent = null;
        updateUI();
    });

    // --- 5. SYSTEM LOGIC ---
    function spawnSystem(type) {
        particles = [];
        let cx = width/2, cy = height/2;

        if(type === 'solar') {
            particles.push(new Particle(cx, cy, 4000, 0, 0, '#ffaa00', true)); // Sun
            particles.push(new Particle(cx+300, cy, 100, 0, 2.5, '#00ccff')); // Earth
            particles.push(new Particle(cx+480, cy, 80, 0, 2.0, '#ff4400')); // Mars
        }
        else if(type === 'binary') {
            particles.push(new Particle(cx-100, cy, 2000, 0, 2.2, '#ff0055'));
            particles.push(new Particle(cx+100, cy, 2000, 0, -2.2, '#0055ff'));
        }
        updateUI();
    }

    function reset() { particles = []; updateUI(); }

    function updatePhysics(val, type) {
        if(type === 'g') { G = parseFloat(val); document.getElementById('g-val').innerText = G.toFixed(2); }
        if(type === 't') { timeScale = parseFloat(val); document.getElementById('time-val').innerText = timeScale.toFixed(1) + "x"; }
    }
    
    function updateUI() {
        document.getElementById('obj-count').innerText = particles.length;
    }

    // --- 6. MAIN LOOP ---
    function loop() {
        // Clear Screen
        ctx.fillStyle = '#050505';
        ctx.fillRect(0, 0, width, height);

        // Draw Stars
        ctx.fillStyle = '#fff';
        for(let s of stars) {
            ctx.globalAlpha = Math.random() * s.alpha;
            ctx.beginPath(); ctx.arc(s.x, s.y, s.size, 0, Math.PI*2); ctx.fill();
        }

        // Draw Particles
        for(let p of particles) {
            p.update();
            p.draw();
        }

        // Draw Slingshot Line
        if(dragStart && dragCurrent) {
            ctx.beginPath();
            ctx.moveTo(dragStart.x, dragStart.y);
            ctx.lineTo(dragCurrent.x, dragCurrent.y);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        requestAnimationFrame(loop);
    }

    // Start
    resize();
    spawnSystem('solar');
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
