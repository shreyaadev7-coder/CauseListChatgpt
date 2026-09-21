# Karnataka High Court Cause List → Excel

Automates the following flow in GitHub Actions:

1. Open the Karnataka High Court cause-list search page.
2. Select **Bengaluru Bench**.
3. Use the **immediately following calendar day** as the cause-list date.
4. Select **Advocate** as the search type.
5. Search for **Mahesh Chowdhary**.
6. Prefer the **GET DETAILS** result table; fall back to the **PRINT LIST** PDF if needed.
7. Extract exactly the 8 requested table columns.
8. Generate a formatted `.xlsx` file and upload it as a GitHub Actions artifact.

## Important

The website could not be live-tested from the current execution environment because the Karnataka judiciary host timed out/DNS resolution was unavailable. The scraper therefore uses flexible label/text discovery, but one live GitHub Actions test may be needed to calibrate the site's exact selectors or date widget.

## Output schema

The workbook intentionally preserves exactly these 8 columns, including the duplicate `SL NO` header:

- SL NO
- CASE NUMBER
- CASE NAME
- CH
- LIST NO
- SL NO
- STATUS
- JUDGES

The date is retained as a title above the table.
