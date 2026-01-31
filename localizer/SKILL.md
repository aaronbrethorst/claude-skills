---
name: localization
description: Creates or updates software localizations/translations. Use when the user wants to translate a project to a new language, add a new locale, create translations, localize strings, or work with i18n/l10n files. Handles any project type (React, Vue, iOS, Android, Rails, Django, .NET, etc.) by auto-detecting the localization framework.
---

# Software Localization Skill

This skill creates high-quality localizations for software projects by using a dual-translation approach with verification.

## Workflow Overview

1. **Detect Project Type** - Identify the localization framework and file format
2. **Validate Target Language** - Ensure a valid ISO 639 language code is provided
3. **Extract Source Strings** - Load English (en/en-us/en_us) as the base
4. **Dual Translation** - Two independent translator sub-agents produce translations
5. **Verification** - A third sub-agent compares results and selects the best translations
6. **Output** - Generate the localization file in the correct format

## Step 1: Detect Project Type

Before any translation work, identify the localization system by examining the project structure.

### Common Patterns to Check

| Framework | Location | Format | Key Pattern |
|-----------|----------|--------|-------------|
| React (react-i18next) | `public/locales/`, `src/locales/` | JSON | `{"key": "value"}` |
| React (react-intl) | `src/translations/`, `lang/` | JSON | `{"key": {"defaultMessage": "..."}}` |
| Vue (vue-i18n) | `src/locales/`, `locales/` | JSON/YAML | `{"key": "value"}` |
| Angular | `src/assets/i18n/`, `src/locale/` | JSON/XLIFF | JSON or XML-based |
| iOS | `*.lproj/Localizable.strings` | Strings | `"key" = "value";` |
| Android | `res/values-*/strings.xml` | XML | `<string name="key">value</string>` |
| Rails (i18n) | `config/locales/` | YAML | `en:\n  key: value` |
| Django | `locale/*/LC_MESSAGES/` | PO/POT | `msgid "key"\nmsgstr "value"` |
| .NET (resx) | `Resources/`, `*.resx` | XML | `<data name="key"><value>...</value></data>` |
| Flutter | `lib/l10n/`, `assets/translations/` | ARB/JSON | `{"key": "value", "@key": {...}}` |
| Go (go-i18n) | `locales/`, `translations/` | JSON/TOML | Various |
| PHP (Laravel) | `resources/lang/` | PHP/JSON | `return ['key' => 'value'];` |
| Next.js | `messages/`, `locales/` | JSON | `{"namespace": {"key": "value"}}` |
| Gettext | `*.po`, `*.pot` | PO | `msgid/msgstr` pairs |

### Detection Commands

```bash
# Find common localization directories
find . -type d \( -name "locales" -o -name "locale" -o -name "i18n" -o -name "l10n" -o -name "translations" -o -name "lang" -o -name "*.lproj" -o -name "values-*" \) 2>/dev/null | head -20

# Find localization files
find . -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.strings" -o -name "*.xml" -o -name "*.po" -o -name "*.pot" -o -name "*.resx" -o -name "*.arb" -o -name "*.xliff" \) 2>/dev/null | grep -E "(locale|i18n|l10n|lang|translation|messages|values)" | head -30
```

### Important: Examine the English Source

Once you locate the localization directory, find the English source file. It may be named:
- `en.json`, `en-US.json`, `en_US.json`
- `en.yaml`, `en-US.yaml`
- `en.lproj/Localizable.strings`
- `values/strings.xml` (Android default)
- `en.po`, `messages.pot`

Read this file to understand the structure before proceeding.

## Step 2: Validate Target Language

### Required Information

You MUST have a valid ISO 639 language code before proceeding. If the user provides only a language name, look up the correct code.

### Clarification Required For

**ALWAYS ask for clarification when the user specifies:**

- **"Chinese"** → Ask: Traditional (zh-TW, zh-HK), Simplified (zh-CN, zh-Hans), or another variant?
- **"Spanish"** → Ask: Spain (es-ES), Latin America (es-419), Mexico (es-MX), or general (es)?
- **"Portuguese"** → Ask: Brazil (pt-BR) or Portugal (pt-PT)?
- **"Serbian"** → Ask: Cyrillic (sr-Cyrl) or Latin (sr-Latn)?
- **"Norwegian"** → Ask: Bokmål (nb) or Nynorsk (nn)?
- **"Malay"** → Ask: Malaysia (ms-MY), Singapore (ms-SG), or Brunei (ms-BN)?

