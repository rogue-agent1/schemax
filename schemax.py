#!/usr/bin/env python3
"""schemax - JSON Schema validator & generator. Zero deps."""
import json, sys, re
from collections import OrderedDict

def infer_type(val):
    if val is None: return "null"
    if isinstance(val, bool): return "boolean"
    if isinstance(val, int): return "integer"
    if isinstance(val, float): return "number"
    if isinstance(val, str): return "string"
    if isinstance(val, list): return "array"
    if isinstance(val, dict): return "object"
    return "string"

def infer_format(val):
    if not isinstance(val, str): return None
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', val): return "date-time"
    if re.match(r'^\d{4}-\d{2}-\d{2}$', val): return "date"
    if re.match(r'^[^@]+@[^@]+\.[^@]+$', val): return "email"
    if re.match(r'^https?://', val): return "uri"
    if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', val): return "ipv4"
    return None

def generate_schema(val, required_all=True):
    t = infer_type(val)
    s = {"type": t}
    if t == "object":
        props = {}
        for k, v in val.items():
            props[k] = generate_schema(v, required_all)
        s["properties"] = props
        if required_all:
            s["required"] = list(val.keys())
    elif t == "array":
        if val:
            # Use first element as schema, merge with others
            s["items"] = generate_schema(val[0], required_all)
        else:
            s["items"] = {}
    elif t == "string":
        fmt = infer_format(val)
        if fmt: s["format"] = fmt
    return s

def validate(doc, schema, path=""):
    errors = []
    st = schema.get("type")
    actual = infer_type(doc)
    
    # Type check
    if st:
        types = [st] if isinstance(st, str) else st
        type_ok = actual in types or (actual == "integer" and "number" in types)
        if not type_ok:
            errors.append(f"{path or '/'}: expected {st}, got {actual}")
            return errors
    
    if st == "object" and isinstance(doc, dict):
        # Required
        for r in schema.get("required", []):
            if r not in doc:
                errors.append(f"{path}/{r}: required field missing")
        # Properties
        for k, ps in schema.get("properties", {}).items():
            if k in doc:
                errors.extend(validate(doc[k], ps, f"{path}/{k}"))
        # additionalProperties
        if schema.get("additionalProperties") is False:
            extra = set(doc.keys()) - set(schema.get("properties", {}).keys())
            for e in extra:
                errors.append(f"{path}/{e}: additional property not allowed")
    
    elif st == "array" and isinstance(doc, list):
        items_schema = schema.get("items", {})
        mn, mx = schema.get("minItems"), schema.get("maxItems")
        if mn is not None and len(doc) < mn:
            errors.append(f"{path}: minItems {mn}, got {len(doc)}")
        if mx is not None and len(doc) > mx:
            errors.append(f"{path}: maxItems {mx}, got {len(doc)}")
        for i, item in enumerate(doc):
            errors.extend(validate(item, items_schema, f"{path}/{i}"))
    
    elif st == "string" and isinstance(doc, str):
        mn, mx = schema.get("minLength"), schema.get("maxLength")
        if mn and len(doc) < mn: errors.append(f"{path}: minLength {mn}")
        if mx and len(doc) > mx: errors.append(f"{path}: maxLength {mx}")
        pat = schema.get("pattern")
        if pat and not re.search(pat, doc):
            errors.append(f"{path}: doesn't match pattern {pat}")
    
    elif st in ("number","integer") and isinstance(doc, (int,float)):
        mn, mx = schema.get("minimum"), schema.get("maximum")
        if mn is not None and doc < mn: errors.append(f"{path}: minimum {mn}")
        if mx is not None and doc > mx: errors.append(f"{path}: maximum {mx}")
    
    # Enum
    if "enum" in schema and doc not in schema["enum"]:
        errors.append(f"{path}: {doc!r} not in enum {schema['enum']}")
    
    return errors

def cmd_generate(args):
    if not args:
        print("Usage: schemax generate <file.json>"); sys.exit(1)
    with open(args[0]) as f: doc = json.load(f)
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
    schema.update(generate_schema(doc))
    print(json.dumps(schema, indent=2))

def cmd_validate(args):
    if len(args) < 2:
        print("Usage: schemax validate <file.json> <schema.json>"); sys.exit(1)
    with open(args[0]) as f: doc = json.load(f)
    with open(args[1]) as f: schema = json.load(f)
    errors = validate(doc, schema)
    if errors:
        print(f"❌ {len(errors)} error(s):")
        for e in errors: print(f"  • {e}")
        sys.exit(1)
    else:
        print("✅ Valid")

CMDS = {"generate": cmd_generate, "gen": cmd_generate, "validate": cmd_validate, "val": cmd_validate}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h","--help"):
        print("schemax - JSON Schema validator & generator")
        print("Commands:")
        print("  generate <file.json>              — infer schema from data")
        print("  validate <file.json> <schema.json> — validate against schema")
        sys.exit(0)
    cmd = args[0]
    if cmd not in CMDS: print(f"Unknown: {cmd}"); sys.exit(1)
    CMDS[cmd](args[1:])
