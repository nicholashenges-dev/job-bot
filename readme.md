
Job Bot — Customizable Multi-Source Job Aggregator & Tracker

GitHub: https://github.com/nicholashenges-dev/job-bot

A lightweight Python tool that aggregates remote and hybrid jobs from 11+ sources, scores them against your criteria, deduplicates them in SQLite, and sends push notifications via ntfy.sh. It includes a mobile-friendly Flask web dashboard to track statuses and notes.

Summary of Key Features & Setup

• Sources & Filtering: Pulls from RemoteOK, Remotive, Jobicy, We Work Remotely, Himalayas, Working Nomads, JSearch, and direct ATS feeds (Greenhouse, Lever, Ashby, Workable) with custom title, experience, and salary filters.
• Quick Setup: Clone the repository, create a virtual environment, install dependencies from requirements.txt, configure config.json, and run python search.py followed by python dashboard.py to access http://127.0.0.1:5000.