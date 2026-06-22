# Veridian Group Limited — Project Handoff Notes

Context for picking this project up in Claude Code. Written after an extended
chat session that built and refined the site and WordPress tooling. This file
exists so the reasoning behind non-obvious decisions isn't lost in the move.

---

## What this project is

**Veridian Group Limited** — a digital advisory practice in Abuja, Nigeria.
Founder & CEO: Segun Dairo. Tagline: "Nothing escapes notice."

Two deliverables live here:
1. **The website** (`veridian-site/`) — 9-page static HTML site, hosted on
   Netlify, with a headless WordPress blog bolted on via client-side fetch.
2. **The WordPress scripts** (`veridian-scripts/`) — 5 Python scripts that
   manage blog posts and case studies on the headless WordPress backend.

Sister company, separate brand, not part of this codebase: **Blitzclean Pro**
(cleaning services, also Abuja). Don't conflate the two — different domains,
different brand colors, different WordPress sites.

---

## Architecture — read this before touching anything

**No build step, no framework, no dependencies.** Plain HTML/CSS/JS. Netlify
serves the folder as-is. This was a deliberate choice — fast load on Abuja
mobile connections, nothing to break, no node_modules to manage.

**Shared markup is duplicated across all 9 HTML files** — header, footer,
WhatsApp float button, social links. There is no templating system. This is
the main tradeoff of the no-framework approach: any change to nav, footer,
or contact details has to be applied to every page individually. Several
rounds of this session were exactly that — propagating a single change
across 9–10 files with a Python script doing the find/replace, then
verifying tag balance and re-zipping.

**The blog and case studies are both headless WordPress**, fetched
client-side in `script.js`, with a 3-layer fallback: WordPress live →
static HTML already in the page → local fallback images. If WordPress is
down or the token expires, the site never visibly breaks — it just falls
back to whatever's already in the HTML.

---

## WordPress backend — the part most likely to bite you

**Critical: this is WordPress.com *hosted*, not self-hosted WordPress.org.**

This matters because WordPress.com's REST API (`public-api.wordpress.com`)
is a different beast from the standard WordPress core REST API. Two
consequences that cost real debugging time in this session:

1. **Application Passwords do NOT work.** They're a WordPress core /
   self-hosted feature. WordPress.com's hosted API rejects them with a
   401 regardless of how correctly they're configured. We tried migrating
   to Application Passwords for the "never expires" benefit — it doesn't
   work on this platform, full stop. Don't try this again without first
   confirming WordPress.com has changed this.

2. **OAuth2 Bearer tokens are the only thing that works for writes**, and
   they expire in ~14 days. There is no way to extend this — it's a
   platform-level decision, not a setting. Get a fresh token at:
   ```
   https://public-api.wordpress.com/oauth2/authorize?client_id=140052&redirect_uri=https://localhost&response_type=token
   ```
   Log in as `veridiangrouplimited`, copy the token from the redirect URL
   between `access_token=` and `&token_type=`.

**Credentials live at the top of every script in `veridian-scripts/`:**
```python
WP_SITE      = "255358071"
WP_DOMAIN    = "veridiangrouplimited.wordpress.com"
BEARER_TOKEN = "..."   # ~14-day expiry — regenerate when scripts 401
PEXELS_API_KEY = "..."  # for featured images; falls back to Pillow-generated branded images if it fails or is missing
```
All 5 scripts must have the **same** `BEARER_TOKEN` value. Keep them in
sync manually if you regenerate — there's no shared config file (intentionally
kept simple, but worth turning into a `.env` if this grows further).

**A subtle bug we hit and fixed:** a startup guard checked
`if BEARER_TOKEN == "PASTE_NEW_TOKEN_HERE"` to detect an unset token. When
the real token got substituted in via find-and-replace, it also replaced
the placeholder *inside that comparison string*, making the guard always
true (`if BEARER_TOKEN == "<actual-token>"` — true after replacement,
so it always failed). Fixed by changing the guard to a length check:
`if not BEARER_TOKEN or len(BEARER_TOKEN) < 20`. If you regenerate tokens
via search-and-replace across multiple files again, watch for this pattern.

---

## Content model — blog vs. case studies

Posts are split into two categories, both inside the same WordPress site:

- **`blog`** category — the 7 (now 8) editorial posts, rendered on `blog.html`
- **`case-studies`** category — 4 case study posts, rendered on `work.html`

This was a deliberate choice over a true Custom Post Type, because true CPTs
require either self-hosted WordPress or a WordPress.com **Business plan**
($25/mo) to install plugins. Using categories on the free/basic plan achieves
the same functional separation at no extra cost — the only difference is
semantic, not architectural.

**Both fetches in `script.js` filter by category slug** so blog posts and
case studies never bleed into each other's feed:
- `fetchBlogPosts()` resolves the `blog` category ID, then fetches
  `/posts?categories={id}`
