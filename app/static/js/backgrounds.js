/**
 * Advanced Background Effects
 * - Digital Waves
 * - Matrix Rain
 * - Starfield Warp
 */

const BackgroundEffects = {
    // 1. Digital Waves
    initWaves: function(canvasId, color) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        // Resize
        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();

        let increment = 0;
        
        function animate() {
            requestAnimationFrame(animate);
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'; // Trail effect
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const waveColor = color || '#6366f1';
            ctx.beginPath();
            
            // Generate multiple sine waves
            for (let i = 0; i < 3; i++) {
                ctx.moveTo(0, canvas.height / 2);
                for (let x = 0; x < canvas.width; x++) {
                    const y = canvas.height / 2 + 
                        Math.sin(x * 0.01 + increment + i) * 50 * Math.sin(increment * 0.1);
                    ctx.lineTo(x, y);
                }
                ctx.strokeStyle = waveColor.replace(')', `, ${0.5 - i * 0.1})`).replace('rgb', 'rgba');
                // Simple opacity hack if hex
                if (waveColor.startsWith('#')) {
                    ctx.strokeStyle = hexToRgba(waveColor, 0.5 - i * 0.1);
                }
                ctx.stroke();
            }
            increment += 0.02;
        }
        animate();
    },

    // 2. Matrix Rain
    initMatrix: function(canvasId, color) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();

        const chars = '0123456789ABCDEF';
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops = [];

        for(let x = 0; x < columns; x++) {
            drops[x] = 1;
        }

        const rainColor = color || '#0F0';

        function animate() {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = rainColor;
            ctx.font = fontSize + 'px monospace';

            for(let i = 0; i < drops.length; i++) {
                const text = chars.charAt(Math.floor(Math.random() * chars.length));
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);

                if(drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
            requestAnimationFrame(animate);
        }
        animate();
    },

    // 3. Starfield Warp
    initStarfield: function(canvasId, color) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();

        let stars = [];
        const numStars = 200;
        const speed = 2;

        for (let i = 0; i < numStars; i++) {
            stars.push({
                x: Math.random() * canvas.width - canvas.width / 2,
                y: Math.random() * canvas.height - canvas.height / 2,
                z: Math.random() * canvas.width
            });
        }

        const starColor = color || '#fff';

        function animate() {
            ctx.fillStyle = 'black';
            ctx.fillRect(0, 0, canvas.width, canvas.height); // Clear screen properly for space

            ctx.fillStyle = starColor;
            
            for (let i = 0; i < stars.length; i++) {
                let star = stars[i];
                star.z -= speed;

                if (star.z <= 0) {
                    star.z = canvas.width;
                    star.x = Math.random() * canvas.width - canvas.width / 2;
                    star.y = Math.random() * canvas.height - canvas.height / 2;
                }

                const x = (star.x / star.z) * (canvas.width / 2) + canvas.width / 2;
                const y = (star.y / star.z) * (canvas.height / 2) + canvas.height / 2;
                
                // Size based on distance
                const r = (1 - star.z / canvas.width) * 3;

                ctx.beginPath();
                ctx.arc(x, y, r, 0, Math.PI * 2);
                ctx.fill();
            }
            requestAnimationFrame(animate);
        }
        animate();
    }
};

// Helper: Hex to RGBA
function hexToRgba(hex, alpha) {
    let c;
    if(/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)){
        c= hex.substring(1).split('');
        if(c.length== 3){
            c= [c[0], c[0], c[1], c[1], c[2], c[2]];
        }
        c= '0x'+c.join('');
        return 'rgba('+[(c>>16)&255, (c>>8)&255, c&255].join(',')+','+alpha+')';
    }
    return 'rgba(255, 255, 255, ' + alpha + ')'; // Fallback
}
