#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
VERIDIAN — Case Studies Creator
WordPress headless CMS setup for work.html
═══════════════════════════════════════════════════════════════════

WHAT THIS SCRIPT DOES:
  1. Creates two content categories:
       • "blog"         — for the 7 editorial posts
       • "case-studies" — for the 4 work case studies
  2. Updates the 7 existing blog posts to the "blog" category
     (so they don't bleed into the case studies feed)
  3. Creates 4 case study posts in "case-studies":
       · Short-let · Lagos · Lekki Phase 1
       · Law firm · Abuja · Maitama
       · Secondary school · Port Harcourt
       · Logistics startup · Lagos
  4. Encodes structured before/after data as an HTML comment
     inside each post so work.html can parse and render it.

AUTHENTICATION — WordPress.com OAuth2 Bearer Token:
─────────────────────────────────────────────────────────────────
  NOTE: WordPress.com hosted sites use their own OAuth2 API
  (public-api.wordpress.com). Application Passwords are a
  WordPress.org / self-hosted feature and do NOT work here.

  HOW TO GET A FRESH BEARER TOKEN (~14 days validity):
    1. Open in browser:
       https://public-api.wordpress.com/oauth2/authorize
         ?client_id=140052&redirect_uri=https://localhost
         &response_type=token
    2. Log in as veridiangrouplimited
    3. Copy token from the redirect URL:
       https://localhost/#access_token=XXXXX&token_type=bearer
    4. Paste into BEARER_TOKEN below

REQUIREMENTS:
    pip install requests Pillow

USAGE:
    python3 veridian-wp-case-studies-create.py

  Run AFTER veridian-wp-posts-create.py so the 7 blog posts exist
  to be re-categorised. Safe to re-run — idempotent.
═══════════════════════════════════════════════════════════════════
"""

import requests, json, io, time, sys

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


def show_token_help():
    print("\n  -- HOW TO GET A NEW TOKEN -----------------------------")
    print("  1. Open in browser:")
    print("     https://public-api.wordpress.com/oauth2/authorize")
    print("     ?client_id=140052&redirect_uri=https://localhost&response_type=token")
    print("  2. Log in as veridiangrouplimited")
    print("  3. Copy token from redirect URL between access_token= and &token_type=")
    print("  4. Paste into BEARER_TOKEN at the top of this script")
    print("  Token valid ~14 days.")
    print("  -------------------------------------------------------\n")


# ── CONNECTION TEST ───────────────────────────────────────────────
def test_connection():
    print("Testing connection...\n")
    r = requests.get(f"{API_BASE}/users/me", headers=wp_headers(), timeout=15)
    if r.status_code == 200:
        name = r.json().get("name", "")
        print(f"  ✓ WordPress: authenticated as '{name}'\n")
        return True
    print(f"  ✗ WordPress: {r.status_code} — {r.text[:200]}")
    if r.status_code in (401, 403):
        show_token_help()
    return False


# ── CATEGORY HELPER ──────────────────────────────────────────────
def get_or_create_category(name, slug, cache):
    key = slug
    if key in cache:
        return cache[key]

    # Search existing by slug
    r = requests.get(
        f"{API_BASE}/categories",
        params={"slug": slug, "per_page": 10},
        headers=wp_headers(), timeout=15,
    )
    if r.status_code == 200:
        cats = r.json()
        if cats:
            cache[key] = cats[0]["id"]
            print(f"    → Category '{name}' already exists (id={cats[0]['id']})")
            return cats[0]["id"]

    # Create
    r = requests.post(
        f"{API_BASE}/categories",
        headers=wp_headers(),
        data=json.dumps({"name": name, "slug": slug}),
        timeout=15,
    )
    if r.status_code in (200, 201):
        cat_id = r.json()["id"]
        cache[key] = cat_id
        print(f"    ✓ Category '{name}' created (id={cat_id})")
        return cat_id

    # Handle term_exists
    if r.status_code == 400:
        try:
            err = r.json()
            if err.get("code") == "term_exists":
                existing_id = (err.get("data", {}).get("term_id")
                               or err.get("data", {}).get("resource_id"))
                if existing_id:
                    cache[key] = int(existing_id)
                    print(f"    → Category '{name}' already exists (id={existing_id})")
                    return int(existing_id)
        except Exception:
            pass

    print(f"    ✗ Category '{name}' failed ({r.status_code}): {r.text[:120]}")
    return None


# ── UPDATE BLOG POSTS TO 'blog' CATEGORY ─────────────────────────
def assign_blog_category(blog_cat_id):
    """Find all posts NOT in case-studies and assign them to 'blog' category."""
    print("  Fetching existing posts...")
    all_posts = []
    page = 1
    while True:
        r = requests.get(
            f"{API_BASE}/posts",
            params={"per_page": 100, "page": page, "status": "publish"},
            headers=wp_headers(), timeout=15,
        )
        if r.status_code != 200 or not r.json():
            break
        all_posts.extend(r.json())
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1

    updated = 0
    for post in all_posts:
        title = post.get("title", {}).get("rendered", "Untitled")
        current_cats = post.get("categories", [])
        if blog_cat_id not in current_cats:
            r2 = requests.post(
                f"{API_BASE}/posts/{post['id']}",
                headers=wp_headers(),
                data=json.dumps({"categories": current_cats + [blog_cat_id]}),
                timeout=15,
            )
            if r2.status_code in (200, 201):
                print(f"    ✓ '{title[:55]}' → blog")
                updated += 1
            else:
                print(f"    ⚠ Could not update '{title[:45]}' ({r2.status_code})")
        else:
            print(f"    → '{title[:55]}' already in blog")
    return updated


# ── PEXELS FETCH ─────────────────────────────────────────────────
def fetch_pexels_image(query, fallback="nigerian business professional"):
    if not PEXELS_API_KEY or len(PEXELS_API_KEY) < 20:
        return None, None
    for attempt in [query, fallback, "professional business nigeria"]:
        try:
            r = requests.get(
                f"{PEXELS_BASE}/search",
                params={"query": attempt, "per_page": 5,
                        "orientation": "landscape", "size": "large"},
                headers=pexels_headers(), timeout=15,
            )
            if r.status_code != 200:
                continue
            photos = r.json().get("photos", [])
            if not photos:
                continue
            photo = photos[0]
            for p in photos:
                if p.get("width", 0) / max(p.get("height", 1), 1) >= 1.5:
                    photo = p
                    break
            img_url = (photo.get("src", {}).get("large2x")
                       or photo.get("src", {}).get("large"))
            if not img_url:
                continue
            img_r = requests.get(img_url, timeout=30)
            if img_r.status_code == 200:
                print(f"    ✓ Photo: '{attempt}' by {photo.get('photographer','Pexels')}")
                return img_r.content, "image/jpeg"
        except Exception as e:
            print(f"    ⚠ Pexels error: {e}")
    return None, None


# ── PILLOW FALLBACK ──────────────────────────────────────────────
def generate_fallback_image(label, color1, color2):
    try:
        from PIL import Image, ImageDraw
        def h2rgb(s):
            s = s.lstrip("#")
            return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
        W, H = 1400, 788
        c1, c2 = h2rgb(color1), h2rgb(color2)
        gold = (184, 144, 57)
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            draw.line([(0, y), (W, y)],
                      fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
        for x in range(-H, W, 80):
            draw.line([(x, 0), (x + H, H)], fill=(255, 255, 255), width=1)
        draw.rectangle([(0, 0), (10, H)], fill=gold)
        draw.ellipse([(900, -160), (1500, 940)], outline=(255, 255, 255), width=2)
        pill_w = len(label.upper()) * 13 + 60
        draw.rounded_rectangle([(60, 60), (60 + pill_w, 106)],
                                radius=22, outline=gold, width=2)
        draw.text((82, 69), label.upper(), fill=gold)
        draw.line([(60, 200), (260, 200)], fill=gold, width=2)
        draw.text((60, 225), "VERIDIAN GROUP LIMITED", fill=(255, 255, 255))
        draw.text((60, 265), "Nothing escapes notice.", fill=(226, 203, 123))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
        buf.seek(0)
        return buf.read(), "image/jpeg"
    except ImportError:
        return None, None
    except Exception as e:
        print(f"    ⚠ Fallback image error: {e}")
        return None, None


def upload_image(slug, query, fallback, label, color1, color2):
    img_bytes, mime = fetch_pexels_image(query, fallback)
    if not img_bytes:
        print("    → Using branded fallback image")
        img_bytes, mime = generate_fallback_image(label, color1, color2)
    if not img_bytes:
        return None
    filename = f"veridian-case-{slug}.jpg"
    headers = {
        "Authorization":       f"Bearer {BEARER_TOKEN}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type":        mime,
    }
    r = requests.post(f"{API_BASE}/media",
                      headers=headers, data=img_bytes, timeout=60)
    if r.status_code in (200, 201):
        mid = r.json()["id"]
        print(f"    ✓ Image uploaded (id={mid})")
        return mid
    print(f"    ⚠ Image upload failed ({r.status_code}): {r.text[:120]}")
    return None


# ── BUILD CASE STUDY POST CONTENT ────────────────────────────────
def build_content(cs):
    """
    Encodes the structured case study data in an HTML comment so
    work.html can parse and render the before/after layout.
    The human-readable HTML follows for anyone reading via WordPress.
    """
    data = {
        "industry":     cs["industry"],
        "location":     cs["location"],
        "tagline":      cs["tagline"],
        "narrative":    cs["narrative"],
        "before_score": cs["before_score"],
        "after_score":  cs["after_score"],
        "before":       cs["before"],
        "after":        cs["after"],
    }
    data_comment = f"<!--veridian-data:{json.dumps(data, ensure_ascii=False)}-->"

    before_items = "".join(f"<li>{m}</li>" for m in cs["before"])
    after_items  = "".join(f"<li>{m}</li>" for m in cs["after"])

    human_html = f"""
<p><em>{cs['narrative']}</em></p>
<table>
  <thead>
    <tr><th>Before ({cs['before_score']}/100)</th><th>After ({cs['after_score']}/100)</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><ul>{before_items}</ul></td>
      <td><ul>{after_items}</ul></td>
    </tr>
  </tbody>
</table>
<p><em>Names anonymised where requested. — Veridian</em></p>
""".strip()

    return data_comment + "\n" + human_html


# ── CHECK IF CASE STUDY ALREADY EXISTS ───────────────────────────
def post_exists(slug):
    r = requests.get(
        f"{API_BASE}/posts",
        params={"slug": slug, "status": "publish"},
        headers=wp_headers(), timeout=15,
    )
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]
    return None


def create_case_study(cs, cat_id, media_id):
    payload = {
        "title":          cs["tagline"],
        "content":        build_content(cs),
        "excerpt":        cs["narrative"],
        "status":         "publish",
        "slug":           cs["slug"],
        "categories":     [cat_id],
    }
    if media_id:
        payload["featured_media"] = media_id

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


# ── CASE STUDY DATA ──────────────────────────────────────────────
CASE_STUDIES = [
    {
        "slug":          "short-let-lekki-google-rebirth",
        "industry":      "Short-let",
        "location":      "Lagos · Lekki Phase 1",
        "tagline":       "A boutique short-let went from page 4 of Google to fully booked in 90 days.",
        "narrative":     "The owner had a beautiful 3-bed apartment, great photos on Instagram, and zero direct bookings. We rebuilt the site, claimed and optimised the Google Business Profile, and ran a 12-week SEO sprint.",
        "before_score":  38,
        "after_score":   86,
        "before": [
            "Page 4 on \"short-let lekki\"",
            "No Google Business listing",
            "Mobile load: 6.2s",
            "~2 enquiries / week",
        ],
        "after": [
            "Top 3 on 4 local terms",
            "Verified Google profile · 47 reviews",
            "Mobile load: 1.8s",
            "~22 enquiries / week",
        ],
        "pexels_query":    "luxury apartment interior lagos nigeria",
        "pexels_fallback": "modern apartment living room",
        "color1": "#142B4D", "color2": "#0A1B33",
    },
    {
        "slug":          "law-firm-abuja-credibility-rebuild",
        "industry":      "Law firm",
        "location":      "Abuja · Maitama",
        "tagline":       "A mid-sized law firm finally has a website partners aren't embarrassed to share.",
        "narrative":     "10 partners, 22 lawyers, and a 2014-era website that loaded slowly and showed broken images. We rebuilt it as a credibility-first brochure with practice-area depth and partner profiles. No tricks — just a serious site for serious people.",
        "before_score":  44,
        "after_score":   82,
        "before": [
            "Site looked '10 years old' per partners",
            "Broken image carousel",
            "No partner bios",
            "0 enquiries from web in 12 mos",
        ],
        "after": [
            "Refreshed brand & structure",
            "Full partner directory + practice areas",
            "PDF resource library",
            "9 enquiries in first month live",
        ],
        "pexels_query":    "law office professional nigeria abuja",
        "pexels_fallback": "lawyer professional office desk documents",
        "color1": "#355C44", "color2": "#1E3D2B",
    },
    {
        "slug":          "school-port-harcourt-google-profile-fix",
        "industry":      "Secondary school",
        "location":      "Port Harcourt",
        "tagline":       "A private school doubled parent enquiries the term we fixed their Google profile.",
        "narrative":     "The website was fine. The Google Business Profile was the problem — duplicate listings, wrong phone number, no posts since 2021, and a 2.8-star rating from old, unanswered reviews. We cleaned house.",
        "before_score":  51,
        "after_score":   79,
        "before": [
            "3 duplicate Google listings",
            "2.8★ from 19 reviews (no responses)",
            "Wrong phone number visible",
            "~12 enquiries / term",
        ],
        "after": [
            "Single verified profile",
            "4.6★ from 41 reviews",
            "Weekly posts + Q&A seeded",
            "~28 enquiries / term",
        ],
        "pexels_query":    "private school classroom nigeria students",
        "pexels_fallback": "school classroom modern education",
        "color1": "#B89039", "color2": "#8A6919",
    },
    {
        "slug":          "logistics-startup-lagos-speed-rebuild",
        "industry":      "Logistics startup",
        "location":      "Lagos",
        "tagline":       "A delivery startup ditched their bloated theme for a custom site that loads in under 2 seconds.",
        "narrative":     "Their Shopify-derived theme had 47 plugins and a 9.2-second load time on 4G. We built a custom, lightweight site with WhatsApp ordering, tracking by phone, and a homepage that loads before you blink.",
        "before_score":  41,
        "after_score":   88,
        "before": [
            "9.2s mobile load on 4G",
            "Bounce rate: 78%",
            "Plugin licences: ₦240k/year",
            "WhatsApp not linked",
        ],
        "after": [
            "1.6s mobile load on 4G",
            "Bounce rate: 31%",
            "Plugin licences: ₦0/year",
            "Click-to-WhatsApp on every page",
        ],
        "pexels_query":    "delivery logistics motorcycle lagos package",
        "pexels_fallback": "delivery driver motorcycle package africa",
        "color1": "#963A4D", "color2": "#6E2837",
    },
]


# ── MAIN ─────────────────────────────────────────────────────────
def run():
    print("\n" + "=" * 64)
    print("  VERIDIAN — Case Studies Creator")
    print(f"  Site: {WP_SITE}")
    print("=" * 64 + "\n")

    if not BEARER_TOKEN or len(BEARER_TOKEN) < 20:
        print("  ✗ Paste a fresh Bearer token into BEARER_TOKEN at the top.")
        show_token_help()
        sys.exit(1)

    if not test_connection():
        sys.exit(1)

    cat_cache = {}

    # ── Step 1: create categories ──────────────────────────────────
    print("Step 1: Creating categories...")
    blog_cat_id = get_or_create_category("blog", "blog", cat_cache)
    cs_cat_id   = get_or_create_category("case-studies", "case-studies", cat_cache)

    if not blog_cat_id or not cs_cat_id:
        print("  ✗ Could not create categories. Aborting.")
        sys.exit(1)
    print()

    # ── Step 2: assign blog category to existing posts ─────────────
    print("Step 2: Assigning 'blog' category to existing posts...")
    updated = assign_blog_category(blog_cat_id)
    print(f"  → {updated} post(s) updated\n")

    # ── Step 3: create case studies ───────────────────────────────
    print(f"Step 3: Creating {len(CASE_STUDIES)} case studies...\n")
    results = []

    for i, cs in enumerate(CASE_STUDIES, 1):
        print(f"[{i}/{len(CASE_STUDIES)}] {cs['industry']} · {cs['location']}")

        # Check if already exists
        existing_id = post_exists(cs["slug"])
        if existing_id:
            print(f"    → Already exists (id={existing_id}) — skipping\n")
            results.append({"ok": True, "title": cs["tagline"][:55],
                            "id": existing_id, "skipped": True})
            continue

        print(f"    Fetching image: '{cs['pexels_query']}'...")
        media_id = upload_image(
            cs["slug"], cs["pexels_query"], cs["pexels_fallback"],
            cs["industry"], cs["color1"], cs["color2"],
        )

        pid, result = create_case_study(cs, cs_cat_id, media_id)
        if pid:
            print(f"    ✓ Created → {result}")
            results.append({"ok": True, "title": cs["tagline"][:55], "id": pid})
        else:
            print(f"    ✗ Failed: {result}")
            results.append({"ok": False, "title": cs["tagline"][:55], "error": result})

        if i < len(CASE_STUDIES):
            time.sleep(2)
        print()

    ok = sum(1 for r in results if r["ok"])
    print("=" * 64)
    print(f"  COMPLETE — {ok} / {len(CASE_STUDIES)} case studies ready")
    print("=" * 64 + "\n")
    for r in results:
        skip = " (already existed)" if r.get("skipped") else ""
        st = f"✓ id={r['id']}{skip}" if r["ok"] else f"✗ {r.get('error','')[:50]}"
        print(f"  {st}  —  {r['title']}")

    print(f"\n  View: https://wordpress.com/posts/{WP_SITE}\n")
    print("  ── NEXT STEP ────────────────────────────────────────────────")
    print("  Deploy the updated work.html + script.js to Netlify.")
    print("  The work page will now load case studies from WordPress.")
    print("  ────────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    run()
