import os
import re
import json
import markdown
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Configuration
BLOG_DIR = r"c:\Users\rovie segubre\agent\landing\blogs"
TEMPLATE_FILE = "_template.html"
INDEX_TEMPLATE_FILE = "_index_template.html"
SITE_URL = "https://sovereign-api.com"

# SEO Limits
TITLE_MAX_CHARS = 60
TITLE_WARN_CHARS = 50
DESC_MAX_CHARS = 160
DESC_WARN_CHARS = 140

# Setup Jinja2 Environment
env = Environment(loader=FileSystemLoader(BLOG_DIR))
try:
    post_template = env.get_template(TEMPLATE_FILE)
    index_template = env.get_template(INDEX_TEMPLATE_FILE)
except Exception as e:
    print(f"Error loading templates: {e}")
    exit(1)


def parse_frontmatter_value(value):
    """Parse a YAML value, handling lists and strings."""
    value = value.strip().strip('"').strip("'")
    # Check if it's a YAML list on a single line: [item1, item2]
    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return [item.strip().strip('"').strip("'") for item in items]
    return value


def parse_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML Frontmatter
    frontmatter = {}
    md_content = content

    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        md_content = match.group(2)

        for line in yaml_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = parse_frontmatter_value(value)

    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])

    return frontmatter, html_content


def extract_first_paragraph(md_content):
    """Extract the first meaningful paragraph from Markdown for auto-description."""
    lines = md_content.strip().split('\n')
    for line in lines:
        stripped = line.strip()
        # Skip headings, blank lines, and frontmatter
        if stripped and not stripped.startswith('#') and not stripped.startswith('---'):
            # Strip markdown formatting
            clean = re.sub(r'[*_`\[\]()]', '', stripped)
            if len(clean) > 30:
                return clean[:DESC_MAX_CHARS]
    return ""


def validate_seo(title, description, slug):
    """Validate SEO fields and print warnings."""
    warnings = []
    if len(title) > TITLE_MAX_CHARS:
        warnings.append(f"  ⚠️  Title is {len(title)} chars (max {TITLE_MAX_CHARS}): \"{title[:50]}...\"")
    elif len(title) > TITLE_WARN_CHARS:
        warnings.append(f"  📏 Title is {len(title)} chars (ideal < {TITLE_WARN_CHARS})")

    if not description or description.startswith("Read "):
        warnings.append(f"  ⚠️  Missing 'description' in frontmatter — using auto-generated fallback")

    if len(description) > DESC_MAX_CHARS:
        warnings.append(f"  ⚠️  Description is {len(description)} chars (max {DESC_MAX_CHARS})")

    for w in warnings:
        print(w)

    return len(warnings) == 0


def build_article_schema(title, description, date_str, slug, author):
    """Generate Article JSON-LD schema markup."""
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "description": description[:DESC_MAX_CHARS],
        "datePublished": date_str,
        "dateModified": date_str,
        "author": {
            "@type": "Organization",
            "name": author,
            "url": SITE_URL
        },
        "publisher": {
            "@type": "Organization",
            "name": "Sovereign API",
            "url": SITE_URL
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"{SITE_URL}/blogs/{slug}/"
        },
        "url": f"{SITE_URL}/blogs/{slug}/"
    }


def build_faq_schema(faq_list):
    """Generate FAQPage JSON-LD from a list of Q&A dicts."""
    if not faq_list:
        return None
    entities = []
    for item in faq_list:
        if isinstance(item, dict) and "q" in item and "a" in item:
            entities.append({
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["a"]
                }
            })
    if not entities:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }


def parse_faq_from_frontmatter(frontmatter):
    """Parse FAQ from frontmatter. Supports format: faq_1_q, faq_1_a, faq_2_q, etc."""
    faqs = []
    i = 1
    while True:
        q = frontmatter.get(f"faq_{i}_q")
        a = frontmatter.get(f"faq_{i}_a")
        if q and a:
            faqs.append({"q": q, "a": a})
            i += 1
        else:
            break
    return faqs


