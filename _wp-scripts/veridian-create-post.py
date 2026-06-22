#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
VERIDIAN — Single Post Creator
═══════════════════════════════════════════════════════════════════
Enter a title + category → AI generates content → Pexels fetches
a featured image → post is pushed live to WordPress.

REQUIREMENTS:
    pip install requests

USAGE:
    python3 veridian-create-post.py

ANTHROPIC API KEY:
    Set via environment variable for the best experience:
      export ANTHROPIC_API_KEY="sk-ant-..."
    Or paste the value into ANTHROPIC_KEY below.
    If left blank, the script falls back to a structured Veridian template.
═══════════════════════════════════════════════════════════════════
"""

import requests
import json
import time
import sys
import re
import os

# ── CREDENTIALS ────────────────────────────────────────────────────
WP_SITE      = "255358071"
WP_DOMAIN    = "veridiangrouplimited.wordpress.com"
BEARER_TOKEN = "7nr(4rp5B$tNvdipxUAhO2y82ppDy(kl(7N#M$ApU)a@PqFY7ETE3eLlr4Jh2wij"
CLIENT_ID      = "140052"
PEXELS_API_KEY = "tEYbi4lcIbtRPR52F93GhfEBwkbNRoulE5ZwajutUEOuhFhS3MaoAlv6"
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
# ANTHROPIC_KEY = "sk-ant-..."   # ← paste your key here if not using env var
# ──────────────────────────────────────────────────────────────────

API_BASE      = f"https://public-api.wordpress.com/wp/v2/sites/{WP_SITE}"
PEXELS_BASE   = "https://api.pexels.com/v1"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

CATEGORIES = [
    "Local SEO",
    "Strategy",
    "Audit Method",
    "Performance",
    "Reputation",
    "AI & Automation",
    "Practice Notes",
]


# ── HELPERS ────────────────────────────────────────────────────────
def wp_headers(content_type="application/json"):
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type":  content_type,
        "Accept":        "application/json",
    }


def pexels_headers():
    return {"Authorization": PEXELS_API_KEY}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:60]


def spinner(msg):
    print(f"  ⏳ {msg}", end="\r", flush=True)


def show_token_help():
    print("\n  ── HOW TO GET A NEW TOKEN ─────────────────────────────────────")
    print("  1. Open this URL in your browser:")
    print(f"     https://public-api.wordpress.com/oauth2/authorize"
          f"?client_id={CLIENT_ID}"
          f"&redirect_uri=https://localhost"
          f"&response_type=token")
    print("  2. Log in with the Veridian Group WordPress.com account")
    print("  3. You'll land at https://localhost/#access_token=XXXXXX&token_type=bearer")
    print("  4. Copy everything between 'access_token=' and '&token_type='")
    print("  5. Replace BEARER_TOKEN at the top of this script")
    print("  ────────────────────────────────────────────────────────────────\n")


# ── STEP 1: USER INPUT ─────────────────────────────────────────────
def get_user_input():
    print("\n" + "=" * 60)
    print("  VERIDIAN — Single Post Creator")
    print("=" * 60 + "\n")

    title = input("  Post Title: ").strip()
    if not title:
        print("  Error: Title cannot be empty.")
        sys.exit(1)

    print("\n  Select a category:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"    {i}. {cat}")
    print(f"    {len(CATEGORIES) + 1}. Enter a custom category")

    while True:
        choice = input(f"\n  Choice (1–{len(CATEGORIES) + 1}): ").strip()
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(CATEGORIES):
                category = CATEGORIES[n - 1]
                break
            elif n == len(CATEGORIES) + 1:
                category = input("  Custom category name: ").strip()
                if category:
                    break
        print(f"  Please enter a number between 1 and {len(CATEGORIES) + 1}.")

    print(f"\n  ✓ Title:    {title}")
    print(f"  ✓ Category: {category}")
    confirm = input("\n  Proceed? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("  Cancelled.")
        sys.exit(0)

    return title, category


# ── STEP 2: AI CONTENT GENERATION ─────────────────────────────────
def generate_content(title, category):
    """Call Anthropic API to generate blog post content."""
    spinner("Generating post content with AI...")

    if not ANTHROPIC_KEY:
        print("  ⚠ No Anthropic API key — using Veridian template instead")
        return generate_template_content(title, category)

    prompt = f"""You are writing a professional blog post for Veridian, a quiet, ethical digital advisory practice based in Nigeria. Veridian serves Nigerian SMEs (real estate, hospitality, schools, professional services, retail) with passive digital audits, website work, local SEO, Google Business Profile, AI advisory, and agentic workflows.

