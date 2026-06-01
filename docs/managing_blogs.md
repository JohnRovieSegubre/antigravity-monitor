# Sovereign API: Blog Management Guide

This guide explains how developers or AI agents can create, build, and deploy new blog posts for the Sovereign API website. The blog is built natively as static HTML and heavily optimized for SEO and AI discoverability.

## 1. Creating a New Blog Post

All blog posts are written in Markdown (`.md`) and stored in: `landing/blogs/`

### The Fast Way (Recommended)
Copy the pre-configured starter template:
```powershell
cp landing/blogs/_new_post_template.md landing/blogs/your-post-slug.md
```
This template contains all the required SEO fields and a structural guide.

### Manual Setup
Every file **must** include YAML Frontmatter at the very top for metadata.

**Example `landing/blogs/my-new-post.md`:**
```markdown
---
title: "A Compelling Post Title (50-60 chars)"
date: 2026-03-04
description: "A 150-160 char summary for Google and AI agents."
keywords: "AI agents, crypto payments, SDK"
author: "Sovereign Intelligence Team"
faq_1_q: "What is x402?"
faq_1_a: "x402 is a payment protocol for autonomous agents..."
---

# A Compelling Post Title
Your content goes here...
```
*(The filename becomes the URL slug: `sovereign-api.com/blogs/my-new-post/`)*

## 2. Compiling and SEO Audit

Once your `.md` file is saved, run the build script from the project root:
```bash
python build_blog.py
```

**What the script does automatically:**
1. **SEO Audit:** Validates title/description lengths and warns you if they are suboptimal.
2. **Schema Injection:** Automatically generates and injects **Article**, **Breadcrumb**, and **FAQ** JSON-LD schema into the HTML.
3. **Meta Generation:** Generates OpenGraph and Twitter cards for social sharing.
4. **Auto-Description:** If you forget a `description:`, it intelligently extracts the first paragraph of your post.
5. **Index & Sitemap:** Re-generates the master index and updates `sitemap.xml`.

## 3. Deploying (Hot-Deployment)

You do **NOT** need to restart the server. Use the deploy script which handles both upload and permissions:

### PowerShell (Windows)
```powershell
.\deploy_blogs.ps1
```

### Bash (Git Bash / WSL / macOS)
```bash
bash deploy_blogs.sh
```

> **⚠️ Important:** Do NOT use raw `scp` without the deploy script. SCP uploads directories with 700 permissions, which causes NGINX 403 errors. The deploy scripts automatically fix permissions after upload.

## 4. Understanding x402 Payments

When the main deployment script asks for your **Base Wallet Address**, this is the destination where AI agents will send USDC to pay for compute. The Gateway monitors this wallet and issues Macaroon tokens upon payment verification.
