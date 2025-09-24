# Web-Based AI Complaint Analysis System
## Pakistan Legal Framework Integration

## 1. Web Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB CLIENT LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  React Dashboard │  Admin Panel │  Report Viewer │  Analytics │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    WEB API GATEWAY                             │
├─────────────────────────────────────────────────────────────────┤
│  Load Balancer │  SSL Termination │  Rate Limiting │  Auth │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    WEB SERVICES LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│ Complaint API │ Investigation API │ Legal API │ Report API │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    AI INTEGRATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│   ChatGPT API   │   Gemini API   │   LLaMA Local   │ Aggregator │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Web Frontend Architecture

### 2.1 React.js Dashboard Components

```typescript
// components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Layout, Menu, Card, Row, Col, Statistic, Table, Button } from 'antd';
import { 
  DashboardOutlined, 
  FileTextOutlined, 
  BarChartOutlined,
  SettingOutlined 
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

interface DashboardProps {
  user: User;
}

const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);

  const menuItems = [
    { key: 'overview', icon: <DashboardOutlined />, label: 'Overview' },
    { key: 'complaints', icon: <FileTextOutlined />, label: 'Complaints' },
    { key: 'reports', icon: <BarChartOutlined />, label: 'Reports' },
    { key: 'settings', icon: <SettingOutlined />, label: 'Settings' }
  ];

  const renderContent = () => {
    switch(activeTab) {
      case 'overview':
        return <OverviewPanel complaints={complaints} />;
      case 'complaints':
        return <ComplaintManagement />;
      case 'reports':
        return <ReportGenerator />;
      case 'settings':
        return <SystemSettings />;
      default:
        return <OverviewPanel complaints={complaints} />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={250} theme="dark">
        <div className="logo" style={{ padding: '16px', color: 'white' }}>
          <h3>Complaint Analysis System</h3>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeTab]}
          items={menuItems}
          onClick={({ key }) => setActiveTab(key)}
        />
      </Sider>
      
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>Welcome, {user.name}</h2>
            <Button type="primary">New Complaint</Button>
          </div>
        </Header>
        
        <Content style={{ margin: '24px', background: '#fff' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
```

### 2.2 Complaint Management Interface

```typescript
// components/ComplaintManagement.tsx
import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Upload, 
  message,
  Tag,
  Progress
} from 'antd';
import { PlusOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons';

const ComplaintManagement: React.FC = () => {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedComplaint, setSelectedComplaint] = useState(null);

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Complaint Text',
      dataIndex: 'complaint_text',
      key: 'complaint_text',
      ellipsis: true,
      render: (text: string) => (
        <div style={{ maxWidth: 300 }}>
          {text.length > 100 ? `${text.substring(0, 100)}...` : text}
        </div>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={getCategoryColor(category)}>{category}</Tag>
      ),
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: number) => (
        <Progress 
          percent={priority} 
          size="small" 
          status={priority > 80 ? 'exception' : priority > 60 ? 'normal' : 'success'}
        />
      ),
    },
    {
      title: 'Compliance Score',
      dataIndex: 'compliance_score',
      key: 'compliance_score',
      render: (score: number) => (
        <Progress 
          percent={score} 
          size="small"
          status={score > 80 ? 'success' : score > 60 ? 'normal' : 'exception'}
        />
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status}</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <div>
          <Button 
            icon={<EyeOutlined />} 
            size="small" 
            onClick={() => viewComplaint(record)}
          />
          <Button 
            icon={<EditOutlined />} 
            size="small" 
            style={{ marginLeft: 8 }}
            onClick={() => editComplaint(record)}
          />
        </div>
      ),
    },
  ];

  const getCategoryColor = (category: string) => {
    const colors = {
      'Banking': 'blue',
      'Financial': 'green',
      'Fraud': 'red',
      'Service': 'orange'
    };
    return colors[category] || 'default';
  };

  const getStatusColor = (status: string) => {
    const colors = {
      'pending': 'orange',
      'in_progress': 'blue',
      'completed': 'green',
      'rejected': 'red'
    };
    return colors[status] || 'default';
  };

  const viewComplaint = (complaint: any) => {
    setSelectedComplaint(complaint);
    setModalVisible(true);
  };

  const editComplaint = (complaint: any) => {
    // Navigate to edit form
    console.log('Edit complaint:', complaint);
  };

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3>Complaint Management</h3>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          Add New Complaint
        </Button>
      </div>
      
      <Table
        dataSource={complaints}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
      />
      
      <Modal
        title="Complaint Details"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedComplaint && <ComplaintDetails complaint={selectedComplaint} />}
      </Modal>
    </div>
  );
};

export default ComplaintManagement;
```

## 3. Web API Architecture

### 3.1 FastAPI Backend Service

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from typing import List, Dict, Any, Optional
import json

app = FastAPI(
    title="Complaint Analysis Web API",
    description="AI-powered complaint analysis system for Pakistan banking sector",
    version="1.0.0"
)

