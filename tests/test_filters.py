from core.filters import duplicate_flags, name_matches, same_option, vit_cohort_names, previous_vit_labels, different_vit_records

def test_name_matches_name_or_surname_prefix():
    assert name_matches('as', 'Asiye Turan')
    assert name_matches('as', 'Mehmet As')
    assert not name_matches('as', 'Mehmet Kirmizi')
    assert name_matches('', 'Anyone')

def test_duplicate_flags_only_same_name_and_email():
    rows = [['A Person', 'a@example.com'], ['A Person', 'a@example.com'], ['A Person', 'b@example.com']]
    duplicate, first = duplicate_flags(rows, 0, 1)
    assert duplicate == [True, True, False]
    assert first == [True, False, True]

def test_recommendation_comparison_tolerates_period_and_longer_wording():
    assert same_option('Suitable to be directed straight to ITPH within the VIT project.', 'Suitable to be directed straight to ITPH')
    assert not same_option('', 'Something')

def test_vit_history_comparison():
    rows = [['Ada Example','VIT1'], ['Bea Example','VIT2'], ['Ada Example','VIT2']]
    cohorts = vit_cohort_names(rows, 0, 1)
    labels = previous_vit_labels([['Ada Example'],['Bea Example'],['New Person']], 0, cohorts)
    assert labels == ['VIT1 + VIT2', 'VIT2', '']
    records = different_vit_records(rows, 0, -1, 1)
    assert records == [['Bea Example', None, 'VIT2 only']]
