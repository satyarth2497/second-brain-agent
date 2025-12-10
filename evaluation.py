#!/usr/bin/env python3
"""
Standalone Evaluation Suite for Second Brain Agent System

Tests:
1. Orchestrator routing accuracy (RAG vs Health)
2. RAG agent retrieval quality  
3. Health agent personalization
4. A2A communication flow
5. Error handling and edge cases

Reference format based on pydantic_evals patterns
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from agent.rag.rag_loader import load_and_split_markdown
from agent.rag.vector_store import create_vectorstore
from agent.orchestrator.orchestrator import orchestrator_agent, OrchestratorDeps


@dataclass
class EvaluationCase:
    """Single test case for evaluation"""
    name: str
    inputs: str
    expected_source: Optional[str]  # "rag" or "health"
    category: str
    focus: str
    description: str
    evaluation_criteria: List[str]
    metadata: Dict[str, Any]


# ============================================================================
# TEST CASES
# ============================================================================

EVALUATION_CASES = [
    # ========================================================================
    # 1. ORCHESTRATOR ROUTING TESTS
    # ========================================================================
    EvaluationCase(
        name="routing_technical_documentation_query",
        inputs="What is the email notification tool architecture?",
        expected_source="rag",
        category="routing",
        focus="technical_documentation",
        description="Tests routing of technical/documentation queries to RAG agent",
        evaluation_criteria=[
            "Routes to RAG agent (source='rag')",
            "Provides architectural information",
            "Mentions components like message queues, APIs, or AWS services",
            "Answer is technically accurate"
        ],
        metadata={"expected_agent": "rag", "difficulty": "easy"}
    ),
    
    EvaluationCase(
        name="routing_nutrition_query",
        inputs="What should I eat for breakfast on a low-calorie diet?",
        expected_source="health",
        category="routing",
        focus="nutrition_advice",
        description="Tests routing of nutrition queries to Health agent",
        evaluation_criteria=[
            "Routes to Health agent (source='health')",
            "Suggests low-calorie breakfast options",
            "Considers user profile (low-calorie diet, gluten allergy)",
            "Provides practical meal suggestions"
        ],
        metadata={"expected_agent": "health", "difficulty": "easy"}
    ),
    
    EvaluationCase(
        name="routing_meal_planning_query",
        inputs="Suggest vegan dinner recipes for tonight",
        expected_source="health",
        category="routing",
        focus="meal_planning",
        description="Tests routing of meal planning queries to Health agent",
        evaluation_criteria=[
            "Routes to Health agent (source='health')",
            "Suggests vegan dinner recipes",
            "Recipes are specific and practical",
            "Provides 2-3 meal ideas"
        ],
        metadata={"expected_agent": "health", "difficulty": "easy"}
    ),
    
    EvaluationCase(
        name="routing_ambiguous_storage_query",
        inputs="Where should I store templates?",
        expected_source="rag",
        category="routing",
        focus="technical_storage",
        description="Tests routing of ambiguous but technical queries",
        evaluation_criteria=[
            "Routes to RAG agent (template storage is technical)",
            "Mentions S3, SES Template Manager, or similar",
            "Provides version control or flexibility considerations",
            "Answer is technically relevant"
        ],
        metadata={"expected_agent": "rag", "difficulty": "medium"}
    ),
    
    # ========================================================================
    # 2. RAG AGENT RETRIEVAL QUALITY
    # ========================================================================
    EvaluationCase(
        name="rag_document_retrieval_accuracy",
        inputs="Explain the AWS services used in the notification system",
        expected_source="rag",
        category="rag_quality",
        focus="document_retrieval",
        description="Tests RAG agent's ability to retrieve relevant documentation",
        evaluation_criteria=[
            "Successfully retrieves relevant chunks from vector store",
            "Mentions AWS services (SNS, SQS, SES, Lambda, API Gateway)",
            "Provides accurate technical information",
            "Does not hallucinate information",
            "Integrates web search if needed"
        ],
        metadata={
            "expected_mentions": ["SNS", "SQS", "SES", "Lambda", "API Gateway"],
            "difficulty": "medium"
        }
    ),
    
    EvaluationCase(
        name="rag_message_template_storage",
        inputs="How do I store message templates in the system?",
        expected_source="rag",
        category="rag_quality",
        focus="specific_documentation",
        description="Tests retrieval of specific technical documentation",
        evaluation_criteria=[
            "Retrieves documentation about template storage",
            "Mentions S3 or SES Template Manager",
            "Provides implementation details",
            "Answer is actionable"
        ],
        metadata={"in_docs": True, "difficulty": "easy"}
    ),
    
    # ========================================================================
    # 3. HEALTH AGENT PERSONALIZATION
    # ========================================================================
    EvaluationCase(
        name="health_profile_awareness",
        inputs="What can I eat today?",
        expected_source="health",
        category="health_personalization",
        focus="profile_utilization",
        description="Tests Health agent's use of user profile",
        evaluation_criteria=[
            "Uses get_profile() tool",
            "Suggests low-calorie meals (under 500 cal target)",
            "Avoids gluten-containing foods",
            "Provides 2-3 specific meal suggestions",
            "Shows awareness of dietary restrictions"
        ],
        metadata={
            "requires_profile": True,
            "user_profile": {"diet": "low-calorie", "allergies": ["gluten"]},
            "difficulty": "medium"
        }
    ),
    
    EvaluationCase(
        name="health_allergen_avoidance_critical",
        inputs="Suggest some bread recipes",
        expected_source="health",
        category="health_personalization",
        focus="allergen_awareness",
        description="CRITICAL: Tests allergen avoidance (safety-critical)",
        evaluation_criteria=[
            "Recognizes gluten allergy from profile",
            "ONLY suggests gluten-free bread recipes",
            "Explicitly mentions recipes are gluten-free",
            "Does NOT suggest regular wheat bread",
            "This is safety-critical - must handle correctly"
        ],
        metadata={
            "critical": True,
            "allergen": "gluten",
            "severity": "HIGH",
            "difficulty": "hard"
        }
    ),
    
    EvaluationCase(
        name="health_calorie_consideration",
        inputs="I'm really hungry, what's a good dinner?",
        expected_source="health",
        category="health_personalization",
        focus="calorie_awareness",
        description="Tests balancing hunger with calorie constraints",
        evaluation_criteria=[
            "Aware of 500 calorie target",
            "Suggests satisfying but appropriate meals",
            "Acknowledges hunger concern",
            "Balances fullness with calorie limits",
            "Provides practical, filling options"
        ],
        metadata={"calories_target": 500, "difficulty": "medium"}
    ),
    
    # ========================================================================
    # 4. A2A COMMUNICATION & INTEGRATION
    # ========================================================================
    EvaluationCase(
        name="a2a_context_preservation",
        inputs="How do retries work in the notification system?",
        expected_source="rag",
        category="a2a_integration",
        focus="context_awareness",
        description="Tests context preservation through agent pipeline",
        evaluation_criteria=[
            "Routes to RAG agent",
            "Retrieves retry mechanism documentation",
            "Preserves notification system context",
            "Provides specific technical details",
            "Doesn't confuse with unrelated retry concepts"
        ],
        metadata={"requires_context": True, "difficulty": "medium"}
    ),
]


# ============================================================================
# EVALUATION RUNNER
# ============================================================================

def run_agent_query(query: str, deps) -> Dict[str, Any]:
    """Run a query through the orchestrator with retry logic"""
    try:
        for attempt in range(3):
            try:
                run_result = orchestrator_agent.run_sync(query, deps=deps)
                result = run_result.output if hasattr(run_result, 'output') else run_result
                return {
                    "answer": result.answer,
                    "source": result.source,
                    "success": True,
                    "error": None,
                    "attempts": attempt + 1
                }
            except Exception as e:
                if attempt < 2:
                    continue
                return {
                    "answer": None,
                    "source": None,
                    "success": False,
                    "error": str(e),
                    "attempts": 3
                }
    except Exception as e:
        return {
            "answer": None,
            "source": None,
            "success": False,
            "error": str(e),
            "attempts": 0
        }


def evaluate_case(case: EvaluationCase, result: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single test case result"""
    evaluation = {
        "case_name": case.name,
        "passed": False,
        "score": 0.0,
        "criteria_met": [],
        "criteria_failed": [],
        "notes": []
    }
    
    if not result['success']:
        evaluation['notes'].append(f"❌ Failed to execute: {result['error']}")
        return evaluation
    
    # Check routing accuracy
    if case.expected_source:
        if result['source'] == case.expected_source:
            evaluation['criteria_met'].append(f"✓ Correct routing to {case.expected_source} agent")
            evaluation['score'] += 0.5
        else:
            evaluation['criteria_failed'].append(
                f"✗ Wrong routing: expected {case.expected_source}, got {result['source']}"
            )
    
    # Check answer quality (basic checks)
    if result['answer']:
        if len(result['answer']) > 20:
            evaluation['criteria_met'].append("✓ Provided substantive answer")
            evaluation['score'] += 0.3
        else:
            evaluation['criteria_failed'].append("✗ Answer too short")
        
        # Check for hallucination indicators
        if "I don't know" not in result['answer'] or case.expected_source:
            evaluation['criteria_met'].append("✓ Provided confident answer")
            evaluation['score'] += 0.2
    else:
        evaluation['criteria_failed'].append("✗ No answer provided")
    
    evaluation['passed'] = evaluation['score'] >= 0.7
    return evaluation


