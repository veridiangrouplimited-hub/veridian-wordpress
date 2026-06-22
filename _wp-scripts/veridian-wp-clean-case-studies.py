#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
VERIDIAN — Case Studies Cleaner
═══════════════════════════════════════════════════════════════════

Deletes ONLY posts in the "case-studies" category.
Blog posts are never touched.

Safe to run before re-seeding case studies with:
  python3 veridian-wp-case-studies-create.py

REQUIREMENTS:  pip install requests

USAGE:
  python3 veridian-wp-clean-case-studies.py

AUTHENTICATION — WordPress.com OAuth2 Bearer Token:
─────────────────────────────────────────────────────────────────
  HOW TO GET A FRESH BEARER TOKEN (~14 days validity):
    1. Open in browser:
       https://public-api.wordpress.com/oauth2/authorize
         ?client_id=140052&redirect_uri=https://localhost
         &response_type=token
    2. Log in as veridiangrouplimited
    3. Copy token from the redirect URL:
       https://localhost/#access_token=XXXXX&token_type=bearer
    4. Paste into BEARER_TOKEN below
═══════════════════════════════════════════════════════════════════
"""

import requests, json, sys, time

# ── CONFIGURATION ─────────────────────────────────────────────────
WP_SITE      = "255358071"
WP_DOMAIN    = "veridiangrouplimited.wordpress.com"
# ── Bearer token (expires ~14 days — regenerate at the URL above)
BEARER_TOKEN = "7nr(4rp5B$tNvdipxUAhO2y82ppDy(kl(7N#M$ApU)a@PqFY7ETE3eLlr4Jh2wij"
# ──────────────────────────────────────────────────────────────────

API_BASE = f"https://public-api.wordpress.com/wp/v2/sites/{WP_SITE}"


def auth():
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def show_token_help():
    print("\n  -- HOW TO GET A NEW TOKEN -----------------------------")
    print("  1. Open in browser:")
    print("     https://public-api.wordpress.com/oauth2/authorize")
    print("     ?client_id=140052&redirect_uri=https://localhost&response_type=token")
    print("  2. Log in as veridiangrouplimited")
    print("  3. Copy token between access_token= and &token_type= in the redirect URL")
    print("  4. Paste into BEARER_TOKEN at the top of this script")
    print("  Token valid ~14 days.")
    print("  -------------------------------------------------------\n")


def get_category_id(slug):
    """Resolve category ID by slug."""
    r = requests.get(
        f"{API_BASE}/categories",
        params={"slug": slug, "per_page": 10},
        headers=auth(), timeout=15,
    )
    if r.status_code == 200:
        cats = r.json()
        if cats:
            return cats[0]["id"], cats[0].get("name", slug)
    return None, None


def get_posts_in_category(cat_id):
    """Fetch all published posts in a specific category."""
    all_posts = []
    page = 1
    while True:
        r = requests.get(
            f"{API_BASE}/posts",
            params={
                "categories": cat_id,
                "per_page":   100,
                "page":       page,
                "status":     "publish,draft,pending,private,future",
            },
            headers=auth(), timeout=15,
        )
        if r.status_code != 200 or not r.json():
            break
        all_posts.extend(r.json())
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    return all_posts


def delete_post(post_id, title):
    r = requests.delete(
        f"{API_BASE}/posts/{post_id}",
        params={"force": True},
        headers=auth(), timeout=15,
    )
    if r.status_code in (200, 201):
        print(f"  ✓ Deleted: {title[:65]}")
        return True
    print(f"  ✗ Failed: '{title[:50]}' ({r.status_code}): {r.text[:80]}")
    return False


def run():
    print("\n" + "=" * 64)
    print("  VERIDIAN — Case Studies Cleaner")
    print(f"  Site: {WP_SITE}")
    print("  Scope: case-studies category only — blog posts untouched")
    print("=" * 64 + "\n")

    if not BEARER_TOKEN or len(BEARER_TOKEN) < 20:
        print("  ✗ Paste a fresh Bearer token into BEARER_TOKEN at the top.")
        show_token_help()
        sys.exit(1)

    # Verify auth
    print("Testing connection...")
    r = requests.get(f"{API_BASE}/users/me", headers=auth(), timeout=15)
    if r.status_code != 200:
        print(f"  ✗ Auth failed ({r.status_code}): {r.text[:120]}")
        if r.status_code in (401, 403):
            show_token_help()
        sys.exit(1)
    print(f"  ✓ Authenticated as '{r.json().get('name', '')}'\n")

    # Resolve case-studies category
    print("Finding case-studies category...")
    cat_id, cat_name = get_category_id("case-studies")
    if not cat_id:
        print("  ✓ No 'case-studies' category found — nothing to delete.\n")
        return
    print(f"  ✓ Found '{cat_name}' (id={cat_id})\n")

    # Fetch posts in that category
    print("Fetching case study posts...")
    posts = get_posts_in_category(cat_id)

    if not posts:
        print("  ✓ No case study posts found — already empty.\n")
        print("  → Ready to run: python3 veridian-wp-case-studies-create.py\n")
        return

    print(f"\n  Found {len(posts)} case study post(s) to delete:\n")
    for p in posts:
        title  = p.get("title", {}).get("rendered", "Untitled")
        status = p.get("status", "")
        print(f"  • [{status}] {title[:65]}")

    print(f"\n  ⚠ This will PERMANENTLY delete {len(posts)} case study post(s).")
    print("  Blog posts are not affected.")
    print("  This cannot be undone.\n")

    confirm = input("  Type  YES  to confirm: ").strip()
    if confirm != "YES":
        print("\n  Cancelled — nothing deleted.\n")
        return

    print(f"\nDeleting {len(posts)} post(s)...\n")
    deleted = failed = 0

    for i, post in enumerate(posts, 1):
        post_id = post["id"]
        title   = post.get("title", {}).get("rendered", "Untitled")
        print(f"  [{i}/{len(posts)}] ", end="")
        if delete_post(post_id, title):
            deleted += 1
        else:
            failed += 1
        if i < len(posts):
            time.sleep(0.5)

    print(f"\n{'=' * 64}")
    print(f"  DONE — {deleted} deleted · {failed} failed")
    print(f"{'=' * 64}\n")

    if failed == 0:
        print("  ✓ All case studies cleared.")
        print("  → Now run: python3 veridian-wp-case-studies-create.py\n")
    else:
        print(f"  ⚠ {failed} post(s) could not be deleted. Try refreshing your token.")
        show_token_help()


if __name__ == "__main__":
    run()
