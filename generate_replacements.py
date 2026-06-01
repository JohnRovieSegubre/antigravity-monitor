tools_data = [
    ("crypto-price", "GET", "/api/crypto/price", 50, "Live crypto prices"),
    ("web-scrape", "GET", "/api/web/scrape", 100, "Web page scraping"),
    ("web-search", "POST", "/api/search/web", 100, "Web search"),
    ("web-screenshot", "GET", "/api/web/screenshot", 100, "Web page screenshot"),
    ("image-gen", "POST", "/api/image/fast", 500, "AI image generation"),
    ("tts", "POST", "/api/tts/openai", 250, "Text-to-speech"),
    ("transcription", "POST", "/api/transcribe", 250, "Audio transcription"),
    ("code-exec", "POST", "/api/code/run", 100, "Sandboxed code execution"),
    ("market-data", "GET", "/api/crypto/markets", 50, "Market data"),
    ("wallet-balance", "POST", "/api/wallet/balances", 50, "Wallet balances"),
    ("ens-resolve", "GET", "/api/ens/resolve", 50, "ENS resolution"),
    ("flight-search", "GET", "/api/travel/flights", 100, "Flight search"),
    ("hotel-search", "GET", "/api/travel/hotels", 100, "Hotel search"),
    ("embeddings", "POST", "/api/embeddings", 50, "Text embeddings")
]

x402_routes_str = []
for name, method, _, sats, desc in tools_data:
    price_str = "X402_PRICE" if sats == 50 else f"\"${sats / 50000:.3f}\""  # roughly assuming X402_PRICE was small
    if sats == 100: price_str = "\"$0.002\""
    elif sats == 250: price_str = "\"$0.005\""
    elif sats == 500: price_str = "\"$0.01\""
    
    route_def = f"""            "{method} /v1/tools/{name}": RouteConfig(
                accepts=[PaymentOption(
                    scheme="exact",
                    pay_to=X402_PAY_TO,
                    price={price_str},
                    network=X402_NETWORK,
                )],
                mime_type="application/json",
                description="{desc} (proxied via x402engine)",
            ),"""
    x402_routes_str.append(route_def)

router_str = []
for name, method, path, sats, _ in tools_data:
    router_str.append(f'    "{name}": {{"x402_path": "{path}", "price_sats": {sats}, "method": "{method}"}},')

with open("generate_code.txt", "w") as f:
    f.write("\n".join(x402_routes_str) + "\n\n=====\n\n" + "\n".join(router_str))
print("Generated code.")