Write a complete blog post with the following details:
- Title: {title}
- Category: {category}
- Tone: Calm, expert, honest — never salesy, never hype-y. Quiet authority. Plain English. Like a senior practitioner explaining something useful.
- Length: 450–600 words
- Audience: Nigerian SME founders and managers — busy, practical, suspicious of marketing fluff

REQUIREMENTS:
1. Start directly with an engaging opening paragraph (no "Introduction" heading)
2. Include 2–3 H2 section headings using HTML <h2> tags
3. Use <ul> or <ol> lists where appropriate
4. Include at least one reference to Lagos, Abuja, Port Harcourt, or specifically Nigerian SME context (currency in ₦, local search behaviour, local hosting, etc.)
5. End with a brief call-to-action paragraph mentioning Veridian
6. Close with this exact line on its own paragraph: <p><em>"Nothing escapes notice." — Veridian</em></p>
7. Use only basic HTML tags: <p>, <h2>, <h3>, <ul>, <ol>, <li>, <strong>, <em>, <code>
8. Do NOT include the title in the content — it will be set separately
9. Do NOT include any meta text, preamble, or explanation — output the HTML content ONLY
10. AVOID AI-SOUNDING PHRASES like "in today's fast-paced digital landscape", "leverage", "synergy", "unlock", "delve into", "in conclusion". Write like a human who's tired of jargon.

Output ONLY the HTML content, nothing else."""

    try:
        r = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key":         ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 1500,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )

        if r.status_code == 200:
            content = r.json()["content"][0]["text"].strip()
            print(f"  ✓ Content generated ({len(content.split())} words)")
            return content
        else:
            print(f"  ⚠ Anthropic API error ({r.status_code}) — using template")
            return generate_template_content(title, category)

    except Exception as e:
        print(f"  ⚠ Anthropic error: {e} — using template")
        return generate_template_content(title, category)


def generate_template_content(title, category):
    """Structured Veridian fallback content when Anthropic API is unavailable."""
    return f"""<p>Most Nigerian SME owners we work with at Veridian have heard about {title.lower().rstrip('.')} — but few have time to dig into what it actually means for their business. This is the short, no-jargon version.</p>

<h2>Why It Matters for Nigerian SMEs</h2>
<p>The digital landscape for Nigerian businesses moves quickly: search behaviour shifts, customer expectations rise, and small advantages compound over time. Ignoring {category.lower()} is a quiet leak — small at first, expensive over years.</p>
<ul>
  <li>Most local competitors haven't fixed this yet — early movers benefit disproportionately</li>
  <li>The fixes are usually free or near-free; the cost is attention, not capital</li>
  <li>Google, customers, and partners all use these signals to judge legitimacy</li>
  <li>Quiet, ethical practice — not hype</li>
</ul>

<h2>The Veridian Method</h2>
<p>Our work on {category.lower()} follows the same four-step pattern we apply to every engagement, whether the client is in Lagos, Abuja, or anywhere else in Nigeria:</p>
<ol>
  <li><strong>Observe quietly</strong> — public-data only, no hacking, no unauthorised access</li>
  <li><strong>Measure honestly</strong> — if it can't be measured, we don't claim it</li>
  <li><strong>Fix what matters most</strong> — three high-impact moves beat thirty small ones</li>
  <li><strong>Review in 90 days</strong> — measurement isn't a one-off</li>
</ol>

