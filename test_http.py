"""Test the actual HTTP server with requests library."""
import urllib.request
import urllib.parse
import http.cookiejar
import json

BASE_URL = 'http://localhost:8001'
TENANT = 'GirlsModel'

# Set up cookie jar to preserve cookies between requests
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'TestClient/1.0')]

def get_cookies_summary():
    return {c.name: c.value[:30] + '...' for c in cj}

def get(url):
    req = urllib.request.Request(f'{BASE_URL}{url}')
    try:
        resp = opener.open(req, timeout=10)
        return resp.getcode(), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, url
    except Exception as e:
        return 0, str(e)

def post(url, data):
    # First get CSRF token
    for c in cj:
        if c.name == 'csrftoken':
            data['csrfmiddlewaretoken'] = c.value
            break
    
    encoded = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(f'{BASE_URL}{url}', data=encoded, method='POST')
    req.add_header('Referer', f'{BASE_URL}{url}')
    try:
        resp = opener.open(req, timeout=10)
        return resp.getcode(), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, url

# Step 1: Get login page (to get CSRF cookie)
print("Step 1: GET login page")
code, url = get(f'/{TENANT}/login/')
print(f"  Status: {code}, URL: {url}")
print(f"  Cookies: {list(c.name for c in cj)}")

# Step 2: POST login
print("\nStep 2: POST login")
code, url = post(f'/{TENANT}/login/', {'username': 'admin', 'password': 'testpass123'})
print(f"  Status: {code}, Final URL: {url}")
print(f"  Cookies: {list(c.name for c in cj)}")

# Step 3: Access students
print("\nStep 3: GET students page")
code, url = get(f'/{TENANT}/students/')
print(f"  Status: {code}, URL: {url}")

# Step 4: Access teachers
print("\nStep 4: GET teachers page")
code, url = get(f'/{TENANT}/teachers/')
print(f"  Status: {code}, URL: {url}")

# Step 5: Access finance
print("\nStep 5: GET finance page")
code, url = get(f'/{TENANT}/finance/')
print(f"  Status: {code}, URL: {url}")

print("\nAll cookies in jar:")
for c in cj:
    print(f"  {c.name}: path={c.path}, secure={c.secure}, expires={c.expires}, value_prefix={c.value[:20]}")
