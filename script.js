/* ==========================================================================
   Veridian Group Limited — script.js
   Mobile nav · theme toggle · scroll behaviour · reveal-on-scroll
   Animated counters · FAQ accordion · contact form · newsletter
   Interactive mini-audit tool · cookie banner · year stamp
   ========================================================================== */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    yearStamp();
    headerScrollState();
    mobileNav();
    themeToggle();
    smoothScroll();
    revealOnScroll();
    countersOnScroll();
    faqAccordion();
    updateBookingMonth();
    captureCampaignParams();
    personalizeForCampaign();
    contactForm();
    newsletterForm();
    cookieBanner();
    blogFilters();
    hydratePost();
    fetchCaseStudies();
    fetchBlogPosts();
    imageFallbacks();
  }

  /* ===== Year ===== */
  function yearStamp() {
    document.querySelectorAll("[data-year]").forEach(function (el) {
      el.textContent = new Date().getFullYear();
    });
  }

  /* ===== Header scroll state ===== */
  function headerScrollState() {
    var header = document.querySelector(".site-header");
    if (!header) return;
    var ticking = false;
    function update() {
      header.classList.toggle("scrolled", window.scrollY > 8);
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });
    update();
  }

  /* ===== Mobile navigation ===== */
  function mobileNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.querySelector(".site-nav");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    });

    // Close on link click
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      });
    });

    // Close on Escape
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      }
    });
  }

  /* ===== Theme toggle (light default, dark optional) ===== */
  function themeToggle() {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    var KEY = "veridian-theme";
    var saved = localStorage.getItem(KEY);
    if (saved === "dark") document.documentElement.setAttribute("data-theme", "dark");

    btn.addEventListener("click", function () {
      var isDark = document.documentElement.getAttribute("data-theme") === "dark";
      if (isDark) {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem(KEY, "light");
      } else {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem(KEY, "dark");
      }
    });
  }

  /* ===== Smooth in-page scroll ===== */
  function smoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
      link.addEventListener("click", function (e) {
        var href = this.getAttribute("href");
        if (href.length <= 1) return;
        var target = document.querySelector(href);
        if (!target) return;
        e.preventDefault();
        var top = target.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top: top, behavior: "smooth" });
      });
    });
  }

  /* ===== Reveal on scroll ===== */
  function revealOnScroll() {
    var els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window) || !els.length) {
      els.forEach(function (el) { el.classList.add("visible"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -50px 0px" });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ===== Animated counters ===== */
  function countersOnScroll() {
    var counters = document.querySelectorAll("[data-count-to]");
    if (!counters.length) return;

    function animate(el) {
      var target = parseFloat(el.getAttribute("data-count-to"));
      var decimals = parseInt(el.getAttribute("data-count-decimals") || "0", 10);
      var prefix = el.getAttribute("data-count-prefix") || "";
      var suffix = el.getAttribute("data-count-suffix") || "";
      var duration = 1600;
      var start = null;

      function step(ts) {
        if (!start) start = ts;
        var p = Math.min((ts - start) / duration, 1);
        // ease-out cubic
        var eased = 1 - Math.pow(1 - p, 3);
        var val = target * eased;
        el.textContent = prefix + val.toFixed(decimals) + suffix;
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }

    if (!("IntersectionObserver" in window)) {
      counters.forEach(animate);
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animate(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    counters.forEach(function (c) { io.observe(c); });
  }

  /* ===== FAQ accordion (close others when opening one) ===== */
  function faqAccordion() {
    var items = document.querySelectorAll(".faq-item");
    items.forEach(function (item) {
      item.addEventListener("toggle", function () {
        if (this.open) {
          items.forEach(function (other) {
            if (other !== item) other.removeAttribute("open");
          });
        }
      });
    });
  }

  /* ===== Campaign attribution =====
   * Captures UTM params + landing page + referrer on first arrival and
   * persists them for the session, so a form submitted three pages later
   * still carries the campaign that brought the visitor in. On submit we
   * inject these as hidden fields, making every Netlify lead attributable
   * to a specific cold-email campaign / industry / source.
   *
   * Cold-email link convention:
   *   https://veridian.ng/audit?utm_source=cold-email
   *     &utm_medium=email&utm_campaign=abuja-pharmacies-jun26&industry=pharmacy
   */
  var CAMPAIGN_KEY = "veridian-campaign";
  var CAMPAIGN_FIELDS = [
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "industry"
  ];

  function captureCampaignParams() {
    try {
      var params = new URLSearchParams(window.location.search);
      var existing = {};
      try { existing = JSON.parse(sessionStorage.getItem(CAMPAIGN_KEY) || "{}"); } catch (e) {}

      var sawAny = false;
      CAMPAIGN_FIELDS.forEach(function (key) {
        var val = params.get(key);
        if (val) { existing[key] = val.slice(0, 120); sawAny = true; }
      });

      // Record landing context once, on the first touch of the session
      if (!existing.landing_page) {
        existing.landing_page = window.location.pathname + window.location.search;
        existing.referrer = document.referrer || "direct";
        existing.first_seen = new Date().toISOString();
        sawAny = true;
      }

      if (sawAny) {
        sessionStorage.setItem(CAMPAIGN_KEY, JSON.stringify(existing));
      }
    } catch (e) { /* sessionStorage blocked — attribution is best-effort */ }
  }

  function getCampaignData() {
    try { return JSON.parse(sessionStorage.getItem(CAMPAIGN_KEY) || "{}"); }
    catch (e) { return {}; }
  }

  // Inject campaign data as hidden inputs just before a form is submitted.
  function attachCampaignFields(form) {
    var data = getCampaignData();
    Object.keys(data).forEach(function (key) {
      if (!data[key]) return;
      var existing = form.querySelector('input[name="' + key + '"]');
      if (existing) { existing.value = data[key]; return; }
      var input = document.createElement("input");
      input.type = "hidden";
      input.name = key;
      input.value = data[key];
      form.appendChild(input);
    });
  }

  /* ===== Landing-page personalization =====
   * Lets a cold email drop a prospect onto a page that speaks to *their*
   * industry. Any element with data-campaign-industry will have its text
   * swapped for the matching phrase when ?industry=… is present. Falls back
   * silently to the default copy when there's no param (e.g. organic visit),
   * so the page is always coherent.
   *
   * Markup example:
   *   <span data-campaign-industry
   *         data-default="Nigerian businesses">Nigerian businesses</span>
   */
  var INDUSTRY_LABELS = {
    pharmacy:     "pharmacies",
    pharmacies:   "pharmacies",
    school:       "schools",
    schools:      "schools",
    realestate:   "real-estate firms",
    "real-estate":"real-estate firms",
    property:     "property businesses",
    hotel:        "hotels",
    hospitality:  "hospitality businesses",
    clinic:       "clinics",
    hospital:     "clinics & hospitals",
    restaurant:   "restaurants",
    law:          "law firms",
    legal:        "law firms",
    logistics:    "logistics companies",
    retail:       "retail businesses",
    fashion:      "fashion brands",
    fintech:      "fintech startups"
  };

  function personalizeForCampaign() {
    var nodes = document.querySelectorAll("[data-campaign-industry]");
    if (!nodes.length) return;

    var data = getCampaignData();
    var raw = (data.industry || "").toLowerCase().trim();
    var label = INDUSTRY_LABELS[raw];

    nodes.forEach(function (el) {
      if (label) {
        el.textContent = label;
      } else if (el.getAttribute("data-default")) {
        el.textContent = el.getAttribute("data-default");
      }
    });
  }

  /* ===== Submit any form to Netlify Forms =====
   * Netlify intercepts POST to "/" when form has data-netlify="true" AND
   * a hidden form-name input. We use fetch() so we can keep the inline
   * success UX (no page reload). The form's existing markup is the source
   * of truth — we just bundle FormData as urlencoded body. Campaign
   * attribution fields are injected immediately before serialization.
   */
  function submitToNetlify(form) {
    attachCampaignFields(form);
    var data = new FormData(form);
    var body = new URLSearchParams(data).toString();
    return fetch("/", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body,
    });
  }

  /* ===== Dynamic booking month =====
   * Keeps "Now booking audits — Month YYYY" current without manual edits.
   * Shows the NEXT calendar month so it reads as forward-looking.
   * E.g. visiting in June → shows "July 2026"
   */
  function updateBookingMonth() {
    var el = document.getElementById("booking-month");
    if (!el) return;
    var months = [
      "January","February","March","April","May","June",
      "July","August","September","October","November","December"
    ];
    var now  = new Date();
    el.textContent = months[now.getMonth()] + " " + now.getFullYear();
  }
  function contactForm() {
    var form = document.querySelector("#contact-form");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = form.querySelector("button[type='submit']");
      var success = form.querySelector(".form-success");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Sending…";
      }
      submitToNetlify(form)
        .then(function (resp) {
          if (!resp.ok) throw new Error("HTTP " + resp.status);
          if (success) success.classList.add("show");
          form.reset();
        })
        .catch(function () {
          if (btn) btn.textContent = "Couldn't send — try WhatsApp?";
          // Keep button disabled briefly so the message is visible
          setTimeout(function () {
            if (btn) {
              btn.disabled = false;
              btn.textContent = "Send message";
            }
          }, 3000);
          return;
        })
        .finally(function () {
          if (btn && success && success.classList.contains("show")) {
            btn.disabled = false;
            btn.textContent = "Send message";
          }
        });
    });
  }

  /* ===== Newsletter ===== */
  function newsletterForm() {
    document.querySelectorAll(".newsletter-form, .footer-newsletter-mini form").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var btn = form.querySelector("button");
        var original = btn ? btn.textContent : "Subscribe";
        if (btn) {
          btn.disabled = true;
          btn.textContent = "Sending…";
        }
        submitToNetlify(form)
          .then(function (resp) {
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            if (btn) btn.textContent = "Thanks!";
            form.reset();
          })
          .catch(function () {
            if (btn) btn.textContent = "Try again";
          })
          .finally(function () {
            setTimeout(function () {
              if (btn) {
                btn.disabled = false;
                btn.textContent = original;
              }
            }, 2400);
          });
      });
    });
  }

  /* ===== Cookie banner ===== */
  function cookieBanner() {
    var banner = document.querySelector("#cookie-banner");
    if (!banner) return;
    var KEY = "veridian-cookie";
    if (localStorage.getItem(KEY)) return;

    setTimeout(function () { banner.classList.add("show"); }, 1500);

    banner.querySelector(".cookie-accept").addEventListener("click", function () {
      localStorage.setItem(KEY, "accepted");
      banner.classList.remove("show");
    });
    banner.querySelector(".cookie-decline").addEventListener("click", function () {
      localStorage.setItem(KEY, "declined");
      banner.classList.remove("show");
    });
  }
  /* ===== Blog category filter ===== */
  function blogFilters() {
    var grid  = document.querySelector(".blog-grid");
    var chips = document.querySelectorAll(".blog-chip");
    var cards = document.querySelectorAll(".blog-grid .blog-card");
    if (!grid || !cards.length) return;

    // Always sync chip counts from current DOM cards
    // (covers both the static-HTML fallback and the post-WP-load path)
    var tally = {}, total = 0;
    cards.forEach(function (card) {
      var cat = (card.getAttribute("data-category") || "").trim();
      if (cat) { tally[cat] = (tally[cat] || 0) + 1; }
      total++;
    });

    // Only rebuild if counts differ from what's in the DOM
    var allChip = document.querySelector(".blog-chip[data-cat='all'] .blog-chip-count");
    if (allChip && parseInt(allChip.textContent, 10) !== total) {
      // counts are stale — rebuild
      var container = document.querySelector(".blog-filters");
      if (container) {
        var cats = Object.keys(tally).sort();
        var html = '<button class="blog-chip active" data-cat="all">All <span class="blog-chip-count">' + total + '</span></button>';
        cats.forEach(function (cat) {
          html += '<button class="blog-chip" data-cat="' + cat + '">' + cat +
                  ' <span class="blog-chip-count">' + tally[cat] + '</span></button>';
        });
        container.innerHTML = html;
      }
    }

    // Wire click handlers on (possibly new) chips
    document.querySelectorAll(".blog-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var cat = chip.getAttribute("data-cat");
        document.querySelectorAll(".blog-chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        document.querySelectorAll(".blog-grid .blog-card").forEach(function (card) {
          var cardCat = card.getAttribute("data-category") ||
                        (card.querySelector(".blog-card-category") || {}).textContent || "";
          card.classList.toggle("is-hidden", cat !== "all" && cardCat.trim() !== cat);
        });
      });
    });
  }
  /* ===== WordPress headless CMS =====
   * Posts are pulled live from the Veridian Group WordPress blog (public REST API,
   * no auth needed for reading published posts). The static manifest stays as
   * a graceful fallback for when WP is slow/down/firewalled.
   *
   * Site: veridiangrouplimited.wordpress.com  (id: 255358071)
   * Endpoints used:
   *   GET /sites/{site}/posts?_embed&per_page=20  → list (blog index)
   *   GET /sites/{site}/posts?slug={slug}&_embed  → single post (hydration)
   */
  var WP_SITE = "veridiangrouplimited.wordpress.com";
  var WP_API  = "https://public-api.wordpress.com/wp/v2/sites/" + WP_SITE;
  var WP_TIMEOUT_MS = 6000;   // keep page snappy — fall back if WP is slow

  function wpFetch(path) {
    var controller = new AbortController();
    var t = setTimeout(function () { controller.abort(); }, WP_TIMEOUT_MS);
    return fetch(WP_API + path, { signal: controller.signal })
      .then(function (r) {
        clearTimeout(t);
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      });
  }

  function stripTags(html) {
    var tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return (tmp.textContent || "").trim();
  }

  function formatDate(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    if (isNaN(d)) return "";
    var months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"];
    return d.getDate() + " " + months[d.getMonth()] + " " + d.getFullYear();
  }

  function estimateReadTime(html) {
    var text = stripTags(html);
    var words = text ? text.split(/\s+/).length : 0;
    var mins = Math.max(1, Math.round(words / 220));
    return mins + " min read";
  }

  function wpToPost(wp) {
    var emb   = wp._embedded || {};
    var media = (emb["wp:featuredmedia"] || [])[0] || null;
    var terms = (emb["wp:term"] || [])[0] || [];
    return {
      slug:      wp.slug,
      title:     stripTags(wp.title && wp.title.rendered),
      excerpt:   stripTags(wp.excerpt && wp.excerpt.rendered).replace(/\s+/g, " "),
      content:   (wp.content && wp.content.rendered) || "",
      category:  (terms[0] && terms[0].name) ? stripTags(terms[0].name) : "",
      date:      formatDate(wp.date),
      read_time: estimateReadTime(wp.content && wp.content.rendered),
      image:     media ? media.source_url : "",
      image_alt: media ? (media.alt_text || "") : "",
      featured:  !!wp.sticky,
    };
  }

  /* ===== Single post hydration ===== */
  function hydratePost() {
    var manifestEl = document.getElementById("posts-manifest");
    if (!manifestEl) return;   // not on a post page

    var manifest;
    try { manifest = JSON.parse(manifestEl.textContent); }
    catch (e) { manifest = {}; }

    var params = new URLSearchParams(window.location.search);
    var slug = params.get("post");
    if (!slug) return;

    // Try WordPress first, fall back to inline manifest
    wpFetch("/posts?slug=" + encodeURIComponent(slug) + "&_embed")
      .then(function (data) {
        if (!data || !data.length) throw new Error("not found");
        return wpToPost(data[0]);
      })
      .catch(function () {
        return manifest[slug] || null;   // fallback
      })
      .then(function (post) {
        if (!post) return;
        renderPost(post, slug, manifest);
      });
  }

  function renderPost(post, slug, manifest) {
    // Swap any element with [data-field] matching a post property
    document.querySelectorAll("[data-field]").forEach(function (el) {
      var field = el.getAttribute("data-field");
      if (!(field in post)) return;
      var value = post[field];
      if (!value) return;
      if (el.tagName === "IMG") {
        var fb = (manifest[slug] && manifest[slug].image_fallback);
        if (fb) el.setAttribute("data-fallback", fb);
        el.setAttribute("src", value);
        if (post.image_alt) el.setAttribute("alt", post.image_alt);
      } else {
        el.textContent = value;
      }
    });

    // Inject WP article body if present (note: this is WP's content.rendered HTML)
    if (post.content) {
      var bodyHost = document.getElementById("post-content");
      if (bodyHost) {
        bodyHost.innerHTML = post.content;
        // Real content arrived — hide the template-mode note
        var note = document.getElementById("post-template-note");
        if (note) note.hidden = true;
      }
    } else {
      // No WP body (fallback case): show template note
      var note2 = document.getElementById("post-template-note");
      if (note2) note2.hidden = false;
    }

    // Browser tab + OG title
    if (post.title) document.title = post.title + " — Veridian";
    var ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle && post.title) ogTitle.setAttribute("content", post.title + " — Veridian");
    var ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc && post.excerpt) ogDesc.setAttribute("content", post.excerpt);
    var ogImage = document.querySelector('meta[property="og:image"]');
    if (ogImage && post.image) ogImage.setAttribute("content", post.image);

    // Wire dynamic share buttons now that post title/URL are known
    var postUrl   = encodeURIComponent(window.location.href);
    var postTitle = encodeURIComponent((post.title || "") + " — Veridian");
    var xBtn = document.querySelector('[aria-label="Share on Twitter"]');
    if (xBtn) {
      xBtn.setAttribute("href", "https://x.com/intent/tweet?text=" + postTitle + "&url=" + postUrl);
      xBtn.setAttribute("target", "_blank");
      xBtn.setAttribute("rel", "noopener");
      xBtn.setAttribute("aria-label", "Share on X");
    }
    var liBtn = document.querySelector('[aria-label="Share on LinkedIn"]');
    if (liBtn) {
      liBtn.setAttribute("href", "https://www.linkedin.com/shareArticle?mini=true&url=" + postUrl + "&title=" + postTitle);
      liBtn.setAttribute("target", "_blank");
      liBtn.setAttribute("rel", "noopener");
    }
    var waBtn = document.querySelector('[aria-label="Share on WhatsApp"]');
    if (waBtn) {
      waBtn.setAttribute("href", "https://wa.me/?text=" + postTitle + "%20" + postUrl);
    }

    // Refresh related-posts grid: hide any related card matching current slug
    var relatedGrid = document.getElementById("related-grid");
    if (relatedGrid && manifest) {
      var relatedCards = relatedGrid.querySelectorAll(".blog-card");
      var shownSlugs = [];
      var dupCard = null;
      relatedCards.forEach(function (c) {
        var s = c.getAttribute("data-post");
        if (s === slug) { dupCard = c; c.remove(); }
        else { shownSlugs.push(s); }
      });
      if (dupCard) {
        var allSlugs = Object.keys(manifest);
        var candidate = allSlugs.find(function (s) {
          return s !== slug && shownSlugs.indexOf(s) === -1;
        });
        if (candidate) {
          var rp = manifest[candidate];
          var rpIdx = allSlugs.indexOf(candidate) + 1;
          var numStr = String(rpIdx).padStart(2, "0");
          var html =
            '<a href="blog-post.html?post=' + candidate + '" class="blog-card" data-category="' + rp.category + '" data-post="' + candidate + '">' +
            '<span class="blog-card-watermark" aria-hidden="true">' + numStr + '</span>' +
            '<span class="blog-card-num"><sup>№</sup>' + numStr + '</span>' +
            '<span class="blog-card-rule" aria-hidden="true"></span>' +
            '<span class="blog-card-category">' + rp.category + '</span>' +
            '<h3>' + rp.title + '</h3>' +
            '<p>' + rp.excerpt + '</p>' +
            '<div class="blog-card-foot">' +
              '<span>' + rp.date + ' · ' + rp.read_time + '</span>' +
              '<span class="blog-card-link">Read &rarr;</span>' +
            '</div>' +
            '</a>';
          relatedGrid.insertAdjacentHTML("beforeend", html);
        }
      }
    }
  }

  /* ===== Case studies — live from WP headless =====
   * Mirrors the fetchBlogPosts 3-layer pattern:
   *   1. WordPress live  — /posts?categories={case-studies-cat-id}&_embed
   *   2. Static HTML     — existing work.html articles stay visible if WP fails
   *
   * Each WP post embeds the structured data in an HTML comment:
   *   <!--veridian-data:{...JSON...}-->
   * The parser extracts it and renders the before/after layout.
   */
  function fetchCaseStudies() {
    var grid = document.getElementById("case-studies-grid");
    if (!grid) return;   // only runs on work.html

    // Step 1: resolve the 'case-studies' category ID by slug
    wpFetch("/categories?slug=case-studies")
      .then(function (cats) {
        if (!Array.isArray(cats) || !cats.length) throw new Error("no cat");
        var catId = cats[0].id;
        return wpFetch("/posts?categories=" + catId + "&_embed&per_page=20");
      })
      .then(function (posts) {
        if (!Array.isArray(posts) || !posts.length) throw new Error("no posts");
        var studies = posts.map(parseCaseStudy).filter(Boolean);
        if (!studies.length) throw new Error("no parseable posts");
        renderCaseStudies(grid, studies);
      })
      .catch(function () {
        // Silent: static fallback articles in work.html stay visible
      });
  }

  function parseCaseStudy(wp) {
    var content = wp.content && wp.content.rendered || "";
    var m = content.match(/<!--veridian-data:([\s\S]*?)-->/);
    if (!m) return null;
    try {
      var data = JSON.parse(m[1]);
      // Attach featured image if available
      var media = wp._embedded && wp._embedded["wp:featuredmedia"]
                  && wp._embedded["wp:featuredmedia"][0];
      data.image     = media ? (media.source_url || "") : "";
      data.image_alt = media ? (media.alt_text || data.industry) : data.industry;
      return data;
    } catch (e) {
      return null;
    }
  }

  function renderCaseStudies(grid, studies) {
    var html = studies.map(function (cs) {
      var beforeItems = cs.before.map(function (m) {
        return "<li>" + escHtml(m) + "</li>";
      }).join("");
      var afterItems = cs.after.map(function (m) {
        return "<li>" + escHtml(m) + "</li>";
      }).join("");
      var imgHtml = cs.image
        ? '<img src="' + cs.image + '" alt="' + escAttr(cs.image_alt) + '" loading="lazy" />'
        : "";

      return (
        '<article class="case-detail reveal">' +
          '<div class="case-detail-head">' +
            '<span class="eyebrow eyebrow--sage">' +
              escHtml(cs.industry) + ' · ' + escHtml(cs.location) +
            '</span>' +
            '<h3>' + escHtml(cs.tagline) + '</h3>' +
            '<p style="max-width:60ch;margin-top:var(--s-3);margin-bottom:0;">' +
              escHtml(cs.narrative) +
            '</p>' +
          '</div>' +
          (cs.image
            ? '<div class="case-image" style="aspect-ratio:21/9;">' + imgHtml + '</div>'
            : '') +
          '<div class="case-detail-body">' +
            '<div class="case-detail-comparison">' +
              '<div class="case-side case-side--before">' +
                '<span class="case-side-label">Before</span>' +
                '<div class="case-side-score">' + cs.before_score + '<sup>/100</sup></div>' +
                '<ul>' + beforeItems + '</ul>' +
              '</div>' +
              '<div class="case-comparison-arrow">\u2192</div>' +
              '<div class="case-side case-side--after">' +
                '<span class="case-side-label">After</span>' +
                '<div class="case-side-score">' + cs.after_score + '<sup>/100</sup></div>' +
                '<ul>' + afterItems + '</ul>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</article>'
      );
    }).join("\n");

    grid.innerHTML = html;
    // Re-trigger reveal animation on newly rendered articles
    revealOnScroll();
  }

  function escHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function escAttr(s) { return escHtml(s); }

  /* ===== Blog index — live posts from WP ===== */
  function fetchBlogPosts() {
    var grid = document.querySelector(".blog-grid");
    if (!grid || document.getElementById("posts-manifest")) return;
    // Only run on the blog index (which has the .blog-grid but no posts-manifest)
    grid.classList.add("is-loading");

    // Resolve 'blog' category first so case studies are never mixed in
    wpFetch("/categories?slug=blog")
      .then(function (cats) {
        var catFilter = (Array.isArray(cats) && cats.length)
          ? "&categories=" + cats[0].id
          : "";
        return wpFetch("/posts?_embed&per_page=20" + catFilter);
      })
      .then(function (wpPosts) {
        if (!Array.isArray(wpPosts) || !wpPosts.length) throw new Error("no posts");
        renderBlogGrid(grid, wpPosts.map(wpToPost));
      })
      .catch(function () {
        // Silent: static fallback cards stay visible
        grid.classList.remove("is-loading");
      });
  }

  function renderBlogGrid(grid, posts) {
    // First post = featured (or sticky if any was sticky)
    var sticky = posts.filter(function (p) { return p.featured; });
    var ordered = sticky.length
      ? sticky.concat(posts.filter(function (p) { return !p.featured; }))
      : posts;

    var html = ordered.map(function (p, i) {
      var num = i + 1;
      var numStr = String(num).padStart(2, "0");
      var isFeatured = i === 0;
      var cls = isFeatured ? "blog-card is-featured" : "blog-card";
      var cta = isFeatured ? "Read the cover article" : "Read";
      var arrow = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>';
      return ''
        + '<a href="blog-post.html?post=' + p.slug + '" class="' + cls + '" data-category="' + p.category + '" data-post="' + p.slug + '">'
        +   '<span class="blog-card-watermark" aria-hidden="true">' + numStr + '</span>'
        +   '<span class="blog-card-num"><sup>№</sup>' + numStr + '</span>'
        +   '<span class="blog-card-rule" aria-hidden="true"></span>'
        +   '<span class="blog-card-category">' + p.category + '</span>'
        +   '<h3>' + p.title + '</h3>'
        +   '<p>' + p.excerpt + '</p>'
        +   '<div class="blog-card-foot">'
        +     '<span>' + p.date + ' · ' + p.read_time + '</span>'
        +     '<span class="blog-card-link">' + cta + ' ' + arrow + '</span>'
        +   '</div>'
        + '</a>';
    }).join("");

    grid.innerHTML = html;
    grid.classList.remove("is-loading");
    grid.classList.add("is-fresh");
    // Rebuild category chips from actual loaded posts, then rewire filters
    updateCategoryChips(ordered);
    blogFilters();
  }

  /* ===== Dynamic category chips =====
   * Rebuilds the filter pill row from the actual posts in play — whether those
   * come from WordPress live or the static manifest fallback. Hides categories
   * with zero posts, updates the "All" count to the real total.
   */
  function updateCategoryChips(posts) {
    var container = document.querySelector(".blog-filters");
    if (!container) return;

    // Tally posts per category
    var tally = {};
    posts.forEach(function (p) {
      var cat = (p.category || "").trim();
      if (cat) tally[cat] = (tally[cat] || 0) + 1;
    });

    var total = posts.length;
    var cats  = Object.keys(tally).sort();

    // Rebuild chips — preserve the active state if possible
    var active = (container.querySelector(".blog-chip.active") || {}).getAttribute
                 ? container.querySelector(".blog-chip.active").getAttribute("data-cat")
                 : "all";

    var newHtml = '<button class="blog-chip' + (active === "all" ? " active" : "") +
                  '" data-cat="all">All <span class="blog-chip-count">' + total +
                  "</span></button>";
    cats.forEach(function (cat) {
      var isActive = active === cat ? " active" : "";
      newHtml += '<button class="blog-chip' + isActive + '" data-cat="' + cat + '">' +
                 cat + ' <span class="blog-chip-count">' + tally[cat] + "</span></button>";
    });

    container.innerHTML = newHtml;
  }
  /* ===== Image fallback swap =====
   * Any <img data-fallback="..."> whose primary src fails will silently
   * swap to its local fallback. Runs in capture phase so it catches
   * errors before they're swallowed (the `error` event doesn't bubble).
   * Works for both initial load and JS-hydrated swaps.
   */
  function imageFallbacks() {
    document.addEventListener("error", function (e) {
      var t = e.target;
      if (!t || t.tagName !== "IMG") return;
      var fb = t.getAttribute("data-fallback");
      if (!fb) return;
      // Prevent loop if the fallback itself fails
      if (t.src.indexOf(fb) !== -1) return;
      t.src = fb;
    }, /* capture */ true);
  }
})();