<h2>Start Small, Start This Week</h2>
<p>You don't need a marketing team or a six-figure budget to move on this. The first three improvements usually take a weekend and produce visible results within 30 days. Veridian is built around helping Nigerian SMEs do exactly that — quietly, methodically, and without the usual sales theatre.</p>

<p>Get in touch with <strong>Veridian</strong> for a free, no-obligation passive audit snapshot of your current digital footprint. 48-hour turnaround.</p>

<p><em>"Nothing escapes notice." — Veridian</em></p>"""


# ── STEP 3: PEXELS IMAGE ───────────────────────────────────────────
def build_pexels_query(title, category):
    """Build a Veridian Pexels search query from title and category."""
    cat_map = {
        "Local SEO":        "smartphone google search business listing",
        "Strategy":         "small business laptop nigerian entrepreneur",
        "Audit Method":     "notebook checklist business audit report",
        "Performance":      "mobile phone web loading screen africa",
        "Reputation":       "smartphone customer review rating stars",
        "AI & Automation":  "laptop screen ai technology business workflow",
        "Practice Notes":   "small business workspace laptop coffee desk",
    }
    base = cat_map.get(category, "nigerian small business laptop")

    # Add a topic-specific noun from the title to refine the search
    stop = {
        'the', 'a', 'an', 'in', 'of', 'for', 'and', 'or', 'to', 'your', 'is',
        'are', 'how', 'why', 'what', 'when', 'does', 'do', 'can', 'should',
        'will', 'with', 'before', 'after', 'than',
    }
    words = [w for w in title.lower().split() if w not in stop and len(w) > 3]
    extra = words[0] if words else ''

    if extra and extra not in base:
        return f"{extra} business technology africa"
    return base


def fetch_pexels_image(query):
    """Fetch a high-quality landscape photo from Pexels."""
    spinner(f"Fetching image from Pexels: '{query}'...")

    for attempt in [query, "nigerian small business laptop", "business technology africa"]:
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

            # Prefer photos with landscape ratio
            photo = next(
                (p for p in photos
                 if p.get("width", 0) / max(p.get("height", 1), 1) >= 1.4),
                photos[0],
            )

            img_url = (photo.get("src", {}).get("large2x")
                       or photo.get("src", {}).get("large")
                       or photo.get("src", {}).get("original"))
            if not img_url:
                continue

            img_r = requests.get(img_url, timeout=30)
            if img_r.status_code == 200:
                photographer = photo.get("photographer", "Pexels")
                print(f"  ✓ Photo by {photographer} (Pexels) — query: '{attempt}'")
                return img_r.content, "image/jpeg"

        except Exception as e:
            print(f"  ⚠ Pexels attempt failed: {e}")
            continue

    print("  ⚠ No image found — post will be created without featured image")
    return None, None


def upload_image(img_bytes, mime, title):
    """Upload image to WordPress media library."""
    spinner("Uploading image to WordPress...")
    slug     = slugify(title)
    filename = f"veridian-{slug}.jpg"

    headers = {
        "Authorization":       f"Bearer {BEARER_TOKEN}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type":        mime,
    }

    r = requests.post(f"{API_BASE}/media", headers=headers, data=img_bytes, timeout=60)

    if r.status_code in (200, 201):
        media_id = r.json()["id"]
        print(f"  ✓ Image uploaded (media id={media_id})")
        return media_id

    print(f"  ⚠ Image upload failed ({r.status_code}): {r.text[:120]}")
    return None


# ── STEP 4: CATEGORY ───────────────────────────────────────────────
def get_or_create_category(name):
    """Get existing category ID or create it."""
    spinner(f"Looking up category '{name}'...")

    r = requests.get(
        f"{API_BASE}/categories",
        params={"search": name, "per_page": 50},
        headers=wp_headers(), timeout=15,
    )
    if r.status_code == 200:
        for cat in r.json():
            api_name = cat.get("name", "").replace("&amp;", "&").replace("&#038;", "&")
            if api_name.lower() == name.lower():
                print(f"  ✓ Category '{name}' exists (id={cat['id']})")
                return cat["id"]

    r = requests.post(
        f"{API_BASE}/categories",
        headers=wp_headers(),
        data=json.dumps({"name": name}),
        timeout=15,
    )

    if r.status_code in (200, 201):
        cat_id = r.json()["id"]
        print(f"  ✓ Category '{name}' created (id={cat_id})")
        return cat_id

    # Handle 400 term_exists
    if r.status_code == 400:
        try:
            err = r.json()
            if err.get("code") == "term_exists":
                existing_id = err.get("data", {}).get("term_id")
                if existing_id:
                    print(f"  ✓ Category '{name}' already exists (id={existing_id})")
                    return int(existing_id)
        except Exception:
            pass

    print(f"  ⚠ Could not get/create category: {r.status_code}")
    return None


# ── STEP 5: CREATE POST ────────────────────────────────────────────
def create_post(title, content, category_id, media_id):
    """Push the post to WordPress."""
    spinner("Publishing post to WordPress...")

    # Build a clean excerpt from the first paragraph
    excerpt = re.sub(r'<[^>]+>', '', content)[:220].strip()
    if not excerpt.endswith('.'):
        excerpt = excerpt.rsplit(' ', 1)[0] + '...'

    payload = {
        "title":   title,
        "content": content,
        "excerpt": excerpt,
        "status":  "publish",
        "slug":    slugify(title),
    }
    if category_id: payload["categories"]     = [category_id]
    if media_id:    payload["featured_media"] = media_id

    r = requests.post(
        f"{API_BASE}/posts",
        headers=wp_headers(),
        data=json.dumps(payload),
        timeout=30,
    )

    if r.status_code in (200, 201):
        post = r.json()
        return post["id"], post.get("link", "")

    return None, f"Error {r.status_code}: {r.text[:150]}"


# ── STEP 6: TEST CONNECTION ────────────────────────────────────────
def test_connection():
    spinner("Checking WordPress connection...")
    try:
        r = requests.get(f"{API_BASE}/users/me", headers=wp_headers(), timeout=15)
        if r.status_code == 200:
            name = r.json().get("name", "")
            print(f"  ✓ Connected to WordPress as: '{name}'")
            return True

        if r.status_code in (401, 403):
            print(f"  ✗ Authentication failed ({r.status_code}) — Bearer token has expired")
            show_token_help()
            return False

        print(f"  ✗ Unexpected response ({r.status_code}): {r.text[:120]}")
        return False

    except requests.exceptions.ConnectionError:
        print("  ✗ No internet connection — check your network and try again")
        return False
    except Exception as e:
        print(f"  ✗ Connection error: {e}")
        return False


# ── MAIN ───────────────────────────────────────────────────────────
def run():
    # 1. Get input
    title, category = get_user_input()

    print("\n" + "─" * 60)
    print("  Creating your post...\n")

    # 2. Test connection
    if not test_connection():
        print()
        new_token = input("  Paste a new Bearer token to retry (or press Enter to exit): ").strip()
        if new_token:
            global BEARER_TOKEN
            BEARER_TOKEN = new_token
            print()
            if not test_connection():
                print("  Still failing — check the token and try again.")
                sys.exit(1)
        else:
            sys.exit(1)

    # 3. Generate content
    content = generate_content(title, category)

    # 4. Fetch + upload image
    query           = build_pexels_query(title, category)
    img_bytes, mime = fetch_pexels_image(query)
    media_id        = upload_image(img_bytes, mime, title) if img_bytes else None

    # 5. Get/create category
    cat_id = get_or_create_category(category)

    # 6. Create post
    post_id, result = create_post(title, content, cat_id, media_id)

    print("\n" + "=" * 60)
    if post_id:
        print(f"  ✅ Post published successfully!\n")
        print(f"  Title:    {title}")
        print(f"  Category: {category}")
        print(f"  URL:      {result}")
        print(f"  Edit:     https://wordpress.com/post/{WP_SITE}/{post_id}")
    else:
        print(f"  ✗ Post creation failed: {result}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run()
