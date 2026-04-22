# HabitLoop Retention Intelligence: A-Z Playbook

## One-Line Explanation

I built a real-data competitive retention benchmark that analyzes public App Store reviews from competing consumer apps and converts customer pain points into lifecycle campaign ideas.

## Role Fit

This is strongest for a Retention Marketing Specialist role because it proves customer journey thinking, segmentation, churn-signal detection, lifecycle campaign ideation, analytical thinking, and structured execution.

It still supports creative roles because the final output includes campaign messaging and customer-language insights, but the center of gravity is retention.

## What To Say If Asked Why These Apps

I chose competitive pairs inside retention-heavy consumer categories because retention is visible in the customer language. Users talk about streaks, reminders, motivation, pricing, content fatigue, bugs, learning progress, and missed routines. Comparing direct or near-direct competitors makes the project more useful because it shows which problems are category-wide and which ones over-index for a specific app.

## What To Say If Asked About Data

The project uses real public App Store review feeds from Apple. I did not use simulated datasets. I collected recent reviews, cleaned the text, classified each review into a retention theme, mapped each theme to a lifecycle stage, and used that to recommend campaign interventions.

## Build Steps

1. Choose retention-heavy categories with clear competitors.
2. Collect public reviews from Apple App Store RSS feeds.
3. Clean review title, text, rating, vote count, app name, category, competitive set, and date.
4. Tag reviews into retention themes using a keyword taxonomy.
5. Score sentiment using rating plus lightweight lexical sentiment.
6. Map each theme to a lifecycle stage.
7. Compare competitors by signal share and risk share.
8. Convert high-volume/high-risk themes into campaign briefs.
9. Build a dashboard with category filters, app filters, evidence, and a campaign decision lab.
10. Package the project with a README, proof sheet, strategy memo, and resume bullet.

## Suggested Interview Explanation

The interesting part was not scraping reviews. The useful part was translating unstructured customer language into lifecycle action and competitor insight. For example, a pricing complaint is not just negative sentiment; it is a save-flow or renewal-value problem. A streak complaint is not just a product issue; it suggests a reactivation or fresh-start flow. The competitive matrix then shows whether a signal is category-wide or over-indexes for one app.

## How To Interpret The Cross-App Pattern Matrix

Each row is one app. Each column is one retention signal. The percentage shows what share of that app's analyzed reviews fell into that signal.

Read it in three passes:

1. Across a row: this tells you the biggest retention pain points for one app.
2. Down a column: this tells you which competitor has more of a specific problem.
3. Within a category filter: this gives the cleanest comparison because it compares apps solving the same user job.

Example interpretation:

If Language Learning is selected and Duolingo has a higher share of "Motivation / content fatigue" than Babbel, the insight is not just "Duolingo has complaints." The stronger interpretation is: Duolingo may need more content variety, difficulty calibration, or comeback flows for users who feel bored or stuck, while Babbel may have a different retention pressure.

The matrix is useful because it turns review labels into competitive strategy: shared problems suggest category-level lifecycle opportunities, while over-indexing problems suggest app-specific campaign priorities.

## Suggested Resume Bullets

Short version:

Built a real-data competitive retention benchmark analyzing public App Store reviews across language learning, meditation, self-care, and habit-building apps, classifying churn signals and translating competitor pain-point patterns into lifecycle campaign briefs.

Stronger version after running the scraper:

Analyzed 3,992 real App Store reviews across four competitive consumer app categories using Python and rule-based NLP, mapped churn signals to lifecycle stages, and built an interactive benchmark with activation, engagement, save, and win-back campaign recommendations.

## Optional Enhancements If You Have Extra Time

- Add a Canva one-page strategy memo.
- Add screenshots of the dashboard to the README.
- Add three CRM mockups: onboarding, streak recovery, renewal save.
- Add a short assumptions/limitations note when presenting it.
- Add a LinkedIn post explaining the project as a public voice-of-customer study.
