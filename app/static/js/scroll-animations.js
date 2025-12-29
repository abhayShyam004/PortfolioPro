/**
 * Scroll Animation Controller
 * Handles scroll-triggered animations for elements with .animate-on-scroll class
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        threshold: 0.15,      // How much of element must be visible to trigger
        rootMargin: '0px 0px -50px 0px',  // Trigger slightly before element enters
        animatedClass: 'animated',
        observeSelector: '.animate-on-scroll, .section-header__title'
    };

    /**
     * Initialize Intersection Observer for scroll animations
     */
    function initScrollAnimations() {
        // Check for Intersection Observer support
        if (!('IntersectionObserver' in window)) {
            // Fallback: show all elements immediately
            document.querySelectorAll(CONFIG.observeSelector).forEach(el => {
                el.classList.add(CONFIG.animatedClass);
            });
            return;
        }

        // Create observer
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Add animated class
                    entry.target.classList.add(CONFIG.animatedClass);
                    
                    // Stop observing this element
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: CONFIG.threshold,
            rootMargin: CONFIG.rootMargin
        });

        // Observe all target elements
        document.querySelectorAll(CONFIG.observeSelector).forEach(el => {
            observer.observe(el);
        });
    }

    /**
     * Add stagger delay classes to child elements
     */
    function addStaggerClasses() {
        // Find containers that should have staggered children
        const staggerContainers = document.querySelectorAll(
            '.folio-list, .about-timelines, .skills-list'
        );

        staggerContainers.forEach(container => {
            const children = container.querySelectorAll('.column, .about-timelines__block, .skill-item');
            children.forEach((child, index) => {
                // Add animate class if not present
                if (!child.classList.contains('animate-on-scroll')) {
                    child.classList.add('animate-on-scroll');
                }
                // Add delay class (max 5)
                const delayClass = `delay-${Math.min(index + 1, 5)}`;
                child.classList.add(delayClass);
            });
        });
    }

    /**
     * Smooth parallax effect for intro section
     */
    function initParallax() {
        const introSection = document.querySelector('.s-intro');
        if (!introSection) return;

        let ticking = false;

        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    const scrolled = window.pageYOffset;
                    const rate = scrolled * 0.3;
                    
                    // Apply subtle parallax to intro content
                    const introContent = introSection.querySelector('.s-intro__content');
                    if (introContent && scrolled < window.innerHeight) {
                        introContent.style.transform = `translateY(${rate}px)`;
                        introContent.style.opacity = 1 - (scrolled / window.innerHeight);
                    }
                    
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    /**
     * Counter animation for stats
     */
    function animateCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const target = parseInt(counter.getAttribute('data-counter'));
                    const duration = 2000;
                    const step = target / (duration / 16);
                    let current = 0;

                    const updateCounter = () => {
                        current += step;
                        if (current < target) {
                            counter.textContent = Math.floor(current);
                            requestAnimationFrame(updateCounter);
                        } else {
                            counter.textContent = target;
                        }
                    };

                    updateCounter();
                    observer.unobserve(counter);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => observer.observe(counter));
    }

    /**
     * Text typing effect
     */
    function typeWriter(element, text, speed = 50) {
        let i = 0;
        element.textContent = '';
        
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        
        type();
    }

    /**
     * Mouse-following glow effect
     */
    function initMouseGlow() {
        const glowElements = document.querySelectorAll('.mouse-glow');
        
        glowElements.forEach(el => {
            el.addEventListener('mousemove', (e) => {
                const rect = el.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                el.style.setProperty('--mouse-x', `${x}px`);
                el.style.setProperty('--mouse-y', `${y}px`);
            });
        });
    }

    /**
     * Initialize all animations
     */
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                addStaggerClasses();
                initScrollAnimations();
                initParallax();
                animateCounters();
                initMouseGlow();
            });
        } else {
            addStaggerClasses();
            initScrollAnimations();
            initParallax();
            animateCounters();
            initMouseGlow();
        }
    }

    // Expose to global scope
    window.ScrollAnimations = {
        init,
        typeWriter,
        reinit: initScrollAnimations
    };

    // Auto-initialize
    init();

})();
