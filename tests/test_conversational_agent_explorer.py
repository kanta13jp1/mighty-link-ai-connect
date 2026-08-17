import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.conversational_agent_explorer import ConversationalAgentExplorer


def test_conversational_agent_explorer_skills_query():
    copilot = ConversationalAgentExplorer()
    response = copilot.ask("Go言語で85万円以上のフルリモート案件はある？")

    assert response.matched_items_count >= 1
    assert "Go" in response.summary_message
    assert response.proposal_draft is not None
    assert len(response.suggested_actions) == 3


def test_conversational_agent_explorer_general_query():
    copilot = ConversationalAgentExplorer()
    response = copilot.ask("来週からアサインできる案件の候補を教えて")

    assert response.matched_items_count > 0
    assert "最有力案件" in response.summary_message
