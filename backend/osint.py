import re
import time
import ipaddress
import hashlib
import asyncio
import httpx
import dns.resolver
from PIL import Image
from PIL.ExifTags import TAGS

# Public profile URL templates. "found" is inferred from HTTP status only —
# always treated as a probabilistic signal, never a confirmed identity match.
PLATFORMS = {
    "GitHub": "https://github.com/{username}",
    "GitLab": "https://gitlab.com/{username}",
    "Reddit": "https://www.reddit.com/user/{username}",
    "X": "https://x.com/{username}",
    "Pinterest": "https://www.pinterest.com/{username}/",
    "Medium": "https://medium.com/@{username}",
    "Dev.to": "https://dev.to/{username}",
    "Stack Overflow": "https://stackoverflow.com/users/{username}",
    "HackerNews": "https://news.ycombinator.com/user?id={username}",
    "Keybase": "https://keybase.io/{username}",
    "Product Hunt": "https://www.producthunt.com/@{username}",
    "npm": "https://www.npmjs.com/~{username}",
    "Twitch": "https://www.twitch.tv/{username}",
    "Telegram": "https://t.me/{username}",
    "YouTube": "https://www.youtube.com/@{username}",
}

DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com",
    "10minutemail.com", "guerrillamail.com",
    "throwawaymail.com", "yopmail.com", "trashmail.com",
}

HEADERS = {"User-Agent": "Ankush-OSINT-Toolkit/2.1 (+public-profile-check)"}


async def _check_one(client, platform, template, username):
    url = template.format(username=username)
    started = time.perf_counter()
    try:
        r = await client.get(url, headers=HEADERS, timeout=8, follow_redirects=True)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "platform": platform,
            "url": url,
            "status": r.status_code,
            "found": r.status_code == 200,
            "response_ms": elapsed_ms,
        }
    except httpx.RequestError:
        return {
            "platform": platform,
            "url": url,
            "status": None,
            "found": False,
            "response_ms": None,
            "error": "unreachable",
        }


async def check_username_async(username):
    username = username.strip()
    async with httpx.AsyncClient() as client:
        tasks = [
            _check_one(client, platform, template, username)
            for platform, template in PLATFORMS.items()
        ]
        results = await asyncio.gather(*tasks)
    results = sorted(results, key=lambda r: (not r["found"], r["platform"]))
    found_count = sum(1 for r in results if r["found"])
    return {
        "type": "username",
        "username": username,
        "checked": len(results),
        "found_count": found_count,
        "results": results,
    }


def check_username(username):
    """Sync wrapper kept for compatibility; prefer check_username_async."""
    return asyncio.run(check_username_async(username))


def validate_email(email):
    email = email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return {"type": "email", "email": email, "valid": False,
                "message": "Invalid email format"}
    local, domain = email.split("@", 1)
    mx_records = []
    try:
        for answer in dns.resolver.resolve(domain, "MX"):
            mx_records.append(str(answer.exchange).rstrip("."))
    except Exception:
        pass
    return {
        "type": "email", "email": email, "valid": True, "domain": domain,
        "disposable": domain in DISPOSABLE_DOMAINS,
        "has_mx": len(mx_records) > 0,
        "mx_records": mx_records,
        "plus_addressed": "+" in local,
    }


def lookup_ip(ip):
    ip = ip.strip()
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return {"type": "ip", "ip": ip, "error": "Invalid IP address"}
    try:
        data = httpx.get(f"https://ipwho.is/{ip}", timeout=10).json()
        if not data.get("success", False):
            return {"type": "ip", "ip": ip, "error": data.get("message", "Lookup failed")}
        c = data.get("connection", {})
        tz = data.get("timezone", {})
        return {
            "type": "ip", "ip": ip,
            "country": data.get("country"), "country_code": data.get("country_code"),
            "region": data.get("region"), "city": data.get("city"),
            "postal": data.get("postal"), "latitude": data.get("latitude"),
            "longitude": data.get("longitude"), "timezone": tz.get("id"),
            "isp": c.get("isp"), "organization": c.get("org"), "asn": c.get("asn"),
            "is_datacenter": bool(data.get("type") == "hosting") if data.get("type") else None,
        }
    except httpx.RequestError as e:
        return {"type": "ip", "ip": ip, "error": str(e)}


def domain_lookup(domain):
    domain = domain.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    result = {"type": "domain", "domain": domain, "ip_addresses": [],
              "mx_records": [], "ns_records": [], "txt_records": []}
    for record_type, key in [("A", "ip_addresses"), ("MX", "mx_records"),
                              ("NS", "ns_records"), ("TXT", "txt_records")]:
        try:
            for answer in dns.resolver.resolve(domain, record_type):
                value = str(answer).rstrip(".")
                if record_type == "MX":
                    value = str(answer.exchange).rstrip(".")
                result[key].append(value)
        except Exception:
            pass
    result["has_spf"] = any("v=spf1" in t for t in result["txt_records"])
    result["has_dmarc"] = False
    try:
        for answer in dns.resolver.resolve(f"_dmarc.{domain}", "TXT"):
            if "v=DMARC1" in str(answer):
                result["has_dmarc"] = True
    except Exception:
        pass
    return result


def image_metadata(file_path):
    result = {"type": "image", "filename": file_path,
              "metadata": {}, "hash_sha256": None}
    try:
        with open(file_path, "rb") as f:
            result["hash_sha256"] = hashlib.sha256(f.read()).hexdigest()
        image = Image.open(file_path)
        result.update({"width": image.width, "height": image.height, "format": image.format})
        exif = image.getexif()
        for tag_id, value in exif.items():
            result["metadata"][TAGS.get(tag_id, str(tag_id))] = str(value)
        result["has_gps"] = 34853 in exif  # GPSInfo tag id
    except Exception as e:
        result["error"] = str(e)
    return result