- `fetchCaseStudies()` resolves `case-studies` the same way

**Case study data is structured, not free text.** Each case study post body
contains an HTML comment: `<!--veridian-data:{...JSON...}-->` holding the
industry, location, tagline, narrative, before/after scores, and before/after
metric lists. `parseCaseStudy()` in `script.js` extracts and renders this
into the before/after layout on `work.html`. If you add a new case study,
follow this exact data shape — it's how the front end knows how to render it.

**Scripts and what they do:**
- `veridian-wp-posts-create.py` — creates the `blog` category, assigns it to
  every post alongside its content category (Local SEO, Strategy, etc.),
  creates blog posts. **Idempotent** — checks `post_exists(slug)` before
  creating, so safe to re-run after adding new posts to the `POSTS` list.
- `veridian-wp-case-studies-create.py` — creates the `case-studies` category,
  re-categorises existing posts into `blog`, creates the 4 case studies.
  Also idempotent.
- `veridian-wp-clean-posts.py` — deletes ALL posts. Use with care.
- `veridian-wp-clean-case-studies.py` — deletes only posts in the
  `case-studies` category. Blog posts untouched. Asks for typed `YES`
  confirmation before deleting.
- `veridian-create-post.py` — ad-hoc single-post creator, used outside the
  main seeding flow.

**8th blog post added this session:** "When the World's Smartest AI Got
Switched Off" — about the Claude Fable 5 launch-and-suspension story,
reframed as a vendor-dependency lesson for SMEs. Category: Strategy.
Run `veridian-wp-posts-create.py` to publish it; the idempotency check
means the existing 7 won't be duplicated.

---

## Brand facts (don't re-derive these — they're settled)

- **Colors:** Navy `#142B4D`, Gold `#B89039` (+ tints used per content
  section: sage green `#355C44`, berry `#963A4D`)
- **Founder:** Segun Dairo, **Founder & CEO** (NOT "Principal" — see below)
- **Tagline:** "Nothing escapes notice."
- **Domain:** `veridian.ng` (canonical URLs, sitemap, JSON-LD all point here
  — if the live Netlify domain differs, this needs a global find/replace)
- **Phone/WhatsApp:** +234 813 098 6851
- **Email:** hello@veridian.ng (Zoho Mail)
- **Socials:** Instagram & TikTok `@veridiangrouplimited`, X `@veridian_ng`
- **Payment terms:** 50% on start, 50% on delivery — deliberately kept this
  way; a request to change it to 70/30 was talked through and declined as
  bad positioning for a new practice with no track record yet.
- **Pricing:** Premium/Custom tier shows "Quoted / per scope" rather than a
  number — removed the anchor price to avoid scaring off serious leads
  before a scoping conversation.

### Why "Founder & CEO" and not "Founder & Principal"
Originally titled "Founder & Principal" — Principal being the standard
consulting-industry title for the senior practitioner who personally owns
the work. Changed to CEO because the target audience (Abuja SME owners —
pharmacy owners, school proprietors, etc.) is more likely to read "Principal"
as a school administrator title than a consulting term. CEO is universally
understood and positions Segun as a peer to the business owners being
emailed cold. The "principal-led" language describing the *firm's working
model* (senior person does the work, not delegated to juniors) was kept
throughout the body copy — that's a different thing from the personal title
and still applies.

In headings/body copy describing the working model, "Segun" (by name) is used
rather than a role — e.g. "Segun takes the engagement," then later changed to
**"Your project lead"** on request, to keep focus on the client and avoid
tying the promise to one named individual. Current state: "Your project
lead" is the standard phrase in about.html, audit.html, and index.html
feature callouts. "Segun Dairo" remains as his actual name in the founder
photo caption, alt text, and JSON-LD.

---

## Cold-email campaign infrastructure

Built specifically because the next planned step (after this site work) is
scraping Abuja business contacts and running a cold-email campaign.

**UTM attribution** — `captureCampaignParams()` in `script.js` reads
`utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`,
`industry` from the URL on arrival, persists them in `sessionStorage`, and
injects them as hidden fields into any form on submit via
`attachCampaignFields()`. So a lead from a cold email who fills the contact
form three pages later still carries attribution.

**Industry personalization** — `personalizeForCampaign()` reads `?industry=`
and swaps text on any element tagged `data-campaign-industry`. Currently
wired on the audit page hero only. `INDUSTRY_LABELS` map in `script.js` has
~17 industries pre-mapped (pharmacy, school, law, logistics, etc.) — easy to
extend or wire onto more elements.

**Example campaign link:**
```
https://veridian.ng/audit?utm_source=cold-email&utm_medium=email&utm_campaign=abuja-pharmacies-jun26&industry=pharmacy
```

**Privacy policy** (`privacy.html`) — written specifically because cold
email under Nigeria's NDPA 2023 needs a real, published privacy policy
covering controller identity, lawful basis (legitimate interest for business
outreach), and a clear opt-out. This was treated as a prerequisite, not an
afterthought — don't remove it before a campaign goes out.

