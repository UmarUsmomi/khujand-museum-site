/**
 * Historical Museum of Sughd Region (Khujand Fortress)
 * Milestone M6: Professional Animation System
 * 
 * Features:
 * - Feature 13: 3D Tilt Cards with Specular Glare (mouse perspective, radial glare, touch guard)
 * - Feature 14: Cinematic Staggered Reveals (GSAP ScrollTrigger batching, 60 FPS compositor)
 * - Feature 15: Micro-Interactions & Parallax (Magnetic buttons, gold shimmer, smooth parallax)
 */

(function () {
  'use strict';

  function initAnimations() {
    // -------------------------------------------------------------------------
    // Accessibility: prefers-reduced-motion check
    // -------------------------------------------------------------------------
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      document.querySelectorAll('.reveal, .reveal-left, .reveal-right').forEach(function (el) {
        el.classList.add('revealed');
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
      return;
    }

    // -------------------------------------------------------------------------
    // Device Capabilities: Pointer and Touch Guarding
    // -------------------------------------------------------------------------
    const hasFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (navigator.msMaxTouchPoints > 0);

    // -------------------------------------------------------------------------
    // Feature 13: 3D Tilt Cards with Specular Glare
    // -------------------------------------------------------------------------
    if (hasFinePointer && !isTouchDevice) {
      const tiltCards = document.querySelectorAll('.exhibit-card, .hero-card, [data-tilt]');
      const MAX_TILT = 12; // Clamped tilt angle <= 15 degrees

      tiltCards.forEach(function (card) {
        // Ensure specular glare overlay element exists
        let glare = card.querySelector('.card-glare');
        if (!glare) {
          glare = document.createElement('div');
          glare.className = 'card-glare';
          card.appendChild(glare);
        }

        card.addEventListener('mousemove', function (e) {
          const rect = card.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          const width = rect.width;
          const height = rect.height;

          // Normalized coordinates (-0.5 to 0.5)
          const normX = (x / width) - 0.5;
          const normY = (y / height) - 0.5;

          // Calculate 3D tilt angles clamped to MAX_TILT <= 15 deg
          const rotateX = Math.max(-MAX_TILT, Math.min(MAX_TILT, -normY * MAX_TILT * 2));
          const rotateY = Math.max(-MAX_TILT, Math.min(MAX_TILT, normX * MAX_TILT * 2));

          card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`;

          // Specular glare position and opacity (clamped <= 0.5)
          const glareX = Math.round((x / width) * 100);
          const glareY = Math.round((y / height) * 100);
          glare.style.background = `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0) 65%)`;
          glare.style.opacity = '1';
        });

        card.addEventListener('mouseleave', function () {
          // Reset transform matrix and glare smoothly on mouseleave
          card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
          if (glare) {
            glare.style.opacity = '0';
          }
        });
      });
    }

    // -------------------------------------------------------------------------
    // Feature 14: Cinematic Staggered Reveals (GSAP ScrollTrigger Batching)
    // -------------------------------------------------------------------------
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);

      // Staggered batch reveals for .reveal elements (stagger: 0.15s within 0.05s-0.3s bound)
      ScrollTrigger.batch('.reveal', {
        interval: 0.1,
        batchMax: 6,
        onEnter: function (batch) {
          gsap.to(batch, {
            opacity: 1,
            y: 0,
            duration: 0.75,
            stagger: 0.15,
            ease: 'power2.out',
            overwrite: true,
            onComplete: function () {
              batch.forEach(function (el) {
                el.classList.add('revealed');
              });
            }
          });
        },
        once: true
      });

      // Directional reveals (.reveal-left, .reveal-right)
      ScrollTrigger.batch('.reveal-left', {
        interval: 0.1,
        onEnter: function (batch) {
          gsap.to(batch, {
            opacity: 1,
            x: 0,
            duration: 0.75,
            stagger: 0.15,
            ease: 'power2.out',
            once: true
          });
        },
        once: true
      });

      ScrollTrigger.batch('.reveal-right', {
        interval: 0.1,
        onEnter: function (batch) {
          gsap.to(batch, {
            opacity: 1,
            x: 0,
            duration: 0.75,
            stagger: 0.15,
            ease: 'power2.out',
            once: true
          });
        },
        once: true
      });
    } else {
      // IntersectionObserver fallback without layout-thrashing scroll listeners
      const revealObserver = new IntersectionObserver(function (entries, observer) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            observer.unobserve(entry.target);
          }
        });
      }, { rootMargin: '0px 0px -40px 0px', threshold: 0.1 });

      document.querySelectorAll('.reveal, .reveal-left, .reveal-right').forEach(function (el) {
        revealObserver.observe(el);
      });
    }

    // -------------------------------------------------------------------------
    // Feature 15: Micro-Interactions (Magnetic Buttons) & Background Parallax
    // -------------------------------------------------------------------------
    // 1. Magnetic button attraction physics on .btn-primary and interactive triggers
    if (hasFinePointer && !isTouchDevice) {
      const magneticButtons = document.querySelectorAll('.btn-primary, .nav-ticket, [data-magnetic]');
      const MAX_MAGNETIC_PULL = 10; // Clamped displacement <= 12px

      magneticButtons.forEach(function (btn) {
        btn.addEventListener('mousemove', function (e) {
          const rect = btn.getBoundingClientRect();
          const centerX = rect.left + rect.width / 2;
          const centerY = rect.top + rect.height / 2;

          const deltaX = e.clientX - centerX;
          const deltaY = e.clientY - centerY;

          // Dampened magnetic pull offset bounded by MAX_MAGNETIC_PULL
          const pullX = Math.max(-MAX_MAGNETIC_PULL, Math.min(MAX_MAGNETIC_PULL, deltaX * 0.22));
          const pullY = Math.max(-MAX_MAGNETIC_PULL, Math.min(MAX_MAGNETIC_PULL, deltaY * 0.22));

          btn.style.transform = `translate(${pullX.toFixed(2)}px, ${pullY.toFixed(2)}px)`;
        });

        btn.addEventListener('mouseleave', function () {
          btn.style.transform = 'translate(0px, 0px)';
        });
      });
    }

    // 2. Smooth background parallax scrolling
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      const parallaxElements = document.querySelectorAll('.hero-pattern, .parallax-bg, [data-parallax]');
      parallaxElements.forEach(function (el) {
        gsap.to(el, {
          yPercent: 15,
          ease: 'none',
          scrollTrigger: {
            trigger: el.parentElement || el,
            start: 'top top',
            end: 'bottom top',
            scrub: true
          }
        });
      });
    } else {
      // Lightweight requestAnimationFrame parallax with passive scroll event listener
      let ticking = false;
      const onParallaxScroll = function () {
        if (!ticking) {
          window.requestAnimationFrame(function () {
            const scrollY = window.pageYOffset || window.scrollY || 0;
            const bgTargets = document.querySelectorAll('.hero-pattern, .parallax-bg');
            bgTargets.forEach(function (bg) {
              bg.style.transform = `translate3d(0, ${(scrollY * 0.12).toFixed(2)}px, 0)`;
            });
            ticking = false;
          });
          ticking = true;
        }
      };
      window.addEventListener('scroll', onParallaxScroll, { passive: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnimations);
  } else {
    initAnimations();
  }
})();
