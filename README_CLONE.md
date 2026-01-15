# XML Clone and Modify Tool

A minimal-risk Python tool for cloning XML feeds and prefixing specific fields (barcode/SKU) while preserving all other structure exactly.

## Features

- **Safe cloning**: Preserves XML structure, CDATA, ordering, and whitespace
- **Atomic writes**: Uses temporary files to prevent partial/corrupted outputs
- **Error handling**: Retries with exponential backoff for network errors
- **Verification**: Separate script to verify stock/price fields weren't modified
- **CLI support**: Flexible command-line interface with config file support

## Supported Feeds

### eBijuteri
- Root: `<Urunler>` with repeated `<Urun>` nodes
- Modifies: `<barcode>` field (set to `prefix + <stok_kodu>`)
- Key fields: `product_id`, `miktar` (stock), `fiyat`/`bayi_fiyati` (price)

### TeknoTok
- Root: `<data>` with repeated `<post>` nodes
- Modifies: `<Sku>` field (prefixes existing value)
- Key fields: `ID`, `Stock`, `Price`

## Installation

1. Install Python 3.7+ (if not already installed)

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to configure:
- Prefix value (default: `isteburada_`)
- Feed URLs
- Default timeout and retry settings

Example `config.yaml`:
```yaml
prefix: "isteburada_"

feeds:
  ebi:
    url: "http://xml.ebijuteri.com/api/xml/606eca02c442805e515961e2?format=old"
    name: "eBijuteri"
  
  tkt:
    url: "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
    name: "TeknoTok"

defaults:
  timeout: 60
  retries: 5
  retry_backoff: 2
```

## Usage

### Basic Usage

Process both feeds with default config:
```bash
python make_clone_xmls.py
```

### Command-Line Options

```bash
python make_clone_xmls.py [OPTIONS]

Options:
  --config PATH       Path to config YAML file (default: config.yaml)
  --prefix PREFIX     Prefix to add (overrides config)
  --out-dir DIR       Output directory (default: current directory)
  --only FEED         Process only specified feed (ebi or tkt)
  --timeout SECONDS   Request timeout (default: 60)
  --retries COUNT     Number of retries (default: 5)
  -h, --help          Show help message
```

### Examples

Process only eBijuteri feed:
```bash
python make_clone_xmls.py --only ebi
```

Process with custom prefix:
```bash
python make_clone_xmls.py --prefix "test_"
```

Process to custom output directory:
```bash
python make_clone_xmls.py --out-dir output
```

Process with custom timeout and retries:
```bash
python make_clone_xmls.py --timeout 120 --retries 3
```

### Output Files

The tool generates:
- `ebi_out.xml` - Cloned eBijuteri feed
- `tkt_out.xml` - Cloned TeknoTok feed

Files are written atomically (via temporary files) to prevent corruption.

## Verification

Use `compare_stock_price.py` to verify that stock and price fields were not modified:

```bash
python compare_stock_price.py ebi original_ebi.xml ebi_out.xml
python compare_stock_price.py tkt original_tkt.xml tkt_out.xml
```

The script reports:
- Item counts (original vs cloned)
- Missing/extra keys
- Stock differences
- Price differences
- First 10 differences found

Example output:
```
============================================================
STOCK & PRICE COMPARISON REPORT
============================================================

Feed Type: EBI

Item Counts:
  Original: 1500
  Cloned:   1500

Key Comparison:
  Missing keys (in original but not cloned): 0
  Extra keys (in cloned but not original): 0

Differences:
  Stock differences: 0
  Price differences: 0
  Total differences: 0

✓ No differences found - stock and price fields preserved correctly!
```

## Windows Build

To create a standalone executable:

1. Run the build script:
```bash
build.bat
```

This creates `dist\xml_clone_tool.exe` using PyInstaller.

2. Run examples:
```bash
run_examples.bat
```

## Safety Features

1. **Atomic writes**: Files are written to `.tmp.xml` first, then renamed atomically
2. **No overwrite on failure**: If fetch or parsing fails, existing output files are not modified
3. **Zero-item check**: If item count is unexpectedly 0, output is not written
4. **Double-prefix prevention**: Checks if value already starts with prefix before modifying
5. **Error recovery**: Retries with exponential backoff for HTTP 429/5xx errors

## Implementation Details

- Uses `lxml` for XML parsing (preserves CDATA and structure)
- Pretty printing disabled to minimize formatting changes
- UTF-8 encoding with XML declaration
- Handles large XML files (5k+ items)
- Preserves all tags, nested structures, and ordering

## Troubleshooting

### "Config file not found"
- Ensure `config.yaml` exists in the current directory
- Or specify path with `--config` option

### "Failed to fetch XML"
- Check network connectivity
- Verify URLs in `config.yaml` are correct
- Try increasing `--timeout` value
- Check if server is returning 429/5xx errors (tool will retry automatically)

### "No items found"
- Verify XML structure matches expected format
- Check if feed URLs are returning valid XML
- Review XML structure with a text editor

### "Item count is 0, skipping write"
- Safety feature: prevents overwriting with empty files
- Check if feed is actually returning data
- Verify XML structure matches expected format

## License

This tool is provided as-is for internal use.
