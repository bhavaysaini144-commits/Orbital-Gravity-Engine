from flask import Flask, render_template_string

app = Flask(__name__)

# --- FINAL PROJECT: CELESTIAL ARCHITECT v3 ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Celestial Architect | Pro Physics</title>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; background: #050505; overflow: hidden; color: #aaddff; font-family: 'Rajdhani', sans-serif; user-select: none; }
        canvas { display: block; }
        
        /* HUD LAYOUT */
        .hud { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; padding: 20px; box-sizing: border-box; display: flex; justify-content: space-between; }
        
        /* PANELS */
        .panel { 
            background: rgba(12, 18, 30, 0.9); 
            border: 1px solid #1e3a5f; 
            padding: 15px; 
            border-radius: 8px; 
            backdrop-filter: blur(8px); 
            pointer-events: auto; 
            width: 260px; 
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }
        
        /* HEADERS & TEXT */
        h2 { margin: 0 0 15px 0; font-size: 18px; letter-spacing: 2px; text-transform: uppercase; color: #00d2ff; border-bottom: 1px solid #1e3a5f; padding-bottom: 5px; }
        .label { font-size: 12px; color: #6699cc; margin-top: 10px; text-transform: uppercase; letter-spacing: 1px; display: flex; justify-content: space-between; }
        .value { color: white; font-weight: bold; }

        /* CONTROLS */
        select, button { 
            width: 100%; background: rgba(0, 0, 0, 0.3); border: 1px solid #335577; color: #aaddff; 
            padding: 8px; margin-top: 5px; font-family: inherit; cursor: pointer; outline: none; 
        }
        select:hover, button:hover { border-color: #00d2ff; color: white; }
        
        input[type=range] { width: 100%; margin: 8px 0; accent-color: #00d2ff; cursor: pointer; }
        
        .toggle-row { display: flex; align-items: center; margin-top: 15px; cursor: pointer; }
        .checkbox { width: 16px; height: 16px; border: 1px solid #00d2ff; margin-right: 10px; display: inline-block; background: rgba(0,0,0,0.5); }
        .checked { background: #00d2ff; box-shadow: 0 0 10px #00d2ff; }

        /* NOTIFICATIONS */
        #alert-box { position: absolute; top: 20px; left: 50%; transform: translateX(-50%); color: #ff4444; font-weight: bold; opacity: 0; transition: 0.5s; text-shadow: 0 0 10px red; }
    </style>
</head>
<body>

<div id="alert-box">⚠ BLACK HOLE DETECTED ⚠</div>

<div class="hud">
    <!-- LEFT: CREATION LAB -->
    <div class="panel">
        <h2>Celestial Forge</h2>
        
        <div class="label">Class Type</div>
        <select id="type-select" onchange="updatePreset()">
            <option value="planet">Standard Planet</option>
            <option value="star_yellow">Star (Yellow Dwarf)</option>
            <option value="star_red">Star (Red Giant)</option>
            <option value="neutron">Neutron Star</option>
            <option value="black_hole">>> BLACK HOLE <<</option>
        </select>

        <div class="label"><span>Mass</span> <span id="mass-val" class="value">50</span></div>
        <input type="range" id="mass-slider" min="10" max="10000" value="50" oninput="manualOverride()">

        <div class="label"><span>Density</span> <span id="dens-val" class="value">1.0</span></div>
        <input type="range" id="dens-slider" min="0.1" max="5.0" step="0.1" value="1.0" oninput="manualOverride()">
        
        <div class="toggle-row" onclick="toggleLock()">
            <div class="checkbox" id="lock-box"></div>
            <span>Lock Position (God Mode)</span>
        </div>

        <div class="label" style="margin-top: 20px; color: #888;">PREDICTION ENGINE: ACTIVE</div>
    </div>

    <!-- RIGHT: TELEMETRY -->
    <div class="panel">
        <h2>Mission Data</h2>
        <div class="label"><span>Object Count</span> <span id="count" class="value">0</span></div>
        <div class="label"><span>Zoom Level</span> <span id="zoom" class="value">1.0x</span></div>
        <div class="label"><span>Sim Speed</span> <span id="speed" class="value">1.0x</span></div>
        
        <button onclick="spawnSystem('solar')" style="margin-top: 20px; border-color: #00d2ff;">Load: Solar System</button>
        <button onclick="spawnSystem('binary')">Load: Binary Stars</button>
        <button onclick="spawnSystem('void')" style="border-color: #ff4444; color: #ff4444;">Clear Sector</button>
    </div>
</div>

<canvas id="sim"></canvas>

<script>
    const canvas = document.getElementById('sim');
    const ctx = canvas.getContext('2d');
    
    // --- CORE ENGINE ---
    let particles = [];
    let stars = []; // Background
    let width, height;
    let G = 0.5;
    
    // --- CAMERA ---
    let camera = { x: 0, y: 0, zoom: 1.0 };
    
    // --- BUILDER STATE ---
    let builder = {
        type: 'planet',
        mass: 50,
        density: 1.0,
        locked: false,
        color: '#00ccff'
    };

    // --- SETUP ---
    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        generateBackground();
    }
    window.addEventListener('resize', resize);

    function generateBackground() {
        stars = [];
        for(let i=0; i<600; i++) {
            stars.push({
                x: (Math.random()-0.5) * width * 4,
                y: (Math.random()-0.5) * height * 4,
                r: Math.random() * 1.5,
                a: Math.random()
            });
        }
    }

    // --- PHYSICS ENTITY ---
    class Body {
        constructor(x, y, mass, vx, vy, color, type, locked) {
            this.x = x;
            this.y = y;
            this.mass = mass;
            this.vx = vx;
            this.vy = vy;
            this.color = color;
            this.type = type; // 'planet', 'star', 'black_hole'
            this.locked = locked;
            this.trail = [];
            
            // Radius derived from Mass & Density (Volume formula approx)
            // Density = Mass / Volume -> Volume = Mass / Density -> R ~ cbrt(Vol)
            // We use sqrt for 2D visual simplicity
            this.radius = Math.sqrt(this.mass / builder.density);
            if(this.type === 'black_hole') this.radius = Math.sqrt(this.mass) * 0.2; // Ultra dense
        }

        update() {
            for (let p of particles) {
                if (p === this) continue;
                
                let dx = p.x - this.x;
                let dy = p.y - this.y;
                let distSq = dx*dx + dy*dy;
                let dist = Math.sqrt(distSq);
                
                // BLACK HOLE LOGIC: Event Horizon
                if (this.type === 'black_hole' && dist < this.radius + p.radius) {
                    // EAT THE PLANET
                    if (p.type !== 'black_hole') {
                        p.dead = true;
                        this.mass += p.mass * 0.1; // Absorb mass
                        continue;
                    }
                }

                if (dist < 5) continue; // Singularity Guard

                let force = (G * this.mass * p.mass) / distSq;
                let forceX = force * (dx / dist);
                let forceY = force * (dy / dist);

                if (!this.locked) {
                    this.vx += forceX / this.mass;
                    this.vy += forceY / this.mass;
                }
            }

            if (!this.locked) {
                this.x += this.vx;
                this.y += this.vy;
            }

            // Trail Buffer
            if(particles.length < 100 && !this.locked) {
                this.trail.push({x: this.x, y: this.y});
                if(this.trail.length > 40) this.trail.shift();
            }
        }

        draw() {
            // Draw Trail
            if (this.trail.length > 1) {
                ctx.beginPath();
                ctx.strokeStyle = this.color;
                ctx.lineWidth = 1 / camera.zoom;
                for(let i=0; i<this.trail.length-1; i++) {
                    ctx.lineTo(this.trail[i].x, this.trail[i].y);
                }
                ctx.stroke();
            }

            // Draw Body
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI*2);
            ctx.fillStyle = this.color;
            
            // Special Effects
            if (this.type === 'star' || this.type === 'neutron') {
                ctx.shadowBlur = 30 * camera.zoom;
                ctx.shadowColor = this.color;
            }
            if (this.type === 'black_hole') {
                ctx.fillStyle = '#000';
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.shadowBlur = 20;
                ctx.shadowColor = '#a00'; // Accretion disk glow
            }
            
            ctx.fill();
            ctx.shadowBlur = 0;
        }
    }

    // --- UI LOGIC ---
    function updatePreset() {
        let type = document.getElementById('type-select').value;
        let mSlider = document.getElementById('mass-slider');
        let dSlider = document.getElementById('dens-slider');
        let alert = document.getElementById('alert-box');
        
        alert.style.opacity = 0;

        if (type === 'planet') {
            builder = { type: 'planet', mass: 50, density: 1.0, color: '#00ccff', locked: false };
        } else if (type === 'star_yellow') {
            builder = { type: 'star', mass: 2000, density: 0.8, color: '#ffaa00', locked: true };
        } else if (type === 'star_red') {
            builder = { type: 'star', mass: 4000, density: 0.3, color: '#ff4400', locked: true };
        } else if (type === 'neutron') {
            builder = { type: 'neutron', mass: 1000, density: 3.0, color: '#00ffff', locked: true };
        } else if (type === 'black_hole') {
            builder = { type: 'black_hole', mass: 10000, density: 10.0, color: '#000', locked: true };
            alert.style.opacity = 1;
        }

        // Update UI Controls to match preset
        mSlider.value = builder.mass;
        dSlider.value = builder.density;
        document.getElementById('mass-val').innerText = builder.mass;
        document.getElementById('dens-val').innerText = builder.density;
        updateLockUI();
    }

    function manualOverride() {
        builder.mass = parseFloat(document.getElementById('mass-slider').value);
        builder.density = parseFloat(document.getElementById('dens-slider').value);
        document.getElementById('mass-val').innerText = builder.mass;
        document.getElementById('dens-val').innerText = builder.density;
    }

    function toggleLock() {
        builder.locked = !builder.locked;
        updateLockUI();
    }

    function updateLockUI() {
        let box = document.getElementById('lock-box');
        box.className = builder.locked ? 'checkbox checked' : 'checkbox';
    }

    // --- INPUT & TRAJECTORY PREDICTION ---
    let dragStart = null;
    let dragCurrent = null;

    function getWorldPos(e) {
        return {
            x: (e.clientX - width/2) / camera.zoom + width/2 - camera.x,
            y: (e.clientY - height/2) / camera.zoom + height/2 - camera.y
        };
    }

    canvas.addEventListener('mousedown', e => {
        dragStart = getWorldPos(e);
        dragCurrent = dragStart;
    });
    
    canvas.addEventListener('mousemove', e => {
        if(dragStart) dragCurrent = getWorldPos(e);
    });

    canvas.addEventListener('mouseup', e => {
        if(!dragStart) return;
        
        // Launch Logic
        let vx = (dragStart.x - dragCurrent.x) * 0.05;
        let vy = (dragStart.y - dragCurrent.y) * 0.05;
        
        particles.push(new Body(
            dragStart.x, dragStart.y, 
            builder.mass, vx, vy, 
            builder.color, builder.type, builder.locked
        ));

        dragStart = null;
        document.getElementById('count').innerText = particles.length;
    });

    // ZOOM
    window.addEventListener('wheel', e => {
        camera.zoom += e.deltaY < 0 ? 0.1 : -0.1;
        if(camera.zoom < 0.1) camera.zoom = 0.1;
        if(camera.zoom > 5) camera.zoom = 5;
        document.getElementById('zoom').innerText = camera.zoom.toFixed(1) + "x";
    });

    // --- SCENES ---
    function spawnSystem(type) {
        particles = [];
        let cx = width/2, cy = height/2;
        
        if(type === 'solar') {
            particles.push(new Body(cx, cy, 5000, 0, 0, '#ffaa00', 'star', true));
            particles.push(new Body(cx+400, cy, 100, 0, 2.5, '#00ccff', 'planet', false));
        }
        if(type === 'binary') {
            particles.push(new Body(cx-200, cy, 3000, 0, 2.5, '#ff0055', 'star', false));
            particles.push(new Body(cx+200, cy, 3000, 0, -2.5, '#0055ff', 'star', false));
        }
        document.getElementById('count').innerText = particles.length;
    }

    // --- RENDER LOOP ---
    function loop() {
        // 1. Draw Background & Camera
        ctx.fillStyle = '#050505';
        ctx.fillRect(0, 0, width, height);
        
        ctx.save();
        ctx.translate(width/2, height/2);
        ctx.scale(camera.zoom, camera.zoom);
        ctx.translate(-width/2 + camera.x, -height/2 + camera.y);

        ctx.fillStyle = '#fff';
        for(let s of stars) {
            ctx.globalAlpha = s.a;
            ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI*2); ctx.fill();
        }

        // 2. Physics Step
        ctx.globalAlpha = 1.0;
        for (let i = particles.length - 1; i >= 0; i--) {
            let p = particles[i];
            if (p.dead) { particles.splice(i, 1); continue; }
            p.update();
            p.draw();
        }

        // 3. PREDICTION LINE (The "Math Flex")
        if (dragStart && dragCurrent) {
            // Draw Pull Line
            ctx.beginPath();
            ctx.moveTo(dragStart.x, dragStart.y);
            ctx.lineTo(dragCurrent.x, dragCurrent.y);
            ctx.strokeStyle = 'white';
            ctx.stroke();

            // CALCULATE FUTURE
            let vx = (dragStart.x - dragCurrent.x) * 0.05;
            let vy = (dragStart.y - dragCurrent.y) * 0.05;
            let simX = dragStart.x;
            let simY = dragStart.y;
            
            ctx.beginPath();
            ctx.moveTo(simX, simY);
            
            // Simulate 100 ticks ahead
            for(let i=0; i<100; i++) {
                // Add forces from existing planets to our ghost particle
                for(let p of particles) {
                    let dx = p.x - simX;
                    let dy = p.y - simY;
                    let distSq = dx*dx + dy*dy;
                    let dist = Math.sqrt(distSq);
                    if(dist < 50) break; // Collision prediction
                    
                    let force = (G * p.mass) / distSq; // Simplified F = ma (mass cancels out for acceleration)
                    let ax = force * (dx / dist);
                    let ay = force * (dy / dist);
                    
                    vx += ax;
                    vy += ay;
                }
                simX += vx;
                simY += vy;
                ctx.lineTo(simX, simY);
            }
            
            ctx.strokeStyle = 'rgba(0, 210, 255, 0.5)';
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        ctx.restore();
        requestAnimationFrame(loop);
    }

    // Start
    resize();
    spawnSystem('solar');
    updatePreset(); // Init UI
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