### Common ISO 639-1/BCP 47 Codes

For reference, see [ISO_CODES.md](ISO_CODES.md) for the complete list.

### Code Format

Match the format used in the existing project:
- If project uses `en-US` → use `fr-FR`, `de-DE`, etc.
- If project uses `en_US` → use `fr_FR`, `de_DE`, etc.
- If project uses `en` → use `fr`, `de`, etc.

## Step 3: Extract Source Strings

Load the English source file and parse all translatable strings. Note:

- **Preserve keys exactly** - Do not modify key names
- **Note placeholders** - `{name}`, `{{count}}`, `%s`, `%d`, `%@`, etc.
- **Note HTML/markup** - `<b>`, `<a href="...">`, etc.
- **Note pluralization** - `one`, `other`, `few`, `many` forms
- **Note context** - ICU message format, gender variations, etc.

## Step 4: Dual Translation with Sub-Agents

Delegate translation to two sub-agents: `translator-alpha` and `translator-beta`.

### Instructions for Translators

Both translators receive the same instructions (see [TRANSLATOR_INSTRUCTIONS.md](TRANSLATOR_INSTRUCTIONS.md)):

1. You are a master linguist fluent in both English and {TARGET_LANGUAGE}
2. Translate each string maintaining natural, idiomatic expression
3. **CRITICAL: Preserve all formatting exactly:**
   - Placeholders: `{variable}`, `{{variable}}`, `%s`, `%d`, `%1$s`, `%@`
   - HTML tags: `<b>`, `<i>`, `<a href="...">`, `<br/>`
   - Special characters: `\n`, `\t`, `\"`, `\'`
   - Whitespace at start/end of strings
   - Markdown formatting if present
4. Adapt idioms appropriately - don't translate literally if unnatural
5. Consider formality level (formal/informal "you" where applicable)
6. Provide a confidence score (0.0-1.0) for each translation:
   - 1.0: Certain, standard translation
   - 0.8-0.9: High confidence, minor ambiguity
   - 0.6-0.7: Moderate confidence, context-dependent
   - Below 0.6: Low confidence, needs review

### Output Format from Translators

Each translator returns:
```json
{
  "translations": [
    {
      "key": "original.key",
      "source": "English text",
      "translation": "Translated text",
      "confidence": 0.95,
      "notes": "Optional notes about translation choices"
    }
  ]
}
```

## Step 5: Verification with Adjudicator Sub-Agent

The `translator-adjudicator` sub-agent receives:
- Original English strings
- Translation A (from translator-alpha) with confidence scores
- Translation B (from translator-beta) with confidence scores

### Adjudicator Instructions

See [ADJUDICATOR_INSTRUCTIONS.md](ADJUDICATOR_INSTRUCTIONS.md) for full details.

The adjudicator evaluates each string pair and selects the better translation based on:

1. **Accuracy** - Does it convey the same meaning?
2. **Idiomaticity** - Does it sound natural in the target language?
3. **Formatting preservation** - Are all placeholders/tags intact?
4. **Consistency** - Does terminology match across strings?
5. **Confidence scores** - Factor in translator certainty

For each string, the adjudicator outputs:
```json
{
  "key": "original.key",
  "selected": "A" | "B" | "merged",
  "final_translation": "The selected or merged translation",
  "reason": "Brief explanation of choice"
}
```

## Step 6: Generate Output File

Create the localization file in the correct format for the project:

### JSON Format
```json
{
  "key1": "translation1",
  "key2": "translation2"
}
```

### YAML Format
```yaml
target_locale:
  key1: translation1
  key2: translation2
```

### iOS Strings Format
```
/* Comment */
"key1" = "translation1";
"key2" = "translation2";
```

### Android XML Format
```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="key1">translation1</string>
    <string name="key2">translation2</string>
</resources>
```

### PO Format
```
msgid "source text"
msgstr "translation"
```

## Error Handling

- **Missing source file**: Ask user to specify the English source location
- **Ambiguous language**: Always ask for clarification (see Step 2)
- **Unknown format**: Ask user about the localization framework
- **Large files**: Process in batches if over 200 strings

## Quality Checklist

Before finalizing, verify:
- [ ] All keys from source are present in output
- [ ] No extra keys were added
- [ ] All placeholders are preserved exactly
- [ ] File encoding matches source (usually UTF-8)
- [ ] File format matches project conventions
- [ ] Pluralization rules are correct for target language
