# Parser Improvements Documentation

## Problem Statement

The original parser had difficulty correctly identifying all inmate records, particularly when:
1. Names appeared embedded within charge descriptions
2. Different patterns of identifier and book-in date placement existed
3. Address lines needed to be properly separated from charge descriptions

## Implemented Solutions

### 1. Enhanced Name Detection

We implemented multiple regex patterns to detect names in various contexts:

```python
# Standard name patterns (at start of line)
NAME_REGEX_STRICT = re.compile(r"^(?P<last>[A-Z][A-Z\-\.' ]+),\s+(?P<firstmid>[A-Z][A-Z\-\.' ]+)$")
NAME_REGEX_TOLERANT = re.compile(r"^(?P<last>[A-Za-z][A-Za-z\-\.' ]+),\s+(?P<firstmid>[A-Za-z][A-Za-z\-\.' ]+)$")

# Embedded name patterns (anywhere in line)
NAME_REGEX_EMBEDDED_STRICT = re.compile(r"(?P<last>[A-Z][A-Z\-\.' ]+),\s+(?P<firstmid>[A-Z][A-Z\-\.' ]+)")
NAME_REGEX_EMBEDDED_TOLERANT = re.compile(r"(?P<last>[A-Za-z][A-Za-z\-\.' ]+),\s+(?P<firstmid>[A-Za-z][A-Za-z\-\.' ]+)")

# Name with ID and date on same line
NAME_ID_DATE_REGEX = re.compile(r"^(?P<name>(?P<last>[A-Z][A-Z\-\.' ]+),\s+(?P<firstmid>[A-Z][A-Z\-\.' ]+))\s+(?P<id>\d{5,8})\s+(?P<date>\d{1,2}/\d{1,2}/\d{4})$")
```

### 2. Improved State Machine Logic

The parser now handles multiple record patterns:

#### Pattern 1: ID and Date before Name
```
1234567 10/15/2025
ADAMS, NINA KISHA
123 MAIN ST
ORLANDO, FL 32801
```

#### Pattern 2: Name, ID, and Date on same line
```
AGUILAR, JUAN 1234567 10/15/2025
123 MAIN ST
ORLANDO, FL 32801
```

#### Pattern 3: Embedded Names in Charge Descriptions
```
25-0240350 NO VALID DL WYATT, JOSH 1234567 10/15/2025
```

### 3. State Machine Enhancements

#### SEEK_NAME State
- Added detection for NAME_ID_DATE pattern (name, ID, and date on same line)
- Added detection for ID_DATE followed by NAME pattern (ID and date before name)
- Maintained standard name detection

#### CAPTURE_ADDRESS State
- Improved ID and date extraction from address lines
- Better handling of address lines with embedded ID/date information
- Added detection for new names that appear before completing the current record

#### CAPTURE_CHARGES State
- Enhanced to detect names embedded within charge descriptions
- Properly handles the text before and after embedded names
- Extracts ID and date information that may follow embedded names

## Key Improvements

1. **Embedded Name Detection**: The parser now correctly identifies names that appear within charge descriptions, creating new records for them.

2. **Flexible ID/Date Handling**: The parser handles various patterns of identifier and book-in date placement:
   - Before the name
   - On the same line as the name
   - Within address lines
   - After embedded names in charge descriptions

3. **Better Address Extraction**: Improved logic to separate address lines from charge descriptions.

4. **Robust Continuation Handling**: Better handling of wrapped lines in charge descriptions.

## Example Scenarios

### Scenario 1: Standard Record
```
ADAMS, NINA KISHA
123 MAIN ST
ORLANDO, FL 32801
1234567 10/15/2025
25-0240350 NO VALID DL
```

### Scenario 2: Name with ID and Date
```
AGUILAR, JUAN 1234567 10/15/2025
123 MAIN ST
ORLANDO, FL 32801
25-0240351 FAILURE TO APPEAR
```

### Scenario 3: Embedded Name in Charge Description
```
25-0240350 NO VALID DL WYATT, JOSH 1234567 10/15/2025
123 MAIN ST
ORLANDO, FL 32801
```

## Testing

The improved parser has been tested with various record patterns to ensure it correctly identifies all inmate records, including those with embedded names in charge descriptions.