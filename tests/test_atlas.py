"""Business/API regression tests. All writes use a temporary ledger."""
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient
from backend import api, ingest, preferences
from backend.analytics import summary
from backend.imports import preview_import

CSV = 'ID,时间,分类,二级分类,类型,金额,备注\n001,2026-09-08 12:00:00,餐饮,外卖,支出,100,午饭\n002,2026-09-20 12:00:00,餐饮,外卖,支出,900,聚会\n003,2026-10-08 12:00:00,日常,学习,支出,200,书\n004,2026-10-09 12:00:00,生活费,,收入,3000,生活费\n'

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.stack = ExitStack()
        origin = root / 'origin'; origin.mkdir()
        (origin / 'seed.csv').write_text(CSV, encoding='utf-8')
        for module, key, value in [
            (ingest, 'ORIGIN_DIR', origin), (api, 'ORIGIN_DIR', origin),
            (ingest, 'ATLAS_PROCESSED_DIR', root / 'processed_atlas'),
            (ingest, 'ATLAS_ARCHIVE_DIR', root / 'archive_atlas'),
            (ingest, 'DB_FILE', root / 'processed_atlas' / 'ledger_atlas.sqlite3'),
            (ingest, 'MANIFEST_FILE', root / 'processed_atlas' / 'dataset_manifest.json'),
            (preferences, 'SETTINGS_FILE', root / 'settings.json'),
            (api, 'ADMIN_TOKEN', ''), (api, '_frame', None), (api, '_stamp', None),
        ]: self.stack.enter_context(patch.object(module, key, value))
        ingest.rebuild()
        self.client = TestClient(api.app)

    def tearDown(self):
        self.client.close(); self.stack.close(); self.temp.cleanup()

    def test_partial_comparison_uses_same_calendar_days(self):
        data = self.client.get('/api/summary?month=2026-10').json()
        self.assertEqual(data['metrics']['expense_change'], 100)
        self.assertEqual(data['comparison']['expense'], 100)
        self.assertEqual(data['coverage']['observed_days'], 9)
        self.assertEqual(len(data['daily']), 9)
        self.assertEqual(data['daily'][0]['amount'], 0)

    def test_missing_previous_month_has_no_fake_percentage(self):
        frame = ingest.load_master(); frame = frame[frame['月份'] == '2026-10']
        self.assertIsNone(summary(frame)['metrics']['expense_change'])

    def test_empty_summary_has_stable_metrics(self):
        data = summary(ingest.load_master().iloc[0:0])
        self.assertIsNone(data['month']); self.assertEqual(data['metrics']['expense'], 0)

    def test_preview_does_not_write_and_preserves_leading_zero_id(self):
        before = list(api.ORIGIN_DIR.iterdir())
        response = self.client.post('/api/import/preview', files={'file': ('test.csv', CSV.encode(), 'text/csv')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['existing_rows'], 4)
        self.assertEqual(response.json()['new_rows'], 0)
        self.assertEqual(list(api.ORIGIN_DIR.iterdir()), before)
        self.assertEqual(ingest.load_master().iloc[0]['ID'], '001')

    def test_reimport_is_idempotent_and_updates_matching_id(self):
        updated = CSV.replace('支出,200,书', '支出,250,书')
        for _ in range(2):
            response = self.client.post('/api/import', files={'file': ('update.csv', updated.encode(), 'text/csv')})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['manifest']['rows'], 4)
        self.assertEqual(self.client.get('/api/summary?month=2026-10').json()['metrics']['expense'], 250)

    def test_invalid_file_never_enters_sources(self):
        before = list(api.ORIGIN_DIR.iterdir())
        invalid = CSV.replace('支出,200', '支出,not-money')
        preview = self.client.post('/api/import/preview', files={'file': ('bad.csv', invalid.encode())})
        self.assertFalse(preview.json()['valid'])
        response = self.client.post('/api/import', files={'file': ('bad.csv', invalid.encode())})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(list(api.ORIGIN_DIR.iterdir()), before)

    def test_import_correction_can_move_date_backwards(self):
        updated = CSV.replace('2026-10-08 12:00:00', '2026-10-02 12:00:00').replace('支出,200,书', '支出,275,改正日期')
        response = self.client.post('/api/import', files={'file': ('correction.csv', updated.encode())})
        self.assertEqual(response.status_code, 200)
        row = ingest.load_master().set_index('ID').loc['003']
        self.assertEqual(row['时间'].day, 2)
        self.assertEqual(row['金额'], 275)

    def test_successive_imports_keep_latest_correction(self):
        for amount in [250, 230, 210]:
            updated = CSV.replace('支出,200,书', f'支出,{amount},书')
            self.assertEqual(self.client.post('/api/import', files={'file': ('update.csv', updated.encode())}).status_code, 200)
        self.assertEqual(self.client.get('/api/summary?month=2026-10').json()['metrics']['expense'], 210)

    def test_missing_columns_and_unsupported_extension(self):
        for name, value in [('missing.csv', b'x,y\n1,2'), ('bad.txt', CSV.encode())]:
            self.assertEqual(self.client.post('/api/import/preview', files={'file': (name, value)}).status_code, 400)

    def test_budget_persistence_bounds_and_removal(self):
        self.assertEqual(self.client.put('/api/budgets/2026-10', json={'amount': 2500}).status_code, 200)
        self.assertEqual(self.client.get('/api/summary?month=2026-10').json()['budget'], 2500)
        self.assertEqual(self.client.put('/api/budgets/2026-10', json={'amount': -1}).status_code, 422)
        self.assertEqual(self.client.put('/api/budgets/2026-13', json={'amount': 10}).status_code, 400)
        self.client.put('/api/budgets/2026-10', json={'amount': None})
        self.assertIsNone(preferences.get_budget('2026-10'))

    def test_token_guards_preview_import_and_budget(self):
        with patch.object(api, 'ADMIN_TOKEN', 'test-token'):
            self.assertTrue(self.client.get('/api/health').json()['auth_required'])
            self.assertEqual(self.client.post('/api/import/preview', files={'file': ('test.csv', CSV.encode())}).status_code, 401)
            self.assertEqual(self.client.post('/api/import', files={'file': ('test.csv', CSV.encode())}).status_code, 401)
            self.assertEqual(self.client.put('/api/budgets/2026-10', json={'amount': 100}).status_code, 401)
            self.assertEqual(self.client.put('/api/budgets/2026-10', json={'amount': 100}, headers={'X-Admin-Token': 'test-token'}).status_code, 200)

    def test_transfer_or_non_finite_amount_is_rejected(self):
        frame = ingest.load_master()
        for bad in [CSV.replace('支出,200', '转账,200'), CSV.replace('支出,200', '支出,inf')]:
            self.assertFalse(preview_import(bad.encode(), '.csv', frame)['valid'])

    def test_month_review_persists_without_overwriting_budget(self):
        preferences.set_budget('2026-10', 3000)
        response = self.client.put('/api/reviews/2026-10', json={'note': '  添置了书本。\n一起打球。  ', 'status': 'auto'})
        self.assertEqual(response.status_code, 200)
        result = self.client.get('/api/summary?month=2026-10').json()
        self.assertEqual(result['review']['note'], '添置了书本。\n一起打球。')
        self.assertEqual(result['budget'], 3000)
        preferences.set_budget('2026-10', 2800)
        self.assertEqual(preferences.get_reviews()['2026-10']['note'], result['review']['note'])

    def test_explicit_month_close_changes_statistics(self):
        self.client.put('/api/reviews/2026-10', json={'note': '', 'status': 'closed'})
        result = self.client.get('/api/summary?month=2026-10').json()
        self.assertFalse(result['coverage']['is_partial'])
        self.assertEqual(result['coverage']['observed_days'], 31)
        self.assertEqual(result['comparison']['expense'], 1000)
        self.assertEqual(result['metrics']['expense_change'], -80)
        self.assertEqual(len(self.client.get('/api/patterns?month=2026-10').json()['daily']), 31)
        self.client.put('/api/reviews/2026-10', json={'note': '', 'status': 'auto'})
        self.assertEqual(self.client.get('/api/summary?month=2026-10').json()['coverage']['observed_days'], 9)

    def test_historical_month_can_be_marked_in_progress(self):
        self.client.put('/api/reviews/2026-09', json={'status': 'in_progress'})
        result = self.client.get('/api/summary?month=2026-09').json()
        self.assertTrue(result['coverage']['is_partial'])
        self.assertEqual(result['coverage']['observed_days'], 20)

    def test_incomplete_comparison_month_suppresses_percentage(self):
        self.client.put('/api/reviews/2026-09', json={'status': 'in_progress'})
        self.client.put('/api/reviews/2026-10', json={'status': 'closed'})
        result = self.client.get('/api/summary?month=2026-10').json()
        self.assertFalse(result['comparison']['available'])
        self.assertIsNone(result['metrics']['expense_change'])

    def test_in_progress_comparison_uses_coverage_before_date_filter(self):
        self.client.put('/api/reviews/2026-09', json={'status': 'in_progress'})
        result = self.client.get('/api/summary?month=2026-10').json()
        # September is recorded through day 20, even if its first-nine-day
        # window contains no transaction exactly on day 9.
        self.assertTrue(result['comparison']['available'])
        self.assertEqual(result['comparison']['expense'], 100)
        self.assertEqual(result['metrics']['expense_change'], 100)

    def test_review_validation_and_write_protection(self):
        self.assertEqual(self.client.put('/api/reviews/2026-10', json={'note': '字'*801}).status_code, 422)
        self.assertEqual(self.client.put('/api/reviews/2026-10', json={'status': 'invalid'}).status_code, 422)
        self.assertEqual(self.client.put('/api/reviews/2099-01', json={'note': ''}).status_code, 404)
        with patch.object(api, 'ADMIN_TOKEN', 'test-token'):
            self.assertEqual(self.client.put('/api/reviews/2026-10', json={'note': ''}).status_code, 401)

    def test_import_preview_reports_actual_field_changes(self):
        updated = CSV.replace('支出,200,书', '支出,250,新书')
        result = preview_import(updated.encode(), '.csv', ingest.load_master())
        self.assertEqual(result['updated_rows'], 1)
        self.assertEqual(result['unchanged_rows'], 3)
        fields = {item['field']: item for item in result['changes'][0]['fields']}
        self.assertEqual(fields['金额'], {'field': '金额', 'before': '200.00', 'after': '250.00'})
        self.assertEqual(fields['备注']['after'], '新书')
        self.assertEqual(ingest.load_master().set_index('ID').loc['003']['金额'], 200)

    def test_unchanged_import_has_no_false_changes(self):
        result = preview_import(CSV.encode(), '.csv', ingest.load_master())
        self.assertEqual(result['updated_rows'], 0)
        self.assertEqual(result['unchanged_rows'], 4)
        self.assertEqual(result['changes'], [])

if __name__ == '__main__': unittest.main()
