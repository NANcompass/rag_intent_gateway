"""
Intent processing router for RAG Intent Gateway.
"""
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models import IntentRequest, IntentResponse, APIResponse, IntentType
from app.services import llm_service

router = APIRouter(prefix="/intent", tags=["Intent Processing"])


@router.post(
    "/process",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Process user query intent",
    description="Analyze user query and history to determine intent and perform query rewriting"
)
async def process_intent(request: IntentRequest) -> APIResponse:
    """
    Process user query to analyze intent and perform query transformation.

    This endpoint:
    1. Analyzes the query using LLM to determine intent (RAG or CHITCHAT)
    2. Performs context resolution for ambiguous references
    3. Generates sub-queries for complex questions
    4. Creates synonym-expanded queries for better retrieval

    Args:
        request: IntentRequest containing query and optional history

    Returns:
        APIResponse with intent analysis result
    """
    try:
        # Call LLM to analyze intent
        intent_response: IntentResponse = await llm_service.analyze_intent(
            query=request.query,
            history=request.history
        )

        # Handle different intent types
        if intent_response.intent_type == IntentType.CHITCHAT:
            # For CHITCHAT, directly return the reply text
            return APIResponse(
                success=True,
                data=intent_response,
                message="Chitchat intent detected - direct reply provided"
            )

        else:  # RAG intent
            # Collect all queries for retrieval
            all_queries = []

            # Add standalone query
            if intent_response.standalone_query:
                all_queries.append(intent_response.standalone_query)

            # Add sub-queries
            if intent_response.sub_queries:
                all_queries.extend(intent_response.sub_queries)

            # Add expanded queries
            if intent_response.expanded_queries:
                all_queries.extend(intent_response.expanded_queries)

            # Print retrieval queries for debugging
            print("\n" + "="*60)
            print("🔍 RAG Intent - Multi-path Retrieval Queries:")
            print("="*60)
            for i, query in enumerate(all_queries, 1):
                print(f"  [{i}] {query}")
            print("="*60 + "\n")

            return APIResponse(
                success=True,
                data=intent_response,
                message="RAG intent detected - retrieval queries generated"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Intent analysis failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
