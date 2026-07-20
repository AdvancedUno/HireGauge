import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hiregauge.analysis.crosscheck import crosscheck_claims

def test_crosscheck_empty():
    assert crosscheck_claims({}) == []
    assert crosscheck_claims(None) == []

def test_crosscheck_star_inflation():
    profile = {
        "resume_text": "I have 10k github stars on my repos.",
        "github_data": {
            "repositories": [
                {"stargazers_count": 5},
                {"stargazers_count": 10}
            ]
        }
    }
    issues = crosscheck_claims(profile)
    assert len(issues) == 1
    assert "10000" in issues[0]
    assert "10" in issues[0]

def test_crosscheck_phantom_pubs():
    profile = {
        "resume_text": "Published a paper at NeurIPS and CVPR.",
        "publications_fetched": True,
        "publications": []
    }
    issues = crosscheck_claims(profile)
    assert len(issues) == 1
    assert "zero papers" in issues[0]
