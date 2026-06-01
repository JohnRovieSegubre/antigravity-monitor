# Sovereign API — Terms of Service

**Effective Date:** March 10, 2026  
**Last Updated:** March 10, 2026

By accessing or using the Sovereign Intelligence API ("Service"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree, do not use the Service.

---

## 1. Description of Service

Sovereign API is **neutral compute infrastructure**. We provide an OpenAI-compatible API gateway that routes AI inference requests to upstream model providers and processes payments via the x402 protocol (USDC on Base).

**What Sovereign enforces:**
- Spend caps and rate limits
- API key validation and session lifecycle
- Payment verification (x402, prepaid keys, burst sessions)
- SSE normalization for client compatibility

**What Sovereign does NOT enforce:**
- Agent behavior, alignment, or decision-making
- Application-level content moderation
- Orchestration logic, recursion depth, or spawn limits
- The quality or accuracy of upstream model outputs

Sovereign is infrastructure. What you build on it is your responsibility.

---

## 2. Eligibility

You must be at least 18 years old or the age of legal majority in your jurisdiction. By using the Service, you represent that you have the legal capacity to enter into these Terms.

---

## 3. Account & API Key Responsibility

- **API Keys** (`sk-sov-…`) are bearer credentials. Anyone who possesses your key can use your balance.
- **You are solely responsible** for safeguarding your API keys, session tokens, and private keys.
- **Never log** API keys or Macaroon session tokens in plaintext, public repositories, or client-side code.
- You must notify us immediately if you believe your credentials have been compromised.
- We are not liable for unauthorized usage resulting from your failure to secure credentials.

---

## 4. Payment & Billing

### 4.1 Prepaid API Keys
- API keys are funded via x402 crypto payments (USDC on Base).
- $1.00 USDC = 100,000 algorithmic credits.
- Credits are non-refundable once purchased.
- Balance is deducted per-request based on model pricing and token usage.

### 4.2 x402 Guest Mode
- Unauthenticated requests are charged per-call via the x402 protocol.
- The x402 SDK handles payment automatically; you are responsible for ensuring sufficient USDC in your wallet.

### 4.3 Burst Sessions
- Session deposits are capped at $1.00 USDC maximum.
- Sessions expire after the configured TTL (max 60 minutes) or when the balance reaches zero, whichever comes first.
- Session tokens are bearer spend tokens and must be treated with the same security as private keys.

### 4.4 Idempotency
- Top-up requests accept an `idempotency_key` to prevent double-charging. It is your responsibility to include one in production environments.

### 4.5 No Refunds
- All payments are final. Credits, session deposits, and per-call payments are non-refundable.
- Blockchain transactions are irreversible by nature.

---

## 5. Acceptable Use

You agree to use the Service only for lawful purposes and in compliance with all applicable local, national, and international laws. You may use the Service for:

- AI agent development and testing
- Research and experimentation
- Commercial applications
- Multi-agent orchestration and swarm computing
- Any other lawful purpose

---

## 6. Prohibited Activities

You agree NOT to use the Service to:

- Generate content that violates applicable law (e.g., CSAM, terrorism-related material, illegal threats)
- Attempt to bypass spend caps, rate limits, or authentication mechanisms
- Conduct denial-of-service attacks against the Gateway or upstream providers
- Exploit vulnerabilities in the payment system, x402 protocol, or session management
- Resell API access without authorization
- Use the Service to launder money or facilitate financial fraud
- Impersonate Sovereign API or its operators in any communication
- Reverse-engineer the Gateway's proprietary routing or pricing logic

Violation of these terms may result in immediate suspension or permanent termination of your API keys without refund.

---

## 7. Spend Caps & Safety Controls

- A default daily spend cap of **1,000,000 credits (~$10 USD)** is enforced per API key.
- Burst session deposits are hard-capped at **$1.00 USDC** with a maximum TTL of **60 minutes**.
- These limits exist to protect both users and the network from runaway agents or infinite loops.
- Sovereign reserves the right to adjust default caps as the platform evolves.

---

## 8. Upstream Model Providers

- Sovereign may route requests to third-party model providers. Such providers operate independently and may change availability, pricing, or policies without notice.
- **We do not control** the content, accuracy, or availability of upstream models.
- Model responses may be subject to the upstream provider's own content policies and rate limits.
- Sovereign is not responsible for model hallucinations, inaccuracies, biases, or outages originating from upstream providers.

---

## 9. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW:

- THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
- SOVEREIGN DOES NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR SECURE.
- IN NO EVENT SHALL SOVEREIGN BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, DATA, OR BUSINESS OPPORTUNITIES.
- SOVEREIGN'S TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT YOU PAID FOR THE SERVICE IN THE 30 DAYS PRECEDING THE CLAIM.

Nothing in these Terms creates a partnership, joint venture, fiduciary, or agency relationship between you and Sovereign. Your use of the Service does not make Sovereign your agent, and Sovereign does not act on your behalf.

---

## 10. Indemnification

You agree to indemnify, defend, and hold harmless Sovereign API, its operators, and affiliates from any claims, damages, losses, or expenses (including reasonable legal fees) arising from:

- Your use of the Service
- Your violation of these Terms
- Any content generated through the Service using your credentials
- Any application, agent, or system you build on top of the Service

---

## 11. Suspension & Termination

Sovereign may suspend or terminate your access immediately, with or without notice, if necessary to protect the integrity of the network, comply with law, or mitigate abuse. This includes the right to:

- **Suspend** your API keys temporarily if suspicious activity is detected
- **Revoke** your API keys permanently for violation of these Terms
- **Rate-limit** or throttle traffic during periods of high demand
- **Modify or discontinue** the Service at any time

You may terminate your use of the Service at any time by ceasing to use your API keys. Unused credits are non-refundable.

---

## 12. Data & Privacy

- Sovereign does **not** persist prompt or response content beyond what is required for real-time routing, billing, and operational security, unless otherwise disclosed.
- API key metadata (registration name, balance, usage counters) is stored for billing purposes.
- Blockchain transaction records are inherently public and immutable.
- We do not sell or share your data with third parties.

---

## 13. Modifications to Terms

We may update these Terms from time to time. Material changes will be communicated via the documentation or website. Continued use of the Service after changes constitutes acceptance of the updated Terms.

---

## 14. Force Majeure

Sovereign shall not be liable for any failure or delay in performance resulting from causes beyond its reasonable control, including but not limited to: blockchain network congestion, upstream provider outages, regulatory changes, natural disasters, cyberattacks, or disruptions to internet infrastructure.

---

## 15. Governing Law & Dispute Resolution

These Terms shall be governed by and construed in accordance with the laws of the Republic of the Philippines, without regard to conflict of law principles. Any dispute arising from these Terms shall first be submitted to good-faith negotiation for a period of 30 days. If unresolved, the dispute shall be settled by binding arbitration under the rules of the Philippine Dispute Resolution Center (PDRC), with the seat of arbitration in Cebu City. The language of arbitration shall be English.

---

## 16. Contact

For questions regarding these Terms, contact us through the channels listed at [sovereign-api.com](https://sovereign-api.com).
