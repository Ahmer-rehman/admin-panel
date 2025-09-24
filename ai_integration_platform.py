"""
Pakistan Banking Compliance & Complaint Analysis System (PBCCAS)
Multi-AI Platform Integration Module

This module integrates multiple AI platforms (ChatGPT, Gemini, LLaMA) for enhanced
analysis, decision support, and cross-validation of results.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import pickle
from pathlib import Path

import openai
import google.generativeai as genai
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import tiktoken
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Supported AI providers"""
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    LLAMA = "llama"
    CLAUDE = "claude"  # For future expansion

class TaskType(Enum):
    """Types of AI tasks"""
    COMPLAINT_ANALYSIS = "complaint_analysis"
    LEGAL_RESEARCH = "legal_research"
    RISK_ASSESSMENT = "risk_assessment"
    REPORT_GENERATION = "report_generation"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    FRAUD_DETECTION = "fraud_detection"
    COMPLIANCE_CHECK = "compliance_check"

class Priority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AIRequest:
    """AI request structure"""
    request_id: str
    task_type: TaskType
    prompt: str
    context: Dict[str, Any]
    priority: Priority
    preferred_providers: List[AIProvider] = field(default_factory=list)
    max_tokens: int = 1000
    temperature: float = 0.3
    timeout: int = 30
    require_consensus: bool = False
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AIResponse:
    """AI response structure"""
    request_id: str
    provider: AIProvider
    response_text: str
    confidence_score: float
    processing_time: float
    token_usage: int
    cost_estimate: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConsensusResult:
    """Result of multi-AI consensus analysis"""
    request_id: str
    consensus_response: str
    confidence_score: float
    agreement_score: float
    participating_providers: List[AIProvider]
    individual_responses: List[AIResponse]
    reasoning: str
    created_at: datetime = field(default_factory=datetime.now)

