
```` flow js
PDF Text
  ↓
[Phase 1: detect_parameters()]
  ↓
Found parameters + hints
  ↓
for each parameter:
  ↓
    Try extract_with_regex()
      ↓
      If fail → extract_with_llm()
  ↓
Clean Final Output JSON
````