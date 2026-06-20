/**
 * Observatory - Three.js 3D Scene for PortfolioPro Landing Page
 * A living star field with orbiting wireframes representing features
 */

(function() {
    'use strict';

    // Colors
    const COLORS = {
        cyan: 0x00E5FF,
        magenta: 0xE040FB,
        purple: 0x7B2FFF,
        white: 0xE8E8FF,
        deep: 0x060612
    };

    let scene, camera, renderer;
    let stars, orbitSystem, centralCore;
    let mouse = { x: 0, y: 0 };
    let targetRotation = { x: 0, y: 0 };
    let currentRotation = { x: 0, y: 0 };
    let isPaused = false;

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        const canvas = document.getElementById('nebula-canvas');
        if (!canvas) return;

        // Scene setup
        scene = new THREE.Scene();
        scene.background = new THREE.Color(COLORS.deep);
        scene.fog = new THREE.FogExp2(COLORS.deep, 0.002);

        // Camera
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000);
        camera.position.z = 150;

        // Renderer
        renderer = new THREE.WebGLRenderer({
            canvas: canvas,
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance'
        });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.toneMapping = THREE.ReinhardToneMapping;

        // Create elements
        createStars();
        createOrbitSystem();
        createCentralCore();

        // Event listeners
        window.addEventListener('resize', onWindowResize);
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('scroll', onScroll);

        // Animation
        animate();
    }

    function createStars() {
        const count = 1200;
        const geometry = new THREE.BufferGeometry();
        const positions = [];
        const colors = [];

        for (let i = 0; i < count; i++) {
            const x = (Math.random() - 0.5) * 2000;
            const y = (Math.random() - 0.5) * 2000;
            const z = (Math.random() - 0.5) * 2000;

            positions.push(x, y, z);

            const color = new THREE.Color();
            const colorType = Math.random();
            if (colorType < 0.33) color.setHex(COLORS.cyan);
            else if (colorType < 0.66) color.setHex(COLORS.magenta);
            else color.setHex(COLORS.purple);

            colors.push(color.r, color.g, color.b);
        }

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
            size: 2,
            vertexColors: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            transparent: true,
            opacity: 0.8
        });

        stars = new THREE.Points(geometry, material);
        scene.add(stars);
    }

    function createOrbitSystem() {
        orbitSystem = new THREE.Group();
        
        // Central hub
        const hubGeo = new THREE.IcosahedronGeometry(8, 1);
        const hubMat = new THREE.MeshBasicMaterial({
            color: COLORS.cyan,
            wireframe: true,
            transparent: true,
            opacity: 0.3
        });
        const hub = new THREE.Mesh(hubGeo, hubMat);
        orbitSystem.add(hub);

        // Orbiting nodes (representing features)
        const themes = [
            { name: 'Classic', color: COLORS.cyan, radius: 35, speed: 0.005 },
            { name: 'Terminal', color: COLORS.magenta, radius: 50, speed: -0.004 },
            { name: '3D', color: COLORS.purple, radius: 65, speed: 0.003 },
            { name: 'Dev', color: COLORS.cyan, radius: 80, speed: -0.006 },
            { name: 'Analytics', color: COLORS.magenta, radius: 95, speed: 0.002 },
            { name: 'Custom', color: COLORS.purple, radius: 110, speed: -0.003 }
        ];

        themes.forEach((theme, i) => {
            // Orbit path
            const orbitGeo = new THREE.RingGeometry(theme.radius - 0.2, theme.radius + 0.2, 128);
            const orbitMat = new THREE.MeshBasicMaterial({
                color: theme.color,
                transparent: true,
                opacity: 0.15,
                side: THREE.DoubleSide
            });
            const orbit = new THREE.Mesh(orbitGeo, orbitMat);
            orbit.rotation.x = Math.PI / 2;
            orbitSystem.add(orbit);

            // Node sphere
            const sphereGeo = new THREE.IcosahedronGeometry(3, 2);
            const sphereMat = new THREE.MeshBasicMaterial({
                color: theme.color,
                wireframe: true,
                transparent: true,
                opacity: 0.5
            });
            const sphere = new THREE.Mesh(sphereGeo, sphereMat);
            sphere.userData = { speed: theme.speed, angle: Math.random() * Math.PI * 2 };
            orbitSystem.add(sphere);

            // Connecting lines to center
            if (i < themes.length - 1) {
                const lineGeo = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(0, 0, 0),
                    new THREE.Vector3(0, 0, theme.radius)
                ]);
                const lineMat = new THREE.LineBasicMaterial({
                    color: theme.color,
                    transparent: true,
                    opacity: 0.1
                });
                const line = new THREE.Line(lineGeo, lineMat);
                orbitSystem.add(line);
            }
        });

        scene.add(orbitSystem);
    }

    function createCentralCore() {
        const geometry = new THREE.IcosahedronGeometry(12, 4);
        
        // Custom shader for glowing core
        const vertexShader = `
            varying vec3 vNormal;
            varying vec3 vPosition;
            void main() {
                vNormal = normalize(normalMatrix * normal);
                vPosition = position;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `;

        const fragmentShader = `
            varying vec3 vNormal;
            varying vec3 vPosition;
            uniform vec3 color1;
            uniform vec3 color2;
            uniform float time;
            
            void main() {
                float intensity = 0.5 + 0.5 * dot(vNormal, vec3(0.0, 0.0, 1.0));
                float noise = fract(sin(dot(vPosition, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
                vec3 finalColor = mix(color1, color2, intensity * 0.7 + noise * 0.3);
                gl_FragColor = vec4(finalColor, 0.8);
            }
        `;

        const material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                color1: { value: new THREE.Vector3(0x00E5FF / 255, 0xE040FB / 255, 0xE8E8FF / 255) },
                color2: { value: new THREE.Vector3(0x7B2FFF / 255, 0x00E5FF / 255, 0xE040FB / 255) }
            },
            vertexShader,
            fragmentShader,
            transparent: true,
            side: THREE.DoubleSide
        });

        centralCore = new THREE.Mesh(geometry, material);
        scene.add(centralCore);

        // Add outer glow lines
        const glowGeo = new THREE.IcosahedronGeometry(15, 1);
        const glowMat = new THREE.MeshBasicMaterial({
            color: COLORS.cyan,
            transparent: true,
            opacity: 0.08,
            wireframe: true
        });
        const glow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(glow);

        // Add inner core
        const innerGeo = new THREE.IcosahedronGeometry(8, 2);
        const innerMat = new THREE.MeshBasicMaterial({
            color: COLORS.white,
            transparent: true,
            opacity: 0.3
        });
        const inner = new THREE.Mesh(innerGeo, innerMat);
        scene.add(inner);
    }

    function onMouseMove(event) {
        const x = (event.clientX / window.innerWidth) * 2 - 1;
        const y = -(event.clientY / window.innerHeight) * 2 + 1;
        
        mouse.x = x;
        mouse.y = y;
    }

    function onScroll() {
        const scrollY = window.scrollY;
        const scrollFactor = Math.min(scrollY / (document.body.scrollHeight - window.innerHeight), 1);
        
        // Pull camera back as user scrolls down
        camera.position.z = 150 - scrollFactor * 50;
        
        // Zoom effect on scroll
        if (camera) {
            camera.fov = 75 + scrollFactor * 15;
            camera.updateProjectionMatrix();
        }
    }

    function onWindowResize() {
        if (camera && renderer) {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }
    }

    function animate() {
        requestAnimationFrame(animate);

        if (isPaused) return;

        const time = Date.now() * 0.001;

        // Update central core shader
        if (centralCore) {
            centralCore.userData.time = time;
            if (centralCore.material.uniforms) {
                centralCore.material.uniforms.time.value = time;
            }
        }

        // Rotate orbit system
        if (orbitSystem) {
            orbitSystem.rotation.x += 0.001;
            orbitSystem.rotation.y += 0.0005;

            // Rotate individual nodes
            orbitSystem.children.forEach(child => {
                if (child.userData && child.userData.speed) {
                    child.userData.angle += child.userData.speed;
                    const radius = 35 + (child.geometry.type === 'IcosahedronGeometry' && child.geometry.radius ? 0 : 0);
                    
                    // Re-position node on its orbit
                    if (child.geometry.type === 'IcosahedronGeometry') {
                        const x = Math.sin(child.userData.angle) * 35;
                        const z = Math.cos(child.userData.angle) * 35;
                        child.position.set(x, 0, z);
                        child.rotation.x += 0.02;
                        child.rotation.y += 0.03;
                    }
                }
            });
        }

        // Star rotation
        if (stars) {
            stars.rotation.y += 0.0002;
        }

        // Camera parallax based on mouse
        if (camera) {
            const targetX = mouse.x * 20;
            const targetY = mouse.y * 20;
            
            currentRotation.x += (targetX - currentRotation.x) * 0.05;
            currentRotation.y += (targetY - currentRotation.y) * 0.05;
            
            camera.rotation.x = currentRotation.y * 0.005;
            camera.rotation.y = currentRotation.x * 0.005;
        }

        renderer.render(scene, camera);
    }
})();
