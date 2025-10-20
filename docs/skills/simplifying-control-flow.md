# Simplifying Control Flow

**Category:** coding
**Location:** `.claude/skills/coding/simplifying-control-flow/`

Flatten nested conditionals with early returns or table-driven methods. Keep nesting depth under 3 levels for maintainable, readable code.

## What It Does

Provides three techniques to eliminate deep nesting:
1. **Flatten with combined conditions** - All conditions at same level
2. **Table-driven logic** - Business rules as data structures
3. **Extract complex conditions** - Named boolean functions

## When to Use

**Apply when:**
- Nesting depth exceeds 2-3 levels
- Multiple conditions determine outcome
- Similar if/else patterns repeat
- Business rules encoded in nested ifs
- Adding new cases requires deep surgery
- Control flow is hard to follow

## Core Principle

**Nesting depth < 3 levels**

Use early returns, table-driven methods, or extracted conditions instead of deep nesting.

## Techniques

### 1. Flatten with Combined Conditions

❌ **Nested (baseline):**
```python
def calculate_discount(order_amount, is_vip):
    if is_vip:
        if order_amount > 1000:
            return 0.20
        elif order_amount > 500:
            return 0.15
    else:
        if order_amount > 1000:
            return 0.10
        elif order_amount > 500:
            return 0.05
    return 0.0
```

✅ **Flattened:**
```python
def calculate_discount(order_amount, is_vip):
    if is_vip and order_amount > 1000: return 0.20
    if is_vip and order_amount > 500: return 0.15
    if order_amount > 1000: return 0.10
    if order_amount > 500: return 0.05
    return 0.0
```

### 2. Table-Driven (Best for Data)

✅ **Business rules as data:**
```python
DISCOUNT_TIERS = [
    (1000, 0.20, 0.10),  # min_amount, vip_rate, regular_rate
    (500,  0.15, 0.05),
]

def calculate_discount(order_amount, is_vip):
    for min_amount, vip_rate, regular_rate in DISCOUNT_TIERS:
        if order_amount > min_amount:
            return vip_rate if is_vip else regular_rate
    return 0.0
```

**When to use:** Pricing tiers, status transitions, configuration-driven logic

### 3. Extract Complex Conditions

✅ **Named boolean for clarity:**
```python
def is_eligible(user, minimum):
    return (user.age >= 18 and user.verified_email and
            user.balance > minimum and not user.suspended)

if is_eligible(user, minimum_purchase):
    allow_purchase()
```

**When to use:** Complex boolean expressions, reused conditions

## Quick Reference

| Problem | Solution |
|---------|----------|
| Nested if/else | Flatten with combined conditions OR table-driven |
| Deep nesting (>3) | Extract inner logic to function |
| Complex boolean | Extract to named function |
| Business rules | Table-driven method |
| Long if/elif chain | Table lookup OR polymorphism |

## Guard Clauses

Use early returns for validation and error cases:

```python
def validate(data):
    if not data:
        return False, "data required"
    if data.amount <= 0:
        return False, "amount must be positive"
    # Main logic here (no nesting)
```

## Red Flags

- Nesting depth > 3
- Can't see matching braces without scrolling
- Duplicate conditions in nested blocks
- Adding new case touches multiple nesting levels

**Fix:** Flatten or use table-driven approach

## Benefits

**From baseline testing:**
- Agents created 2-level nesting for 4 discount tiers
- With table-driven: All tiers visible at once, easy to add/modify
- Reduced duplication
- Clearer business logic

## Related Skills

- **Keeping Routines Focused** - Extract when nesting gets deep
- **Reducing Complexity** - Simpler control flow = less complexity

## Files

- **SKILL.md** - Complete specification with examples

Adapted from obra/clank with focus on practical patterns.
