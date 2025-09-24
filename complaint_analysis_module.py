"""
Pakistan Banking Compliance & Complaint Analysis System (PBCCAS)
Complaint Analysis Module

This module handles complaint intake, analysis, and investigation report generation
with integration of Pakistan's legal framework (CRPC, NAB, Banking Laws).
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import spacy
from transformers import pipeline, AutoTokenizer, AutoModel
import openai
import google.generativeai as genai
from langchain.llms import LlamaCpp
from langchain.embeddings import HuggingFaceEmbeddings

# Load Pakistan-specific legal models and configurations
Base = declarative_base()

class ComplaintType(Enum):
    """Categories of complaints based on Pakistan banking regulations"""
    FRAUD = "fraud"
    UNAUTHORIZED_TRANSACTION = "unauthorized_transaction"
    LOAN_HARASSMENT = "loan_harassment"
    INTEREST_DISPUTES = "interest_disputes"
    ACCOUNT_CLOSURE = "account_closure"
    DISCRIMINATION = "discrimination"
    PRIVACY_VIOLATION = "privacy_violation"
    CORRUPTION = "corruption"
    MONEY_LAUNDERING = "money_laundering"
    FOREIGN_EXCHANGE = "foreign_exchange"

class LegalFramework(Enum):
    """Pakistan legal frameworks applicable to banking complaints"""
    CRPC = "crpc"  # Code of Criminal Procedure
    NAB = "nab"    # National Accountability Bureau
    SBP = "sbp"    # State Bank of Pakistan
    BCO = "bco"    # Banking Companies Ordinance
    AML = "aml"    # Anti-Money Laundering Act

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ComplaintEntity:
    """Extracted entities from complaint text"""
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "PKR"
    date_incident: Optional[datetime] = None
    branch_location: Optional[str] = None
    complainant_name: Optional[str] = None
    complainant_cnic: Optional[str] = None
    complainant_phone: Optional[str] = None
    suspect_names: List[str] = field(default_factory=list)
    transaction_ids: List[str] = field(default_factory=list)

@dataclass
class LegalCitation:
    """Legal reference with specific section and relevance"""
    framework: LegalFramework
    section: str
    title: str
    description: str
    relevance_score: float
    applicable_penalty: Optional[str] = None

@dataclass
class ComplianceViolation:
    """Identified compliance violation"""
    regulation: str
    severity: Priority
    description: str
    legal_citations: List[LegalCitation]
    recommended_action: str
    financial_impact: Optional[float] = None

class Complaint(Base):
    """Database model for complaints"""
    __tablename__ = 'complaints'
    
    id = Column(Integer, primary_key=True)
    complaint_id = Column(String(50), unique=True, nullable=False)
    complainant_name = Column(String(200))
    complainant_cnic = Column(String(15))
    complainant_phone = Column(String(15))
    complaint_text = Column(Text, nullable=False)
    complaint_type = Column(String(50))
    priority = Column(Integer)
    status = Column(String(20), default='received')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bank_name = Column(String(100))
    amount_involved = Column(Float)
    incident_date = Column(DateTime)
    investigation_report_id = Column(String(50))

class ComplaintAnalyzer:
    """Main complaint analysis engine with AI integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.nlp = spacy.load("en_core_web_sm")
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.embeddings = HuggingFaceEmbeddings()
        
        # Initialize AI platforms
        self.setup_ai_platforms()
        
        # Load Pakistan legal knowledge base
        self.legal_kb = self.load_legal_knowledge_base()
        
        # Database setup
        self.engine = create_engine(config['database_url'])
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def setup_ai_platforms(self):
        """Initialize multiple AI platforms for analysis"""
        # OpenAI ChatGPT
        openai.api_key = self.config.get('openai_api_key')
        
        # Google Gemini
        genai.configure(api_key=self.config.get('gemini_api_key'))
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Local LLaMA
        self.llama_model = LlamaCpp(
            model_path=self.config.get('llama_model_path', './models/llama-2-7b-chat.gguf'),
            temperature=0.3,
            max_tokens=2000,
            top_p=1,
            verbose=False
        )

    def load_legal_knowledge_base(self) -> Dict[str, List[LegalCitation]]:
        """Load Pakistan legal framework knowledge base"""
        legal_kb = {
            'crpc': [
                LegalCitation(
                    framework=LegalFramework.CRPC,
                    section="Section 154",
                    title="Information in cognizable cases",
                    description="First Information Report (FIR) for financial crimes",
                    relevance_score=0.9,
                    applicable_penalty="Investigation initiation"
                ),
                LegalCitation(
                    framework=LegalFramework.CRPC,
                    section="Section 161",
                    title="Examination of witnesses by police",
                    description="Statement recording procedures for banking complaints",
                    relevance_score=0.8,
                    applicable_penalty="Legal statement recording"
                ),
            ],
            'nab': [
                LegalCitation(
                    framework=LegalFramework.NAB,
                    section="Section 9",
                    title="Powers of Chairman, Deputy Chairman, DG and others",
                    description="Investigation powers for corruption and financial crimes",
                    relevance_score=0.95,
                    applicable_penalty="Up to 14 years imprisonment and fine"
                ),
                LegalCitation(
                    framework=LegalFramework.NAB,
                    section="Section 15",
                    title="Plea bargain and voluntary return",
                    description="Voluntary return of assets in corruption cases",
                    relevance_score=0.7,
                    applicable_penalty="Asset recovery with reduced penalty"
                ),
            ],
            'sbp': [
                LegalCitation(
                    framework=LegalFramework.SBP,
                    section="Banking Policy Circular No. 2021",
                    title="Customer complaint handling",
                    description="Mandatory complaint resolution within 45 days",
                    relevance_score=0.8,
                    applicable_penalty="Regulatory fine up to PKR 10 million"
                ),
            ],
            'aml': [
                LegalCitation(
                    framework=LegalFramework.AML,
                    section="Section 3",
                    title="Prohibition of money laundering",
                    description="Anti-money laundering compliance requirements",
                    relevance_score=0.9,
                    applicable_penalty="Imprisonment up to 10 years and fine up to PKR 50 million"
                ),
            ]
        }
        return legal_kb

    async def analyze_complaint(self, complaint_text: str, complainant_info: Dict) -> Dict[str, Any]:
        """Main complaint analysis function using multiple AI platforms"""
        
        # Extract entities
        entities = await self.extract_entities(complaint_text)
        
        # Classify complaint type
        complaint_type = await self.classify_complaint(complaint_text)
        
        # Analyze sentiment and urgency
        sentiment_analysis = await self.analyze_sentiment(complaint_text)
        
        # Get multi-AI analysis
        ai_analysis = await self.get_multi_ai_analysis(complaint_text)
        
        # Check legal compliance
        legal_analysis = await self.check_legal_compliance(complaint_text, entities)
        
        # Determine priority
        priority = await self.calculate_priority(complaint_text, entities, legal_analysis)
        
        # Generate preliminary investigation steps
        investigation_steps = await self.generate_investigation_steps(
            complaint_text, entities, legal_analysis
        )
        
        return {
            'complaint_id': self.generate_complaint_id(),
            'entities': entities,
            'complaint_type': complaint_type,
            'sentiment': sentiment_analysis,
            'ai_analysis': ai_analysis,
            'legal_analysis': legal_analysis,
            'priority': priority,
            'investigation_steps': investigation_steps,
            'compliance_violations': await self.detect_violations(entities, legal_analysis),
            'recommended_actions': await self.generate_recommendations(legal_analysis, priority)
        }

    async def extract_entities(self, text: str) -> ComplaintEntity:
        """Extract key entities from complaint text using NLP"""
        doc = self.nlp(text)
        entities = ComplaintEntity()
        
        # Extract bank names (common Pakistani banks)
        bank_patterns = [
            r'\b(HBL|UBL|MCB|ABL|NBP|Standard Chartered|Askari|Soneri|Faysal|JS Bank|Bank Alfalah|BOP|Allied Bank|Meezan Bank|Bank Al Habib)\b',
            r'\b(\w+\s+Bank)\b'
        ]
        
        for pattern in bank_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.bank_name = match.group(1)
                break
        
        # Extract account numbers
        account_pattern = r'\b\d{10,20}\b'
        account_matches = re.findall(account_pattern, text)
        if account_matches:
            entities.account_number = account_matches[0]
        
        # Extract amounts
        amount_patterns = [
            r'(?:PKR|Rs\.?|Rupees)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:PKR|Rs\.?|Rupees)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:thousand|lakh|crore)'
        ]
        
        for pattern in amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    entities.amount = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract CNIC numbers
        cnic_pattern = r'\b\d{5}-\d{7}-\d{1}\b'
        cnic_matches = re.findall(cnic_pattern, text)
        if cnic_matches:
            entities.complainant_cnic = cnic_matches[0]
        
        # Extract phone numbers
        phone_pattern = r'\b(?:\+92|0)?3\d{9}\b'
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            entities.complainant_phone = phone_matches[0]
        
        # Extract named entities using spaCy
        for ent in doc.ents:
            if ent.label_ == "PERSON" and not entities.complainant_name:
                entities.complainant_name = ent.text
            elif ent.label_ == "GPE":  # Geographic entity
                entities.branch_location = ent.text
            elif ent.label_ == "DATE":
                # Try to parse date
                try:
                    # This would need more sophisticated date parsing
                    entities.date_incident = datetime.now()  # Placeholder
                except:
                    pass
        
        return entities

    async def classify_complaint(self, text: str) -> ComplaintType:
        """Classify complaint type using AI analysis"""
        
        # Keywords mapping for Pakistani banking context
        type_keywords = {
            ComplaintType.FRAUD: ['fraud', 'fake', 'scam', 'cheat', 'deceive', 'unauthorized withdrawal'],
            ComplaintType.UNAUTHORIZED_TRANSACTION: ['unauthorized', 'without permission', 'illegal transaction'],
            ComplaintType.LOAN_HARASSMENT: ['harassment', 'pressure', 'threats', 'loan recovery', 'force'],
            ComplaintType.INTEREST_DISPUTES: ['interest', 'markup', 'profit', 'riba', 'islamic banking'],
            ComplaintType.CORRUPTION: ['bribe', 'corruption', 'kickback', 'illegal payment'],
            ComplaintType.MONEY_LAUNDERING: ['money laundering', 'hawala', 'illegal transfer', 'suspicious transaction'],
        }
        
        text_lower = text.lower()
        scores = {}
        
        for complaint_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[complaint_type] = score
        
        # Return the type with highest score, or fraud as default
        return max(scores.items(), key=lambda x: x[1])[0] if max(scores.values()) > 0 else ComplaintType.FRAUD

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment and emotional urgency"""
        sentiment_result = self.sentiment_analyzer(text)[0]
        
        # Additional urgency indicators for Pakistani context
        urgency_keywords = [
            'urgent', 'emergency', 'immediate', 'help', 'crisis', 'desperate',
            'فوری', 'ہنگامی', 'مدد', 'بحران'  # Urdu urgency terms
        ]
        
        urgency_score = sum(1 for keyword in urgency_keywords if keyword.lower() in text.lower())
        
        return {
            'sentiment': sentiment_result['label'],
            'confidence': sentiment_result['score'],
            'urgency_score': min(urgency_score / len(urgency_keywords), 1.0),
            'emotional_indicators': urgency_keywords
        }

    async def get_multi_ai_analysis(self, text: str) -> Dict[str, str]:
        """Get analysis from multiple AI platforms"""
        
        prompt = f"""
        Analyze this banking complaint from Pakistan and provide:
        1. Key issues identified
        2. Potential legal violations under Pakistan law
        3. Recommended immediate actions
        4. Risk assessment for the bank
        
        Complaint: {text}
        """
        
        analyses = {}
        
        # ChatGPT Analysis
        try:
            chatgpt_response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            analyses['chatgpt'] = chatgpt_response.choices[0].message.content
        except Exception as e:
            analyses['chatgpt'] = f"Error: {str(e)}"
        
        # Gemini Analysis
        try:
            gemini_response = await asyncio.to_thread(
                self.gemini_model.generate_content, prompt
            )
            analyses['gemini'] = gemini_response.text
        except Exception as e:
            analyses['gemini'] = f"Error: {str(e)}"
        
        # LLaMA Analysis
        try:
            llama_response = await asyncio.to_thread(
                self.llama_model, prompt
            )
            analyses['llama'] = llama_response
        except Exception as e:
            analyses['llama'] = f"Error: {str(e)}"
        
        return analyses

    async def check_legal_compliance(self, text: str, entities: ComplaintEntity) -> Dict[str, Any]:
        """Check compliance against Pakistan legal framework"""
        
        applicable_laws = []
        violations = []
        
        # Check CRPC applicability
        if any(keyword in text.lower() for keyword in ['fraud', 'theft', 'criminal']):
            applicable_laws.extend(self.legal_kb['crpc'])
        
        # Check NAB applicability
        if any(keyword in text.lower() for keyword in ['corruption', 'bribe', 'kickback']):
            applicable_laws.extend(self.legal_kb['nab'])
            
        # Check AML applicability
        if entities.amount and entities.amount > 500000:  # PKR 5 lakh threshold
            applicable_laws.extend(self.legal_kb['aml'])
        
        # Check SBP regulations
        applicable_laws.extend(self.legal_kb['sbp'])
        
        return {
            'applicable_laws': applicable_laws,
            'compliance_status': 'requires_investigation',
            'mandatory_reporting': entities.amount and entities.amount > 1000000,  # PKR 10 lakh
            'timeline_requirements': {
                'initial_response': timedelta(days=3),
                'investigation_completion': timedelta(days=45),
                'final_report': timedelta(days=60)
            }
        }

    async def calculate_priority(self, text: str, entities: ComplaintEntity, legal_analysis: Dict) -> Priority:
        """Calculate complaint priority based on multiple factors"""
        
        priority_score = 0
        
        # Amount-based priority
        if entities.amount:
            if entities.amount > 10000000:  # PKR 1 crore
                priority_score += 4
            elif entities.amount > 1000000:  # PKR 10 lakh
                priority_score += 3
            elif entities.amount > 100000:  # PKR 1 lakh
                priority_score += 2
            else:
                priority_score += 1
        
        # Legal framework priority
        if any(law.framework == LegalFramework.NAB for law in legal_analysis['applicable_laws']):
            priority_score += 3
        if any(law.framework == LegalFramework.CRPC for law in legal_analysis['applicable_laws']):
            priority_score += 2
        
        # Urgency keywords
        urgent_keywords = ['urgent', 'emergency', 'immediate', 'crisis']
        if any(keyword in text.lower() for keyword in urgent_keywords):
            priority_score += 2
        
        # Convert score to priority
        if priority_score >= 8:
            return Priority.CRITICAL
        elif priority_score >= 6:
            return Priority.HIGH
        elif priority_score >= 3:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    async def generate_investigation_steps(self, text: str, entities: ComplaintEntity, legal_analysis: Dict) -> List[Dict]:
        """Generate structured investigation steps"""
        
        steps = []
        
        # Standard initial steps
        steps.append({
            'step': 1,
            'action': 'Acknowledge complaint receipt',
            'timeline': '24 hours',
            'responsible': 'Customer Service',
            'legal_requirement': 'SBP Banking Policy'
        })
        
        steps.append({
            'step': 2,
            'action': 'Gather initial documentation',
            'timeline': '3 days',
            'responsible': 'Investigation Team',
            'required_documents': [
                'Account statements',
                'Transaction logs',
                'CCTV footage (if applicable)',
                'Staff statements'
            ]
        })
        
        # Add specific steps based on complaint type and legal requirements
        if entities.amount and entities.amount > 1000000:
            steps.append({
                'step': 3,
                'action': 'File mandatory reporting to SBP/FMU',
                'timeline': '3 days',
                'responsible': 'Compliance Officer',
                'legal_requirement': 'AML Act 2010'
            })
        
        if any(law.framework == LegalFramework.NAB for law in legal_analysis['applicable_laws']):
            steps.append({
                'step': len(steps) + 1,
                'action': 'Coordinate with NAB if required',
                'timeline': '7 days',
                'responsible': 'Legal Department',
                'legal_requirement': 'NAB Ordinance 1999'
            })
        
        steps.append({
            'step': len(steps) + 1,
            'action': 'Complete investigation and prepare report',
            'timeline': '45 days',
            'responsible': 'Investigation Team',
            'deliverables': [
                'Investigation report',
                'Compliance assessment',
                'Recommended actions',
                'Penalty/compensation determination'
            ]
        })
        
        return steps

    async def detect_violations(self, entities: ComplaintEntity, legal_analysis: Dict) -> List[ComplianceViolation]:
        """Detect potential compliance violations"""
        
        violations = []
        
        # Large transaction reporting violation
        if entities.amount and entities.amount > 1000000:
            violations.append(ComplianceViolation(
                regulation="AML Act 2010 - Large Transaction Reporting",
                severity=Priority.HIGH,
                description="Potential failure to report large transaction to FMU",
                legal_citations=self.legal_kb['aml'],
                recommended_action="Verify CTR filing and report to FMU if missed",
                financial_impact=entities.amount * 0.01  # 1% penalty
            ))
        
        # Customer complaint handling violation
        violations.append(ComplianceViolation(
            regulation="SBP Banking Policy - Complaint Handling",
            severity=Priority.MEDIUM,
            description="Must resolve complaint within 45 days",
            legal_citations=self.legal_kb['sbp'],
            recommended_action="Ensure timely resolution and customer communication",
            financial_impact=1000000  # PKR 10 lakh potential fine
        ))
        
        return violations

    async def generate_recommendations(self, legal_analysis: Dict, priority: Priority) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Priority-based recommendations
        if priority == Priority.CRITICAL:
            recommendations.append("Escalate to senior management immediately")
            recommendations.append("Consider external legal counsel")
            recommendations.append("Prepare for potential regulatory scrutiny")
        
        # Legal framework specific recommendations
        applicable_frameworks = [law.framework for law in legal_analysis['applicable_laws']]
        
        if LegalFramework.NAB in applicable_frameworks:
            recommendations.append("Coordinate with NAB compliance requirements")
            recommendations.append("Prepare voluntary disclosure if applicable")
        
        if LegalFramework.CRPC in applicable_frameworks:
            recommendations.append("Cooperate with law enforcement investigation")
            recommendations.append("Preserve all relevant evidence")
        
        # Standard recommendations
        recommendations.extend([
            "Document all investigation steps",
            "Maintain regular customer communication",
            "Ensure compliance with reporting timelines",
            "Review and update internal controls"
        ])
        
        return recommendations

    def generate_complaint_id(self) -> str:
        """Generate unique complaint ID"""
        import uuid
        return f"PKB-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    async def save_complaint(self, analysis_result: Dict[str, Any], complainant_info: Dict) -> str:
        """Save complaint and analysis to database"""
        
        complaint = Complaint(
            complaint_id=analysis_result['complaint_id'],
            complainant_name=complainant_info.get('name'),
            complainant_cnic=analysis_result['entities'].complainant_cnic,
            complainant_phone=analysis_result['entities'].complainant_phone,
            complaint_text=complainant_info.get('complaint_text'),
            complaint_type=analysis_result['complaint_type'].value,
            priority=analysis_result['priority'].value,
            bank_name=analysis_result['entities'].bank_name,
            amount_involved=analysis_result['entities'].amount,
            incident_date=analysis_result['entities'].date_incident
        )
        
        self.session.add(complaint)
        self.session.commit()
        
        return analysis_result['complaint_id']

# Example usage
if __name__ == "__main__":
    import asyncio
    
    config = {
        'database_url': 'postgresql://user:password@localhost/pbccas',
        'openai_api_key': 'your-openai-key',
        'gemini_api_key': 'your-gemini-key',
        'llama_model_path': './models/llama-2-7b-chat.gguf'
    }
    
    analyzer = ComplaintAnalyzer(config)
    
    sample_complaint = """
    I am filing a complaint against HBL Bank Lahore Branch. They have 
    fraudulently withdrawn PKR 500,000 from my account 12345678901234 
    without my permission. This happened on 15th December 2024. I suspect 
    the branch manager Mr. Ahmed is involved in this corruption. My CNIC 
    is 12345-1234567-1 and phone is 03001234567. This is urgent as I need 
    this money for my daughter's medical treatment.
    """
    
    async def test_analysis():
        result = await analyzer.analyze_complaint(
            sample_complaint,
            {'name': 'Muhammad Ali', 'complaint_text': sample_complaint}
        )
        print(json.dumps(result, default=str, indent=2))
    
    # asyncio.run(test_analysis())