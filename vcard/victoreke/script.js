/*==============================================================
  VictorEke Portfolio Theme - JavaScript
  Theme Toggle + Mobile Menu + Scroll Animations
==============================================================*/

document.addEventListener('DOMContentLoaded', function() {
  initThemeToggle();
  initMobileMenu();
  initScrollAnimations();
});


/* ===== THEME TOGGLE ===== */
function initThemeToggle() {
  const themeToggle = document.getElementById('theme-toggle');
  const html = document.documentElement;
  
  // Check for saved theme preference or default to system preference
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    html.classList.add('dark');
  }
  
  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      html.classList.toggle('dark');
      
      // Save preference
      const isDark = html.classList.contains('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
  }
}


/* ===== MOBILE MENU ===== */
function initMobileMenu() {
  const menuBtn = document.getElementById('mobile-menu-btn');
  const closeBtn = document.getElementById('mobile-menu-close');
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileLinks = document.querySelectorAll('.mobile-nav-link');
  
  function openMenu() {
    mobileMenu.classList.add('active');
    document.body.classList.add('body-no-scroll');
  }
  
  function closeMenu() {
    mobileMenu.classList.remove('active');
    document.body.classList.remove('body-no-scroll');
  }
  
  if (menuBtn) {
    menuBtn.addEventListener('click', openMenu);
  }
  
  if (closeBtn) {
    closeBtn.addEventListener('click', closeMenu);
  }
  
  // Close menu when clicking a link
  mobileLinks.forEach(link => {
    link.addEventListener('click', closeMenu);
  });
  
  // Close on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
      closeMenu();
    }
  });
}


/* ===== SCROLL ANIMATIONS ===== */
function initScrollAnimations() {
  const animatedElements = document.querySelectorAll('[data-animate]');
  
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const delay = el.dataset.animateDelay || 0;
          
          setTimeout(() => {
            el.classList.add('slide-up');
          }, delay);
          
          observer.unobserve(el);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(el => {
      observer.observe(el);
    });
  } else {
    // Fallback: show all elements if IntersectionObserver not supported
    animatedElements.forEach(el => {
      el.classList.add('slide-up');
    });
  }
}
