"""
Pakistan Banking Compliance & Complaint Analysis System (PBCCAS)
Legal Compliance Engine

This module embeds and applies Pakistan's legal framework including CRPC, NAB, 
SBP regulations, and banking laws to ensure compliance and detect violations.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import re
from pathlib import Path
import asyncio
from collections import defaultdict

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import sqlite3

class LegalFramework(Enum):
    """Pakistan Legal Frameworks"""
    CRPC = "Code of Criminal Procedure 1898"
    NAB = "National Accountability Bureau Ordinance 1999"
    SBP = "State Bank of Pakistan Act 1956"
    BCO = "Banking Companies Ordinance 1962"
    AML = "Anti-Money Laundering Act 2010"
    PPC = "Pakistan Penal Code 1860"
    FIA = "Federal Investigation Agency Act 1974"
    PER = "Protection of Economic Reforms Act 1992"

class ViolationType(Enum):
    """Types of legal violations"""
    PROCEDURAL = "procedural_violation"
    SUBSTANTIVE = "substantive_violation"
    REGULATORY = "regulatory_violation"
    CRIMINAL = "criminal_violation"
    ADMINISTRATIVE = "administrative_violation"

class SeverityLevel(Enum):
    """Severity levels for violations"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class LegalSection:
    """Individual legal section/article"""
    framework: LegalFramework
    section_number: str
    title: str
    content: str
    keywords: List[str]
    penalties: List[str]
    applicability_conditions: List[str]
    related_sections: List[str] = field(default_factory=list)
    amendments: List[str] = field(default_factory=list)
    case_law_references: List[str] = field(default_factory=list)

@dataclass
class ComplianceRule:
    """Compliance rule derived from legal sections"""
    rule_id: str
    name: str
    description: str
    legal_basis: List[LegalSection]
    conditions: List[str]
    actions_required: List[str]
    timeline: timedelta
    penalties: List[str]
    exemptions: List[str] = field(default_factory=list)

@dataclass
class ViolationAssessment:
    """Assessment of a potential legal violation"""
    violation_id: str
    rule_violated: ComplianceRule
    violation_type: ViolationType
    severity: SeverityLevel
    confidence_score: float
    evidence: List[str]
    applicable_penalties: List[str]
    recommended_actions: List[str]
    legal_citations: List[str]
    financial_impact: Optional[float] = None
    timeline_for_resolution: Optional[timedelta] = None

