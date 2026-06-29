---
title: Project 1 - Core Analytics Warehouse
description: Build the warehouse foundation for later AI analytics projects.
order: 1
tags: [warehouse, dbt, sql]
---

# Project 1 - Core Analytics Warehouse

## Goal

Build a clean analytics warehouse from raw data to staging models and business marts.

## Architecture

```txt
Raw files/API
→ ingestion
→ staging tables
→ dbt transformations
→ marts
→ dashboard-ready data
```

## Deliverables

- Source data contracts
- Staging models
- Dimensional marts
- dbt tests
- dbt documentation
- Data quality report

## Output used by next project

Project 2 uses these marts as the trusted SQL layer for Text2SQL.
