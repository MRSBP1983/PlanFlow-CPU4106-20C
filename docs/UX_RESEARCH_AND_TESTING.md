# PlanFlow UX research and testing record

## Evidence scope and integrity note

This document records technical validation completed by Marcos Pereira on **16 November 2026**. It separates completed developer testing from user research that has not happened yet. The app uses fictional warehouse-planning data, so these results do not show that the system is suitable for a real workplace.

- Local address: `http://127.0.0.1:8765`
- Runtime used: Python 3.14.4 with Flask 3.1.2
- Database during the completed checks: local SQLite demo
- Browser checks: local Chrome at desktop size (1440 x 1100) and narrow size (390 x 844)
- MySQL credentials were not supplied, so no live MySQL connection was attempted.

## User research status

No planner interview, questionnaire or participant usability session has been completed. No participant responses, timings or feedback have been invented for this document. A future session should use fictional data, identify participants only as P01/P02, obtain their agreement, and record where they become stuck without leading them through the task.

## Automated regression testing

| Date | Command | Result | Observation |
| --- | --- | --- | --- |
| 16 November 2026 | `python -m unittest -v test_app` | **PASS: 19/19 tests passed in 2.051 seconds** | The test suite used a temporary SQLite database. It covered capacity calculations, rounding, invalid input, duplicate plans, absence updates, scenario isolation and snapshots, actuals, CSV export, CSRF, date validation, seeded data, page/assets and database constraints. |

## Completed functional checks

| Test area | Procedure completed | Actual result | Status | Evidence |
| --- | --- | --- | --- | --- |
| Report filters | Selected 1 October 2026 to 31 October 2026 and Day shift in the Reports page. Queried the same range through `/api/reports`. | The UI displayed the chosen dates and Day shift. The API returned HTTP 200, 93 department-shift records across 31 days and 380,000 forecast cases. | **PASS** | [Filtered report screenshot](evidence/report_filters_day_shift_2026-11-16.png) |
| Invalid input | Entered 31 October 2026 as the start date and 1 October 2026 as the end date, then updated the report. | The page displayed “Start date must be before end date.” The matching API request returned HTTP 400. The previous valid report was not replaced with invalid data. | **PASS** | [Invalid-range screenshot](evidence/invalid_date_range_2026-11-16.png) |
| CSV export | Requested the filtered Day-shift CSV for 1–31 October 2026 and compared its record count with the report result. | HTTP 200. The export contained 22 headings and 93 data rows, matching the filtered report. The rows include plan date, department, shift, forecast, staffing, capacity, deadline, actuals and cost fields. | **PASS** | [Exported CSV](evidence/report_export_day_shift_2026-10-01_to_2026-10-31.csv) |
| SQLite demo connection | Checked `/api/health` while the local app was running. | The health response was `status: ok` and `backend: SQLite demo`. The full October–December demonstration report also loaded with 552 department-shift records. | **PASS** | [Full demo report screenshot](evidence/report_page_2026-11-16.png) |
| Responsive layout | Repeated the valid report-filter check at a 390-pixel-wide browser viewport. | Navigation, date fields, shift filter, action buttons and report summary stayed visible without horizontal page overflow in the captured view. | **PASS (basic check)** | [390px responsive screenshot](evidence/responsive_report_filters_390px_2026-11-16.png) |
| Keyboard and focus | Put focus on the report date control and reviewed its visible focus styling. | The Start date control received focus and showed a visible outline. The headless Tab-event check did not advance focus to the next control, so a full real-keyboard journey remains to be retested manually. | **PARTIAL** | [Focus screenshot](evidence/keyboard_focus_report_start_2026-11-16.png) |
| MySQL connection | Not attempted because no authorised host, username or password were provided. | No claim is made about live MySQL connectivity, tables, queries or persistence. | **NOT TESTED** | N/A |

## Accessibility observations

The report controls have visible labels for Start date, End date and Shift. The invalid-range message is announced through the page error area and is visible in the evidence above. The narrow-screen check gives basic evidence that the filter layout responds to a smaller viewport.

This is not a full accessibility evaluation. The following still need testing with people or appropriate tools: complete keyboard-only navigation in a normal browser, screen-reader announcements, colour contrast measurement, zoom/reflow at higher magnification, and user understanding of chart labels and deadline-risk messages.

## Planned participant usability session

This section remains pending until real participants take part.

| Task | Success condition | Current status |
| --- | --- | --- |
| Find the 8 October Day shift shortage | Identifies Picking 2 and Packing 1 | Not tested with a participant |
| Edit a workload plan | Saves the intended forecast without a duplicate | Not tested with a participant |
| Account for one absence | Understands scheduled staff minus absent staff | Not tested with a participant |
| Cover forecast in Scenarios | Gets 20 staff and zero volume shortfall | Not tested with a participant |
| Interpret the deadline warning | Understands that zero shortfall does not guarantee the deadline | Not tested with a participant |
| Export a report | Selects a range and obtains a matching CSV | Not tested with a participant |

## Next steps

1. Run at least one task-based usability session using fictional data and record the participant code, date, task outcome, assistance required and feedback.
2. Repeat the database, save/reload, scenario and CSV checks after an authorised MySQL connection is available.
3. Retest keyboard navigation in a normal browser with a physical keyboard and record the result before describing it as accessible.
4. Use any user feedback to make a small interface improvement, then record the retest result and a new screenshot.