# CORS middleware for web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Web API Endpoints
@app.get("/api/dashboard/overview")
async def get_dashboard_overview(current_user: User = Depends(get_current_user)):
    """Get dashboard overview statistics"""
    try:
        stats = await dashboard_service.get_overview_stats()
        return {
            "total_complaints": stats["total_complaints"],
            "pending_complaints": stats["pending_complaints"],
            "completed_investigations": stats["completed_investigations"],
            "compliance_rate": stats["compliance_rate"],
            "recent_activity": stats["recent_activity"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/complaints")
async def create_complaint(
    complaint_data: ComplaintCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create new complaint"""
    try:
        complaint = await complaint_service.create_complaint(
            complaint_data.dict(),
            current_user.id
        )
        return {"complaint_id": complaint.id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/complaints")
async def get_complaints(
    page: int = 1,
    limit: int = 10,
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get paginated complaints list"""
    try:
        complaints = await complaint_service.get_complaints(
            page=page,
            limit=limit,
            category=category,
            status=status,
            user_id=current_user.id
        )
        return {
            "complaints": complaints["data"],
            "total": complaints["total"],
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/complaints/{complaint_id}/analyze")
async def analyze_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user)
):
    """Trigger AI analysis for complaint"""
    try:
        # Start background task for AI analysis
        task = asyncio.create_task(
            ai_orchestrator.analyze_complaint_async(complaint_id)
        )
        
        return {
            "task_id": str(task),
            "status": "analysis_started",
            "estimated_time": "2-5 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/complaints/{complaint_id}/analysis")
async def get_analysis_result(
    complaint_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get AI analysis results"""
    try:
        analysis = await ai_orchestrator.get_analysis_result(complaint_id)
        return {
            "complaint_id": complaint_id,
            "analysis": analysis,
            "confidence_score": analysis.get("confidence_score", 0),
            "legal_compliance": analysis.get("legal_compliance", {}),
            "recommendations": analysis.get("recommendations", [])
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Analysis not found")

@app.post("/api/complaints/{complaint_id}/investigate")
async def start_investigation(
    complaint_id: int,
    investigation_data: InvestigationRequest,
    current_user: User = Depends(get_current_user)
):
    """Start investigation process"""
    try:
        investigation = await investigation_service.start_investigation(
            complaint_id,
            investigation_data.dict(),
            current_user.id
        )
        return {
            "investigation_id": investigation.id,
            "status": "started",
            "estimated_completion": investigation.estimated_completion
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/investigations/{investigation_id}/report")
async def get_investigation_report(
    investigation_id: int,
    format: str = "json",  # json, pdf, html
    current_user: User = Depends(get_current_user)
):
    """Get investigation report in specified format"""
    try:
        report = await investigation_service.get_report(
            investigation_id,
            format,
            current_user.id
        )
        
        if format == "pdf":
            return Response(
                content=report,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=report.pdf"}
            )
        elif format == "html":
            return Response(
                content=report,
                media_type="text/html"
            )
        else:
            return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Report not found")

@app.get("/api/legal/compliance-check")
async def check_legal_compliance(
    complaint_id: int,
    current_user: User = Depends(get_current_user)
):
    """Check legal compliance for complaint"""
    try:
        compliance = await legal_service.check_compliance(complaint_id)
        return {
            "complaint_id": complaint_id,
            "crpc_compliance": compliance["crpc_compliance"],
            "nab_compliance": compliance["nab_compliance"],
            "overall_score": compliance["overall_score"],
            "violations": compliance["violations"],
            "recommendations": compliance["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/dashboard")
async def get_analytics_data(
    period: str = "30d",  # 7d, 30d, 90d, 1y
    current_user: User = Depends(get_current_user)
):
    """Get analytics data for dashboard"""
    try:
        analytics = await analytics_service.get_dashboard_data(period)
        return {
            "complaints_trend": analytics["complaints_trend"],
            "category_distribution": analytics["category_distribution"],
            "compliance_trends": analytics["compliance_trends"],
            "investigation_metrics": analytics["investigation_metrics"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 4. Web Security Implementation

### 4.1 Authentication & Authorization

```python
# auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class WebAuthManager:
    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            return username
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

# Role-based access control for web users
class WebRBAC:
    def __init__(self):
        self.roles = {
            "admin": ["read", "write", "delete", "manage_users"],
            "investigator": ["read", "write", "create_reports"],
            "analyst": ["read", "analyze", "create_reports"],
            "viewer": ["read"]
        }
    
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        user_permissions = self.roles.get(user_role, [])
        return required_permission in user_permissions

# Web session management
class WebSessionManager:
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hour
    
    def create_session(self, user_id: str, user_role: str) -> str:
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "user_role": user_role,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        return session_id
    
    def validate_session(self, session_id: str) -> dict:
        if session_id not in self.active_sessions:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        session = self.active_sessions[session_id]
        if (datetime.utcnow() - session["last_activity"]).seconds > self.session_timeout:
            del self.active_sessions[session_id]
            raise HTTPException(status_code=401, detail="Session expired")
        
        session["last_activity"] = datetime.utcnow()
        return session
```

### 4.2 Web-Specific Security Measures

```python
# web_security.py
from fastapi import Request, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import hashlib

class WebSecurityManager:
    def __init__(self):
        self.rate_limits = {}
        self.blocked_ips = set()
        self.max_requests_per_minute = 60
    
    def rate_limit_check(self, request: Request):
        """Rate limiting for web API"""
        client_ip = request.client.host
        current_time = time.time()
        
        if client_ip in self.blocked_ips:
            raise HTTPException(status_code=429, detail="IP blocked")
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
        
        # Remove old requests
        self.rate_limits[client_ip] = [
            req_time for req_time in self.rate_limits[client_ip]
            if current_time - req_time < 60
        ]
        
        if len(self.rate_limits[client_ip]) >= self.max_requests_per_minute:
            self.blocked_ips.add(client_ip)
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        self.rate_limits[client_ip].append(current_time)
    
    def validate_web_request(self, request: Request):
        """Validate web request headers and content"""
        # Check for required headers
        required_headers = ["User-Agent", "Accept"]
        for header in required_headers:
            if header not in request.headers:
                raise HTTPException(status_code=400, detail=f"Missing {header} header")
        
        # Check for suspicious patterns
        user_agent = request.headers.get("User-Agent", "")
        if any(pattern in user_agent.lower() for pattern in ["bot", "crawler", "scraper"]):
            raise HTTPException(status_code=403, detail="Bot access not allowed")
    
    def sanitize_input(self, data: dict) -> dict:
        """Sanitize user input for web forms"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = value.replace("<", "&lt;").replace(">", "&gt;")
            else:
                sanitized[key] = value
        return sanitized

# CSRF protection for web forms
class CSRFProtection:
    def __init__(self):
        self.csrf_tokens = {}
    
    def generate_csrf_token(self, session_id: str) -> str:
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[session_id] = token
        return token
    
    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        return self.csrf_tokens.get(session_id) == token
```

## 5. Web Deployment Configuration

### 5.1 Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # API Routes
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static Files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # React App
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### 5.2 Docker Compose for Web Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  # React Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend

  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/complaints_db
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=your-secret-key
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  # PostgreSQL Database
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=complaints_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

## 6. Web Performance Optimization

### 6.1 Frontend Optimization

```typescript
// utils/performance.ts
import { lazy, Suspense } from 'react';

// Lazy loading for large components
const ComplaintDetails = lazy(() => import('./ComplaintDetails'));
const ReportGenerator = lazy(() => import('./ReportGenerator'));
const AnalyticsDashboard = lazy(() => import('./AnalyticsDashboard'));

// Code splitting for routes
export const routes = [
  {
    path: '/complaints/:id',
    component: lazy(() => import('./pages/ComplaintDetails')),
  },
  {
    path: '/reports',
    component: lazy(() => import('./pages/Reports')),
  },
  {
    path: '/analytics',
    component: lazy(() => import('./pages/Analytics')),
  }
];

// Memoization for expensive components
export const MemoizedComplaintTable = React.memo(ComplaintTable);
export const MemoizedDashboard = React.memo(Dashboard);

// Virtual scrolling for large lists
export const VirtualizedComplaintList = ({ complaints }) => {
  return (
    <FixedSizeList
      height={600}
      itemCount={complaints.length}
      itemSize={80}
      itemData={complaints}
    >
      {({ index, style, data }) => (
        <div style={style}>
          <ComplaintItem complaint={data[index]} />
        </div>
      )}
    </FixedSizeList>
  );
};
```

### 6.2 Backend Caching Strategy

```python
# caching.py
import redis
from functools import wraps
import json
import hashlib

class WebCacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.default_ttl = 3600  # 1 hour
    
    def cache_response(self, ttl: int = None):
        """Decorator for caching API responses"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.generate_cache_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                self.redis_client.setex(
                    cache_key, 
                    ttl or self.default_ttl, 
                    json.dumps(result, default=str)
                )
                return result
            return wrapper
        return decorator
    
    def generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        keys = self.redis_client.keys(f"cache:{pattern}*")
        if keys:
            self.redis_client.delete(*keys)

# Usage in API endpoints
@cache_manager.cache_response(ttl=1800)  # 30 minutes
async def get_dashboard_overview():
    # Expensive operation
    return await dashboard_service.get_overview_stats()

@cache_manager.cache_response(ttl=3600)  # 1 hour
async def get_complaints_list(page: int, limit: int):
    return await complaint_service.get_complaints(page, limit)
```

This web-based system provides a comprehensive solution for AI-powered complaint analysis with a focus on web accessibility, security, and performance optimization.