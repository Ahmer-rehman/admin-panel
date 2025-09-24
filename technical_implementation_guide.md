# Technical Implementation Guide
## AI-Powered Complaint Analysis System

### Core Implementation Components

## 1. FastAPI Backend Service

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import asyncio
from typing import List, Dict, Any

app = FastAPI(title="Complaint Analysis System", version="1.0.0")
security = HTTPBearer()

# Database models
class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True)
    complaint_text = Column(Text)
    category = Column(String(100))
    priority = Column(Integer)
    status = Column(String(50))
    created_at = Column(DateTime)
    legal_compliance_score = Column(Float)

# AI Orchestrator Service
class AIOrchestrator:
    def __init__(self):
        self.chatgpt = ChatGPTClient()
        self.gemini = GeminiClient()
        self.llama = LLaMAClient()
    
    async def analyze_complaint(self, complaint_data: Dict) -> Dict:
        tasks = [
            self.chatgpt.analyze(complaint_data),
            self.gemini.analyze(complaint_data),
            self.llama.analyze(complaint_data)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self.aggregate_results(results)

# Legal Compliance Service
class LegalComplianceService:
    def __init__(self):
        self.crpc_db = CRPCDatabase()
        self.nab_db = NABDatabase()
    
    def check_compliance(self, complaint_data: Dict) -> Dict:
        crpc_score = self.crpc_db.assess_compliance(complaint_data)
        nab_score = self.nab_db.assess_compliance(complaint_data)
        
        return {
            "crpc_compliance": crpc_score,
            "nab_compliance": nab_score,
            "overall_score": (crpc_score + nab_score) / 2,
            "violations": self.detect_violations(complaint_data)
        }

# API Endpoints
@app.post("/api/complaints/analyze")
async def analyze_complaint(
    complaint: ComplaintRequest,
    current_user: User = Depends(get_current_user)
):
    ai_orchestrator = AIOrchestrator()
    legal_service = LegalComplianceService()
    
    # Parallel processing
    ai_analysis, legal_compliance = await asyncio.gather(
        ai_orchestrator.analyze_complaint(complaint.dict()),
        legal_service.check_compliance(complaint.dict())
    )
    
    return {
        "complaint_id": complaint.id,
        "ai_analysis": ai_analysis,
        "legal_compliance": legal_compliance,
        "recommendations": generate_recommendations(ai_analysis, legal_compliance)
    }
```

## 2. React Frontend Dashboard

```typescript
// components/ComplaintDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Table, Progress } from 'antd';
import { LineChart, BarChart, PieChart } from 'recharts';

interface ComplaintData {
  id: string;
  category: string;
  priority: number;
  status: string;
  compliance_score: number;
  ai_analysis: any;
}

const ComplaintDashboard: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchComplaints();
  }, []);

  const fetchComplaints = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/complaints');
      const data = await response.json();
      setComplaints(data);
    } catch (error) {
      console.error('Error fetching complaints:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: number) => (
        <Progress percent={priority} size="small" />
      ),
    },
    {
      title: 'Compliance Score',
      dataIndex: 'compliance_score',
      key: 'compliance_score',
      render: (score: number) => (
        <Progress 
          percent={score} 
          status={score > 80 ? 'success' : score > 60 ? 'normal' : 'exception'}
        />
      ),
    },
  ];

  return (
    <div className="dashboard">
      <Row gutter={16}>
        <Col span={24}>
          <Card title="Complaint Analysis Dashboard">
            <Table 
              dataSource={complaints} 
              columns={columns} 
              loading={loading}
              rowKey="id"
            />
          </Card>
        </Col>
      </Row>
      
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Compliance Trends">
            <LineChart data={complaints} width={400} height={300}>
              <XAxis dataKey="created_at" />
              <YAxis />
              <CartesianGrid strokeDasharray="3 3" />
              <Line type="monotone" dataKey="compliance_score" stroke="#8884d8" />
            </LineChart>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Category Distribution">
            <PieChart width={400} height={300}>
              <Pie
                data={complaints}
                dataKey="category"
                nameKey="category"
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                label
              />
            </PieChart>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ComplaintDashboard;
```

## 3. Database Schema

```sql
-- PostgreSQL Schema
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    complaint_text TEXT NOT NULL,
    category VARCHAR(100),
    priority INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    legal_compliance_score FLOAT,
    ai_analysis JSONB,
    investigation_report JSONB
);

CREATE TABLE legal_frameworks (
    id SERIAL PRIMARY KEY,
    framework_name VARCHAR(100) NOT NULL,
    section_number VARCHAR(50),
    section_text TEXT,
    applicable_categories TEXT[],
    compliance_requirements JSONB
);

CREATE TABLE investigation_reports (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER REFERENCES complaints(id),
    report_type VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_content JSONB,
    legal_compliance_check JSONB,
    ai_confidence_score FLOAT
);

-- Indexes for performance
CREATE INDEX idx_complaints_category ON complaints(category);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_created_at ON complaints(created_at);
CREATE INDEX idx_legal_frameworks_category ON legal_frameworks USING GIN(applicable_categories);
```

## 4. Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/complaints_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=complaints_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

volumes:
  postgres_data:
```

## 5. Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: complaint-analysis-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: complaint-analysis
  template:
    metadata:
      labels:
        app: complaint-analysis
    spec:
      containers:
      - name: app
        image: complaint-analysis:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: complaint-analysis-service
spec:
  selector:
    app: complaint-analysis
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 6. Monitoring and Logging

```python
# monitoring.py
import logging
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request
import time

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

This implementation provides a complete technical foundation for the AI-powered complaint analysis system, including backend services, frontend dashboard, database schema, containerization, and monitoring capabilities.