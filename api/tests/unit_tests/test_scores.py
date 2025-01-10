from api.endpoints.legislators import calculate_legislator_scores, VoteData, SponsorData


def test_empty_data():
    result = calculate_legislator_scores([], {}, [])
    assert result == {
        "delinquency": None,
        "bipartisanship": None,
        "success": None,
        "virtue_signaling": 0,
    }


def test_delinquency_score():
    votes = [
        VoteData("absent", "", 1, 1),
        VoteData("yes", "", 2, 2),
        VoteData("no", "", 3, 3),
        VoteData("absent", "", 4, 4),
    ]
    result = calculate_legislator_scores(votes, {}, [])
    assert result["delinquency"] == 0.5  # 2 absent votes out of 4 total


def test_bipartisanship_score():
    votes = [
        VoteData("yes", "", 1, 1),
        VoteData("no", "", 2, 2),
        VoteData("yes", "", 3, 3),
        VoteData("no", "", 4, 4),
    ]
    # Opposite party voted the same way on bills 1 and 4
    opposite_votes = {(1, 1): 10, (4, 4): 15}
    result = calculate_legislator_scores(votes, opposite_votes, [])
    assert result["bipartisanship"] == 0.5  # 2 matching votes out of 4 total


def test_success_score():
    votes = [
        VoteData("yes", "Bill passed", 1, 1),
        VoteData("no", "Bill failed", 2, 2),
        VoteData("yes", "Bill failed", 3, 3),
        VoteData("no", "Bill passed", 4, 4),
        VoteData("absent", "Bill passed", 5, 5),  # Should be ignored
    ]
    result = calculate_legislator_scores(votes, {}, [])
    assert result["success"] == 0.5  # 2 successful votes out of 4 yes/no votes


def test_virtue_signaling_score():
    sponsored_bills = [
        SponsorData("Introduced"),
        SponsorData("Passed"),
        SponsorData("Introduced - Referred to Committee"),
        SponsorData("Signed into Law"),
    ]
    result = calculate_legislator_scores([], {}, sponsored_bills)
    assert result["virtue_signaling"] == 0.5  # 2 introduced bills out of 4 total


def test_all_scores_combined():
    votes = [
        VoteData("yes", "Bill passed", 1, 1),
        VoteData("absent", "Bill failed", 2, 2),
        VoteData("no", "Bill failed", 3, 3),
    ]
    opposite_votes = {(1, 1): 5}  # Opposite party agreed on first vote
    sponsored_bills = [
        SponsorData("Introduced"),
        SponsorData("Passed"),
    ]

    result = calculate_legislator_scores(votes, opposite_votes, sponsored_bills)
    assert all(0 <= score <= 1 for score in result.values())
    assert result["delinquency"] == round(1 / 3, 3)  # 1 absent out of 3
    assert result["bipartisanship"] == round(1 / 3, 3)  # 1 matching out of 3
    assert result["success"] == round(2 / 2, 3)  # 2 successful out of 2 yes/no votes
    assert result["virtue_signaling"] == 0.5  # 1 introduced out of 2
