#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
VERIDIAN — WordPress Bulk Post Creator
Featured images: real photography via Pexels, with branded
Pillow-generated fallback if Pexels is unavailable.
═══════════════════════════════════════════════════════════════════

CREATES THE 7 POSTS THAT APPEAR ON THE VERIDIAN WEBSITE:
  No. 01 · Your Google Business Profile is doing more for your business…
  No. 02 · 5 things to fix on your site before spending one naira on ads.
  No. 03 · How to read your own digital audit (without an MBA).
  No. 04 · Why your site is slow in Lagos — and how to fix it.
  No. 05 · Reviews aren't just stars: a guide to responding like a pro.
  No. 06 · Credibility on a startup budget: 10 cheap moves that work.
  No. 07 · NAP consistency: the boring SEO fix that pays off most.

CATEGORIES CREATED:
  Local SEO · Strategy · Audit Method · Performance · Reputation

REQUIREMENTS:
    pip install requests Pillow

SETUP — 2 things to configure:
─────────────────────────────────────────────────────────────────
  1. PEXELS API KEY (free, takes 2 minutes)
     → https://www.pexels.com/api/ → "Get Started" → sign up
     → Paste it into PEXELS_API_KEY below
     → (If left blank, posts will use the Pillow-generated fallback)

  2. BEARER TOKEN — already configured ✓

  Then run:  python veridian-wp-posts-create.py
