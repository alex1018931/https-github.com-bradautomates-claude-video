# Nordlicht KI – Premium-Onepager für eine KI-Agentur

Moderne, helle, conversion-optimierte Onepager-Website für eine Digital- und KI-Agentur,
die **KI-Mitarbeiter** (KI-Rezeptionistin, KI-Sales, KI-Kundenberater, KI-Telefonassistent,
Website-Chat, Follow-up-Automation u. a.) für Unternehmen anbietet.

**Tech:** Reines HTML, CSS und Vanilla-JavaScript – keine Frameworks, keine Build-Tools,
keine externen Abhängigkeiten. Sofort deploybar auf GitHub Pages, Netlify, Vercel oder
jedem Webspace.

## Struktur

```
index.html        – komplette Seite (18 Sektionen, semantisch, eine H1)
css/fonts.css     – lokal gehostete Fonts (Sora + Inter, DSGVO-freundlich, kein Google-CDN)
css/styles.css    – Design-System (Tokens oben in :root) + alle Komponenten
js/main.js        – Navigation, Reveal-Animationen, ROI-Kalkulator, Chat-Demo,
                    FAQ-Accordion, Formular-Validierung
fonts/            – Sora & Inter als variable WOFF2 (latin + latin-ext)
```

## Features

- Transparente Sticky-Navigation mit Glas-Effekt beim Scrollen, barrierefreies Burger-Menü
- Heller Hero mit animierter „KI-Kommunikationszentrale“ (pures CSS-Dashboard) und Floating Cards
- Interaktiver **ROI-Kalkulator** mit Live-Berechnung und deutscher Zahlenformatierung
- Chat-**Live-Demo** mit Tipp-Animation (startet beim Scrollen in den Viewport, Replay-Button)
- Vergleich „Ohne KI vs. mit KI-Mitarbeiter“, 7-Schritte-Timeline, 8 Branchen-Cards
- Sicherheits-/DSGVO-Sektion, Beispielstimmen, barrierefreies FAQ-Accordion (inkl. FAQ-Schema für SEO)
- Kontaktformular mit sichtbaren Labels, Client-Validierung und verständlichen Fehlermeldungen
- Barrierefreiheit: Fokus-Zustände, Tastaturbedienung, `prefers-reduced-motion`, Skip-Link, ARIA
- Responsive bis 360 px, kein horizontales Scrollen, Core-Web-Vitals-freundlich

## Anpassen (Platzhalter)

| Was | Wo |
| --- | --- |
| Agenturname „Nordlicht KI“ | `index.html` (Suchen & Ersetzen), Logo-SVG im Header/Footer |
| Telefon / E-Mail / Adresse | Kontakt-Sektion + Footer (als „Platzhalter“ markiert) |
| Kennzahlen | Sektion `#kennzahlen` (`data-count`-Attribute) |
| Teamfoto | Sektion `#ueber-uns` (`.about-placeholder` durch `<img>` ersetzen) |
| Testimonials | Sektion `#stimmen` (als Beispielstimmen gekennzeichnet) |
| Formular-Backend | `js/main.js`, Kommentar „Hier Formular-Backend anbinden“ |
| Farben / Radien / Schatten | `css/styles.css`, `:root`-Tokens ganz oben |
| Impressum / Datenschutz | Footer-Links auf echte Unterseiten zeigen lassen |

## Lokal ansehen

```bash
python3 -m http.server 8000
# → http://localhost:8000
```
