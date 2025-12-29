/**
 * INTERACTIVE 3D THEME LOGIC
 * Handles: 3D Tilt, Scroll Animations, HUD Navigation, Vanta Init
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Initialize VanillaTilt
    if (typeof VanillaTilt !== 'undefined') {
        VanillaTilt.init(document.querySelectorAll("[data-tilt]"), {
            max: 10,
            speed: 400,
            glare: true,
            "max-glare": 0.5,
            scale: 1.02
        });
    }

    // 2. HUD Navigation Logic (Scroll Spy)
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.dock-item');
    
    window.addEventListener('scroll', () => {
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= (sectionTop - sectionHeight / 3)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.target === current) {
                link.classList.add('active');
            }
        });
    });

    // 3. Z-Section Entrance Animations (Intersection Observer)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.z-section').forEach(section => {
        observer.observe(section);
    });

    // 4. Initialize Vanta (Net Effect)
    if (typeof VANTA !== 'undefined') {
        VANTA.NET({
            el: "#vanta-bg",
            mouseControls: true,
            touchControls: true,
            gyroControls: false,
            minHeight: 200.00,
            minWidth: 200.00,
            scale: 1.00,
            scaleMobile: 1.00,
            color: getComputedStyle(document.documentElement).getPropertyValue('--neon-color').trim(),
            backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-color').trim(),
            points: 10.00,
            maxDistance: 20.00,
            spacing: 15.00
        });
    }
    
    console.log("Interactive 3D Theme Initialized");
});
