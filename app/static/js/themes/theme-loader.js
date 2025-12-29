/*
 * Theme Loader - Handles dynamic theme switching
 */

(function() {
    'use strict';
    
    const ThemeLoader = {
        currentTheme: 'classic',
        
        /**
         * Initialize theme system
         */
        init: function() {
            // Get theme from body data attribute
            const body = document.body;
            this.currentTheme = body.dataset.theme || 'classic';
            
            // Add theme class to body
            this.applyThemeClass(this.currentTheme);
            
            // Mark as loaded
            document.documentElement.classList.add('theme-loaded');
            document.documentElement.classList.remove('theme-loading');
            
            console.log('[ThemeLoader] Initialized with theme:', this.currentTheme);
        },
        
        /**
         * Apply theme class to body
         */
        applyThemeClass: function(themeName) {
            const body = document.body;
            
            // Remove existing theme classes
            body.classList.forEach(cls => {
                if (cls.startsWith('theme-')) {
                    body.classList.remove(cls);
                }
            });
            
            // Add new theme class
            body.classList.add('theme-' + themeName);
        },
        
        /**
         * Switch to a different theme (for preview)
         */
        switchTheme: function(themeName) {
            if (themeName === this.currentTheme) return;
            
            // Add loading state
            document.documentElement.classList.add('theme-loading');
            
            // Apply new theme
            setTimeout(() => {
                this.currentTheme = themeName;
                this.applyThemeClass(themeName);
                
                // Dispatch event for theme-specific JS
                window.dispatchEvent(new CustomEvent('themeChanged', {
                    detail: { theme: themeName }
                }));
                
                // Remove loading state
                document.documentElement.classList.remove('theme-loading');
            }, 100);
        },
        
        /**
         * Get current theme
         */
        getTheme: function() {
            return this.currentTheme;
        }
    };
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ThemeLoader.init());
    } else {
        ThemeLoader.init();
    }
    
    // Expose globally
    window.ThemeLoader = ThemeLoader;
})();
