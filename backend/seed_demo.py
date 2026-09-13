import io
import zipfile
import requests
import time

zip_buf = io.BytesIO()
with zipfile.ZipFile(zip_buf, 'w') as zf:
    zf.writestr('app/calculator.py', """# Mathematical Computation Module
# Provides foundational arithmetic operations

class Calculator:
    def __init__(self):
        self.history = []

    def compute(self, op: str, a: float, b: float) -> float:
        # Computes operation with branch logic
        if op == 'add':
            val = a + b
        elif op == 'subtract':
            val = a - b
        elif op == 'multiply':
            val = a * b
        elif op == 'divide':
            if b != 0:
                val = a / b
            else:
                raise ValueError('Division by zero')
        elif op == 'modulo':
            val = a % b
        else:
            val = 0.0
        self.history.append((op, a, b, val))
        return val
""")
    zf.writestr('app/auth_service.py', """# Authentication and Credential Service
import hashlib

class AuthService:
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
        self.failed_attempts = 0

    def verify_credentials(self, username, password):
        if not username or not password:
            return False
        # Insecure MD5 hash for bandit security detection
        hashed = hashlib.md5(password.encode()).hexdigest()
        if username == 'admin' and hashed == '21232f297a57a5a743894a0e4a801fc3':
            return True
        self.failed_attempts += 1
        return False
""")
    zf.writestr('web/dashboard.js', """// Front-end user interface logic
function renderUserStats(user) {
    if (!user) return;
    if (user.role == 'admin') {
        console.log('Admin user access granted');
    }
}
""")
    zf.writestr('tests/test_calculator.py', """# Automated test coverage
from app.calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.compute('add', 2, 3) == 5
""")

zip_buf.seek(0)
repo_bytes = zip_buf.read()

# Create project
resp = requests.post('http://127.0.0.1:8000/api/projects', json={
    'name': 'FinTech Microservices Platform',
    'description': 'Core financial transaction and authentication services repository.'
})
proj = resp.json()
proj_id = proj['id']
print('Created Project ID:', proj_id)

# Trigger Run 1
files = {'file': ('fintech_repo.zip', repo_bytes, 'application/zip')}
res = requests.post(f'http://127.0.0.1:8000/api/projects/{proj_id}/analyze', files=files)
run_id = res.json()['run_id']
print('Queued Run 1 ID:', run_id)

for _ in range(30):
    time.sleep(1)
    status = requests.get(f'http://127.0.0.1:8000/api/runs/{run_id}/status').json()['status']
    print('Run 1 status:', status)
    if status in ['done', 'failed']:
        break

# Trigger Run 2 (to enable run diffing)
files2 = {'file': ('fintech_repo_v2.zip', repo_bytes, 'application/zip')}
res2 = requests.post(f'http://127.0.0.1:8000/api/projects/{proj_id}/analyze', files=files2).json()
run_id2 = res2['run_id']
print('Queued Run 2 ID:', run_id2)

for _ in range(30):
    time.sleep(1)
    status2 = requests.get(f'http://127.0.0.1:8000/api/runs/{run_id2}/status').json()['status']
    print('Run 2 status:', status2)
    if status2 in ['done', 'failed']:
        break

print(f"DONE! Project: {proj_id}, Run 1: {run_id}, Run 2: {run_id2}")
