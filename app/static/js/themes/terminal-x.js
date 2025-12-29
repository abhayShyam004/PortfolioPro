/*
 * Terminal X Theme - JavaScript Interactions
 * 
 * Handles typing effects, command system, and interactive terminal features
 */

(function() {
    'use strict';
    
    // Only run if Terminal X theme is active
    if (!document.body.classList.contains('theme-terminal_x')) {
        console.log('[Terminal X] Theme not active, skipping initialization');
        return;
    }
    
    console.log('[Terminal X] Theme initializing...');
    
    const TerminalX = {
        config: {
            typingSpeed: 30,
            enableScanlines: false,
            enableMatrixRain: false,
            enableTypingCursor: true,
        },
        
        commands: {
            'whoami': { section: 'intro', desc: 'Show introduction' },
            'about': { section: 'about', desc: 'Show about section' },
            'skills': { section: 'skills', desc: 'List skills' },
            'projects': { section: 'projects', desc: 'Show projects' },
            'experience': { section: 'experience', desc: 'Show experience' },
            'education': { section: 'education', desc: 'Show education' },
            'contact': { section: 'contact', desc: 'Contact information' },
            'help': { handler: 'showHelp', desc: 'Show available commands' },
            'clear': { handler: 'clearTerminal', desc: 'Clear terminal' },
        },
        
        /**
         * Initialize Terminal X theme
         */
        init: function() {
            this.addTerminalElements();
            this.initTypingEffects();
            this.initCommandHints();
            this.initKeyboardNav();
            
            if (this.config.enableScanlines) {
                document.body.classList.add('scanlines');
            }
            
            console.log('[Terminal X] Theme initialized successfully');
        },
        
        /**
         * Add terminal-specific elements to the page
         */
        addTerminalElements: function() {
            // Add typing cursor to hero title
            const heroTitle = document.querySelector('.text-huge-title');
            if (heroTitle && this.config.enableTypingCursor) {
                const cursor = document.createElement('span');
                cursor.className = 'terminal-cursor';
                heroTitle.appendChild(cursor);
            }
            
            // Add command prefixes to section titles
            const sectionTitles = document.querySelectorAll('.text-pretitle.with-line');
            sectionTitles.forEach(title => {
                const section = title.closest('section');
                if (section && section.id) {
                    title.setAttribute('data-section', section.id);
                }
            });
        },
        
        /**
         * Initialize typing effects for key elements
         */
        initTypingEffects: function() {
            // Typing effect is now handled via CSS for performance
            // This function reserved for future dynamic typing needs
        },
        
        /**
         * Initialize command hints on navigation links
         */
        initCommandHints: function() {
            const navLinks = document.querySelectorAll('.s-header__nav-list a');
            
            navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (!href) return;
                
                const section = href.replace('#', '').toLowerCase();
                const command = this.getCommandForSection(section);
                
                if (command) {
                    link.setAttribute('data-command', `$ ${command}`);
                }
            });
        },
        
        /**
         * Get command name for a section
         */
        getCommandForSection: function(section) {
            for (const [cmd, data] of Object.entries(this.commands)) {
                if (data.section === section) {
                    return cmd;
                }
            }
            return section; // fallback to section name
        },
        
        /**
         * Initialize keyboard navigation
         */
        initKeyboardNav: function() {
            document.addEventListener('keydown', (e) => {
                // Only handle if not in an input field
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    return;
                }
                
                // Ctrl/Cmd + K to show command palette (future feature)
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    this.showCommandPalette();
                }
                
                // Arrow keys for section navigation
                if (e.key === 'ArrowDown' && e.altKey) {
                    e.preventDefault();
                    this.navigateToNextSection();
                }
                if (e.key === 'ArrowUp' && e.altKey) {
                    e.preventDefault();
                    this.navigateToPrevSection();
                }
            });
        },
        
        /**
         * Execute a command
         */
        executeCommand: function(cmd) {
            const command = this.commands[cmd.toLowerCase()];
            
            if (!command) {
                console.log(`[Terminal X] Unknown command: ${cmd}`);
                return false;
            }
            
            if (command.section) {
                this.scrollToSection(command.section);
            } else if (command.handler && typeof this[command.handler] === 'function') {
                this[command.handler]();
            }
            
            return true;
        },
        
        /**
         * Scroll to a section smoothly
         */
        scrollToSection: function(sectionId) {
            const section = document.getElementById(sectionId);
            if (section) {
                section.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
                console.log(`[Terminal X] Navigating to: ${sectionId}`);
            }
        },
        
        /**
         * Navigate to next section
         */
        navigateToNextSection: function() {
            const sections = document.querySelectorAll('section[id]');
            const currentScroll = window.scrollY + 100;
            
            for (const section of sections) {
                if (section.offsetTop > currentScroll) {
                    this.scrollToSection(section.id);
                    break;
                }
            }
        },
        
        /**
         * Navigate to previous section
         */
        navigateToPrevSection: function() {
            const sections = Array.from(document.querySelectorAll('section[id]')).reverse();
            const currentScroll = window.scrollY - 100;
            
            for (const section of sections) {
                if (section.offsetTop < currentScroll) {
                    this.scrollToSection(section.id);
                    break;
                }
            }
        },
        
        /**
         * Show help information
         */
        showHelp: function() {
            const commands = Object.entries(this.commands)
                .map(([cmd, data]) => `  ${cmd.padEnd(15)} - ${data.desc}`)
                .join('\n');
            
            console.log('[Terminal X] Available commands:\n' + commands);
            
            // Could show a modal or overlay in the future
            alert('Terminal X Commands:\n\n' + commands + '\n\nUse Alt+Up/Down to navigate between sections.');
        },
        
        /**
         * Show command palette (future feature placeholder)
         */
        showCommandPalette: function() {
            console.log('[Terminal X] Command palette (Ctrl+K) - Coming soon!');
            // Future: Show a VS Code-style command palette
        },
        
        /**
         * Clear terminal (scroll to top)
         */
        clearTerminal: function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },
        
        /**
         * Type text effect (utility)
         */
        typeText: function(element, text, speed, callback) {
            let i = 0;
            element.textContent = '';
            
            const type = () => {
                if (i < text.length) {
                    element.textContent += text.charAt(i);
                    i++;
                    setTimeout(type, speed);
                } else if (callback) {
                    callback();
                }
            };
            
            type();
        },
    };
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => TerminalX.init());
    } else {
        TerminalX.init();
    }
    
    // Expose globally for debugging and external use
    window.TerminalX = TerminalX;
    
    // Log available commands
    console.log('[Terminal X] Commands available via TerminalX.executeCommand("command")');
    console.log('[Terminal X] Try: help, whoami, about, skills, projects, contact');
})();
