"""Full HTTP navigation test with session persistence."""
import urllib.request, urllib.parse, http.cookiejar, sys, time

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'TestClient/1.0')]

def get_page(url):
    try:
        start = time.time()
        r = opener.open(f'http://localhost:8001{url}', timeout=60)
        t = time.time() - start
        return r.getcode(), r.geturl(), t
    except Exception as e:
        return 0, str(e)[:100], 0

# Step 1: GET login
sys.stdout.write("Step 1: GET login page\n"); sys.stdout.flush()
code, url, t = get_page('/GirlsModel/login/')
sys.stdout.write(f"  {code} - {url} ({t:.1f}s)\n"); sys.stdout.flush()

# Step 2: POST login
csrf = next((c.value for c in cj if c.name == 'csrftoken'), '')
data = urllib.parse.urlencode({'username': 'admin', 'password': 'testpass123', 'csrfmiddlewaretoken': csrf}).encode()
req = urllib.request.Request('http://localhost:8001/GirlsModel/login/', data=data, method='POST')
req.add_header('Referer', 'http://localhost:8001/GirlsModel/login/')
sys.stdout.write("Step 2: POST login\n"); sys.stdout.flush()
try:
    start = time.time()
    r2 = opener.open(req, timeout=60)
    t = time.time() - start
    sys.stdout.write(f"  {r2.getcode()} - {r2.geturl()} ({t:.1f}s)\n"); sys.stdout.flush()
except Exception as e:
    sys.stdout.write(f"  ERROR: {e}\n"); sys.stdout.flush()

sys.stdout.write(f"  Cookies after login: {[c.name for c in cj]}\n"); sys.stdout.flush()

# Step 3: Navigate to students page (simulating button click)
sys.stdout.write("Step 3: GET students page (button click)\n"); sys.stdout.flush()
code, url, t = get_page('/GirlsModel/students/')
sys.stdout.write(f"  {code} - {url} ({t:.1f}s)\n"); sys.stdout.flush()
if 'login' in url:
    sys.stdout.write("  *** REDIRECTED TO LOGIN! Session lost!\n")
    
# Step 4: Navigate to teachers
sys.stdout.write("Step 4: GET teachers page\n"); sys.stdout.flush()
code, url, t = get_page('/GirlsModel/teachers/')
sys.stdout.write(f"  {code} - {url} ({t:.1f}s)\n"); sys.stdout.flush()
if 'login' in url:
    sys.stdout.write("  *** REDIRECTED TO LOGIN! Session lost!\n")

# Step 5: Navigate to finance
sys.stdout.write("Step 5: GET finance page\n"); sys.stdout.flush()
code, url, t = get_page('/GirlsModel/finance/')
sys.stdout.write(f"  {code} - {url} ({t:.1f}s)\n"); sys.stdout.flush()
if 'login' in url:
    sys.stdout.write("  *** REDIRECTED TO LOGIN! Session lost!\n")

sys.stdout.write("Done!\n"); sys.stdout.flush()