─────────────────────────────────────────────────────────────────
"""

import requests, json, io, time, sys, os

# ── CONFIGURATION ─────────────────────────────────────────────────
WP_SITE      = "255358071"
WP_DOMAIN    = "veridiangrouplimited.wordpress.com"
# ── Bearer token (expires ~14 days — regenerate at the URL below)
# https://public-api.wordpress.com/oauth2/authorize?client_id=140052&redirect_uri=https://localhost&response_type=token
BEARER_TOKEN = "7nr(4rp5B$tNvdipxUAhO2y82ppDy(kl(7N#M$ApU)a@PqFY7ETE3eLlr4Jh2wij"
PEXELS_API_KEY = "tEYbi4lcIbtRPR52F93GhfEBwkbNRoulE5ZwajutUEOuhFhS3MaoAlv6"
# ──────────────────────────────────────────────────────────────────

API_BASE    = f"https://public-api.wordpress.com/wp/v2/sites/{WP_SITE}"
PEXELS_BASE = "https://api.pexels.com/v1"


def wp_headers(content_type="application/json"):
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type":  content_type,
        "Accept":        "application/json",
    }


def pexels_headers():
    return {"Authorization": PEXELS_API_KEY}


# ── CONNECTION TEST ───────────────────────────────────────────────
def test_connection():
    print("Testing connections...\n")

    print("  WordPress.com API...")
    try:
        r = requests.get(f"{API_BASE}/users/me", headers=wp_headers(), timeout=15)
        if r.status_code == 200:
            name = r.json().get("name", "")
            print(f"  ✓ WordPress: authenticated as '{name}'")
        else:
            print(f"  ✗ WordPress: {r.status_code} — {r.text[:120]}")
            if r.status_code in (401, 403):
                show_token_help()
            return False
    except Exception as e:
        print(f"  ✗ WordPress: {e}")
        return False

    print("  Pexels API...")
    if not PEXELS_API_KEY or len(PEXELS_API_KEY) < 20:
        print("  ⚠ Pexels: key not set — posts will use Pillow fallback images")
        return True

    try:
        r2 = requests.get(
            f"{PEXELS_BASE}/search",
            params={"query": "business", "per_page": 1},
            headers=pexels_headers(),
            timeout=15,
        )
        if r2.status_code == 200:
            total = r2.json().get("total_results", 0)
            print(f"  ✓ Pexels: connected ({total:,} photos available)")
        else:
            print(f"  ⚠ Pexels: {r2.status_code} — using fallback images")
    except Exception as e:
        print(f"  ⚠ Pexels: {e} — using fallback images")

    print()
    return True


def show_token_help():
    print("\n  -- HOW TO GET A NEW TOKEN -----------------------------")
    print("  1. Open this URL in your browser:")
    print("     https://public-api.wordpress.com/oauth2/authorize")
    print("     ?client_id=140052&redirect_uri=https://localhost&response_type=token")
    print("  2. Log in as veridiangrouplimited")
    print("  3. Copy token from the redirect URL between access_token= and &token_type=")
    print("  4. Paste into BEARER_TOKEN at the top of this script")
    print("  Token is valid for ~14 days.")
    print("  -------------------------------------------------------\n")

def fetch_pexels_image(query, fallback_query="nigerian small business laptop"):
    """Search Pexels for a landscape photo. Returns (bytes, mime) or (None, None)."""
    if not PEXELS_API_KEY or len(PEXELS_API_KEY) < 20:
        return None, None

    for attempt in [query, fallback_query, "business technology laptop africa"]:
        try:
            r = requests.get(
                f"{PEXELS_BASE}/search",
                params={
                    "query":       attempt,
                    "per_page":    5,
                    "orientation": "landscape",
                    "size":        "large",
                },
                headers=pexels_headers(),
                timeout=15,
            )
            if r.status_code != 200:
                continue

            photos = r.json().get("photos", [])
            if not photos:
                continue

            # Prefer landscape (≥ 1.5 aspect ratio)
            photo = photos[0]
            for p in photos:
                if p.get("width", 0) / max(p.get("height", 1), 1) >= 1.5:
                    photo = p
                    break

            img_url = (photo.get("src", {}).get("large2x")
                       or photo.get("src", {}).get("large")
                       or photo.get("src", {}).get("original"))
            if not img_url:
                continue

            img_r = requests.get(img_url, timeout=30)
            if img_r.status_code == 200:
                photographer = photo.get("photographer", "Pexels")
                print(f"    ✓ Photo: '{attempt}' by {photographer} (Pexels)")
                return img_r.content, "image/jpeg"

        except Exception as e:
            print(f"    ⚠ Pexels search error: {e}")
            continue

    return None, None


# ── PILLOW FALLBACK IMAGE — branded for Veridian ──────────────────
def generate_fallback_image(category, color1, color2, issue_num):
    """
    Generate a brand-aligned fallback cover image when Pexels has nothing.
    Uses Veridian navy/gold palette, category pill, issue number, and
    'Nothing escapes notice.' tagline.
    """
    try:
        from PIL import Image, ImageDraw

        def h2rgb(s):
            s = s.lstrip("#")
            return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

        W, H   = 1400, 788                   # 16:9 cover ratio
        c1, c2 = h2rgb(color1), h2rgb(color2)
        gold   = (184, 144, 57)              # --mustard / Veridian gold
        gold_s = (226, 203, 123)             # gold-soft

        img  = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Diagonal gradient background
        for y in range(H):
            t = y / H
            draw.line(
                [(0, y), (W, y)],
                fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)),
            )

        # Subtle diagonal texture lines
        for x in range(-H, W, 80):
            draw.line([(x, 0), (x + H, H)], fill=(255, 255, 255), width=1)

        # Gold accent bar — left edge
        draw.rectangle([(0, 0), (10, H)], fill=gold)

        # Large faded circle — right-side decoration
        draw.ellipse([(900, -160), (1500, 940)],
                     outline=(255, 255, 255), width=2)

        # Category pill — outlined gold
        cat_upper = category.upper()
        pill_w    = len(cat_upper) * 14 + 64
        draw.rounded_rectangle(
            [(60, 60), (60 + pill_w, 108)],
            radius=24, outline=gold, width=2,
        )
        draw.text((84, 70), cat_upper, fill=gold)

        # Issue number (big serif-ish — Pillow's default looks fine at scale)
        draw.text((60, 170), f"No. {issue_num:02d}", fill=(255, 255, 255))

        # Divider line
        draw.line([(60, 280), (260, 280)], fill=gold, width=2)

        # Brand wordmark + tagline
        draw.text((60, 310), "VERIDIAN", fill=(255, 255, 255))
        draw.text((60, 350), "Nothing escapes notice.", fill=gold_s)

        # Bottom-right stamp
        draw.text((W - 320, H - 56), "THE QUIET LETTER · NIGERIA",
                  fill=(255, 255, 255))

        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
        buf.seek(0)
        return buf.read(), "image/jpeg"

    except ImportError:
        print("    ⚠ Pillow not installed — run: pip install Pillow")
        return None, None
    except Exception as e:
        print(f"    ⚠ Fallback image error: {e}")
        return None, None


def upload_image(post_slug, query, fallback_query, category,
                 color1, color2, issue_num):
    """Try Pexels first, fall back to Pillow. Returns WordPress media ID or None."""
    img_bytes, mime = fetch_pexels_image(query, fallback_query)

    if not img_bytes:
        print(f"    → Using branded fallback image")
        img_bytes, mime = generate_fallback_image(category, color1, color2, issue_num)

    if not img_bytes:
        print(f"    ⚠ No image available (install Pillow: pip install Pillow)")
        return None

    ext      = "jpg" if "jpeg" in mime else "png"
    filename = f"veridian-{post_slug}.{ext}"

    headers = {
        "Authorization":       f"Bearer {BEARER_TOKEN}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type":        mime,
    }

    r = requests.post(f"{API_BASE}/media",
                      headers=headers, data=img_bytes, timeout=60)
    if r.status_code in (200, 201):
        mid = r.json()["id"]
        print(f"    ✓ Image uploaded to WordPress (id={mid})")
        return mid

    print(f"    ⚠ Image upload failed ({r.status_code}): {r.text[:120]}")
    return None


# ── CATEGORY HELPER ──────────────────────────────────────────────
def get_or_create_category(name, cache):
    """Get or create a WP category. Idempotent + handles term_exists edge cases."""
    if name in cache:
        return cache[name]

    search_name = name.replace("&amp;", "&")

    # 1) Search existing
    r = requests.get(
        f"{API_BASE}/categories",
        params={"search": search_name, "per_page": 100},
        headers=wp_headers(), timeout=15,
    )
    if r.status_code == 200:
        for cat in r.json():
            api_name = cat.get("name", "").replace("&amp;", "&").replace("&#038;", "&")
            if api_name.lower() == search_name.lower():
                cache[name] = cat["id"]
                print(f"    → Category '{name}' already exists (id={cat['id']})")
                return cat["id"]

    # 2) Create
    r = requests.post(
        f"{API_BASE}/categories",
        headers=wp_headers(),
        data=json.dumps({"name": name}),
        timeout=15,
    )
    if r.status_code in (200, 201):
        cat_id = r.json()["id"]
        cache[name] = cat_id
        print(f"    ✓ Category '{name}' created (id={cat_id})")
        return cat_id

    # 3) Handle 400 term_exists
    if r.status_code == 400:
        try:
            err = r.json()
            if err.get("code") == "term_exists":
                existing_id = (err.get("data", {}).get("term_id")
                               or err.get("data", {}).get("resource_id"))
                if existing_id:
                    cache[name] = int(existing_id)
                    print(f"    → Category '{name}' already exists (id={existing_id})")
                    return int(existing_id)
        except Exception as e:
            print(f"    ⚠ Error parsing 400 response: {e}")

    print(f"    ✗ Category '{name}' failed ({r.status_code}): {r.text[:120]}")
    return None


def post_exists(slug):
    """Check if a post with this slug already exists — keeps re-runs safe."""
    r = requests.get(
        f"{API_BASE}/posts",
        params={"slug": slug, "status": "publish,draft,pending,private,future"},
        headers=wp_headers(), timeout=15,
    )
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]
    return None


def create_post(post, cat_ids, media_id):
    payload = {
        "title":   post["title"],
        "content": post["content"],
        "excerpt": post["excerpt"],
        "status":  "publish",
        "slug":    post["slug"],
    }
    if cat_ids:  payload["categories"]     = cat_ids
    if media_id: payload["featured_media"] = media_id

    r = requests.post(
        f"{API_BASE}/posts",
        headers=wp_headers(),
        data=json.dumps(payload),
        timeout=30,
    )
    if r.status_code in (200, 201):
        p = r.json()
        return p["id"], p.get("link", "")
    return None, f"{r.status_code}: {r.text[:150]}"


# ── POST DEFINITIONS — the 7 Veridian blog posts ─────────────────
# Each post has:
#   pexels_query    — primary Pexels search term
#   pexels_fallback — backup search if primary returns nothing
#   color1/color2   — brand gradient for fallback image
#   issue_num       — magazine-style issue number
# Colours rotate through Veridian brand palette: navy → sage → gold → berry
POSTS = [
    {
        "issue_num":       1,
        "title":           "Your Google Business Profile is doing more for your business than your website.",
        "slug":            "google-business-profile-vs-website",
        "category":        "Local SEO",
        "pexels_query":    "smartphone google search business listing",
        "pexels_fallback": "google maps phone screen business",
        "color1": "#142B4D", "color2": "#0A1B33",
        "excerpt": "If you only had budget for one online thing this quarter, it shouldn't be a website redesign. Here's the surprisingly small task that drives most local enquiries — and why most Nigerian SMEs ignore it.",
        "content": "<p>If you only had budget for one online thing this quarter, it shouldn't be a website redesign. For most Nigerian SMEs serving customers in a specific city or area, your <strong>Google Business Profile</strong> generates more enquiries than your website ever will — and most owners don't even realise they have one.</p>"
                   "<h2>Why It Matters</h2>"
                   "<p>When someone in Lagos searches <em>plumber near me</em> or <em>law firm Lekki</em>, Google doesn't show ten websites. It shows three business profiles in a map pack. Those three businesses win 70% of the clicks. If you're not in that map pack, your website might as well not exist.</p>"
                   "<h2>What to Fix First</h2>"
                   "<ul>"
                   "<li><strong>Claim and verify your profile</strong> — search for your business on Google Maps. If a listing exists, claim it. If not, create one.</li>"
                   "<li><strong>Complete every field</strong> — hours, services, payment methods, website URL, descriptions. Profiles with 100% completion get 2.7× more enquiries.</li>"
                   "<li><strong>Upload real photos monthly</strong> — Google rewards activity. Even ten photos a month tells the algorithm your business is alive.</li>"
                   "<li><strong>Respond to every review</strong> — yes, even the bad ones. Especially the bad ones.</li>"
                   "<li><strong>Post weekly updates</strong> — offers, events, news. Treat it like a free social media channel.</li>"
                   "</ul>"
                   "<h2>The Quiet Truth</h2>"
                   "<p>A polished Google Business Profile takes about three focused hours to set up properly. It costs nothing. And for a service business anywhere in Nigeria, it will outperform an expensive website redesign for local enquiries every single time.</p>"
                   "<p>If you'd like a free passive snapshot of where your profile stands today, get in touch with <strong>Veridian</strong>.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
    {
        "issue_num":       2,
        "title":           "5 things to fix on your site before spending one naira on ads.",
        "slug":            "five-fixes-before-ads",
        "category":        "Strategy",
        "pexels_query":    "laptop website analytics dashboard nigerian business",
        "pexels_fallback": "small business laptop analytics charts",
        "color1": "#355C44", "color2": "#1E3D2B",
        "excerpt": "Running ads to a leaky site is a fast way to burn budget. These five free, boring fixes will lift conversions before you write a single ad headline.",
        "content": "<p>Running paid ads to a leaky website is one of the most expensive mistakes a Nigerian SME can make. Every naira you spend on Google Ads, Meta Ads, or LinkedIn Ads sends a visitor to your site. If that visitor lands and immediately leaves, you've paid for a glance — not a customer.</p>"
                   "<h2>The Audit Before the Spend</h2>"
                   "<p>Before you authorise a single ad campaign, do these five free fixes. They take a weekend and they'll lift your conversion rate before you write a single ad headline.</p>"
                   "<ol>"
                   "<li><strong>Test your mobile site on a real phone.</strong> 70% of Nigerian web traffic is mobile. If your site doesn't load in under 3 seconds on a phone, fix this first.</li>"
                   "<li><strong>Make your phone number tappable.</strong> Wrap it in <code>&lt;a href=\"tel:+234...\"&gt;</code>. Click-to-call is the highest-converting CTA on most service sites.</li>"
                   "<li><strong>Add a contact form that actually sends.</strong> Test it. Send a form to yourself. If you don't receive it in 30 seconds, your form is broken and you don't know.</li>"
                   "<li><strong>Show real prices, or at least a range.</strong> Visitors who can't see what you charge bounce. \"Starting from ₦150,000\" beats \"Contact us for pricing\" every single time.</li>"
                   "<li><strong>Put three real photos of your work.</strong> Not stock images. Not logos. Actual photos. Trust is built in seconds.</li>"
                   "</ol>"
                   "<h2>Now Run the Ads</h2>"
                   "<p>Once these five are sorted, your ad budget works two to three times harder. The same campaign on a fixed site produces 2-3× the leads of the broken one. This isn't theory — it's what happens every time we run the comparison.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
    {
        "issue_num":       3,
        "title":           "How to read your own digital audit (without an MBA).",
        "slug":            "reading-your-audit",
        "category":        "Audit Method",
        "pexels_query":    "notebook checklist business audit report",
        "pexels_fallback": "professional reviewing report notes",
        "color1": "#B89039", "color2": "#8A6919",
        "excerpt": "Audits are observations, not verdicts. Here's our reading guide for the founder who has 20 minutes and no patience for jargon.",
        "content": "<p>A good digital audit is observations, not verdicts. It tells you what's true about your online presence today — and lets you decide what to do about it. Here's how to read one without getting lost in jargon.</p>"
                   "<h2>What an Audit Actually Measures</h2>"
                   "<p>A passive digital audit looks at <em>public-facing signals only</em> — the same things Google, your customers, and your competitors can already see. No hacking, no scanning, no unauthorised access. Just the surface.</p>"
                   "<ul>"
                   "<li><strong>Discoverability</strong> — can people find you when they search?</li>"
                   "<li><strong>Trust signals</strong> — does the site read as legitimate within 7 seconds?</li>"
                   "<li><strong>Conversion paths</strong> — is it obvious what to do next?</li>"
                   "<li><strong>Technical hygiene</strong> — load speed, mobile readiness, HTTPS, broken links.</li>"
                   "<li><strong>Local presence</strong> — Google Business Profile, NAP consistency, reviews.</li>"
                   "</ul>"
                   "<h2>How to Read the Scores</h2>"
                   "<p>Most audits use a 0–100 scale per category. Treat these as <em>relative</em>, not absolute. A 60 means there's room to improve, not that you're failing. The goal isn't perfection — it's to surface the cheapest, highest-impact fixes first.</p>"
                   "<h2>What to Do With It</h2>"
                   "<ol>"
                   "<li><strong>Read the red flags first.</strong> Items marked critical usually take under an hour to fix and produce immediate gains.</li>"
                   "<li><strong>Ignore vanity metrics.</strong> A high \"SEO score\" means nothing if visitors leave in 3 seconds.</li>"
                   "<li><strong>Pick three things this month.</strong> Not thirty. Three. Implementation beats ambition every time.</li>"
                   "<li><strong>Re-audit in 90 days.</strong> Measurement isn't a one-off.</li>"
                   "</ol>"
                   "<p>If something in the audit doesn't make sense, push back. We've changed recommendations after founder pushback many times. The point is to help you decide — not to win an argument.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
    {
        "issue_num":       4,
        "title":           "Why your site is slow in Lagos — and how to fix it.",
        "slug":            "site-speed-in-nigeria",
        "category":        "Performance",
        "pexels_query":    "mobile phone web loading lagos africa",
        "pexels_fallback": "smartphone slow web browsing screen",
        "color1": "#963A4D", "color2": "#6E2837",
        "excerpt": "Most Nigerian SME sites take 5+ seconds to load on a phone. Here's why, and the four-line checklist that fixes most of it.",
        "content": "<p>Most Nigerian SME websites take five to eight seconds to fully load on a mobile phone over 4G in Lagos. 53% of mobile visitors abandon a page that takes longer than three seconds. That means more than half the people clicking your link never see your site.</p>"
                   "<h2>Why It's Slow</h2>"
                   "<p>The slowness usually isn't the network — it's the site. Specific patterns we see in Nigerian SME sites again and again:</p>"
                   "<ul>"
                   "<li><strong>Massive unoptimised images.</strong> 4MB photos served as-is. Compress and resize.</li>"
                   "<li><strong>Bloated WordPress themes.</strong> Themes loaded with sliders, animations, and 14 plugins each adding 200KB.</li>"
                   "<li><strong>No caching.</strong> Every visitor regenerates pages from scratch.</li>"
                   "<li><strong>Foreign hosting with no CDN.</strong> Your server is in Frankfurt; your customer is in Lekki. That's 200ms per round-trip, multiplied by every asset on the page.</li>"
                   "</ul>"
                   "<h2>The Four-Line Checklist</h2>"
                   "<ol>"
                   "<li><strong>Compress all images.</strong> Use Squoosh.app or TinyPNG. Most images should be under 200KB.</li>"
                   "<li><strong>Add a free caching plugin.</strong> WP Rocket, W3 Total Cache, or LiteSpeed Cache.</li>"
                   "<li><strong>Enable Cloudflare's free tier.</strong> A global CDN with one DNS change. Brings your assets closer to Lagos.</li>"
                   "<li><strong>Remove plugins you don't actively use.</strong> Every plugin is a load cost. Audit and prune monthly.</li>"
                   "</ol>"
                   "<h2>Measure Twice, Fix Once</h2>"
                   "<p>Test your site with <strong>Google PageSpeed Insights</strong> on a mobile profile. Then on a real phone over 4G. The difference between Lighthouse score and real-world speed is often where the bodies are buried.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
    {
        "issue_num":       5,
        "title":           "Reviews aren't just stars: a guide to responding like a pro.",
        "slug":            "responding-to-reviews",
        "category":        "Reputation",
        "pexels_query":    "smartphone customer review rating five star",
        "pexels_fallback": "phone screen review business reputation",
        "color1": "#142B4D", "color2": "#0A1B33",
        "excerpt": "Your response says more about your business than the review itself. A short, practical guide to handling reviews — including the bad ones.",
        "content": "<p>Your response to a review tells future customers more about your business than the review itself. A thoughtful reply to a one-star complaint impresses readers more than a generic \"Thanks!\" to a five-star compliment.</p>"
                   "<h2>The Three-Part Framework</h2>"
                   "<p>Whether the review is glowing or scathing, the same structure works:</p>"
                   "<ol>"
                   "<li><strong>Acknowledge specifically.</strong> Reference something concrete from the review — not \"Thanks for your feedback\" but \"Glad the team got the leak fixed before your guests arrived.\"</li>"
                   "<li><strong>Take responsibility, if warranted.</strong> \"You're right — the install ran two days late. That shouldn't have happened, and here's why it did…\"</li>"
                   "<li><strong>Show what changed.</strong> \"We've added a same-day acknowledgement protocol for all enquiries since.\" This signals the business actually learns.</li>"
                   "</ol>"
                   "<h2>The Bad-Review Playbook</h2>"
                   "<ul>"
                   "<li><strong>Respond within 24 hours.</strong> Silence is the worst answer.</li>"
                   "<li><strong>Never argue publicly.</strong> Even if the reviewer is wrong, future readers see you as the problem.</li>"
                   "<li><strong>Take it offline.</strong> \"I'd like to make this right — please email hello@yourcompany.com or call +234… directly.\"</li>"
                   "<li><strong>Never delete legitimate reviews.</strong> Even on Google. The replies are seen by every future customer.</li>"
                   "</ul>"
                   "<h2>The Good-Review Playbook</h2>"
                   "<p>Even on a five-star review, don't say \"Thanks!\" Say something like: \"Thanks Adebola — really glad the Wuse property came together for you. Tell Maria the marble we sourced was worth the wait.\" This shows future customers you remember real clients by name.</p>"
                   "<p>Every reply you write is a tiny piece of marketing. Future customers read them before they read your website.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
    {
        "issue_num":       6,
        "title":           "Credibility on a startup budget: 10 cheap moves that work.",
        "slug":            "credibility-on-a-budget",
        "category":        "Strategy",
        "pexels_query":    "small business workspace laptop nigerian entrepreneur",
        "pexels_fallback": "african small business owner laptop desk",
        "color1": "#355C44", "color2": "#1E3D2B",
        "excerpt": "You don't need a marketing team to look serious online. Ten things you can do this weekend that immediately raise the trust signal.",
        "content": "<p>You don't need a marketing team or a six-figure brand budget to look serious online. Ten things you can do this weekend — most of them free — that immediately raise your trust signal with new visitors.</p>"
                   "<h2>The Ten Moves</h2>"
                   "<ol>"
                   "<li><strong>Use a custom email.</strong> <em>hello@yourcompany.com</em> beats <em>yourcompany@gmail.com</em>. Costs ₦5,000/year.</li>"
                   "<li><strong>Add HTTPS.</strong> If your URL still shows \"Not Secure\", you're losing 30% of visitors before they read a word.</li>"
                   "<li><strong>Include real names and photos.</strong> Even one founder photo on your About page lifts conversion. Stock images hurt more than no images.</li>"
                   "<li><strong>List a Lagos / Abuja / Port Harcourt address.</strong> \"Based in Lagos\" is fine. No address at all signals fly-by-night.</li>"
                   "<li><strong>Show a real phone number.</strong> Tappable. With country code. Answer it.</li>"
                   "<li><strong>Add three customer testimonials.</strong> With first name, business name, and city. Generic five-star quotes feel fake.</li>"
                   "<li><strong>Display your registration number.</strong> CAC RC number, where relevant. Free to add; signals legitimacy instantly.</li>"
                   "<li><strong>Set up a LinkedIn company page.</strong> Even sparse, it's a credibility check most visitors will run.</li>"
                   "<li><strong>Get your first three Google reviews.</strong> Ask your most satisfied past customers. Zero reviews is worse than two reviews.</li>"
                   "<li><strong>Refresh your favicon.</strong> The little icon in browser tabs. Custom favicon costs nothing and signals attention to detail.</li>"
                   "</ol>"
                   "<h2>The Compound Effect</h2>"
                   "<p>Each of these moves individually is small. Together, they compound. A new visitor running through your site picks up a dozen tiny \"this is a real business\" signals — none of them noticed consciously, all of them counted.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
    {
        "issue_num":       7,
        "title":           "NAP consistency: the boring SEO fix that pays off most.",
        "slug":            "nap-consistency",
        "category":        "Local SEO",
        "pexels_query":    "business card address contact information",
        "pexels_fallback": "business directory contact card",
        "color1": "#B89039", "color2": "#8A6919",
        "excerpt": "Name, Address, Phone — if these differ across the web, Google notices and your rankings suffer. The plain-English fix.",
        "content": "<p>NAP stands for Name, Address, Phone. If those three details differ across the web — your website says one address, your Google Business Profile another, your Facebook page a third — Google notices, and your local rankings suffer.</p>"
                   "<h2>Why Google Cares</h2>"
                   "<p>Google uses NAP consistency as one of its main local-ranking signals. The logic: a real business has one name, one address, one phone — and uses them consistently everywhere. When details vary, Google can't tell if it's one business or several, and downweights the listing.</p>"
                   "<h2>Where Inconsistencies Hide</h2>"
                   "<ul>"
                   "<li>Your website header vs your footer</li>"
                   "<li>Your Google Business Profile</li>"
                   "<li>Your Facebook business page</li>"
                   "<li>LinkedIn company page</li>"
                   "<li>Old directory listings (VConnect, Yellowpages.ng, etc.)</li>"
                   "<li>Email signatures</li>"
                   "<li>Invoices and quotes</li>"
                   "</ul>"
                   "<h2>The Plain-English Fix</h2>"
                   "<ol>"
                   "<li><strong>Pick one canonical version.</strong> Decide: is it \"12 Adeola Odeku Street\" or \"12 Adeola Odeku St.\"? Does the phone use \"+234\" or \"0\"? Choose once, use everywhere.</li>"
                   "<li><strong>List every place your business appears online.</strong> Search your business name in quotes. Make a list.</li>"
                   "<li><strong>Update each listing.</strong> Some are easy (your website). Some require a quick form (Google Business Profile). Some need a phone call (old directory listings).</li>"
                   "<li><strong>Set a quarterly reminder.</strong> Things drift. Phone numbers change, you relocate, a directory imports old data. Re-check every 90 days.</li>"
                   "</ol>"
                   "<h2>The Payoff</h2>"
                   "<p>Most Nigerian SMEs with patchy NAP see a 10–20% lift in local map-pack visibility within 60 days of fixing it. It's the most boring SEO win available — and the most reliable.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
    {
        "issue_num":       8,
        "title":           "When the World's Smartest AI Got Switched Off: What the Claude Fable 5 Saga Means for Your Business.",
        "slug":            "claude-fable-5-vendor-risk-lesson",
        "category":        "Strategy",
        "pexels_query":    "server data center technology abstract",
        "pexels_fallback": "computer technology network abstract blue",
        "color1": "#142B4D", "color2": "#0A1B33",
        "excerpt": "Anthropic's most capable public AI model launched on a Tuesday. By Friday evening, a US government directive had taken it offline worldwide. Here's the four-day story — and the dependency lesson every business using AI tools should sit with.",
        "content": "<p>On 9 June 2026, Anthropic released Claude Fable 5 — at the time, one of the most capable AI models publicly available anywhere. Four days later, it was gone. Not slowed down, not rate-limited — switched off entirely, for every user, everywhere, including the company's own staff.</p>"
                   "<h2>What Actually Happened</h2>"
                   "<p>Fable 5 launched as the public-facing version of Anthropic's most advanced model family, built for long, complex tasks in software engineering, research, and knowledge work. On Friday, 12 June, the US Commerce Department sent Anthropic an export-control directive citing a suspected security bypass — colloquially, a \"jailbreak\" — and ordered the company to block access for all foreign nationals, inside or outside the United States, including its own foreign-national employees.</p>"
                   "<p>Anthropic had no reliable way to check a user's nationality at the point of every request. Rather than risk non-compliance, the company disabled the model worldwide for every customer that same evening. Anthropic said publicly that it disagreed with the decision and called it a misunderstanding, while confirming it would comply. As of this writing, the company says it is working to restore access, with no confirmed date.</p>"
                   "<h2>Why This Isn't Just Tech-Industry Gossip</h2>"
                   "<p>It's tempting to read this as a story about Silicon Valley and Washington politics. For a business in Abuja running customer service on a chatbot, drafting documents with an AI assistant, or building any workflow around a single AI provider, it's a much closer story than that.</p>"
                   "<p>A model can disappear for reasons that have nothing to do with your business and everything to do with decisions made somewhere else entirely — a regulatory order, a licensing dispute, a pricing change, a company pivot. Fable 5 went from launch to global blackout in 96 hours. If your invoicing assistant, your support bot, or your content workflow depended on it specifically, you lost that capability with zero warning.</p>"
                   "<h2>The Three Questions Worth Asking Yourself</h2>"
                   "<ul>"
                   "<li><strong>What AI tools is my business actually depending on right now?</strong> Most owners can't answer this quickly. That's the first gap.</li>"
                   "<li><strong>If one of them vanished tomorrow, what would break?</strong> Customer replies? Invoice generation? Content production? Know the blast radius before it happens, not after.</li>"
                   "<li><strong>Do I have a fallback that doesn't require a rebuild?</strong> Multi-model flexibility — even just knowing which alternative tool covers the same task — turns a crisis into an inconvenience.</li>"
                   "</ul>"
                   "<h2>The Quiet Lesson</h2>"
                   "<p>This isn't a call to distrust AI tools, and it isn't a verdict on who was right between Anthropic and the directive that grounded it. It's a reminder that <em>any</em> single point of dependency — one vendor, one model, one platform — carries a risk that's invisible until the day it isn't. The businesses least disrupted by the Fable 5 shutdown were the ones that had never put all their weight on one provider in the first place.</p>"
                   "<p>This is exactly the kind of blind spot a proper digital and tooling audit surfaces — not just \"is your website fast,\" but \"what happens to your operations if any one piece goes away overnight.\" If you've never mapped out your AI and software dependencies, it's worth twenty minutes before it costs you a Friday evening.</p>"
                   "<p><em>\"Nothing escapes notice.\" — Veridian</em></p>",
    },
]


# ── MAIN ──────────────────────────────────────────────────────────
def run():
    print("\n" + "=" * 64)
    print("  VERIDIAN — WordPress Bulk Post Creator")
    print(f"  Site: {WP_SITE}")
    print("  Featured images: Pexels real photography + branded fallback")
    print("=" * 64 + "\n")

    if not BEARER_TOKEN or len(BEARER_TOKEN) < 20:
        print("  ✗ Paste a fresh Bearer token into BEARER_TOKEN at the top.")
        show_token_help()
        sys.exit(1)

    if not test_connection():
        sys.exit(1)

    print(f"Creating {len(POSTS)} posts...\n")

    results, cat_cache = [], {}

    # Create the top-level 'blog' category first so every post
    # gets tagged with it — this keeps blog posts cleanly separated
    # from case studies when work.html fetches /posts?categories={cs-id}
    print("Creating blog category...")
    blog_cat_id = get_or_create_category("blog", cat_cache)
    if not blog_cat_id:
        print("  ⚠ Could not create blog category — posts will be uncategorised")
        blog_cat_id = None
    print()

    for i, post in enumerate(POSTS, 1):
        print(f"[{i}/{len(POSTS)}] {post['title'][:65]}...")

        existing_id = post_exists(post["slug"])
        if existing_id:
            print(f"    → Already exists (id={existing_id}) — skipping\n")
            results.append({"ok": True, "title": post["title"][:55],
                            "id": existing_id, "skipped": True})
            continue

        content_cat_id = get_or_create_category(post["category"], cat_cache)
        cat_ids = [c for c in [content_cat_id, blog_cat_id] if c]

        print(f"    Fetching featured image from Pexels: '{post['pexels_query']}'...")
        media_id = upload_image(
            post["slug"],
            post["pexels_query"],
            post["pexels_fallback"],
            post["category"],
            post["color1"],
            post["color2"],
            post["issue_num"],
        )

        pid, result = create_post(post, cat_ids, media_id)

        if pid:
            print(f"    ✓ Post created → {result}")
            results.append({"ok": True, "title": post["title"][:55], "id": pid})
        else:
            print(f"    ✗ Failed: {result}")
            results.append({"ok": False, "title": post["title"][:55], "error": result})

        if i < len(POSTS):
            time.sleep(2)   # courtesy pause between posts

    ok = sum(1 for r in results if r["ok"])
    print(f"\n{'=' * 64}")
    print(f"  COMPLETE — {ok} / {len(POSTS)} posts created")
    print(f"{'=' * 64}\n")
    for r in results:
        skip = " (already existed)" if r.get("skipped") else ""
        st = f"✓ id={r['id']}{skip}" if r["ok"] else f"✗ {r.get('error', '')[:50]}"
        print(f"  {st}  —  {r['title']}")
    print(f"\n  View:  https://wordpress.com/posts/{WP_SITE}\n")


if __name__ == "__main__":
    run()
