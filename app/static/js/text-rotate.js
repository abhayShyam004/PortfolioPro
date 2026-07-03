/**
 * TextRotate - Vanilla JavaScript implementation of 21st.dev TextRotate component.
 * Features zero-jitter hardware compositor transitions and synchronized box-width scaling.
 */
class TextRotate {
    constructor(element, options = {}) {
        this.element = element;
        this.texts = options.texts || JSON.parse(element.getAttribute('data-texts') || '[]');
        this.rotationInterval = options.rotationInterval || parseInt(element.getAttribute('data-interval') || '2000', 10);
        this.staggerDuration = options.staggerDuration || parseFloat(element.getAttribute('data-stagger-duration') || '25'); // ms per char
        this.staggerFrom = options.staggerFrom || element.getAttribute('data-stagger-from') || 'last'; // 'first', 'last', 'center', 'random'
        this.splitBy = options.splitBy || element.getAttribute('data-split-by') || 'characters'; // 'characters', 'words'
        this.loop = options.loop !== undefined ? options.loop : (element.getAttribute('data-loop') !== 'false');
        this.auto = options.auto !== undefined ? options.auto : (element.getAttribute('data-auto') !== 'false');
        
        this.currentIndex = 0;
        this.timer = null;
        this.isAnimating = false;

        if (this.texts.length > 0) {
            this.init();
        }
    }

    init() {
        this.element.classList.add('text-rotate-wrapper');
        this.renderText(this.currentIndex, false);
        
        // Interactive click: clicking jumps to next text immediately
        this.element.addEventListener('click', () => {
            this.next();
            if (this.auto) {
                this.start(); // reset interval
            }
        });

        // Resize listener to adjust width when crossing mobile breakpoint
        window.addEventListener('resize', () => {
            if (!this.isAnimating) {
                this.element.style.width = 'auto';
                const newWidth = this.element.getBoundingClientRect().width;
                this.element.style.width = newWidth + 'px';
            }
        });

        if (this.auto) {
            this.start();
        }
    }

    splitIntoCharacters(text) {
        if (typeof Intl !== 'undefined' && 'Segmenter' in Intl) {
            const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
            return Array.from(segmenter.segment(text), ({ segment }) => segment);
        }
        return Array.from(text);
    }

    getStaggerDelay(index, totalChars) {
        if (this.staggerFrom === 'first') return index * this.staggerDuration;
        if (this.staggerFrom === 'last') return (totalChars - 1 - index) * this.staggerDuration;
        if (this.staggerFrom === 'center') {
            const center = Math.floor(totalChars / 2);
            return Math.abs(center - index) * this.staggerDuration;
        }
        if (this.staggerFrom === 'random') {
            return Math.floor(Math.random() * totalChars) * this.staggerDuration;
        }
        return index * this.staggerDuration;
    }

