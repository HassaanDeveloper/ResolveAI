from typing import Optional, List
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import PolicySearchResult, ToolResult
from app.rag import retrieval_service, SearchCompanyPolicyRequest, SearchCompanyPolicyResponse
from app.reliability import with_retry, DEFAULT_READ_RETRY, gemini_circuit_breaker


class SearchCompanyPolicyInput(ToolInput):
    query: str = Field(..., description="Search query for company policies")
    max_results: int = Field(default=5, ge=1, le=20)


class SearchCompanyPolicyOutput(ToolOutput):
    results: List[PolicySearchResult] = []
    error: Optional[str] = None


class SearchCompanyPolicyTool(BaseTool):
    name = "search_company_policy"
    category = "read"
    description = "Search company policies using RAG retrieval from Supabase pgvector"
    input_schema = SearchCompanyPolicyInput
    output_schema = SearchCompanyPolicyOutput

    async def execute(self, input_data: SearchCompanyPolicyInput) -> ToolResult:
        async def _search():
            # Use the RAG retrieval service
            request = SearchCompanyPolicyRequest(
                query=input_data.query,
                max_results=input_data.max_results
            )
            
            # Use circuit breaker for Gemini embeddings
            async def _retrieve():
                return await retrieval_service.search_company_policy(request)
            
            response = await gemini_circuit_breaker.call(_retrieve)
            
            if response.error:
                return self.error_result("RETRIEVAL_ERROR", response.error)
            
            # Convert Evidence objects to PolicySearchResult
            results = [
                PolicySearchResult(
                    document_name=ev.document_name,
                    section=ev.section,
                    content=ev.content,
                    source=ev.source,
                    version=ev.version,
                    relevance_score=ev.relevance_score
                )
                for ev in response.results
            ]
            
            return self.success_result(SearchCompanyPolicyOutput(results=results))
        
        # Execute with retry
        return await with_retry(_search, policy=DEFAULT_READ_RETRY, operation_name="search_company_policy")


search_company_policy_tool = SearchCompanyPolicyTool()