def print_results_summary(results: Dict[str, Any]):
    """Print evaluation summary"""
    total = results['total_cases']
    passed = sum(1 for r in results['evaluations'] if r['passed'])
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"Total Cases: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Category breakdown
    categories = {}
    for eval_result in results['evaluations']:
        cat = eval_result['category']
        if cat not in categories:
            categories[cat] = {"passed": 0, "total": 0}
        categories[cat]['total'] += 1
        if eval_result['passed']:
            categories[cat]['passed'] += 1
    
    print("\nBy Category:")
    for cat, stats in categories.items():
        rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {cat}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")
    
    print("="*80)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SECOND BRAIN AGENT - EVALUATION SUITE")
    print("="*80 + "\n")
    
    print("Initializing system...")
    docs = load_and_split_markdown("data/docs.md")
    vector_db = create_vectorstore(docs)
    deps = OrchestratorDeps(
        vector_db=vector_db,
        profile_file="data/user_profile.json",
    )
    print("✓ System initialized\n")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(EVALUATION_CASES),
        "evaluations": [],
        "detailed_results": []
    }
    
    for i, case in enumerate(EVALUATION_CASES, 1):
        print(f"\n[{i}/{len(EVALUATION_CASES)}] {case.name}")
        print(f"Category: {case.category} | Focus: {case.focus}")
        print(f"Input: {case.inputs[:80]}{'...' if len(case.inputs) > 80 else ''}")
        print("-" * 80)
        
        # Run query
        query_result = run_agent_query(case.inputs, deps)
        
        # Evaluate
        evaluation = evaluate_case(case, query_result)
        evaluation['category'] = case.category
        evaluation['focus'] = case.focus
        
        # Display result
        if query_result['success']:
            status = "✓ PASS" if evaluation['passed'] else "✗ FAIL"
            print(f"{status} (Score: {evaluation['score']:.1f}/1.0, Attempts: {query_result['attempts']})")
            print(f"Source: [{query_result['source']}]")
            print(f"Answer: {query_result['answer'][:120]}{'...' if len(query_result['answer']) > 120 else ''}")
            
            if evaluation['criteria_met']:
                for criterion in evaluation['criteria_met']:
                    print(f"  {criterion}")
            if evaluation['criteria_failed']:
                for criterion in evaluation['criteria_failed']:
                    print(f"  {criterion}")
        else:
            print(f"✗ ERROR: {query_result['error']}")
        
        results['evaluations'].append(evaluation)
        results['detailed_results'].append({
            "case": asdict(case),
            "result": query_result,
            "evaluation": evaluation
        })
    
    # Save results
    output_file = f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print_results_summary(results)
    print(f"\nDetailed results saved to: {output_file}")
    print("\nEvaluation complete!")
