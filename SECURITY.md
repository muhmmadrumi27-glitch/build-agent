# Security Documentation

## Security Architecture

```
┌─────────────────────────────────────────┐
│           Security Layers               │
├─────────────────────────────────────────┤
│  1. Network (Firewall, TLS)             │
│  2. Authentication (JWT, OAuth)          │
│  3. Authorization (RBAC, Permissions)   │
│  4. Input Validation (Sanitization)      │
│  5. Action Validation (Security Agent) │
│  6. Audit Logging (Immutable Logs)     │
│  7. Data Protection (Encryption)         │
└─────────────────────────────────────────┘
```

## Authentication

### JWT Token Flow

1. User provides credentials
2. Server validates and issues JWT
3. Client includes JWT in Authorization header
4. Server validates JWT on each request

### Token Configuration

```python
# config.py
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Short-lived tokens
SECRET_KEY = "cryptographically-random-key"  # Minimum 32 bytes
ALGORITHM = "HS256"
```

### Password Policy

- Minimum 12 characters
- Must contain uppercase, lowercase, number, special char
- Bcrypt hashing with salt rounds = 12
- Password history prevents reuse

## Authorization

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| Admin | Full access to all resources |
| User | Create/read/update own tasks, workflows |
| Viewer | Read-only access to sessions, tasks |

### Permission Matrix

```
                    Admin   User   Viewer
user:create          ✓       ✗       ✗
user:read            ✓       ✓       ✗
session:create       ✓       ✓       ✗
session:read         ✓       ✓       ✓
task:create          ✓       ✓       ✗
task:delete          ✓       ✓       ✗
workflow:create      ✓       ✓       ✗
settings:update      ✓       ✓       ✗
audit:read           ✓       ✗       ✗
```

## Action Security

### Dangerous Pattern Detection

Blocked patterns:
- `rm -rf` - Recursive deletion
- `format` - Disk formatting
- `mkfs` - Filesystem creation
- `dd if=` - Direct disk operations
- `eval(` - Code evaluation
- `system(` - System command execution

### File Access Control

Protected paths:
- `.ssh/` - SSH keys
- `.aws/` - AWS credentials
- `.env` - Environment files
- `id_rsa` - Private keys
- `.pgpass` - PostgreSQL passwords
- `.netrc` - Netrc credentials

### URL Filtering

Blocked domains:
- Known malware sites
- Phishing domains
- Suspicious TLDs

Allowed domains (when restricted mode enabled):
- Configurable whitelist

## Data Protection

### Encryption

**At Rest:**
- Database: PostgreSQL native encryption
- Files: AES-256 encryption
- Backups: Encrypted with GPG

**In Transit:**
- TLS 1.3 for all communications
- Certificate pinning for API clients

**In Memory:**
- Sensitive data masked in logs
- Automatic memory clearing
- No sensitive data in error messages

### Data Masking

```python
# Examples
password: "********1234"
api_key: "sk-********abcd"
ssn: "***-**-6789"
```

## Audit Logging

### Logged Events

All events include:
- Timestamp (UTC)
- User ID
- Session ID
- IP Address
- User Agent
- Action Type
- Resource Type
- Resource ID
- Details (masked)
- Severity Level

### Event Types

| Event | Severity | Description |
|-------|----------|-------------|
| login | low | User login attempt |
| logout | low | User logout |
| task_start | low | Task execution started |
| action_execute | medium | Action executed |
| action_blocked | high | Action blocked by security |
| file_access | medium | File accessed |
| url_access | medium | URL accessed |
| config_change | high | Configuration changed |
| permission_denied | high | Access denied |
| dangerous_pattern | critical | Dangerous pattern detected |

### Log Storage

- Immutable append-only logs
- Retention: 90 days active, 1 year archive
- Separate log server
- Regular integrity checks

## Safe Mode

### Operation Levels

**Level 1 - Low:**
- Basic monitoring
- Log all actions
- No restrictions

**Level 2 - Medium:**
- Approval for file operations
- Approval for downloads
- Approval for app installation

**Level 3 - High:**
- Approval for all browser actions
- Approval for system commands
- Approval for network operations

**Level 4 - Critical:**
- Approval for ALL actions
- Read-only mode available
- Maximum logging

### Approval Workflow

```
Action Requested
      ↓
Security Evaluation
      ↓
Approval Required? ──No──► Execute
      ↓ Yes
Queue for Approval
      ↓
User Notification
      ↓
User Decision
      ↓
Approved? ──No──► Reject
      ↓ Yes
Execute Action
      ↓
Log Result
```

## Security Headers

```python
# FastAPI middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

## Vulnerability Management

### Dependency Scanning

```bash
# Python
pip install safety
safety check

# Node.js
npm audit
npm audit fix
```

### Container Scanning

```bash
# Trivy
trivy image buildagent/backend

# Clair
clair-scanner buildagent/backend
```

### Penetration Testing

- Quarterly external pentests
- Annual red team exercises
- Bug bounty program
- Automated vulnerability scanning

## Incident Response

### Severity Levels

1. **Critical**: System compromise, data breach
2. **High**: Unauthorized access, privilege escalation
3. **Medium**: Policy violation, suspicious activity
4. **Low**: Minor policy violation, informational

### Response Procedures

**Critical:**
1. Immediate containment
2. Notify security team
3. Preserve evidence
4. Activate incident response team
5. External notification if required

**High:**
1. Block affected user/session
2. Investigate scope
3. Apply remediation
4. Document findings

## Compliance

### Standards

- SOC 2 Type II
- ISO 27001
- GDPR (EU data protection)
- CCPA (California privacy)

### Data Retention

| Data Type | Retention | Encryption |
|-----------|-----------|------------|
| Session logs | 90 days | AES-256 |
| Screenshots | 30 days | AES-256 |
| User data | Until deletion | AES-256 |
| Audit logs | 1 year | AES-256 |
| Memory vectors | 30 days | AES-256 |

## Security Checklist

### Pre-Deployment

- [ ] Change default passwords
- [ ] Configure strong JWT secret
- [ ] Enable TLS/SSL
- [ ] Configure firewall rules
- [ ] Set up log monitoring
- [ ] Enable audit logging
- [ ] Configure backup encryption
- [ ] Set up alerting
- [ ] Review RBAC permissions
- [ ] Test incident response

### Regular Maintenance

- [ ] Review access logs weekly
- [ ] Update dependencies monthly
- [ ] Rotate secrets quarterly
- [ ] Review permissions quarterly
- [ ] Test backups monthly
- [ ] Run vulnerability scans weekly
- [ ] Review audit logs daily
- [ ] Update security policies annually
