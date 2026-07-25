/* Nordlicht KI – One-Pager Interaktionen
   Vanilla JS, keine Abhängigkeiten. */
(function () {
  'use strict';

  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fmtNumber = new Intl.NumberFormat('de-DE');
  var fmtEuro = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 });

  /* ---------- Sticky Nav: Glas-Effekt beim Scrollen ---------- */
  var nav = document.getElementById('siteNav');
  function onScroll() {
    nav.classList.toggle('is-scrolled', window.scrollY > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Burger-Menü ---------- */
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');

  function setMenu(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Menü schließen' : 'Menü öffnen');
    links.classList.toggle('is-open', open);
  }

  toggle.addEventListener('click', function () {
    setMenu(toggle.getAttribute('aria-expanded') !== 'true');
  });

  links.addEventListener('click', function (e) {
    if (e.target.closest('a')) setMenu(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      toggle.focus();
    }
  });

  document.addEventListener('click', function (e) {
    if (toggle.getAttribute('aria-expanded') === 'true' &&
        !links.contains(e.target) && !toggle.contains(e.target)) {
      setMenu(false);
    }
  });

  /* ---------- Aktiven Nav-Link markieren ---------- */
  var sectionIds = ['start', 'ki-mitarbeiter', 'roi', 'demo', 'ablauf', 'branchen', 'faq', 'kontakt'];
  var navAnchors = Array.prototype.slice.call(links.querySelectorAll('a:not(.btn)'));

  function markActive(id) {
    navAnchors.forEach(function (a) {
      var match = a.getAttribute('href') === '#' + id;
      a.classList.toggle('is-active', match);
      if (match) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  }

  if ('IntersectionObserver' in window) {
    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) markActive(entry.target.id);
      });
    }, { rootMargin: '-40% 0px -55% 0px' });

    sectionIds.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) navObserver.observe(el);
    });
  }

  /* ---------- Reveal-Animationen beim Scrollen ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window) || prefersReducedMotion) {
    document.documentElement.classList.add('no-observer');
  } else {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { revealObserver.observe(el); });
  }

  /* ---------- Zahlen-Animation (Kennzahlen) ---------- */
  function animateCount(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    if (prefersReducedMotion || isNaN(target)) {
      el.textContent = fmtNumber.format(target || 0);
      return;
    }
    var start = null;
    var duration = 1200;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = fmtNumber.format(Math.round(target * eased));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  var counters = document.querySelectorAll('.count');
  if ('IntersectionObserver' in window && counters.length) {
    var countObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          countObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { countObserver.observe(el); });
  } else {
    counters.forEach(function (el) {
      el.textContent = el.getAttribute('data-count');
    });
  }

  /* ---------- ROI-Kalkulator ---------- */
  var roi = {
    inquiries: document.getElementById('roiInquiries'),
    missed: document.getElementById('roiMissed'),
    value: document.getElementById('roiValue'),
    close: document.getElementById('roiClose'),
    minutes: document.getElementById('roiMinutes'),
    rate: document.getElementById('roiRate')
  };
  var roiOut = {
    inquiries: document.getElementById('roiInquiriesOut'),
    missed: document.getElementById('roiMissedOut'),
    close: document.getElementById('roiCloseOut'),
    minutes: document.getElementById('roiMinutesOut')
  };
  var res = {
    missed: document.getElementById('resMissed'),
    revenue: document.getElementById('resRevenue'),
    time: document.getElementById('resTime'),
    total: document.getElementById('resTotal')
  };

  function paintRangeFill(input) {
    var min = parseFloat(input.min) || 0;
    var max = parseFloat(input.max) || 100;
    var pct = ((parseFloat(input.value) - min) / (max - min)) * 100;
    input.style.setProperty('--fill', pct + '%');
  }

  function setResult(el, text) {
    if (el.textContent === text) return;
    el.textContent = text;
    if (!prefersReducedMotion) {
      el.classList.add('is-updating');
      window.setTimeout(function () { el.classList.remove('is-updating'); }, 220);
    }
  }

  function num(input) {
    var v = parseFloat(input.value);
    return isNaN(v) || v < 0 ? 0 : v;
  }

  function calcRoi() {
    var inquiries = num(roi.inquiries);
    var missedPct = num(roi.missed) / 100;
    var orderValue = num(roi.value);
    var closePct = num(roi.close) / 100;
    var minutes = num(roi.minutes);
    var rate = num(roi.rate);

    var missedInquiries = inquiries * missedPct;
    var winnableCustomers = missedInquiries * closePct;
    var revenuePotential = winnableCustomers * orderValue;
    var manualHours = (inquiries * minutes) / 60;
    var timeCost = manualHours * rate;
    var totalLeverage = revenuePotential + timeCost;

    roiOut.inquiries.textContent = fmtNumber.format(inquiries);
    roiOut.missed.textContent = fmtNumber.format(num(roi.missed)) + ' %';
    roiOut.close.textContent = fmtNumber.format(num(roi.close)) + ' %';
    roiOut.minutes.textContent = fmtNumber.format(minutes) + ' Min.';

    setResult(res.missed, fmtNumber.format(Math.round(missedInquiries)));
    setResult(res.revenue, fmtEuro.format(Math.round(revenuePotential)) + ' €');
    setResult(res.time, fmtEuro.format(Math.round(timeCost)) + ' €');
    setResult(res.total, fmtEuro.format(Math.round(totalLeverage)) + ' €');
  }

  Object.keys(roi).forEach(function (key) {
    var input = roi[key];
    if (!input) return;
    input.addEventListener('input', function () {
      if (input.type === 'range') paintRangeFill(input);
      calcRoi();
    });
    if (input.type === 'range') paintRangeFill(input);
  });
  calcRoi();

  document.getElementById('roiForm').addEventListener('submit', function (e) {
    e.preventDefault();
  });

  /* ---------- Chat-Demo ---------- */
  var chatBody = document.getElementById('chatBody');
  var chatReplay = document.getElementById('chatReplay');
  var chatScript = [
    { who: 'user', text: 'Hallo, ich interessiere mich für eure Leistung. Was kostet das ungefähr?' },
    { who: 'ai', text: 'Gerne. Damit ich dir sinnvoll helfen kann: Geht es um eine allgemeine Anfrage, einen konkreten Termin oder möchtest du erst wissen, ob die Lösung zu deinem Unternehmen passt?' },
    { who: 'user', text: 'Ich möchte wissen, ob sich ein KI-Mitarbeiter für mein Unternehmen lohnt.' },
    { who: 'ai', text: 'Perfekt. Dann schauen wir zuerst auf deine monatlichen Anfragen, deine Antwortzeiten und den durchschnittlichen Kundenwert. Daraus lässt sich schnell erkennen, ob ein KI-Mitarbeiter wirtschaftlich sinnvoll sein könnte.' },
    { who: 'ai', text: 'Möchtest du direkt eine kurze Potenzialanalyse anfragen?' }
  ];
  var chatTimers = [];
  var chatStarted = false;

  function clearChat() {
    chatTimers.forEach(window.clearTimeout);
    chatTimers = [];
    chatBody.querySelectorAll('.chat-msg, .chat-typing').forEach(function (n) { n.remove(); });
  }

  function addMessage(msg) {
    var div = document.createElement('div');
    div.className = 'chat-msg ' + (msg.who === 'user' ? 'msg-user' : 'msg-ai');
    div.textContent = msg.text;
    chatBody.appendChild(div);
  }

  function showTyping() {
    var t = document.createElement('div');
    t.className = 'chat-typing';
    t.setAttribute('aria-hidden', 'true');
    t.innerHTML = '<span></span><span></span><span></span>';
    chatBody.appendChild(t);
    return t;
  }

  function playChat() {
    clearChat();
    if (prefersReducedMotion) {
      chatScript.forEach(addMessage);
      return;
    }
    var delay = 300;
    chatScript.forEach(function (msg) {
      if (msg.who === 'ai') {
        var typingDelay = delay;
        chatTimers.push(window.setTimeout(function () {
          var t = showTyping();
          chatTimers.push(window.setTimeout(function () {
            t.remove();
            addMessage(msg);
          }, 900));
        }, typingDelay));
        delay += 900 + 700;
      } else {
        chatTimers.push(window.setTimeout(function () { addMessage(msg); }, delay));
        delay += 800;
      }
    });
  }

  if ('IntersectionObserver' in window && !prefersReducedMotion) {
    var chatObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting && !chatStarted) {
          chatStarted = true;
          playChat();
          chatObserver.disconnect();
        }
      });
    }, { threshold: 0.35 });
    chatObserver.observe(document.getElementById('chatDemo'));
  } else {
    chatScript.forEach(addMessage);
  }

  chatReplay.addEventListener('click', playChat);

  /* ---------- FAQ Accordion ---------- */
  document.querySelectorAll('.acc-trigger').forEach(function (trigger) {
    trigger.addEventListener('click', function () {
      var item = trigger.closest('.acc-item');
      var open = trigger.getAttribute('aria-expanded') === 'true';
      trigger.setAttribute('aria-expanded', String(!open));
      item.classList.toggle('is-open', !open);
    });
  });

  /* ---------- Kontaktformular ---------- */
  var form = document.getElementById('contactForm');
  var successMsg = document.getElementById('formSuccess');

  function setFieldError(input, errorEl, show) {
    input.classList.toggle('is-invalid', show);
    input.setAttribute('aria-invalid', String(show));
    if (errorEl) errorEl.hidden = !show;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var name = document.getElementById('cfName');
    var email = document.getElementById('cfEmail');
    var consent = document.getElementById('cfConsent');
    var valid = true;

    var nameOk = name.value.trim().length > 1;
    setFieldError(name, document.getElementById('cfNameError'), !nameOk);
    if (!nameOk) valid = false;

    var emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim());
    setFieldError(email, document.getElementById('cfEmailError'), !emailOk);
    if (!emailOk) valid = false;

    var consentOk = consent.checked;
    setFieldError(consent, document.getElementById('cfConsentError'), !consentOk);
    if (!consentOk) valid = false;

    if (!valid) {
      var firstInvalid = form.querySelector('.is-invalid');
      if (firstInvalid) firstInvalid.focus();
      return;
    }

    /* Platzhalter: Hier Formular-Backend anbinden
       (z. B. eigenes API-Endpoint, Formspree, Netlify Forms o. Ä.). */
    successMsg.hidden = false;
    form.querySelector('button[type="submit"]').disabled = true;
    successMsg.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'nearest' });
  });

  ['cfName', 'cfEmail'].forEach(function (id) {
    var input = document.getElementById(id);
    input.addEventListener('input', function () {
      setFieldError(input, document.getElementById(id + 'Error'), false);
    });
  });
  document.getElementById('cfConsent').addEventListener('change', function () {
    setFieldError(this, document.getElementById('cfConsentError'), false);
  });

  /* ---------- Footer-Jahr ---------- */
  document.getElementById('year').textContent = String(new Date().getFullYear());
})();
