# Протокол проверки проекта

Дата: 2026-11-10T23:44:54

Выполнено 31 тестов; ошибок 0; непройденных 0.

Команда: `python scripts/check_project.py`.

Проверки выполняются на временных SQLite-базах и копии исходной базы. Рабочая база не изменяется.

| Проверка | Результат |
|---|---|
| `test_system.SystemTests.test_backup_round_trip_and_atomic_rollback` | passed |
| `test_system.SystemTests.test_concurrent_capacity` | passed |
| `test_system.SystemTests.test_contact_duplicate` | passed |
| `test_system.SystemTests.test_cyrillic_search` | passed |
| `test_system.SystemTests.test_delete_assignment_returns_hours` | passed |
| `test_system.SystemTests.test_delete_teacher_returns_hours` | passed |
| `test_system.SystemTests.test_duplicate_assignment_and_multiple_groups` | passed |
| `test_system.SystemTests.test_excel_pdf_export_matches_filters` | passed |
| `test_system.SystemTests.test_existing_database_migration_is_idempotent` | passed |
| `test_system.SystemTests.test_failed_edit_keeps_both_balances` | passed |
| `test_system.SystemTests.test_filters_semester_teacher` | passed |
| `test_system.SystemTests.test_legacy_backup_preserved` | passed |
| `test_system.SystemTests.test_missing_pool_rejected` | passed |
| `test_system.SystemTests.test_normalized_exact_duplicate` | passed |
| `test_system.SystemTests.test_numeric_sort` | passed |
| `test_system.SystemTests.test_overallocation_rejected` | passed |
| `test_system.SystemTests.test_plan_cannot_shrink_below_assignments` | passed |
| `test_system.SystemTests.test_pool_validation_and_duplicate` | passed |
| `test_system.SystemTests.test_rate_is_per_year_and_720_boundary` | passed |
| `test_system.SystemTests.test_reduction_returns_hours` | passed |
| `test_system.SystemTests.test_remaining_by_type_and_week` | passed |
| `test_system.SystemTests.test_separate_names` | passed |
| `test_system.SystemTests.test_teacher_validation` | passed |
| `test_system.SystemTests.test_transfer_between_pools` | passed |
| `test_system.SystemTests.test_typo_requires_explicit_override` | passed |
| `test_system.SystemTests.test_update_own_card_not_duplicate` | passed |
| `test_ui.UITests.test_dialogs_and_phone_mask` | passed |
| `test_ui.UITests.test_main_window_all_tabs` | passed |
| `test_ui.UITests.test_methodist_buttons_hidden` | passed |
| `test_ui.UITests.test_report_filters_and_refresh_preserved` | passed |
| `test_ui.UITests.test_table_numbers_sort_numerically` | passed |

Проверены сервисы и запуск Qt в режиме offscreen. PostgreSQL-сервер и работа на Windows/macOS в этом прогоне не проверялись.

```text
test_backup_round_trip_and_atomic_rollback (test_system.SystemTests.test_backup_round_trip_and_atomic_rollback) ... ok
test_concurrent_capacity (test_system.SystemTests.test_concurrent_capacity) ... ok
test_contact_duplicate (test_system.SystemTests.test_contact_duplicate) ... ok
test_cyrillic_search (test_system.SystemTests.test_cyrillic_search) ... ok
test_delete_assignment_returns_hours (test_system.SystemTests.test_delete_assignment_returns_hours) ... ok
test_delete_teacher_returns_hours (test_system.SystemTests.test_delete_teacher_returns_hours) ... ok
test_duplicate_assignment_and_multiple_groups (test_system.SystemTests.test_duplicate_assignment_and_multiple_groups) ... ok
test_excel_pdf_export_matches_filters (test_system.SystemTests.test_excel_pdf_export_matches_filters) ... ok
test_existing_database_migration_is_idempotent (test_system.SystemTests.test_existing_database_migration_is_idempotent) ... ok
test_failed_edit_keeps_both_balances (test_system.SystemTests.test_failed_edit_keeps_both_balances) ... ok
test_filters_semester_teacher (test_system.SystemTests.test_filters_semester_teacher) ... ok
test_legacy_backup_preserved (test_system.SystemTests.test_legacy_backup_preserved) ... ok
test_missing_pool_rejected (test_system.SystemTests.test_missing_pool_rejected) ... ok
test_normalized_exact_duplicate (test_system.SystemTests.test_normalized_exact_duplicate) ... ok
test_numeric_sort (test_system.SystemTests.test_numeric_sort) ... ok
test_overallocation_rejected (test_system.SystemTests.test_overallocation_rejected) ... ok
test_plan_cannot_shrink_below_assignments (test_system.SystemTests.test_plan_cannot_shrink_below_assignments) ... ok
test_pool_validation_and_duplicate (test_system.SystemTests.test_pool_validation_and_duplicate) ... ok
test_rate_is_per_year_and_720_boundary (test_system.SystemTests.test_rate_is_per_year_and_720_boundary) ... ok
test_reduction_returns_hours (test_system.SystemTests.test_reduction_returns_hours) ... ok
test_remaining_by_type_and_week (test_system.SystemTests.test_remaining_by_type_and_week) ... ok
test_separate_names (test_system.SystemTests.test_separate_names) ... ok
test_teacher_validation (test_system.SystemTests.test_teacher_validation) ... ok
test_transfer_between_pools (test_system.SystemTests.test_transfer_between_pools) ... ok
test_typo_requires_explicit_override (test_system.SystemTests.test_typo_requires_explicit_override) ... ok
test_update_own_card_not_duplicate (test_system.SystemTests.test_update_own_card_not_duplicate) ... ok
test_dialogs_and_phone_mask (test_ui.UITests.test_dialogs_and_phone_mask) ... ok
test_main_window_all_tabs (test_ui.UITests.test_main_window_all_tabs) ... ok
test_methodist_buttons_hidden (test_ui.UITests.test_methodist_buttons_hidden) ... ok
test_report_filters_and_refresh_preserved (test_ui.UITests.test_report_filters_and_refresh_preserved) ... ok
test_table_numbers_sort_numerically (test_ui.UITests.test_table_numbers_sort_numerically) ... ok

----------------------------------------------------------------------
Ran 31 tests in 1.442s

OK
```
