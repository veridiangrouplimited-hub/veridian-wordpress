# Veridian Limited — Website (v2)

> **This is the WordPress-integrated version.** Blog posts and case
> studies are fetched live, client-side, from a WordPress.com backend
> (`script.js`: `wpFetch`, `fetchBlogPosts`, `hydratePost`,
> `fetchCaseStudies`). For the build-time Eleventy version — static
> markdown content, no WordPress dependency, real per-page SEO tags —
> see [veridian](https://github.com/veridiangrouplimited-hub/veridian).
> Both repos otherwise share the same site content and design as of
> 2026-07-02; only the blog/case-study data pipeline differs.

A multi-page, light-themed magazine-style website for an online private practice serving Nigerian SMEs with ethical digital audits, website redesign, SEO and Google Business work.

> Tagline: **Nothing escapes notice.**

---

## What changed from v1

The v1 was a single dark-themed mega-scroll page. v2 is a complete rebuild:

| | v1 | v2 |
|---|---|---|
| **Aesthetic** | Editorial dark | Warm magazine / light |
| **Structure** | One long page | 7 focused pages |
| **Personality** | Minimal | Hand-drawn annotations, photos, stickers |
| **Interactivity** | Audit score animation | Live mini audit tool, theme toggle, animated counters |
| **Visual elements** | Mostly type | Custom SVG icons per industry, photo placeholders, illustrated stickers |
| **Lead capture** | One contact section | Free-snapshot CTAs throughout + dedicated contact page + cookie banner + newsletter |

---

## File structure

```
/
├── index.html          Home (slim, photo-driven, mini-audit teaser)
├── services.html       All 11 services, detailed rows
├── audit.html          Audit method + INTERACTIVE mini-audit tool
├── work.html           4 case studies (before/after scores)
├── pricing.html        6 tiers + pricing FAQ
├── about.html          Founder story, ethics, FAQ
├── contact.html        Form + WhatsApp/email/phone
├── styles.css          Design system (light default, [data-theme="dark"] supported)
└── script.js           All interactions
```

No build tool — drop the folder anywhere it can serve static files. All CSS / JS is shared across every page.

---

## Design system at a glance

**Palette (light theme — default):**
- Background: `#F7F2E7` (bone)
- Surface: `#FDFAF2` (cream) / `#FFFFFF` (cards)
- Ink text: `#1A1B1F`
- Primary accent: `#DE5826` (terracotta)
- Trust accent: `#355C44` (sage)
- Highlight: `#E8B43C` (mustard)
- Case-study accent: `#963A4D` (berry)

**Dark theme:** auto-applies via `[data-theme="dark"]` on `<html>`, toggled by the sun/moon button in the header. Preference is stored in `localStorage`.

**Type stack:**
- **Fraunces** — display / headlines (variable font, opsz axis)
- **Manrope** — UI / body
- **Caveat** — handwritten annotations (used sparingly)
- **JetBrains Mono** — eyebrow labels, numerals

All four are loaded from Google Fonts via a single preconnected stylesheet link.

---

## Key features

### 🎨 Hand-drawn annotation utilities (CSS-only)
Apply these classes to any inline element:

- `.circle-it` — sketchy circle around the text (terracotta)
- `.circle-it--sage` — sage variant
- `.underline-it` — wavy underline (terracotta)
- `.underline-it--mustard` — mustard variant
- `.highlight-it` — marker-style highlight (mustard)
- `.highlight-it--terracotta` — terracotta highlight
- `.hand` — apply handwritten font + colour
- `.handwritten-note` — handwritten-style note block
- `.sparkle` — spinning sparkle decoration

### ✨ Interactive Mini Audit tool
Lives on `index.html` (teaser) and `audit.html` (full version). When a visitor enters a domain it:

1. Validates the input (must look like a domain).
2. Shows a "Auditing…" loading state for 1.5s.
3. Generates a deterministic-but-realistic scorecard (so the same domain always produces the same result).
4. Displays a visibility score (38–68 range) and 4 categorical metrics: SEO, mobile speed, trust, lead capture.
5. Closes with a CTA to request the full audit.

The scoring is illustrative — see `simulateAudit()` in `script.js` to wire it to a real backend (PageSpeed Insights API, Google Places API, etc.).

### 🌗 Light / dark toggle
Light by default. The button in the header toggles `data-theme="dark"` on `<html>` and persists the choice in localStorage. Both themes are fully styled.

### 📊 Animated counters
Any element with `data-count-to="N"` will count up from 0 to N when scrolled into view. Options:

```html
<span data-count-to="48" data-count-suffix="h">0h</span>
<span data-count-to="2.5" data-count-decimals="1" data-count-prefix="$">$0</span>
```

### 🍪 Cookie banner
Slides up 1.5s after page load. Privacy-first wording. Choice persists in localStorage (`veridian-group-cookie` key).

### 💬 Floating WhatsApp
Bottom-right ripple-animated button on every page. URL has a pre-filled message.

### 📧 Newsletter signup
Appears in the footer (mini) and as a standalone block (`.newsletter` class) where used. Currently shows a "Thanks!" state — wire to your provider as below.

### 📱 Mobile navigation
Slides in from the right at <1000px. Hamburger animates to an X. Body scroll locks while open.

### ⬆️ Reveal on scroll
Any element with class `reveal` fades + slides up when it enters the viewport. Staggered delays via `:nth-child`.

---

## Replace before launching

Search-and-replace these placeholders globally:

| Placeholder | Replace with |
|---|---|
| `Veridian Limited` | Your final brand name |
| `veridian-group.com` | Your domain |
| `hello@veridian-group.com` | Your contact email |
| `+234 000 000 0000` | Your phone number |
| `2340000000000` | Your WhatsApp number (no +, no spaces) — appears in `wa.me/` links |
| `https://images.unsplash.com/...` URLs | Your actual photography |

**⚠ The specialist bench on the About page is placeholder.** Four names appear under *"How the work actually happens — The bench"*: `Tunde A.`, `Adaeze N.`, `Halima M.`, `Chinedu O.`. These are placeholders with example credentials. Before launch, replace each with a real specialist from your actual vetted network — their real first name + last initial, real craft, and a one-line credential that's truthful. Look for the `TODO BEFORE LAUNCH` comment in `build_about.py` for the exact block to edit. **Do not ship fabricated specialists — it undermines the entire trust position of the brand.**

---

## Forms — already wired for Netlify

Both forms are already wired up for [Netlify Forms](https://www.netlify.com/products/forms/). No additional work is needed unless you want email notifications or a custom thank-you page (steps below).

**Forms in the site:**

| Form name | Where it lives | Fields captured |
|---|---|---|
| `veridian-group-contact` | `contact.html` (main form) | `name`, `business`, `email`, `phone`, `website`, `service`, `message` |
| `veridian-group-newsletter` | Footer of every page + top of `blog.html` | `email` |

Both forms include a Netlify honeypot (`bot-field`) for spam protection, and submissions go through JS via `fetch()` to `/` (Netlify's form handler endpoint) — so the visitor stays on the page and sees an inline success message rather than a full page reload.

### Step-by-step: deploying with Netlify Forms

**1. Push the site to a Git repo.** GitHub, GitLab, or Bitbucket all work. The site is a flat static site — no build step required.

```bash
cd veridian-group-website
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:veridian-group/website.git
git push -u origin main
```

**2. Connect the repo to Netlify.**
- Sign up at [app.netlify.com](https://app.netlify.com) (free)
- Click **Add new site** → **Import an existing project**
- Choose your Git provider, authorise, and pick the `veridian-group/website` repo
- Build settings:
  - **Branch to deploy:** `main`
  - **Build command:** *leave blank* (no build step)
  - **Publish directory:** `.` (the repo root — already set in `netlify.toml`)
- Click **Deploy site**

Netlify will build and deploy in ~30 seconds. The default URL will be something like `random-name-12345.netlify.app` — you can rename it in **Site configuration → Site information → Change site name**.

**3. Verify Netlify detected both forms.**
- In the Netlify dashboard, go to **Forms** (left sidebar)
- After the first deploy, both forms should appear:
  - `veridian-group-contact`
  - `veridian-group-newsletter`
- If they don't, trigger a redeploy (**Deploys → Trigger deploy → Clear cache and deploy site**) — Netlify scans HTML at build time, so a fresh build picks them up.

**4. Test by submitting a real form.**
- Visit the live site (or your Netlify preview URL)
- Fill in the contact form and submit
- Go to **Forms → veridian-group-contact** in the Netlify dashboard
- Your submission should appear within seconds

**5. Wire up email notifications.**
- **Forms → Settings → Form notifications → Add notification**
- Choose **Email notification**
- Email to notify: `hello@veridian-group.example` (or your work address)
- Form: `veridian-group-contact` (and again for `veridian-group-newsletter`)
- Save. Every submission now also lands in your inbox.

**6. (Optional) Slack notifications.**
- **Forms → Settings → Form notifications → Add notification → Outgoing webhook**
- Slack's [incoming webhooks](https://api.slack.com/messaging/webhooks) URL goes here
- Each submission posts to the channel you chose

**7. (Optional) Custom thank-you page.**
- Create `thanks.html` in the repo root
- In `script.js`, change the `contactForm()` success branch to redirect there:
  ```js
  if (resp.ok) { window.location.href = "/thanks.html"; return; }
  ```

**8. Pricing.** Netlify's free tier includes 100 form submissions/month. For a quiet practice that's plenty. Paid tiers start at $19/month for 1,000.

### How to remove or rename a form

To stop using a form, delete it from the HTML (or remove the `data-netlify="true"` attribute). To change a form's name, update both the `name=""` attribute on the `<form>` tag AND the hidden `<input name="form-name" value="…">` — they must match. Then redeploy.

---

## Wire up the audit tool (optional)

To make the mini-audit tool use real signals instead of simulated ones, replace `simulateAudit()` in `script.js` with a fetch to your backend that calls:

- **Google PageSpeed Insights API** for mobile speed
- **Google Places API** for Google Business Profile health
- **A custom scraper** (server-side) for trust & lead-capture signals

Keep the output shape (score + 4 metrics) so the UI doesn't change.

---

## Analytics

The site is analytics-free out of the box. To add Google Analytics 4, drop this into the `<head>` of every page (or use a tag manager):

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', { 'anonymize_ip': true });
</script>
```

For privacy-first alternatives consider [Plausible](https://plausible.io) or [Fathom](https://usefathom.com).

---

## WordPress headless — already wired

The blog index (`blog.html`) and single-post template (`blog-post.html`) **already fetch live content** from the Veridian Limited WordPress site:

```
https://veridian-grouplimited.wordpress.com
```

The integration is via the [WordPress.com Public REST API](https://developer.wordpress.com/docs/api/) — no plugin install, no CORS config, no authentication needed for reading published posts. WP.com handles all of that.

### How it works at runtime

```
   User opens blog.html
        │
        ▼
   Static HTML loads with 7 fallback cards (built from posts_data.py)
        │
        ▼
   JS init() calls fetchBlogPosts()
        │
        ▼
   GET https://public-api.wordpress.com/wp/v2/sites/veridian-grouplimited.wordpress.com
       /posts?_embed&per_page=20
        │
        ├── Success (typical case)
        │     → fade in fresh cards, render from WP data
        │
        └── Failure / timeout (6s)
              → keep static fallback cards visible
```

The same pattern applies to single posts (`blog-post.html?post=slug`):
1. The post hero renders immediately from the inline manifest (fast first paint)
2. JS fetches the live WP post in parallel
3. If WP returns the post, hydrate the hero AND inject `content.rendered` into `#post-content` (replacing the sample article)
4. If WP fails, fall back to the manifest data — the page still works

### Populating the WordPress blog

Three Python helper scripts ship in a separate zip (`veridian-group-wp-scripts.zip`):

| Script | What it does |
|---|---|
| `veridian-group-wp-clean-posts.py` | Deletes every existing post (cleanup before re-seeding) |
| `veridian-group-wp-posts-create.py` | Creates the 7 default posts that match the site, with categories and featured images |
| `veridian-group-create-post.py` | Interactive single-post creator — title + category → AI generates content → publishes |

All three are configured to talk to `veridian-grouplimited.wordpress.com` with your Bearer token already embedded. Run:

```bash
pip install requests Pillow
python3 veridian-group-wp-clean-posts.py          # optional: start clean
python3 veridian-group-wp-posts-create.py          # populate the 7 defaults
python3 veridian-group-create-post.py              # add more posts ad-hoc
```

### Data shape mapping (WP REST → site)

The mapper in `script.js` (`wpToPost()`) converts WordPress's nested REST response into the flat shape the site uses:

| Site field | WP REST source |
|---|---|
| `slug` | `wpPost.slug` |
| `title` | `wpPost.title.rendered` (HTML entities decoded) |
| `excerpt` | `wpPost.excerpt.rendered` (tags stripped) |
| `content` | `wpPost.content.rendered` (full HTML) |
| `category` | `wpPost._embedded["wp:term"][0][0].name` |
| `date` | `wpPost.date` → formatted as `"12 May 2026"` |
| `read_time` | Computed from word count (220 wpm) |
| `image` | `wpPost._embedded["wp:featuredmedia"][0].source_url` |
| `image_alt` | `wpPost._embedded["wp:featuredmedia"][0].alt_text` |
| `featured` | `wpPost.sticky` (sticky posts become the cover article) |

### Defense in depth: three-layer fallback

The blog content has three independent rendering paths, so visitors always see *something*:

1. **WP live** (primary) — fetched from `veridian-grouplimited.wordpress.com` on each page load
2. **Static manifest** (fallback) — embedded in `blog-post.html` as inline JSON, built from `posts_data.py` at deploy time
3. **Local placeholder images** (image-level fallback) — `images/blog/{slug}.jpg` if a WP featured image fails to load

Any one of the three can fail and the page still renders. To verify the fallback chain works, open the site with the browser's network panel set to "Offline" — the static cards remain visible.

### Featured images — primary + fallback

Each post in `posts_data.py` has two image fields:

```python
"image":           "https://images.unsplash.com/photo-...",   # real, primary
"image_fallback":  "images/blog/{slug}.jpg",                  # local, backup
```

When WP is live, `image` is overwritten at runtime with the real WP featured-image URL. The `data-fallback` attribute keeps pointing at the local placeholder, so a global `error` listener in `script.js` (`imageFallbacks()`) silently swaps in the brand-aligned local file if either the WP image or the Unsplash placeholder fails.

The 7 local placeholders in `images/blog/` are programmatically generated brand-aligned designs (color-rotated through navy/sage/gold/berry, with V-shield watermark and category number). They're self-contained — no external CDN dependency, works offline, renders in airgapped environments.

---

## Deploy to Netlify (5 minutes)

1. Push the folder to a GitHub repo (or use Netlify Drop).
2. On Netlify: **Add new site → Import from Git** (or drag-and-drop with Drop).
3. Build settings: **none required** — this is static HTML/CSS/JS.
4. Publish directory: `/` (root).
5. Set your custom domain in **Site settings → Domain management** and Netlify will issue an SSL certificate automatically.

For Cloudflare Pages or Vercel the process is essentially the same — no build command, root publish directory.

---

## Suggested domains

Pick one that feels right:

- **veridian-group.com** — matches the brand we used
- **auditandgrow.com** — function-led
- **visiblenaija.com** — visibility-led
- **northgatedigital.ng** — slightly more formal
- **leadsmith.ng** — outcome-led
- **digitalauditng.com** — keyword-rich
- **presence.ng** — short, premium

Domain availability changes weekly — check at the Nigerian registrar (NiRA) for `.ng` extensions and any registrar for `.com`.

---

## Browser support

- Chrome / Edge / Safari / Firefox — current and one previous version.
- Backdrop-filter and CSS variables required (universally supported since 2022).
- All animations respect `prefers-reduced-motion`.
- Keyboard navigation supported throughout, with visible focus rings.

---

## Customising further

- **Add a page:** copy any sub-page (e.g. `services.html`), update the `<nav>` `aria-current="page"` attribute, swap the content. The header/footer markup is identical across pages.
- **Tweak the palette:** edit the `:root` variables at the top of `styles.css`. Every accent colour is a single variable.
- **Swap photos:** Unsplash URLs are placeholders — replace `<img src="https://images.unsplash.com/...">` with your own.
- **Adjust audit-tool scoring:** the `simulateAudit()` function in `script.js` controls the score range and metric copy.

---

## Credits

- **Fonts:** Fraunces (Stephen Nixon), Manrope (Mikhail Sharanda), Caveat (Pablo Impallari), JetBrains Mono (JetBrains) — all SIL Open Font Licence.
- **Photos:** Placeholders from Unsplash. Replace with your own before launch.
- **Icons:** Custom inline SVG (no external icon library).

---

*Nothing escapes notice.*