---

## Form configuration — Netlify-specific gotchas

Both forms (`veridian-group-contact`, `veridian-group-newsletter`) use
Netlify Forms with `data-netlify="true"` and JS `fetch()` submission
(no page reload). **Important things that aren't obvious from the HTML:**

- **Forms only register with Netlify after a deploy** — Netlify scans HTML
  at build time. If a form doesn't appear in the dashboard, redeploy with
  cache cleared.
- **Email notifications are NOT under "Forms" in the dashboard** — despite
  being the intuitive place to look, they're under **Project configuration
  → Notifications → Emails and webhooks → Form submission notifications**.
  This tripped us up mid-session; the UI moved at some point.
- **First notification email reliably lands in spam** on a brand-new Zoho
  Mail inbox, because `formresponses@netlify.com` is an unrecognized sender.
  Mark not-spam + add to contacts once, and it self-resolves.
- **Subject lines:** contact form subject is set in the Netlify dashboard
  using field interpolation (`New enquiry: {name} — {service}`). Newsletter
  subject is set via a hidden `_subject` HTML field directly in the form
  (`New subscriber — The Quiet Letter`) — the HTML field takes precedence
  over any dashboard setting for that form.
- **Required fields:** contact form requires name, business, email, and
  message (min 20 characters — low bar, filters blank/bot submissions
  without blocking genuine short enquiries). Phone, website, and service
  are intentionally optional — service has a default value so it always
  submits something; phone/website optional reduces friction for first-touch
  cold leads who aren't ready to share more yet.

---

## Things explicitly tried and reverted (don't redo these)

- **Application Passwords for WordPress auth** — doesn't work on
  WordPress.com hosted. See WordPress backend section above.
- **70/30 payment split** — considered, rejected. Stick with 50/50 unless
  there's a strong new reason and the practice has a track record by then.
- **Facebook page** — advised against launching one now. An inactive page
  hurts more than having none. Revisit only if paid Meta/Instagram ads
  become a priority — that needs a Business Manager account, not a public
  page with followers.
- **CPT (Custom Post Type) for case studies** — would require a WordPress.com
  Business plan upgrade ($25/mo). Categories achieve the same separation for
  free. Revisit only if the practice scales enough to justify the upgrade
  for other reasons too.

## Verantis — a dead brand name, already purged

The company was previously going to be named "Verantis" before settling on
Veridian. Old logo files (`verantis-full.png/svg`, `verantis-mark.png/svg`)
were found and deleted from `assets/logo/`. A full-codebase grep confirmed
zero remaining references. If a `verantis` reference resurfaces anywhere
(old backups, cached files, etc.), it's a leftover from before the rename —
remove it.

---

## Known gaps / next steps not yet done

- **Real bench specialist names** — `about.html` still needs real names to
  replace any remaining placeholder content if it exists; verify before
  launch.
- **Real case study client names/photos** — the 4 case studies currently use
  fictional/anonymized businesses with Pexels stock photography. Replace
  with real, permissioned client stories as they become available — this
  was flagged repeatedly as the single highest-leverage trust improvement
  for cold-email conversion, more impactful than any code change.
- **Analytics** — deliberately not wired in yet (no snippet hardcoded)
  since no account existed. Recommended: Plausible or Fathom (cookieless,
  NDPA-friendly) over GA4, given the site already declines non-essential
  cookies by default.
- **RC number** — footer shows placeholder `RC 0000000`. Replace with the
  real CAC registration number once available.
- **Domain confirmation** — all canonical URLs, sitemap, and JSON-LD assume
  `veridian.ng`. Confirm this matches the live Netlify domain before launch,
  or do a global find/replace if it differs.
- **Logo format** — only PNG logos exist (`veridian-group-horizontal.png`,
  `veridian-group-full.png`). No SVG master exists. Fine for web use at
  current resolution; would need a vector trace for print/signage.

---

## File locations

```
veridian-site/          → the website (deploy this to Netlify)
  index.html, about.html, services.html, work.html, pricing.html,
  blog.html, blog-post.html, contact.html, audit.html, privacy.html
  styles.css, script.js
  robots.txt, sitemap.xml, netlify.toml
  assets/, images/

veridian-scripts/        → WordPress management (run locally, not deployed)
  veridian-wp-posts-create.py
  veridian-wp-case-studies-create.py
  veridian-wp-clean-posts.py
  veridian-wp-clean-case-studies.py
  veridian-create-post.py
```

Run order for a fresh WordPress seed:
```bash
pip install requests Pillow
python3 veridian-wp-clean-posts.py          # optional, if starting clean
python3 veridian-wp-posts-create.py         # 8 blog posts, idempotent
python3 veridian-wp-case-studies-create.py  # categories + 4 case studies
```
