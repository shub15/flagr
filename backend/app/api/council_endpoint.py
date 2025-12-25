@router.get("/reviews/{review_id}/council", response_model=CouncilTransparencyResponse)
async def get_council_responses(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> CouncilTransparencyResponse:
    """
    Get individual LLM responses from the council for transparency.
    
    **Authentication required**
    
    Shows how each LLM model (GPT, Groq models, Mistral) analyzed the contract:
    - Skeptic agent's council responses
    - Strategist agent's council responses  
    - Auditor agent's council responses
    
    Useful for:
    - Understanding AI decision-making process
    - Debugging consensus failures
    - Seeing which models found what issues
    - Comparing model performance
    
    Note: Only available for reviews created after this feature was deployed.
    """
    from app.services.llm_service import llm_service
    import json
    
    try:
        # Get review
        review = db.query(ContractReview).filter(
            ContractReview.review_id == review_id,
            ContractReview.user_id == current_user.id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {review_id}"
            )
        
        # Get all LLM responses for this review
        llm_responses = db.query(AgentLLMResponse).filter(
            AgentLLMResponse.review_id == review.id
        ).all()
        
        if not llm_responses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Council responses not found. This feature is only available for recent reviews."
            )
        
        # Group responses by agent
        agents_data = {}
        for resp in llm_responses:
            agent_name = resp.agent_name
            if agent_name not in agents_data:
                agents_data[agent_name] = []
            
            # Parse findings from JSON
            findings = []
            if resp.parsed_findings:
                try:
                    findings_data = json.loads(resp.parsed_findings)
                    findings = [ReviewPoint(**f) for f in findings_data]
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse findings for {resp.id}")
            
            agents_data[agent_name].append(LLMResponse(
                provider=resp.llm_provider,
                model=resp.llm_model,
                raw_response=resp.raw_response,
                findings=findings,
                confidence=resp.confidence,
                response_time_ms=resp.response_time_ms
            ))
        
        # Build agent council responses with summaries
        agent_councils = []
        
        # Get final deduplicated findings for context
        final_points_per_agent = {}
        for db_point in review.review_points:
            agent = db_point.agent_source
            if agent not in final_points_per_agent:
                final_points_per_agent[agent] = 0
            final_points_per_agent[agent] += 1
        
        for agent_name, llm_resps in agents_data.items():
            # Generate summary
            num_llms = len(llm_resps)
            total_findings_before_dedup = sum(len(r.findings) for r in llm_resps)
            final_findings = final_points_per_agent.get(agent_name, 0)
            
            # Build detailed summary
            summary_parts = [
                f"{num_llms} LLM{'s' if num_llms > 1 else ''} responded.",
                f"Total findings before dedup: {total_findings_before_dedup}."
            ]
            
            # Show individual model findings
            for llm_resp in llm_resps:
                summary_parts.append(
                    f"{llm_resp.model}: {len(llm_resp.findings)} finding{'s' if len(llm_resp.findings) != 1 else ''} "
                    f"({llm_resp.response_time_ms}ms)."
                )
            
            summary_parts.append(f"Final after dedup: {final_findings} findings.")
            initial_stats = " ".join(summary_parts)
            
            # Generate LLM summary of the raw responses
            prompt = f"""
            You are a helpful legal assistant. Summarize the following findings/responses from multiple AI models regarding a contract review for the '{agent_name}' role.
            Focus on the key risks or points identified. Keep it to a SINGLE paragraph.
            
            Responses:
            {json.dumps([{'model': r.model, 'response': r.raw_response} for r in llm_resps], indent=2)}
            """
            
            try:
                # Use referee (Gemini) for summarization as it's free/fast
                llm_result = await llm_service.gemini_referee.generate(prompt)
                if llm_result['success']:
                    llm_summary = llm_result['content']
                else:
                    llm_summary = "AI summarization unavailable."
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                llm_summary = "AI summarization failed."

            
            agent_councils.append(AgentCouncilResponse(
                agent_name=agent_name,
                llm_responses=llm_resps,
                summary=f"{llm_summary}\n\nSTATS: {initial_stats}",
                total_findings=total_findings_before_dedup,
                final_findings=final_findings
            ))
        
        # Sort by agent name for consistency
        agent_councils.sort(key=lambda x: x.agent_name)
        
        logger.info(
            f"Retrieved council transparency for review {review_id}: "
            f"{len(agent_councils)} agents, {len(llm_responses)} total LLM responses"
        )
        
        return CouncilTransparencyResponse(
            review_id=review_id,
            agents=agent_councils
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get council responses for {review_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve council responses: {str(e)}"
        )
