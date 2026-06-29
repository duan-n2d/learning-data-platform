---
title: Project 2 - Text2SQL Chatbot
description: Build a chatbot that converts business questions into validated SQL.
order: 2
tags: [text2sql, chatbot, semantic layer]
---

# Project 2 - Text2SQL Chatbot

## Goal

Build a chatbot that allows users to ask business questions in natural language and receive SQL-backed answers.

## Why this matters

Text2SQL is not just about generating SQL. It requires correct business logic, trusted metrics, semantic definitions, and validation.

## Architecture

```txt
User question
→ semantic layer lookup
→ SQL generation
→ SQL validator
→ database query
→ answer formatter
```

## Deliverables

- Semantic metric definitions
- Prompt templates
- SQL validator
- Evaluation question set
- Web UI or Streamlit UI
- Error analysis report
