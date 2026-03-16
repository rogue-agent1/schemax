# schemax

JSON Schema validator & generator. Zero dependencies.

## Commands

```bash
schemax generate <file.json>                # Infer schema from data
schemax validate <file.json> <schema.json>  # Validate against schema
```

## Features

- **Generate:** Infers types, required fields, formats (date-time, email, URI, IPv4)
- **Validate:** Type checking, required fields, enum, min/max, pattern, array bounds, additionalProperties

## Example

```bash
# Generate schema from sample data
python3 schemax.py gen data.json > schema.json

# Validate data against schema
python3 schemax.py val data.json schema.json
```

## Requirements

- Python 3.6+ (stdlib only)
