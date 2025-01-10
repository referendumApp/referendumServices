from api.endpoints.legislators import calculate_legislator_scores
from common.database.referendum.models import LegislatorVote


def test_empty_data():
    result = calculate_legislator_scores([], {})
    assert result == {
        "delinquency": None,
        "bipartisanship": None,
    }


def test_legislator_scores():
    votes = [
        LegislatorVote(
            legislator_id=0,
            bill_id=0,
            bill_action_id=0,
            vote_choice_id=1,
        ),
        LegislatorVote(legislator_id=0, bill_id=1, bill_action_id=1, vote_choice_id=4),
        LegislatorVote(legislator_id=0, bill_id=2, bill_action_id=2, vote_choice_id=2),
    ]
    opposite_votes = {(0, 1): 50}  # Opposite party agreed on first vote

    result = calculate_legislator_scores(votes, opposite_votes)
    assert all(0 <= score <= 1 for score in result.values())
    assert result["delinquency"] == round(1 / 3, 3)
    assert result["bipartisanship"] == round(1 / 3, 3)