class AIProviderConfig:
    """Configuration for AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Provider-specific settings
        self.chatgpt_models = ["gpt-4", "gpt-3.5-turbo"]
        self.gemini_models = ["gemini-pro", "gemini-pro-vision"]
        self.llama_models = ["llama-2-7b-chat", "llama-2-13b-chat"]
        
        # Cost per 1K tokens (USD)
        self.cost_per_1k_tokens = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "llama-2-7b-chat": {"input": 0.0, "output": 0.0}  # Local deployment
        }
        
        # Performance characteristics
        self.provider_characteristics = {
            AIProvider.CHATGPT: {
                "strengths": ["reasoning", "analysis", "code_generation"],
                "response_time": "fast",
                "reliability": 0.95,
                "cost": "high"
            },
            AIProvider.GEMINI: {
                "strengths": ["multimodal", "factual_accuracy", "translation"],
                "response_time": "medium",
                "reliability": 0.90,
                "cost": "medium"
            },
            AIProvider.LLAMA: {
                "strengths": ["privacy", "customization", "local_deployment"],
                "response_time": "slow",
                "reliability": 0.85,
                "cost": "low"
            }
        }

class ChatGPTProvider:
    """ChatGPT integration wrapper"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('openai_api_key')
        self.model = config.get('chatgpt_model', 'gpt-4')
        self.organization = config.get('openai_organization')
        
        openai.api_key = self.api_key
        if self.organization:
            openai.organization = self.organization
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate response using ChatGPT"""
        start_time = time.time()
        
        try:
            # Prepare messages for Pakistan banking context
            system_prompt = """You are an expert AI assistant specializing in Pakistan's banking 
            regulations, compliance, and legal framework. You have deep knowledge of CRPC, NAB 
            ordinance, SBP regulations, and Islamic banking principles. Provide accurate, 
            detailed responses with proper legal citations when applicable."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ]
            
            # Add context if provided
            if request.context:
                context_str = f"Additional context: {json.dumps(request.context, indent=2)}"
                messages.append({"role": "user", "content": context_str})
            
            # Make API call
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=request.timeout
            )
            
            # Calculate metrics
            processing_time = time.time() - start_time
            token_usage = response.usage.total_tokens
            cost_estimate = self.calculate_cost(token_usage, self.model)
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Calculate confidence (simplified heuristic)
            confidence_score = min(0.9, len(response_text) / 1000)
            
            return AIResponse(
                request_id=request.request_id,
                provider=AIProvider.CHATGPT,
                response_text=response_text,
                confidence_score=confidence_score,
                processing_time=processing_time,
                token_usage=token_usage,
                cost_estimate=cost_estimate,
                metadata={
                    "model": self.model,
                    "finish_reason": response.choices[0].finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            )
            
        except Exception as e:
            logger.error(f"ChatGPT error for request {request.request_id}: {str(e)}")
            raise

    def calculate_cost(self, token_usage: int, model: str) -> float:
        """Calculate cost based on token usage"""
        # Simplified cost calculation (assumes 50/50 input/output split)
        input_tokens = token_usage // 2
        output_tokens = token_usage // 2
        
        if model in ["gpt-4"]:
            cost = (input_tokens / 1000 * 0.03) + (output_tokens / 1000 * 0.06)
        elif model in ["gpt-3.5-turbo"]:
            cost = (input_tokens / 1000 * 0.0015) + (output_tokens / 1000 * 0.002)
        else:
            cost = 0.0
        
        return cost

class GeminiProvider:
    """Google Gemini integration wrapper"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('gemini_api_key')
        self.model_name = config.get('gemini_model', 'gemini-pro')
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate response using Gemini"""
        start_time = time.time()
        
        try:
            # Enhance prompt for Pakistan context
            enhanced_prompt = f"""
            As an expert in Pakistan's banking and legal system, analyze the following:
            
            {request.prompt}
            
            Consider:
            - Pakistan's banking regulations (SBP, BCO)
            - Criminal law (CRPC, PPC)
            - Anti-corruption laws (NAB)
            - Islamic banking principles (where applicable)
            - Cultural and linguistic context of Pakistan
            
            Provide detailed analysis with legal references.
            """
            
            # Add context if provided
            if request.context:
                enhanced_prompt += f"\n\nContext: {json.dumps(request.context, indent=2)}"
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                enhanced_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            )
            
            # Calculate metrics
            processing_time = time.time() - start_time
            token_usage = len(enhanced_prompt.split()) + len(response.text.split())  # Rough estimate
            cost_estimate = self.calculate_cost(token_usage)
            
            # Calculate confidence based on response characteristics
            confidence_score = min(0.85, len(response.text) / 800)
            
            return AIResponse(
                request_id=request.request_id,
                provider=AIProvider.GEMINI,
                response_text=response.text,
                confidence_score=confidence_score,
                processing_time=processing_time,
                token_usage=token_usage,
                cost_estimate=cost_estimate,
                metadata={
                    "model": self.model_name,
                    "safety_ratings": getattr(response, 'safety_ratings', []),
                    "citation_metadata": getattr(response, 'citation_metadata', None)
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini error for request {request.request_id}: {str(e)}")
            raise

    def calculate_cost(self, token_usage: int) -> float:
        """Calculate cost for Gemini usage"""
        # Simplified cost calculation for Gemini Pro
        return (token_usage / 1000) * 0.00025

class LLaMAProvider:
    """Local LLaMA integration wrapper"""
    
    def __init__(self, config: Dict[str, Any]):
        self.model_path = config.get('llama_model_path', './models/llama-2-7b-chat.gguf')
        self.model_params = config.get('llama_params', {})
        
        # Initialize LLaMA model
        self.model = LlamaCpp(
            model_path=self.model_path,
            temperature=0.3,
            max_tokens=2000,
            top_p=1,
            verbose=False,
            **self.model_params
        )
    
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate response using local LLaMA"""
        start_time = time.time()
        
        try:
            # Format prompt for Pakistan banking domain
            pakistan_context = """
            You are an AI assistant expert in Pakistan's banking sector, legal framework, 
            and compliance requirements. Your knowledge includes:
            
            - Pakistan Banking laws (SBP Act, BCO)
            - Criminal procedures (CRPC)
            - Anti-corruption (NAB Ordinance)
            - Islamic banking (Shariah compliance)
            - Local business practices and cultural context
            
            Provide detailed, accurate responses with relevant legal citations.
            """
            
            formatted_prompt = f"{pakistan_context}\n\nUser Query: {request.prompt}"
            
            if request.context:
                formatted_prompt += f"\n\nAdditional Context: {json.dumps(request.context, indent=2)}"
            
            # Generate response
            response_text = await asyncio.to_thread(
                self.model,
                formatted_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Calculate metrics
            processing_time = time.time() - start_time
            token_usage = len(formatted_prompt.split()) + len(response_text.split())
            cost_estimate = 0.0  # Local deployment has no API costs
            
            # Calculate confidence based on response length and coherence
            confidence_score = min(0.8, len(response_text) / 600)
            
            return AIResponse(
                request_id=request.request_id,
                provider=AIProvider.LLAMA,
                response_text=response_text,
                confidence_score=confidence_score,
                processing_time=processing_time,
                token_usage=token_usage,
                cost_estimate=cost_estimate,
                metadata={
                    "model_path": self.model_path,
                    "local_deployment": True,
                    "privacy_compliant": True
                }
            )
            
        except Exception as e:
            logger.error(f"LLaMA error for request {request.request_id}: {str(e)}")
            raise

class AIRouterAndLoadBalancer:
    """Intelligent AI router and load balancer"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_config = AIProviderConfig(config)
        
        # Initialize providers
        self.providers = {}
        if config.get('openai_api_key'):
            self.providers[AIProvider.CHATGPT] = ChatGPTProvider(config)
        if config.get('gemini_api_key'):
            self.providers[AIProvider.GEMINI] = GeminiProvider(config)
        if config.get('llama_model_path'):
            self.providers[AIProvider.LLAMA] = LLaMAProvider(config)
        
        # Performance tracking
        self.performance_metrics = {
            provider: {
                "total_requests": 0,
                "success_rate": 1.0,
                "avg_response_time": 0.0,
                "avg_confidence": 0.0,
                "total_cost": 0.0
            }
            for provider in self.providers.keys()
        }
        
        # Request queue and cache
        self.request_queue = asyncio.Queue()
        self.cache = {}
        if config.get('redis_url'):
            self.redis_client = redis.from_url(config['redis_url'])
        else:
            self.redis_client = None

    def select_optimal_provider(self, request: AIRequest) -> AIProvider:
        """Select the optimal AI provider based on task type and performance"""
        
        # If specific providers are preferred, use them
        if request.preferred_providers:
            available_preferred = [p for p in request.preferred_providers if p in self.providers]
            if available_preferred:
                return self.select_best_from_list(available_preferred, request)
        
        # Task-specific provider selection
        task_preferences = {
            TaskType.COMPLAINT_ANALYSIS: [AIProvider.CHATGPT, AIProvider.GEMINI, AIProvider.LLAMA],
            TaskType.LEGAL_RESEARCH: [AIProvider.CHATGPT, AIProvider.LLAMA, AIProvider.GEMINI],
            TaskType.RISK_ASSESSMENT: [AIProvider.CHATGPT, AIProvider.GEMINI, AIProvider.LLAMA],
            TaskType.FRAUD_DETECTION: [AIProvider.CHATGPT, AIProvider.GEMINI, AIProvider.LLAMA],
            TaskType.ENTITY_EXTRACTION: [AIProvider.GEMINI, AIProvider.CHATGPT, AIProvider.LLAMA],
            TaskType.SENTIMENT_ANALYSIS: [AIProvider.GEMINI, AIProvider.CHATGPT, AIProvider.LLAMA],
            TaskType.REPORT_GENERATION: [AIProvider.CHATGPT, AIProvider.LLAMA, AIProvider.GEMINI],
            TaskType.COMPLIANCE_CHECK: [AIProvider.LLAMA, AIProvider.CHATGPT, AIProvider.GEMINI]  # Privacy preference
        }
        
        preferred_order = task_preferences.get(request.task_type, list(self.providers.keys()))
        available_providers = [p for p in preferred_order if p in self.providers]
        
        if not available_providers:
            raise ValueError("No available AI providers")
        
        return self.select_best_from_list(available_providers, request)

    def select_best_from_list(self, providers: List[AIProvider], request: AIRequest) -> AIProvider:
        """Select the best provider from a given list based on performance metrics"""
        
        scores = {}
        
        for provider in providers:
            metrics = self.performance_metrics[provider]
            
            # Calculate composite score
            score = (
                metrics["success_rate"] * 0.4 +
                (1 / max(metrics["avg_response_time"], 0.1)) * 0.3 +
                metrics["avg_confidence"] * 0.2 +
                (1 / max(metrics["total_cost"] / max(metrics["total_requests"], 1), 0.01)) * 0.1
            )
            
            # Priority adjustment
            if request.priority == Priority.CRITICAL:
                # Favor reliability for critical requests
                score *= (1 + metrics["success_rate"])
            elif request.priority == Priority.LOW:
                # Favor cost-effectiveness for low priority
                if provider == AIProvider.LLAMA:  # Local = free
                    score *= 1.5
            
            scores[provider] = score
        
        return max(scores.items(), key=lambda x: x[1])[0]

    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process a single AI request"""
        
        # Check cache first
        cache_key = self.generate_cache_key(request)
        cached_response = self.get_cached_response(cache_key)
        if cached_response:
            logger.info(f"Returning cached response for request {request.request_id}")
            return cached_response
        
        # Select provider
        provider = self.select_optimal_provider(request)
        logger.info(f"Selected {provider.value} for request {request.request_id}")
        
        try:
            # Generate response
            response = await self.providers[provider].generate_response(request)
            
            # Update performance metrics
            self.update_performance_metrics(provider, response, success=True)
            
            # Cache response
            self.cache_response(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Provider {provider.value} failed for request {request.request_id}: {str(e)}")
            
            # Update failure metrics
            self.update_performance_metrics(provider, None, success=False)
            
            # Try fallback provider
            fallback_providers = [p for p in self.providers.keys() if p != provider]
            if fallback_providers:
                fallback_provider = self.select_best_from_list(fallback_providers, request)
                logger.info(f"Trying fallback provider {fallback_provider.value}")
                
                try:
                    response = await self.providers[fallback_provider].generate_response(request)
                    self.update_performance_metrics(fallback_provider, response, success=True)
                    self.cache_response(cache_key, response)
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback provider {fallback_provider.value} also failed: {str(fallback_error)}")
            
            raise Exception(f"All providers failed for request {request.request_id}")

    async def process_consensus_request(self, request: AIRequest) -> ConsensusResult:
        """Process request using multiple providers for consensus"""
        
        # Select multiple providers for consensus
        available_providers = list(self.providers.keys())
        consensus_providers = available_providers[:min(3, len(available_providers))]
        
        # Process requests concurrently
        tasks = []
        for provider in consensus_providers:
            provider_request = AIRequest(
                request_id=f"{request.request_id}-{provider.value}",
                task_type=request.task_type,
                prompt=request.prompt,
                context=request.context,
                priority=request.priority,
                preferred_providers=[provider],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=request.timeout
            )
            tasks.append(self.process_request(provider_request))
        
        # Wait for all responses
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful responses
        successful_responses = [r for r in responses if isinstance(r, AIResponse)]
        
        if not successful_responses:
            raise Exception("No successful responses for consensus analysis")
        
        # Analyze consensus
        consensus_result = self.analyze_consensus(request.request_id, successful_responses)
        
        return consensus_result

    def analyze_consensus(self, request_id: str, responses: List[AIResponse]) -> ConsensusResult:
        """Analyze consensus among multiple AI responses"""
        
        if len(responses) == 1:
            return ConsensusResult(
                request_id=request_id,
                consensus_response=responses[0].response_text,
                confidence_score=responses[0].confidence_score,
                agreement_score=1.0,
                participating_providers=[responses[0].provider],
                individual_responses=responses,
                reasoning="Single provider response - no consensus analysis possible"
            )
        
        # Extract response texts
        response_texts = [r.response_text for r in responses]
        
        # Calculate text similarity using TF-IDF
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(response_texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Calculate average similarity (agreement score)
        n = len(responses)
        agreement_score = (similarity_matrix.sum() - n) / (n * (n - 1)) if n > 1 else 1.0
        
        # Select consensus response (highest confidence among similar responses)
        if agreement_score > 0.7:
            # High agreement - select highest confidence response
            consensus_response_obj = max(responses, key=lambda r: r.confidence_score)
            consensus_response = consensus_response_obj.response_text
            confidence_score = consensus_response_obj.confidence_score * agreement_score
            reasoning = f"High agreement ({agreement_score:.2f}) among providers. Selected highest confidence response."
        else:
            # Low agreement - create hybrid response
            consensus_response = self.create_hybrid_response(responses)
            confidence_score = sum(r.confidence_score for r in responses) / len(responses) * agreement_score
            reasoning = f"Low agreement ({agreement_score:.2f}) among providers. Created hybrid response."
        
        return ConsensusResult(
            request_id=request_id,
            consensus_response=consensus_response,
            confidence_score=confidence_score,
            agreement_score=agreement_score,
            participating_providers=[r.provider for r in responses],
            individual_responses=responses,
            reasoning=reasoning
        )

    def create_hybrid_response(self, responses: List[AIResponse]) -> str:
        """Create a hybrid response when there's disagreement among providers"""
        
        hybrid_response = "Multiple AI systems provided different analyses:\n\n"
        
        for i, response in enumerate(responses, 1):
            hybrid_response += f"Analysis {i} ({response.provider.value}):\n"
            hybrid_response += f"{response.response_text}\n\n"
        
        hybrid_response += "Recommendation: Consider all perspectives and conduct additional verification."
        
        return hybrid_response

    def generate_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request"""
        key_data = f"{request.task_type.value}:{request.prompt}:{json.dumps(request.context, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_cached_response(self, cache_key: str) -> Optional[AIResponse]:
        """Get cached response if available"""
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return pickle.loads(cached_data)
            except Exception as e:
                logger.warning(f"Redis cache error: {str(e)}")
        
        return self.cache.get(cache_key)

    def cache_response(self, cache_key: str, response: AIResponse):
        """Cache response for future use"""
        # Local cache
        self.cache[cache_key] = response
        
        # Redis cache with TTL
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key, 
                    3600,  # 1 hour TTL
                    pickle.dumps(response)
                )
            except Exception as e:
                logger.warning(f"Redis cache error: {str(e)}")

    def update_performance_metrics(self, provider: AIProvider, response: Optional[AIResponse], success: bool):
        """Update performance metrics for a provider"""
        metrics = self.performance_metrics[provider]
        metrics["total_requests"] += 1
        
        if success and response:
            # Update success rate
            total_requests = metrics["total_requests"]
            current_successes = metrics["success_rate"] * (total_requests - 1)
            metrics["success_rate"] = (current_successes + 1) / total_requests
            
            # Update average response time
            metrics["avg_response_time"] = (
                (metrics["avg_response_time"] * (total_requests - 1) + response.processing_time) / 
                total_requests
            )
            
            # Update average confidence
            metrics["avg_confidence"] = (
                (metrics["avg_confidence"] * (total_requests - 1) + response.confidence_score) / 
                total_requests
            )
            
            # Update total cost
            metrics["total_cost"] += response.cost_estimate
        else:
            # Update success rate for failure
            total_requests = metrics["total_requests"]
            current_successes = metrics["success_rate"] * (total_requests - 1)
            metrics["success_rate"] = current_successes / total_requests

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all providers"""
        return {
            "timestamp": datetime.now(),
            "providers": self.performance_metrics,
            "total_requests": sum(m["total_requests"] for m in self.performance_metrics.values()),
            "total_cost": sum(m["total_cost"] for m in self.performance_metrics.values()),
            "cache_hit_rate": len(self.cache) / max(sum(m["total_requests"] for m in self.performance_metrics.values()), 1)
        }

# Main AI Integration Manager
class MultiAIIntegrationManager:
    """Main manager for multi-AI platform integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.router = AIRouterAndLoadBalancer(config)
        self.executor = ThreadPoolExecutor(max_workers=config.get('max_workers', 10))
        
    async def analyze_complaint(self, complaint_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Comprehensive complaint analysis using multiple AI platforms"""
        
        request_id = f"complaint-{int(time.time())}"
        
        # Create analysis request
        request = AIRequest(
            request_id=request_id,
            task_type=TaskType.COMPLAINT_ANALYSIS,
            prompt=f"""
            Analyze this banking complaint from Pakistan and provide:
            
            1. **Complaint Classification**: Categorize the complaint type
            2. **Severity Assessment**: Rate the severity (1-10) and urgency
            3. **Legal Implications**: Identify potential legal violations under Pakistan law
            4. **Stakeholders**: Identify all parties involved
            5. **Recommended Actions**: Immediate and long-term actions required
            6. **Compliance Issues**: Any regulatory compliance concerns
            7. **Financial Impact**: Potential financial implications
            8. **Timeline**: Suggested investigation and resolution timeline
            
            Complaint Text: {complaint_text}
            """,
            context=context or {},
            priority=Priority.HIGH,
            require_consensus=True,
            max_tokens=1500
        )
        
        # Get consensus analysis
        consensus_result = await self.router.process_consensus_request(request)
        
        return {
            "analysis": consensus_result.consensus_response,
            "confidence": consensus_result.confidence_score,
            "agreement_score": consensus_result.agreement_score,
            "providers_used": [p.value for p in consensus_result.participating_providers],
            "individual_analyses": {
                r.provider.value: r.response_text 
                for r in consensus_result.individual_responses
            },
            "processing_time": sum(r.processing_time for r in consensus_result.individual_responses),
            "total_cost": sum(r.cost_estimate for r in consensus_result.individual_responses)
        }
    
    async def research_legal_precedent(self, legal_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Research legal precedents and applicable laws"""
        
        request = AIRequest(
            request_id=f"legal-{int(time.time())}",
            task_type=TaskType.LEGAL_RESEARCH,
            prompt=f"""
            Research Pakistan legal framework for the following query:
            
            {legal_query}
            
            Provide:
            1. Applicable laws and sections (CRPC, NAB, SBP, BCO, AML)
            2. Relevant case law or precedents
            3. Penalties and consequences
            4. Procedural requirements
            5. Recent amendments or updates
            6. Practical implementation guidance
            
            Focus on Pakistani banking and financial crime laws.
            """,
            context=context or {},
            priority=Priority.MEDIUM,
            preferred_providers=[AIProvider.CHATGPT, AIProvider.LLAMA],  # Favor accuracy and privacy
            max_tokens=2000
        )
        
        response = await self.router.process_request(request)
        
        return {
            "legal_research": response.response_text,
            "confidence": response.confidence_score,
            "provider": response.provider.value,
            "processing_time": response.processing_time,
            "cost": response.cost_estimate
        }
    
    async def generate_investigation_report(self, investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive investigation report"""
        
        request = AIRequest(
            request_id=f"report-{int(time.time())}",
            task_type=TaskType.REPORT_GENERATION,
            prompt=f"""
            Generate a comprehensive investigation report for a Pakistan banking complaint with the following structure:
            
            1. **Executive Summary**
            2. **Case Details and Background**
            3. **Investigation Methodology**
            4. **Findings and Evidence**
            5. **Legal Analysis** (relevant Pakistan laws)
            6. **Compliance Assessment**
            7. **Financial Impact Analysis**
            8. **Recommendations**
            9. **Conclusion and Next Steps**
            
            Ensure the report meets Pakistan regulatory requirements and SBP guidelines.
            
            Investigation Data: {json.dumps(investigation_data, indent=2)}
            """,
            context=investigation_data,
            priority=Priority.HIGH,
            preferred_providers=[AIProvider.CHATGPT],  # Favor structured output
            max_tokens=3000
        )
        
        response = await self.router.process_request(request)
        
        return {
            "report": response.response_text,
            "confidence": response.confidence_score,
            "provider": response.provider.value,
            "processing_time": response.processing_time,
            "cost": response.cost_estimate,
            "metadata": response.metadata
        }

# Example usage
if __name__ == "__main__":
    async def test_ai_integration():
        config = {
            'openai_api_key': 'your-openai-key',
            'gemini_api_key': 'your-gemini-key',
            'llama_model_path': './models/llama-2-7b-chat.gguf',
            'redis_url': 'redis://localhost:6379',
            'max_workers': 5
        }
        
        ai_manager = MultiAIIntegrationManager(config)
        
        # Test complaint analysis
        sample_complaint = """
        I am filing a complaint against HBL Bank. They have fraudulently 
        withdrawn PKR 500,000 from my account without authorization. 
        This is urgent as it involves my business funds.
        """
        
        result = await ai_manager.analyze_complaint(sample_complaint)
        print("Complaint Analysis Result:")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Agreement Score: {result['agreement_score']:.2f}")
        print(f"Providers Used: {result['providers_used']}")
        print(f"Analysis: {result['analysis'][:500]}...")
        
        # Performance report
        performance = ai_manager.router.get_performance_report()
        print("\nPerformance Report:")
        print(json.dumps(performance, indent=2, default=str))
    
    # asyncio.run(test_ai_integration())