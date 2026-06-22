#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
VERIDIAN — WordPress Post Cleaner
═══════════════════════════════════════════════════════════════════
Deletes ALL existing posts on the Veridian WordPress blog before
the bulk-upload script populates the site with the default seven.

REQUIREMENTS:  pip install requests

USAGE:
  Step 1 — Run this script first:
    python veridian-wp-clean-posts.py

  Step 2 — Then run the post creator:
    python veridian-wp-posts-create.py
═══════════════════════════════════════════════════════════════════
"""

import requests, json, sys, time

# ── CONFIGURATION ─────────────────────────────────────────────────
WP_SITE      = "255358071"
WP_DOMAIN    = "veridiangrouplimited.wordpress.com"
# ── Bearer token (expires ~14 days — regenerate at the URL below)
# https://public-api.wordpress.com/oauth2/authorize?client_id=140052&redirect_uri=https://localhost&response_type=token
BEARER_TOKEN = "7nr(4rp5B$tNvdipxUAhO2y82ppDy(kl(7N#M$ApU)a@PqFY7ETE3eLlr4Jh2wij"
# ──────────────────────────────────────────────────────────────────

API_BASE = f"https://public-api.wordpress.com/wp/v2/sites/{WP_SITE}"


def auth():
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def get_all_posts():
    """Fetch all posts across all pages and all statuses."""
    all_posts = []
    page = 1

    while True:
        r = requests.get(
            f"{API_BASE}/posts",
            params={
                "per_page": 100,
                "page":     page,
                "status":   "publish,draft,pending,private,future",
            },
            headers=auth(),
            timeout=15,
        )

        if r.status_code == 200:
            posts = r.json()
            if not posts:
                break
            all_posts.extend(posts)
            print(f"  Found {len(posts)} posts on page {page}")

            total_pages = int(r.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break
            page += 1

        elif r.status_code == 400:
            break
        else:
            print(f"  ⚠ Error fetching posts ({r.status_code}): {r.text[:120]}")
            break

    return all_posts


def delete_post(post_id, title):
    """Permanently delete a post (bypass trash)."""
    r = requests.delete(
        f"{API_BASE}/posts/{post_id}",
        params={"force": True},
        headers=auth(),
        timeout=15,
    )
    if r.status_code in (200, 201):
        print(f"  ✓ Deleted: {title[:60]}")
        return True
    print(f"  ✗ Failed to delete '{title[:50]}' ({r.status_code}): {r.text[:80]}")
    return False


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

def run():
    print("\n" + "=" * 64)
    print("  VERIDIAN — WordPress Post Cleaner")
    print(f"  Site: {WP_SITE}")
    print("=" * 64 + "\n")

    print("Fetching all existing posts...")
    posts = get_all_posts()

    if not posts:
        print("\n  ✓ No posts found — WordPress is already empty.")
        print("  You can now run veridian-wp-posts-create.py\n")
        return

    print(f"\n  Found {len(posts)} post(s) to delete.\n")

    print("Posts that will be PERMANENTLY deleted:")
    for p in posts:
        title  = p.get("title", {}).get("rendered", "Untitled")
        status = p.get("status", "")
        print(f"  • [{status}] {title[:65]}")

    print(f"\n  ⚠ This will PERMANENTLY delete all {len(posts)} post(s).")
    print("  This cannot be undone.\n")

    confirm = input("  Type  YES  to confirm deletion: ").strip()
    if confirm != "YES":
        print("\n  Cancelled — no posts were deleted.\n")
        return

    print(f"\nDeleting {len(posts)} posts...\n")
    deleted, failed = 0, 0

    for i, post in enumerate(posts, 1):
        post_id = post["id"]
        title   = post.get("title", {}).get("rendered", "Untitled")
        print(f"  [{i}/{len(posts)}] ", end="")

        if delete_post(post_id, title):
            deleted += 1
        else:
            failed += 1

        if i < len(posts):
            time.sleep(0.5)   # courtesy pause to avoid rate limiting

    print(f"\n{'=' * 64}")
    print(f"  DONE — {deleted} deleted · {failed} failed")
    print(f"{'=' * 64}\n")

    if failed == 0:
        print("  ✓ All posts cleared.")
        print("  → Now run: python veridian-wp-posts-create.py\n")
    else:
        print(f"  ⚠ {failed} post(s) could not be deleted.")
        if failed == len(posts):
            show_token_help()


if __name__ == "__main__":
    run()
