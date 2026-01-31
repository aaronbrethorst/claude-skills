# ISO Language Codes Reference

## Common ISO 639-1 / BCP 47 Language Codes

### Major World Languages

| Code | Language | Notes |
|------|----------|-------|
| ar | Arabic | RTL language |
| bn | Bengali | |
| de | German | |
| en | English | Often en-US or en-GB for regional variants |
| es | Spanish | es-ES (Spain), es-419 (Latin America), es-MX (Mexico) |
| fr | French | fr-FR (France), fr-CA (Canada) |
| hi | Hindi | |
| id | Indonesian | |
| it | Italian | |
| ja | Japanese | |
| ko | Korean | |
| nl | Dutch | |
| pl | Polish | |
| pt | Portuguese | pt-BR (Brazil), pt-PT (Portugal) |
| ru | Russian | |
| th | Thai | |
| tr | Turkish | |
| uk | Ukrainian | |
| vi | Vietnamese | |

### Chinese Variants (REQUIRE CLARIFICATION)

| Code | Variant | Script | Region |
|------|---------|--------|--------|
| zh-CN | Simplified Chinese | Simplified | Mainland China |
| zh-Hans | Simplified Chinese | Simplified | Generic |
| zh-TW | Traditional Chinese | Traditional | Taiwan |
| zh-HK | Traditional Chinese | Traditional | Hong Kong |
| zh-Hant | Traditional Chinese | Traditional | Generic |
| yue | Cantonese | Traditional | Spoken in Guangdong/HK |
| hak | Hakka | Various | |
| nan | Min Nan/Hokkien | Various | |

### European Languages

| Code | Language | Notes |
|------|----------|-------|
| bg | Bulgarian | |
| ca | Catalan | |
| cs | Czech | |
| da | Danish | |
| el | Greek | |
| et | Estonian | |
| fi | Finnish | |
| hr | Croatian | |
| hu | Hungarian | |
| lt | Lithuanian | |
| lv | Latvian | |
| nb | Norwegian Bokmål | (not "no") |
| nn | Norwegian Nynorsk | |
| ro | Romanian | |
| sk | Slovak | |
| sl | Slovenian | |
| sr | Serbian | sr-Cyrl or sr-Latn for script |
| sv | Swedish | |

### Middle Eastern & African

| Code | Language | Notes |
|------|----------|-------|
| am | Amharic | |
| fa | Persian/Farsi | RTL |
| he | Hebrew | RTL |
| sw | Swahili | |
| ur | Urdu | RTL |
| zu | Zulu | |

### South & Southeast Asian

| Code | Language | Notes |
|------|----------|-------|
| fil | Filipino | (not "tl" for formal use) |
| km | Khmer | |
| lo | Lao | |
| ml | Malayalam | |
| mr | Marathi | |
| ms | Malay | ms-MY, ms-SG, ms-BN for regional |
| my | Burmese | |
| ne | Nepali | |
| si | Sinhala | |
| ta | Tamil | |
| te | Telugu | |

### Regional Variant Patterns

When a project uses regional variants, follow the same pattern:
- `en-US` style → `fr-FR`, `de-DE`, `es-MX`
- `en_US` style → `fr_FR`, `de_DE`, `es_MX`
- `en` only → `fr`, `de`, `es`

### Script Subtags (when needed)

| Subtag | Script |
|--------|--------|
| -Hans | Simplified Chinese |
| -Hant | Traditional Chinese |
| -Cyrl | Cyrillic |
| -Latn | Latin |
| -Arab | Arabic |

### Right-to-Left (RTL) Languages

These languages require RTL text direction:
- Arabic (ar)
- Hebrew (he)
- Persian/Farsi (fa)
- Urdu (ur)
- Pashto (ps)
- Dari (prs)
- Yiddish (yi)

When localizing to RTL languages, note any UI implications in the output.

## Pluralization Rules

Different languages have different plural forms:

| Category | Languages | Forms |
|----------|-----------|-------|
| No plurals | Chinese, Japanese, Korean, Vietnamese | 1 form |
| Two forms (1, other) | English, German, Spanish, etc. | 2 forms |
| Two forms (0-1, other) | French, Brazilian Portuguese | 2 forms |
| Three forms | Russian, Ukrainian, Polish, Czech | 3+ forms |
| Four forms | Arabic, Welsh | 4+ forms |
| Six forms | Arabic (full) | 6 forms |

When the source uses pluralization (e.g., ICU format), ensure the target includes appropriate plural categories.