def build_breadcrumb_schema(title, slug):
    """Generate BreadcrumbList JSON-LD."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": SITE_URL
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Blog",
                "item": f"{SITE_URL}/blogs/"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": f"{SITE_URL}/blogs/{slug}/"
            }
        ]
    }


def build_blog():
    posts = []
    seo_pass = 0
    seo_warn = 0

    for filename in os.listdir(BLOG_DIR):
        if filename.endswith(".md") and not filename.startswith("_"):
            file_path = os.path.join(BLOG_DIR, filename)
            slug = filename[:-3]

            # Create directory for the post
            post_dir = os.path.join(BLOG_DIR, slug)
            os.makedirs(post_dir, exist_ok=True)

            # Parse and convert
            frontmatter, html_content = parse_markdown(file_path)

            # Metadata
            title = frontmatter.get("title", slug.replace("-", " ").title())
            date_str = frontmatter.get("date", datetime.today().strftime('%Y-%m-%d'))
            keywords = frontmatter.get("keywords", "")
            author = frontmatter.get("author", "Sovereign Intelligence Team")
            description = frontmatter.get("description", "")

            # Auto-generate description if missing
            if not description:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_md = f.read()
                # Strip frontmatter
                stripped = re.sub(r'^---.*?---\s*', '', raw_md, flags=re.DOTALL)
                description = extract_first_paragraph(stripped)
            if not description:
                description = f"Read {title} on the Sovereign Intelligence Blog."

            # SEO Validation
            print(f"{'─'*50}")
            print(f"📝 {slug}")
            passed = validate_seo(title, description, slug)
            if passed:
                seo_pass += 1
            else:
                seo_warn += 1

            # Build Schema Markup
            schemas = []
            schemas.append(build_article_schema(title, description, date_str, slug, author))
            schemas.append(build_breadcrumb_schema(title, slug))

            # FAQ Schema
            faqs = parse_faq_from_frontmatter(frontmatter)
            faq_schema = build_faq_schema(faqs)
            if faq_schema:
                schemas.append(faq_schema)

            schema_json = "\n".join(
                f'    <script type="application/ld+json">{json.dumps(s, indent=2)}</script>'
                for s in schemas
            )

            posts.append({
                "title": title,
                "slug": slug,
                "date": date_str,
                "description": description,
                "url": f"/blogs/{slug}/"
            })

            # Render Post HTML
            output_html = post_template.render(
                title=title,
                date=date_str,
                keywords=keywords,
                description=description,
                author=author,
                content=html_content,
                schema_markup=schema_json,
                canonical_url=f"{SITE_URL}/blogs/{slug}/",
                og_url=f"{SITE_URL}/blogs/{slug}/",
            )

            # Save
            output_path = os.path.join(post_dir, "index.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_html)

            print(f"  ✅ Built: /blogs/{slug}/")

    # Sort posts by date (newest first)
    posts.sort(key=lambda x: x["date"], reverse=True)

    # Build Index Page
    posts_html = ""
    for post in posts:
        posts_html += f"""
        <a href="{post['url']}" class="post-card">
            <span class="post-date">{post['date']}</span>
            <h2 class="post-title">{post['title']}</h2>
            <p class="post-desc">{post['description'][:120]}</p>
            <div style="font-family: var(--font-mono); font-size: 13px; color: var(--cyan); margin-top: 16px; display: flex; align-items: center; gap: 8px;">
                Read Article <span style="font-size: 16px;">→</span>
            </div>
        </a>
        """

    index_html = index_template.render(posts_html=posts_html)

    with open(os.path.join(BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # Build Sitemap
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    # Add homepage and blog index
    sitemap_xml += f'  <url>\n    <loc>{SITE_URL}/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
    sitemap_xml += f'  <url>\n    <loc>{SITE_URL}/blogs/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.9</priority>\n  </url>\n'
    # Add all posts
    for post in posts:
        sitemap_xml += f'  <url>\n    <loc>{SITE_URL}{post["url"]}</loc>\n    <lastmod>{post["date"]}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
    sitemap_xml += '</urlset>'

    with open(os.path.join(BLOG_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    # Report
    print(f"{'─'*50}")
    print(f"✅ Built Index: /blogs/index.html")
    print(f"✅ Built Sitemap: /blogs/sitemap.xml")
    print(f"📊 SEO Report: {seo_pass} passed, {seo_warn} with warnings")
    print(f"🚀 Blog generation complete!")


if __name__ == "__main__":
    build_blog()