    renderText(index, animate = true) {
        const text = this.texts[index];
        const oldWordEl = this.element.querySelector('.text-rotate-word');
        
        let charArray = [];
        if (this.splitBy === 'words') {
            charArray = text.split(' ').map((w, i, arr) => w + (i < arr.length - 1 ? ' ' : ''));
        } else {
            charArray = this.splitIntoCharacters(text);
        }

        const totalChars = charArray.length;

        // Helper to construct DOM structure
        const buildWordEl = (chars, isEntering = false) => {
            const wordEl = document.createElement('span');
            wordEl.className = 'text-rotate-word';
            const isPortfolioPro = text.toLowerCase().includes('portfoliopro');
            chars.forEach((char, idx) => {
                const charEl = document.createElement('span');
                charEl.className = 'text-rotate-char' + (isEntering ? ' enter-start' : '');
                if (isPortfolioPro && (char === '✽' || char === '*' || (char === ' ' && (chars[idx + 1] === '✽' || chars[idx + 1] === '*')))) {
                    charEl.classList.add('mobile-hide');
                }
                charEl.textContent = char;
                if (isEntering) {
                    charEl.style.transitionDelay = this.getStaggerDelay(idx, totalChars) + 'ms';
                }
                wordEl.appendChild(charEl);
            });
            return wordEl;
        };

        if (!animate || !oldWordEl) {
            this.element.innerHTML = '';
            const wordEl = buildWordEl(charArray, false);
            this.element.appendChild(wordEl);
            return;
        }

        this.isAnimating = true;

        // 1. Lock current width while old characters exit
        const oldWidth = this.element.getBoundingClientRect().width;
        if (oldWidth > 0) {
            this.element.style.width = oldWidth + 'px';
        }

        // 2. Animate out old characters using hardware CSS transition-delay
        const oldChars = oldWordEl.querySelectorAll('.text-rotate-char');
        const oldTotal = oldChars.length;
        let maxOutDelay = 0;

        oldChars.forEach((charEl, idx) => {
            const delay = this.getStaggerDelay(idx, oldTotal);
            if (delay > maxOutDelay) maxOutDelay = delay;
            charEl.style.transitionDelay = delay + 'ms';
            charEl.classList.add('exit-end');
        });

        // 3. Once old characters finish exiting, swap DOM and animate new characters + box width in lockstep!
        setTimeout(() => {
            if (oldWordEl.parentNode === this.element) {
                this.element.removeChild(oldWordEl);
            }

            // Create temporary word element WITHOUT enter-start to measure exact natural width
            const measureWordEl = buildWordEl(charArray, false);
            this.element.style.width = 'auto';
            this.element.appendChild(measureWordEl);
            const targetWidth = this.element.getBoundingClientRect().width;
            this.element.removeChild(measureWordEl);

            // Set box back to oldWidth instantly so there is no layout flash
            this.element.style.width = oldWidth + 'px';
            this.element.offsetHeight; // force DOM reflow

            // Append actual entering word with enter-start class
            const wordEl = buildWordEl(charArray, true);
            this.element.appendChild(wordEl);

            // In the next frame, start width transition and letter animations simultaneously!
            requestAnimationFrame(() => {
                this.element.style.width = targetWidth + 'px';
                const enteringChars = wordEl.querySelectorAll('.text-rotate-char');
                enteringChars.forEach(charEl => {
                    charEl.classList.remove('enter-start');
                });
            });

            // Clean up animation flag after transition settles
            let maxInDelay = 0;
            charArray.forEach((_, idx) => {
                const d = this.getStaggerDelay(idx, totalChars);
                if (d > maxInDelay) maxInDelay = d;
            });

            setTimeout(() => {
                this.isAnimating = false;
                if (!this.loop && this.currentIndex === this.texts.length - 1) {
                    this.stop();
                    this.element.dispatchEvent(new CustomEvent('textRotateComplete', { detail: { index: this.currentIndex } }));
                }
            }, maxInDelay + 460);

        }, maxOutDelay + 250);
    }

    next() {
        if (this.isAnimating) return;
        const nextIdx = this.currentIndex === this.texts.length - 1
            ? (this.loop ? 0 : this.currentIndex)
            : this.currentIndex + 1;
            
        if (nextIdx !== this.currentIndex) {
            this.currentIndex = nextIdx;
            this.renderText(this.currentIndex, true);
        }
    }

    previous() {
        if (this.isAnimating) return;
        const prevIdx = this.currentIndex === 0
            ? (this.loop ? this.texts.length - 1 : this.currentIndex)
            : this.currentIndex - 1;
            
        if (prevIdx !== this.currentIndex) {
            this.currentIndex = prevIdx;
            this.renderText(this.currentIndex, true);
        }
    }

    jumpTo(index) {
        if (this.isAnimating || index === this.currentIndex) return;
        this.currentIndex = Math.max(0, Math.min(index, this.texts.length - 1));
        this.renderText(this.currentIndex, true);
    }

    start() {
        this.stop();
        this.timer = setInterval(() => this.next(), this.rotationInterval);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
}

// Expose globally for API / programmatic control
window.TextRotate = TextRotate;

// Auto-initialize all elements marked with data-text-rotate on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-text-rotate]').forEach((el) => {
        if (!el._textRotateInstance) {
            el._textRotateInstance = new TextRotate(el);
        }
    });
});
