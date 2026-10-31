import core.data_store as ds

class FakeDB:
    def __init__(self, rows): self.rows = rows; self.last_query = ''
    def fetch_all(self, query, params=()): self.last_query=query; return self.rows

def test_application_loader_keeps_database_ids_and_separate_processing_status(monkeypatch):
    monkeypatch.setattr(ds, '_schema_ready', True)
    row = {'_row_id': 41, 'Timestamp': None, 'Full Name': 'Example Person', 'Email': 'person@example.com',
           'Phone': None, 'Postal Code': None, 'Province': None, 'Current Status': 'In the camp',
           'Desired Training': None, 'Financial Situation': None, 'Currently in a Language Course': None,
           'English Level': None, 'Dutch Level': None, 'Municipal Pressure Regarding Work': None,
           'Completed Another IT Bootcamp': None, 'Followed an Online IT Course': None, 'Prior IT Work Experience': None,
           'Currently Involved in Another Project': None, 'Desired IT Department(s)': None,
           'Reasons for Applying to VIT': None, 'Motivation': None, 'Mentor Meeting': 'OK',
           'Application Period': None, 'Green Check': None, 'Internal Tracking 1': None,
           'Internal Tracking 2': None, 'Internal Tracking 3': None, 'Processing Status': 'DONE'}
    fake=FakeDB([row]); monkeypatch.setattr(ds, '_db', fake)
    table=ds.load_applications()
    assert table.row_ids == [41]
    assert table.rows[0][table.index('Current Status')] == 'In the camp'
    assert table.rows[0][table.index('Processing Status')] == 'DONE'
    assert table.rows[0][table.index('Mentor Meeting')] == 'OK'
    assert '"ProcessingStatus"' in fake.last_query


def test_delete_record_rejects_unknown_entity_without_database(monkeypatch):
    monkeypatch.setattr(ds, '_schema_ready', True)
    try:
        ds.delete_record('users', 1)
    except ds.DataError as exc:
        assert 'cannot be deleted' in str(exc)
    else:
        raise AssertionError('Unknown entity should be rejected')


def test_delete_record_rejects_missing_id_without_database(monkeypatch):
    monkeypatch.setattr(ds, '_schema_ready', True)
    try:
        ds.delete_record('application', None)
    except ds.DataError as exc:
        assert 'Select a record' in str(exc)
    else:
        raise AssertionError('Missing record id should be rejected')


def test_admin_contact_directory_joins_applications_and_mentor_records(monkeypatch):
    monkeypatch.setattr(ds, '_schema_ready', True)
    fake = FakeDB([{'trainee_id': 7, 'full_name': 'Example Person',
                    'email': 'example@example.com', 'phone': '+31 6 12345678',
                    'application_status': 'Active', 'mentor_names': 'Example Mentor'}])
    monkeypatch.setattr(ds, '_db', fake)
    contacts = ds.load_admin_contacts()
    assert contacts[0]['trainee_id'] == 7
    assert contacts[0]['email'] == 'example@example.com'
    assert contacts[0]['mentor_names'] == 'Example Mentor'
    assert 'JOIN "Applications"' in fake.last_query
    assert 'JOIN "Mentors"' in fake.last_query