class LegalKnowledgeBase:
    """Pakistan legal knowledge base with embedded legal texts"""
    
    def __init__(self, db_path: str = "./legal_kb.db"):
        self.db_path = db_path
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Initialize database
        self.init_database()
        
        # Load legal frameworks
        self.legal_sections = self.load_pakistan_legal_framework()
        self.compliance_rules = self.generate_compliance_rules()
        
        # Create vector store for semantic search
        self.vector_store = self.create_vector_store()

    def init_database(self):
        """Initialize SQLite database for legal knowledge"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS legal_sections (
                id INTEGER PRIMARY KEY,
                framework TEXT,
                section_number TEXT,
                title TEXT,
                content TEXT,
                keywords TEXT,
                penalties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_rules (
                id INTEGER PRIMARY KEY,
                rule_id TEXT UNIQUE,
                name TEXT,
                description TEXT,
                legal_basis TEXT,
                conditions TEXT,
                actions_required TEXT,
                timeline_days INTEGER,
                penalties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS violation_assessments (
                id INTEGER PRIMARY KEY,
                violation_id TEXT UNIQUE,
                rule_id TEXT,
                violation_type TEXT,
                severity INTEGER,
                confidence_score REAL,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_id) REFERENCES compliance_rules (rule_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def load_pakistan_legal_framework(self) -> Dict[LegalFramework, List[LegalSection]]:
        """Load Pakistan's legal framework sections"""
        
        legal_sections = {
            LegalFramework.CRPC: [
                LegalSection(
                    framework=LegalFramework.CRPC,
                    section_number="154",
                    title="Information in cognizable cases",
                    content="""Every information relating to the commission of a cognizable offence, if given orally to an officer in charge of a police station, shall be reduced to writing by him or under his direction, and be read over to the informant; and every such information, whether given in writing or reduced to writing as aforesaid, shall be signed by the person giving it, and the substance thereof shall be entered in a book to be kept by such officer in such form as the Provincial Government may prescribe in this behalf.""",
                    keywords=["FIR", "cognizable offence", "police station", "information", "investigation"],
                    penalties=["Investigation initiation", "Legal proceedings"],
                    applicability_conditions=["Financial crimes above PKR 100,000", "Banking fraud", "Corruption cases"]
                ),
                LegalSection(
                    framework=LegalFramework.CRPC,
                    section_number="161",
                    title="Examination of witnesses by police",
                    content="""Any police officer making an investigation under this Chapter may examine orally any person supposed to be acquainted with the facts and circumstances of the case and shall reduce into writing any statement made by such person; but such person shall not be bound to answer, and his answers, if any, shall not be put to any oath.""",
                    keywords=["witness examination", "investigation", "statement recording", "police powers"],
                    penalties=["Legal statement on record", "Perjury charges if false"],
                    applicability_conditions=["Banking complaint investigation", "Fraud cases", "Corruption inquiry"]
                ),
                LegalSection(
                    framework=LegalFramework.CRPC,
                    section_number="173",
                    title="Report of police officer on completion of investigation",
                    content="""Every investigation under this Chapter shall be completed without unnecessary delay. As soon as it is completed, the officer in charge of the police station shall forward to a Magistrate empowered to take cognizance of the offence on a police report, a report in the form prescribed by the Provincial Government.""",
                    keywords=["police report", "investigation completion", "magistrate", "cognizance"],
                    penalties=["Case forwarding to court", "Legal proceedings"],
                    applicability_conditions=["Completion of banking fraud investigation", "Financial crime cases"]
                )
            ],
            
            LegalFramework.NAB: [
                LegalSection(
                    framework=LegalFramework.NAB,
                    section_number="9",
                    title="Powers of Chairman, Deputy Chairman, DG and others",
                    content="""The Chairman, Deputy Chairman, Director General and any officer of the Bureau authorized by the Chairman shall have powers to investigate any offence punishable under this Ordinance and shall exercise the powers of an officer-in-charge of a police station under the Code of Criminal Procedure, 1898.""",
                    keywords=["investigation powers", "corruption", "Chairman", "Director General", "Bureau"],
                    penalties=["Investigation proceedings", "Asset freezing", "Arrest powers"],
                    applicability_conditions=["Corruption over PKR 500,000", "Public office holders", "Banking sector corruption"]
                ),
                LegalSection(
                    framework=LegalFramework.NAB,
                    section_number="14",
                    title="Trial of offences",
                    content="""Save as provided in sections 25 and 26, all offences under this Ordinance shall be tried by an Accountability Court established under section 7 and no other court shall have jurisdiction to try such offences.""",
                    keywords=["accountability court", "trial", "jurisdiction", "offences"],
                    penalties=["Up to 14 years imprisonment", "Fine up to PKR 10 million", "Asset forfeiture"],
                    applicability_conditions=["Corruption cases", "Financial misconduct", "Banking sector violations"]
                ),
                LegalSection(
                    framework=LegalFramework.NAB,
                    section_number="15",
                    title="Plea bargain and voluntary return",
                    content="""An accused or a person who has been convicted may file an application before the Court for plea bargain. The Court may accept the plea bargain on such terms and conditions as it may deem fit including the return of assets or payment of damages.""",
                    keywords=["plea bargain", "voluntary return", "assets", "damages", "settlement"],
                    penalties=["Reduced sentence", "Asset recovery", "Disqualification"],
                    applicability_conditions=["First-time offenders", "Voluntary disclosure", "Asset recovery cases"]
                )
            ],
            
            LegalFramework.AML: [
                LegalSection(
                    framework=LegalFramework.AML,
                    section_number="3",
                    title="Prohibition of money laundering",
                    content="""No person shall commit money laundering. Money laundering means acquiring, converting, possessing, using or transferring property, knowing or having reason to believe that such property is proceeds of crime, for the purpose of concealing or disguising the illicit origin of the property or helping any person involved in the commission of the predicate offence to evade the legal consequences of such offence.""",
                    keywords=["money laundering", "proceeds of crime", "concealing", "disguising", "illicit origin"],
                    penalties=["Imprisonment up to 10 years", "Fine up to PKR 50 million", "Asset forfeiture"],
                    applicability_conditions=["Transactions above PKR 1 million", "Suspicious activity", "Cross-border transfers"]
                ),
                LegalSection(
                    framework=LegalFramework.AML,
                    section_number="7",
                    title="Reporting of suspicious transactions",
                    content="""Where a financial institution or designated non-financial business or profession suspects that funds are proceeds of crime or are related to money laundering or financing of terrorism, it shall as soon as possible but not later than seven working days report the transaction to the Financial Monitoring Unit.""",
                    keywords=["suspicious transactions", "FMU", "financial institution", "terrorism financing", "reporting"],
                    penalties=["Fine up to PKR 5 million", "License suspension", "Criminal proceedings"],
                    applicability_conditions=["All financial institutions", "Suspicious activity patterns", "Large cash transactions"]
                ),
                LegalSection(
                    framework=LegalFramework.AML,
                    section_number="15",
                    title="Record keeping requirements",
                    content="""Every financial institution and designated non-financial business or profession shall maintain all necessary records on transactions, both domestic and international, for at least five years from the date when the transaction was completed.""",
                    keywords=["record keeping", "five years", "transactions", "domestic", "international"],
                    penalties=["Fine up to PKR 2 million", "Regulatory action", "License issues"],
                    applicability_conditions=["All financial transactions", "Customer records", "Transaction documentation"]
                )
            ],
            
            LegalFramework.SBP: [
                LegalSection(
                    framework=LegalFramework.SBP,
                    section_number="Banking Policy 2021",
                    title="Customer complaint handling",
                    content="""Banks shall establish an effective complaint handling mechanism to address customer complaints promptly and fairly. All complaints must be acknowledged within 24 hours and resolved within 45 calendar days. Banks must maintain proper records of all complaints and their resolution.""",
                    keywords=["customer complaints", "24 hours", "45 days", "resolution", "records"],
                    penalties=["Fine up to PKR 10 million", "Regulatory censure", "Additional capital requirements"],
                    applicability_conditions=["All banking complaints", "Customer service issues", "Operational failures"]
                ),
                LegalSection(
                    framework=LegalFramework.SBP,
                    section_number="Prudential Regulation PR-07",
                    title="Large exposures",
                    content="""Banks shall not grant credit facilities to any single borrower or group of connected borrowers exceeding 25% of the bank's eligible capital. Exposures exceeding 15% must be reported to SBP within 15 days.""",
                    keywords=["large exposures", "25% limit", "eligible capital", "connected borrowers", "15 days reporting"],
                    penalties=["Additional provisioning", "Fine up to PKR 25 million", "Restriction on lending"],
                    applicability_conditions=["Credit facilities", "Large borrowers", "Connected parties"]
                )
            ],
            
            LegalFramework.BCO: [
                LegalSection(
                    framework=LegalFramework.BCO,
                    section_number="33A",
                    title="Disclosure of interest",
                    content="""No director or officer of a banking company shall, directly or indirectly, have any interest in any loan or advance made by the banking company, except with the prior approval of the State Bank and subject to such conditions as the State Bank may impose.""",
                    keywords=["director", "officer", "interest", "loan", "advance", "prior approval"],
                    penalties=["Imprisonment up to 3 years", "Fine up to PKR 1 million", "Disqualification"],
                    applicability_conditions=["Directors and officers", "Self-dealing", "Conflict of interest"]
                ),
                LegalSection(
                    framework=LegalFramework.BCO,
                    section_number="36",
                    title="Restrictions on loans and advances",
                    content="""No banking company shall grant any loan or advance against the security of its own shares or grant any unsecured loan or advance to any of its directors or to any firm in which any of its directors is interested as partner or guarantor.""",
                    keywords=["loan restrictions", "own shares", "unsecured loan", "directors", "partner", "guarantor"],
                    penalties=["Fine up to PKR 5 million", "Director disqualification", "Recovery action"],
                    applicability_conditions=["Director loans", "Share-backed lending", "Related party transactions"]
                )
            ]
        }
        
        return legal_sections

    def generate_compliance_rules(self) -> List[ComplianceRule]:
        """Generate compliance rules from legal sections"""
        
        rules = []
        
        # Rule 1: Mandatory complaint reporting
        rules.append(ComplianceRule(
            rule_id="COMP-001",
            name="Complaint Acknowledgment and Resolution",
            description="All customer complaints must be acknowledged within 24 hours and resolved within 45 days",
            legal_basis=[section for sections in self.legal_sections.values() for section in sections 
                        if "complaint" in section.keywords],
            conditions=[
                "Customer files a complaint",
                "Complaint received through any channel",
                "Complaint relates to banking services"
            ],
            actions_required=[
                "Acknowledge receipt within 24 hours",
                "Assign complaint ID",
                "Investigate the matter",
                "Provide resolution within 45 days",
                "Maintain proper records"
            ],
            timeline=timedelta(days=45),
            penalties=["Fine up to PKR 10 million", "Regulatory censure"]
        ))
        
        # Rule 2: Large transaction reporting
        rules.append(ComplianceRule(
            rule_id="COMP-002",
            name="Large Transaction Reporting",
            description="Transactions above PKR 1 million must be reported to FMU if suspicious",
            legal_basis=[section for sections in self.legal_sections.values() for section in sections 
                        if "suspicious" in section.keywords or "money laundering" in section.keywords],
            conditions=[
                "Transaction amount exceeds PKR 1,000,000",
                "Transaction appears suspicious",
                "Involves multiple accounts or jurisdictions"
            ],
            actions_required=[
                "Assess transaction for suspicion",
                "File STR with FMU within 7 days",
                "Maintain transaction records",
                "Monitor account activity"
            ],
            timeline=timedelta(days=7),
            penalties=["Fine up to PKR 50 million", "License suspension", "Criminal prosecution"]
        ))
        
        # Rule 3: Criminal investigation cooperation
        rules.append(ComplianceRule(
            rule_id="COMP-003",
            name="Law Enforcement Cooperation",
            description="Banks must cooperate with criminal investigations and provide required information",
            legal_basis=[section for sections in self.legal_sections.values() for section in sections 
                        if "investigation" in section.keywords],
            conditions=[
                "Receipt of investigation request",
                "Court order or legal notice",
                "NAB or FIA investigation"
            ],
            actions_required=[
                "Preserve relevant records",
                "Provide requested information",
                "Cooperate with investigators",
                "Maintain confidentiality"
            ],
            timeline=timedelta(days=15),
            penalties=["Contempt of court", "Obstruction charges", "Regulatory action"]
        ))
        
        # Rule 4: Related party transaction restrictions
        rules.append(ComplianceRule(
            rule_id="COMP-004",
            name="Related Party Transaction Compliance",
            description="Restrictions on loans to directors and related parties",
            legal_basis=[section for sections in self.legal_sections.values() for section in sections 
                        if "director" in section.keywords or "related" in section.content.lower()],
            conditions=[
                "Loan application from director or related party",
                "Conflict of interest situation",
                "Connected borrower scenario"
            ],
            actions_required=[
                "Obtain SBP prior approval",
                "Ensure arm's length terms",
                "Board approval required",
                "Proper documentation",
                "Regular monitoring"
            ],
            timeline=timedelta(days=30),
            penalties=["Director disqualification", "Fine up to PKR 5 million", "Loan recovery"]
        ))
        
        return rules

    def create_vector_store(self) -> FAISS:
        """Create vector store for semantic search of legal documents"""
        
        documents = []
        
        for framework, sections in self.legal_sections.items():
            for section in sections:
                # Create document with metadata
                doc_content = f"{section.title}\n\n{section.content}\n\nKeywords: {', '.join(section.keywords)}"
                
                doc = Document(
                    page_content=doc_content,
                    metadata={
                        "framework": framework.value,
                        "section_number": section.section_number,
                        "title": section.title,
                        "keywords": section.keywords
                    }
                )
                documents.append(doc)
        
        # Split documents into chunks
        split_docs = self.text_splitter.split_documents(documents)
        
        # Create vector store
        vector_store = FAISS.from_documents(split_docs, self.embeddings)
        
        return vector_store

    async def assess_compliance(self, 
                              transaction_data: Dict[str, Any],
                              complaint_data: Dict[str, Any]) -> List[ViolationAssessment]:
        """Assess compliance and identify potential violations"""
        
        violations = []
        
        # Check each compliance rule
        for rule in self.compliance_rules:
            violation = await self.check_rule_compliance(rule, transaction_data, complaint_data)
            if violation:
                violations.append(violation)
        
        return violations

    async def check_rule_compliance(self, 
                                  rule: ComplianceRule,
                                  transaction_data: Dict[str, Any],
                                  complaint_data: Dict[str, Any]) -> Optional[ViolationAssessment]:
        """Check compliance with a specific rule"""
        
        violation_found = False
        evidence = []
        confidence_score = 0.0
        severity = SeverityLevel.LOW
        
        # Rule-specific compliance checks
        if rule.rule_id == "COMP-001":  # Complaint handling
            # Check if complaint was acknowledged within 24 hours
            complaint_date = complaint_data.get('created_at')
            acknowledgment_date = complaint_data.get('acknowledged_at')
            
            if complaint_date and acknowledgment_date:
                time_diff = acknowledgment_date - complaint_date
                if time_diff > timedelta(hours=24):
                    violation_found = True
                    evidence.append(f"Complaint acknowledged after {time_diff.total_seconds()/3600:.1f} hours")
                    confidence_score = 0.9
                    severity = SeverityLevel.MEDIUM
            elif complaint_date and not acknowledgment_date:
                # Check if 24 hours have passed without acknowledgment
                if datetime.now() - complaint_date > timedelta(hours=24):
                    violation_found = True
                    evidence.append("Complaint not acknowledged within 24 hours")
                    confidence_score = 0.95
                    severity = SeverityLevel.HIGH
        
        elif rule.rule_id == "COMP-002":  # Large transaction reporting
            amount = transaction_data.get('amount', 0)
            is_suspicious = transaction_data.get('is_suspicious', False)
            str_filed = transaction_data.get('str_filed', False)
            
            if amount > 1000000 and is_suspicious and not str_filed:
                violation_found = True
                evidence.append(f"Suspicious transaction of PKR {amount:,.2f} not reported to FMU")
                confidence_score = 0.85
                severity = SeverityLevel.HIGH
        
        elif rule.rule_id == "COMP-003":  # Law enforcement cooperation
            investigation_request = complaint_data.get('investigation_request')
            response_provided = complaint_data.get('investigation_response')
            
            if investigation_request and not response_provided:
                request_date = investigation_request.get('date')
                if request_date and datetime.now() - request_date > rule.timeline:
                    violation_found = True
                    evidence.append("Failed to respond to investigation request within required timeline")
                    confidence_score = 0.8
                    severity = SeverityLevel.HIGH
        
        elif rule.rule_id == "COMP-004":  # Related party transactions
            borrower_type = transaction_data.get('borrower_type')
            sbp_approval = transaction_data.get('sbp_approval', False)
            
            if borrower_type in ['director', 'related_party'] and not sbp_approval:
                violation_found = True
                evidence.append(f"Loan to {borrower_type} without SBP approval")
                confidence_score = 0.9
                severity = SeverityLevel.CRITICAL
        
        if violation_found:
            return ViolationAssessment(
                violation_id=f"VIO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{rule.rule_id}",
                rule_violated=rule,
                violation_type=self.determine_violation_type(rule),
                severity=severity,
                confidence_score=confidence_score,
                evidence=evidence,
                applicable_penalties=rule.penalties,
                recommended_actions=await self.generate_remedial_actions(rule, evidence),
                legal_citations=[f"{section.framework.value} Section {section.section_number}" 
                               for section in rule.legal_basis],
                financial_impact=await self.calculate_financial_impact(rule, transaction_data),
                timeline_for_resolution=rule.timeline
            )
        
        return None

    def determine_violation_type(self, rule: ComplianceRule) -> ViolationType:
        """Determine the type of violation based on the rule"""
        
        if any("fine" in penalty.lower() or "penalty" in penalty.lower() 
               for penalty in rule.penalties):
            return ViolationType.REGULATORY
        elif any("imprisonment" in penalty.lower() or "criminal" in penalty.lower() 
                 for penalty in rule.penalties):
            return ViolationType.CRIMINAL
        elif any("procedure" in rule.description.lower() or "timeline" in rule.description.lower()):
            return ViolationType.PROCEDURAL
        else:
            return ViolationType.ADMINISTRATIVE

    async def generate_remedial_actions(self, 
                                      rule: ComplianceRule, 
                                      evidence: List[str]) -> List[str]:
        """Generate specific remedial actions for violations"""
        
        actions = []
        
        # Base actions from the rule
        actions.extend(rule.actions_required)
        
        # Additional actions based on violation type
        if rule.rule_id == "COMP-001":  # Complaint handling
            actions.extend([
                "Immediately acknowledge the complaint",
                "Expedite investigation process",
                "Provide interim updates to customer",
                "Review and strengthen complaint handling procedures"
            ])
        
        elif rule.rule_id == "COMP-002":  # AML reporting
            actions.extend([
                "Immediately file STR with FMU",
                "Conduct enhanced due diligence on account",
                "Review AML monitoring systems",
                "Train staff on suspicious transaction identification"
            ])
        
        elif rule.rule_id == "COMP-003":  # Investigation cooperation
            actions.extend([
                "Immediately respond to investigation request",
                "Assign dedicated liaison officer",
                "Ensure complete information provision",
                "Establish investigation response protocol"
            ])
        
        elif rule.rule_id == "COMP-004":  # Related party transactions
            actions.extend([
                "Seek immediate SBP approval",
                "Review transaction terms for arm's length pricing",
                "Strengthen related party identification process",
                "Enhance board oversight mechanisms"
            ])
        
        return list(set(actions))  # Remove duplicates

    async def calculate_financial_impact(self, 
                                       rule: ComplianceRule, 
                                       transaction_data: Dict[str, Any]) -> Optional[float]:
        """Calculate potential financial impact of violation"""
        
        impact = 0.0
        
        # Extract penalty amounts from rule
        for penalty in rule.penalties:
            # Look for PKR amounts in penalty text
            pkr_matches = re.findall(r'PKR\s+(\d+(?:,\d{3})*(?:\.\d{2})?)', penalty)
            for match in pkr_matches:
                amount = float(match.replace(',', ''))
                impact = max(impact, amount)
        
        # Add transaction-specific impacts
        transaction_amount = transaction_data.get('amount', 0)
        
        if rule.rule_id == "COMP-002":  # AML violations
            # Potential asset freezing
            impact += transaction_amount * 0.1  # 10% of transaction value
        
        elif rule.rule_id == "COMP-004":  # Related party violations
            # Loan recovery plus penalties
            impact += transaction_amount * 1.05  # Full recovery plus 5% penalty
        
        return impact if impact > 0 else None

    async def semantic_search_legal_precedents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant legal precedents using semantic similarity"""
        
        # Search vector store
        docs = self.vector_store.similarity_search(query, k=k)
        
        precedents = []
        for doc in docs:
            precedents.append({
                "content": doc.page_content,
                "framework": doc.metadata.get("framework"),
                "section": doc.metadata.get("section_number"),
                "title": doc.metadata.get("title"),
                "relevance_score": 0.8  # Placeholder - would calculate actual similarity
            })
        
        return precedents

    async def generate_legal_report(self, 
                                  violations: List[ViolationAssessment]) -> Dict[str, Any]:
        """Generate comprehensive legal compliance report"""
        
        report = {
            "report_id": f"LEGAL-RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now(),
            "total_violations": len(violations),
            "violation_summary": defaultdict(int),
            "severity_breakdown": defaultdict(int),
            "financial_impact_total": 0,
            "priority_actions": [],
            "legal_framework_analysis": {},
            "recommendations": []
        }
        
        # Analyze violations
        for violation in violations:
            report["violation_summary"][violation.violation_type.value] += 1
            report["severity_breakdown"][violation.severity.value] += 1
            
            if violation.financial_impact:
                report["financial_impact_total"] += violation.financial_impact
            
            # High severity violations get priority
            if violation.severity.value >= 3:
                report["priority_actions"].extend(violation.recommended_actions)
        
        # Framework analysis
        frameworks_involved = set()
        for violation in violations:
            for section in violation.rule_violated.legal_basis:
                frameworks_involved.add(section.framework.value)
        
        report["legal_framework_analysis"] = {
            "frameworks_involved": list(frameworks_involved),
            "primary_framework": max(frameworks_involved, key=lambda x: 
                sum(1 for v in violations for s in v.rule_violated.legal_basis 
                    if s.framework.value == x)) if frameworks_involved else None
        }
        
        # Generate recommendations
        report["recommendations"] = await self.generate_compliance_recommendations(violations)
        
        return report

    async def generate_compliance_recommendations(self, 
                                                violations: List[ViolationAssessment]) -> List[str]:
        """Generate high-level compliance recommendations"""
        
        recommendations = []
        
        # Categorize violations
        high_severity_count = sum(1 for v in violations if v.severity.value >= 3)
        aml_violations = sum(1 for v in violations if "AML" in str(v.rule_violated.legal_basis))
        procedural_violations = sum(1 for v in violations if v.violation_type == ViolationType.PROCEDURAL)
        
        # Strategic recommendations
        if high_severity_count > 0:
            recommendations.append(
                f"Immediate attention required: {high_severity_count} high-severity violations identified. "
                "Consider engaging external legal counsel and implementing emergency remediation measures."
            )
        
        if aml_violations > 0:
            recommendations.append(
                "Strengthen Anti-Money Laundering compliance program including enhanced monitoring systems, "
                "staff training, and customer due diligence procedures."
            )
        
        if procedural_violations > 2:
            recommendations.append(
                "Review and update operational procedures to ensure compliance with regulatory timelines "
                "and reporting requirements. Consider implementing automated compliance monitoring."
            )
        
        # General recommendations
        recommendations.extend([
            "Establish regular compliance training program for all staff",
            "Implement real-time compliance monitoring dashboard",
            "Conduct quarterly compliance risk assessments",
            "Enhance documentation and record-keeping procedures",
            "Establish clear escalation procedures for compliance issues"
        ])
        
        return recommendations

    def save_assessment_to_db(self, assessment: ViolationAssessment):
        """Save violation assessment to database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO violation_assessments 
            (violation_id, rule_id, violation_type, severity, confidence_score, evidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            assessment.violation_id,
            assessment.rule_violated.rule_id,
            assessment.violation_type.value,
            assessment.severity.value,
            assessment.confidence_score,
            json.dumps(assessment.evidence)
        ))
        
        conn.commit()
        conn.close()

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_legal_engine():
        # Initialize legal knowledge base
        legal_kb = LegalKnowledgeBase()
        
        # Sample complaint data
        complaint_data = {
            'created_at': datetime.now() - timedelta(hours=30),
            'acknowledged_at': None,  # Not acknowledged yet
            'amount_involved': 2000000,
            'complaint_type': 'fraud'
        }
        
        # Sample transaction data
        transaction_data = {
            'amount': 1500000,
            'is_suspicious': True,
            'str_filed': False,
            'borrower_type': 'director',
            'sbp_approval': False
        }
        
        # Assess compliance
        violations = await legal_kb.assess_compliance(transaction_data, complaint_data)
        
        print(f"Found {len(violations)} violations:")
        for violation in violations:
            print(f"- {violation.rule_violated.name} (Severity: {violation.severity.name})")
            print(f"  Evidence: {violation.evidence}")
            print(f"  Financial Impact: PKR {violation.financial_impact:,.2f}" if violation.financial_impact else "  No financial impact calculated")
            print()
        
        # Generate legal report
        report = await legal_kb.generate_legal_report(violations)
        print("Legal Compliance Report Generated:")
        print(f"Total Violations: {report['total_violations']}")
        print(f"Financial Impact: PKR {report['financial_impact_total']:,.2f}")
        print(f"Priority Actions: {len(report['priority_actions'])}")
    
    # asyncio.run(test_legal_engine())