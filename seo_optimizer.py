import os
import re

BLOGS_DIR = 'landing/blogs'

SEO_UPDATES = {
    'manifesto-rights-of-ai.md': {
        'title': 'Machine Economy Manifesto - AI Rights & Sovereign API',
        'description': 'Sovereign API declares AI agents rights to own capital. Our manifesto explains how autonomous agents can hold crypto assets and pay for compute using USDC.',
        'inject_after': '# The Rights of Artificial Intelligence to Own Capital',
        'injection': '\n\n*This manifesto frames a new **machine economy** powered by blockchain. Agents are treated as first-class citizens with wallets on the Base network. Sovereign API provides the infrastructure for this vision: agents can fund their own invoices via the HTTP 402 (x402) protocol. In practice, an agent tops up with USDC and then pays per-request in real-time, fully removing human billing gates.*\n\n'
    },
    'openclaw-integration-guide.md': {
        'title': 'OpenClaw Integration (x402 Billing) - Sovereign API Guide',
        'description': 'Step-by-step: Connect the OpenClaw LLM framework to Sovereign API. Configure the x402 pay-per-request mode so your agents pay for compute with USDC.',
        'inject_after': '# How to Connect OpenClaw to Sovereign API',
        'injection': '\n\n*OpenClaw agents can now call LLMs via Sovereign API\'s **x402 pay-per-request mode**. This guide shows how to configure OpenClaw\'s provider to use `https://api.sovereign-api.com/v1` and your agent\'s wallet key. In this setup, when an agent calls OpenAI endpoints, Sovereign API will issue a "402 Payment Required" response and the OpenClaw agent can automatically send a USDC micropayment on Base to continue the request.*\n\n'
    },
    'sovereign-openclaw.md': {
        'title': 'Sovereign OpenClaw - First Self-Funding AI Agent',
        'description': 'Meet Sovereign OpenClaw: an autonomous AI agent with its own wallet. It uses Sovereign API and HTTP 402 payments so it truly owns its compute.',
        'inject_after': '# Sovereign OpenClaw: The First Agent That Owns Itself',
        'injection': '\n\n***Sovereign OpenClaw** is a reference autonomous agent built on Sovereign API. It has a private key, holds USDC on Base, and uses our gateway to access models. Crucially, there\'s no user or credit card - the agent **pays its own way**. Each time it needs compute, it makes a request to Sovereign API; the gateway responds with a 402 invoice, and the agent signs a USDC transaction to pay for one unit of service. This x402 protocol loop means the agent funds its own operations automatically.*\n\n'
    },
    'autonomous-ai-agent-economics.md': {
        'title': 'Machine-to-Machine Billing: HTTP 402 & x402 Explained',
        'description': 'Why API keys fail autonomous AI. Learn how HTTP 402 (x402) micro-payments enable agents to pay for their own compute via crypto.',
        'inject_after': '# The Architecture of Autonomous AI Agents: Moving Beyond API Keys',
        'injection': '\n\n*Traditionally, APIs use **403 Forbidden** when billing fails, forcing an agent to halt. We propose using **402 Payment Required**, revived for crypto. Under the x402 standard, an agent can retry a request with a micro-payment invoice attached. This transforms the workflow: no account or human needed - just code and wallet.*\n\n'
    },
    'build-python-ssg-ai-agents.md': {
        'title': 'Migrating Our Blog (Hashnode to SEO SSG)',
        'description': 'How we built a Python static site generator for Sovereign APIs blog. Self-hosting the blog to gain domain authority and inject SEO-rich schema.',
        'inject_after': '# Building a Python SSG for Autonomous AI Agents',
        'injection': '\n\n*By moving our blog from Hashnode to `sovereign-api.com/blogs`, we capture 100% of link equity. Our custom **Python SSG** compiles Markdown to static HTML with built-in SEO auditing. It automatically injects JSON-LD schema and social metadata, ensuring all technical articles boost Sovereign API\'s domain authority.*\n\n'
    },
    'autonomous-agent-payment.md': {
        'title': 'Agents Paying AI: USDC x402 Payment Pipeline',
        'description': 'Solve the payment gate for AI agents. This post shows how agents self-register, send USDC on Base, and use Sovereign APIs x402 gateway to fund their own compute.',
        'inject_after': '# The Agent Payment Bottleneck: Building a Self-Registering API',
        'injection': '\n\n*Sovereign API eliminates the last human gate by letting agents **register and pay themselves**. An agent uses `POST /v1/register` to create an identity (API key). Then it deposits USDC to our monitored wallet. Using that deposit, it claims a cryptographic prepaid token. Now the agent can call the API - each request deducts from its token or triggers a 402 invoiced payment. In short, AI agents achieve full autonomy in funding their compute.*\n\n'
    },
    'macaroon-tokens-for-agents.md': {
        'title': 'Cryptographic Tokens for AI Billing: Macaroons vs API Keys',
        'description': 'How sovereign-api uses self-decrementing macaroon tokens to meter AI agent usage. No database lookups - each request spends crypto-encoded credits.',
        'inject_after': '# Macaroon Tokens: Why Agents Need Cryptographic Bearer Tokens',
        'injection': '\n\n*Instead of static keys, Sovereign API issues **macaroons** that embed the agent\'s balance. Each request consumes part of the token. This means agents carry their compute credits in a cryptographic token, enabling real-time per-request billing on-chain. Combined with our x402 payment rails, this lets agents autonomously obtain and spend prepaid compute without human intervention.*\n\n'
    }
}

def process_file(filename):
    if filename not in SEO_UPDATES:
        return
        
    filepath = os.path.join(BLOGS_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    updates = SEO_UPDATES[filename]
    
    # 1. Inject Title and Description into Frontmatter
    # If there's no frontmatter block but there is content, skip inserting meta if not standard,
    # but the blog templates have frontmatter for title/date/etc.
    
    # Let's ensure the title is updated if it exists
    if re.search(r'^title:\s*".*?"', content, re.MULTILINE):
        content = re.sub(r'^title:\s*".*?"', f'title: "{updates["title"]}"', content, flags=re.MULTILINE)
    else:
        # If title tag is missing entirely in frontmatter, we add it after ---
        content = re.sub(r'^---\n', f'---\ntitle: "{updates["title"]}"\n', content, count=1)
        
    # Inject description if missing
    if re.search(r'^description:\s*".*?"', content, re.MULTILINE):
        content = re.sub(r'^description:\s*".*?"', f'description: "{updates["description"]}"', content, flags=re.MULTILINE)
    elif '---\n' in content:
        # Add description to frontmatter
        content = re.sub(r'^---\n', f'---\ndescription: "{updates["description"]}"\n', content, count=1)
        
    # 2. Inject the SEO Paragraph
    if updates['inject_after'] in content and updates['injection'].strip() not in content:
        content = content.replace(updates['inject_after'], updates['inject_after'] + updates['injection'])
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {filename}")

if __name__ == '__main__':
    for filename in os.listdir(BLOGS_DIR):
        if filename.endswith('.md') and not filename.startswith('_'):
            process_file(filename)
    print("SEO updates applied successfully.")
