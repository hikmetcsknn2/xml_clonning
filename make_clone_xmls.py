#!/usr/bin/env python3
"""
XML Clone and Modify Tool

Fetches XML feeds, clones them, and prefixes specific fields (barcode/SKU)
while preserving all other structure exactly.
"""

import argparse
import os
import sys
import time
import yaml
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlsplit
import requests
from lxml import etree


class XMLCloneTool:
    """Main tool for cloning and modifying XML feeds."""
    
    def __init__(self, config_path: str, prefix: Optional[str] = None, 
                 out_dir: str = ".", timeout: int = 60, retries: int = 5):
        """Initialize the tool with configuration."""
        self.config = self._load_config(config_path)
        self.prefix = prefix or self.config.get('prefix', 'isteburada_')
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries
        self.backoff = self.config.get('defaults', {}).get('retry_backoff', 2)
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Config file not found: {config_path}", file=sys.stderr)
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML in config: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _fetch_xml(self, url: str) -> Optional[bytes]:
        """Fetch XML from URL with retries and backoff."""
        # Use browser-like headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': url,
        }
        session = requests.Session()
        session.headers.update(headers)
        primed_cookies = False
        base_url = None
        try:
            parts = urlsplit(url)
            if parts.scheme and parts.netloc:
                base_url = f"{parts.scheme}://{parts.netloc}/"
        except Exception:
            base_url = None
        
        for attempt in range(self.retries):
            try:
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                # Retry on 403 (Forbidden) as it might be temporary rate limiting
                if status_code in (403, 429, 500, 502, 503, 504):
                    if status_code == 403 and not primed_cookies and base_url:
                        primed_cookies = True
                        try:
                            session.get(base_url, timeout=self.timeout)
                        except requests.exceptions.RequestException:
                            pass
                        continue
                    if attempt < self.retries - 1:
                        wait_time = self.backoff * (2 ** attempt)
                        print(f"HTTP {status_code} error, retrying in {wait_time}s... (attempt {attempt + 1}/{self.retries})")
                        time.sleep(wait_time)
                        continue
                print(f"Error fetching {url}: {e}", file=sys.stderr)
                return None
            except requests.exceptions.RequestException as e:
                if attempt < self.retries - 1:
                    wait_time = self.backoff * (2 ** attempt)
                    print(f"Request error, retrying in {wait_time}s... (attempt {attempt + 1}/{self.retries})")
                    time.sleep(wait_time)
                    continue
                print(f"Error fetching {url}: {e}", file=sys.stderr)
                return None
        
        return None
    
    def _clone_ebijuteri(self, xml_content: bytes) -> Optional[Tuple[etree.ElementTree, int]]:
        """Clone eBijuteri XML and prefix barcode field.
        
        Returns:
            (ElementTree, updated_count) or None on error
        """
        try:
            # Parse XML preserving CDATA
            parser = etree.XMLParser(strip_cdata=False, recover=True)
            root = etree.fromstring(xml_content, parser=parser)
            
            # Find all <Urun> nodes
            urun_nodes = root.xpath('//Urun')
            
            if len(urun_nodes) == 0:
                print("Warning: No <Urun> nodes found in eBijuteri feed", file=sys.stderr)
                return None
            
            updated_count = 0
            
            for urun in urun_nodes:
                # Get stok_kodu
                stok_kodu_elem = urun.find('stok_kodu')
                if stok_kodu_elem is None or stok_kodu_elem.text is None:
                    continue
                
                stok_kodu = stok_kodu_elem.text.strip()
                if not stok_kodu:
                    continue
                
                # Get or create barcode element
                barcode_elem = urun.find('barcode')
                if barcode_elem is None:
                    barcode_elem = etree.SubElement(urun, 'barcode')
                
                # Check if already prefixed
                current_barcode = barcode_elem.text or ""
                if current_barcode.startswith(self.prefix):
                    continue
                
                # Set barcode to prefix + stok_kodu
                new_barcode = f"{self.prefix}{stok_kodu}"
                barcode_elem.text = new_barcode
                updated_count += 1
            
            print(f"  Updated {updated_count} barcode fields")
            return (etree.ElementTree(root), updated_count)
            
        except etree.XMLSyntaxError as e:
            print(f"Error parsing eBijuteri XML: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error processing eBijuteri XML: {e}", file=sys.stderr)
            return None
    
    def _clone_teknatok(self, xml_content: bytes) -> Optional[Tuple[etree.ElementTree, int]]:
        """Clone TeknoTok XML and prefix Sku field.
        
        Returns:
            (ElementTree, updated_count) or None on error
        """
        try:
            # Parse XML preserving CDATA
            parser = etree.XMLParser(strip_cdata=False, recover=False)
            root = etree.fromstring(xml_content, parser=parser)
            
            # Find all <post> nodes
            post_nodes = root.xpath('//post')
            
            if len(post_nodes) == 0:
                print("Warning: No <post> nodes found in TeknoTok feed", file=sys.stderr)
                return None
            
            updated_count = 0
            
            for post in post_nodes:
                # Get Sku element
                sku_elem = post.find('Sku')
                if sku_elem is None or sku_elem.text is None:
                    continue
                
                current_sku = sku_elem.text.strip()
                if not current_sku:
                    continue
                
                # Check if already prefixed
                if current_sku.startswith(self.prefix):
                    continue
                
                # Prefix the Sku value
                new_sku = f"{self.prefix}{current_sku}"
                sku_elem.text = new_sku
                updated_count += 1
            
            print(f"  Updated {updated_count} Sku fields")
            return (etree.ElementTree(root), updated_count)
            
        except etree.XMLSyntaxError as e:
            print(f"Error parsing TeknoTok XML: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error processing TeknoTok XML: {e}", file=sys.stderr)
            return None
    
    def _write_xml_safely(self, tree: etree.ElementTree, output_path: Path) -> bool:
        """Write XML to file atomically (via temp file)."""
        # Use _tmp.xml suffix (e.g., ebi_out_tmp.xml)
        temp_path = output_path.parent / f"{output_path.stem}_tmp{output_path.suffix}"
        
        try:
            # Write to temp file
            with open(temp_path, 'wb') as f:
                # Write XML declaration
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                # Write tree without pretty printing to preserve structure
                tree.write(f, encoding='utf-8', xml_declaration=False, pretty_print=False)
            
            # Atomic rename (works on Windows too)
            temp_path.replace(output_path)
            return True
            
        except Exception as e:
            print(f"Error writing {output_path}: {e}", file=sys.stderr)
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            return False
    
    def process_feed(self, feed_key: str, feed_config: dict) -> Tuple[bool, int, int]:
        """
        Process a single feed.
        
        Returns:
            (success, item_count, updated_count)
        """
        feed_name = feed_config.get('name', feed_key)
        url = feed_config.get('url')
        
        if not url:
            print(f"Error: No URL configured for {feed_key}", file=sys.stderr)
            return False, 0, 0
        
        print(f"\nProcessing {feed_name} ({feed_key})...")
        print(f"  URL: {url}")
        
        # Fetch XML
        xml_content = self._fetch_xml(url)
        if xml_content is None:
            print(f"  Failed to fetch XML", file=sys.stderr)
            return False, 0, 0
        
        # Clone and modify based on feed type
        if feed_key == 'ebi':
            result = self._clone_ebijuteri(xml_content)
            output_file = self.out_dir / 'ebi_out.xml'
            # Count items for summary
            try:
                parser = etree.XMLParser(strip_cdata=False, recover=True)
                root = etree.fromstring(xml_content, parser=parser)
                item_count = len(root.xpath('//Urun'))
            except:
                item_count = 0
        elif feed_key == 'tkt':
            result = self._clone_teknatok(xml_content)
            output_file = self.out_dir / 'tkt_out.xml'
            # Count items for summary
            try:
                parser = etree.XMLParser(strip_cdata=False, recover=True)
                root = etree.fromstring(xml_content, parser=parser)
                item_count = len(root.xpath('//post'))
            except:
                item_count = 0
        else:
            print(f"  Unknown feed type: {feed_key}", file=sys.stderr)
            return False, 0, 0
        
        if result is None:
            print(f"  Failed to process XML", file=sys.stderr)
            return False, item_count, 0
        
        tree, updated_count = result
        
        # Safety check: don't write if item count is unexpectedly 0
        if item_count == 0:
            print(f"  Warning: Item count is 0, skipping write to prevent data loss", file=sys.stderr)
            return False, 0, 0
        
        # Write safely
        if not self._write_xml_safely(tree, output_file):
            return False, item_count, updated_count
        
        print(f"  Successfully wrote {output_file}")
        print(f"  Items processed: {item_count}")
        
        return True, item_count, updated_count
    
    def run(self, only: Optional[str] = None):
        """Run the tool for configured feeds."""
        feeds = self.config.get('feeds', {})
        
        if only:
            if only not in feeds:
                print(f"Error: Unknown feed '{only}'. Available: {list(feeds.keys())}", file=sys.stderr)
                sys.exit(1)
            feeds = {only: feeds[only]}
        
        results = {}
        
        for feed_key, feed_config in feeds.items():
            success, item_count, updated_count = self.process_feed(feed_key, feed_config)
            results[feed_key] = {
                'success': success,
                'item_count': item_count,
                'updated_count': updated_count
            }
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        for feed_key, result in results.items():
            feed_name = feeds[feed_key].get('name', feed_key)
            if result['success']:
                print(f"{feed_name}:")
                print(f"  Items processed: {result['item_count']}")
                print(f"  Fields updated: {result['updated_count']}")
            else:
                print(f"{feed_name}: FAILED")
        
        # Exit with error if any feed failed
        if any(not r['success'] for r in results.values()):
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Clone XML feeds and prefix barcode/SKU fields',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config YAML file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--prefix',
        help='Prefix to add (overrides config)'
    )
    
    parser.add_argument(
        '--out-dir',
        default='.',
        help='Output directory (default: current directory)'
    )
    
    parser.add_argument(
        '--only',
        choices=['ebi', 'tkt'],
        help='Process only specified feed'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Request timeout in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=5,
        help='Number of retries for failed requests (default: 5)'
    )

    parser.add_argument(
        '--pause',
        action='store_true',
        help="Pause and wait for Enter after successful run (useful for double-clicked EXE)"
    )
    
    args = parser.parse_args()

    # Resolve config path: if the given config file doesn't exist, try to find it
    # relative to the executable/script parent directories. This fixes the common
    # case where users double-click the EXE inside `dist\` and the config.yaml
    # lives one level above the `dist` folder.
    config_path = Path(args.config)
    if not config_path.exists():
        candidates = []
        try:
            # Path of the running program (script or exe)
            runner = Path(sys.argv[0]).resolve()
            candidates.append(runner.parent.parent / args.config)
            candidates.append(runner.parent / args.config)
        except Exception:
            pass
        try:
            candidates.append(Path(__file__).resolve().parent.parent / args.config)
        except Exception:
            pass

        found = None
        for c in candidates:
            if c.exists():
                found = c
                break

        if found:
            print(f"Config file {config_path} not found, using {found}")
            args.config = str(found)
        else:
            print(f"Warning: Config file {config_path} not found; proceeding and XMLCloneTool will report an error if needed.", file=sys.stderr)

    tool = XMLCloneTool(
        config_path=args.config,
        prefix=args.prefix,
        out_dir=args.out_dir,
        timeout=args.timeout,
        retries=args.retries
    )
    
    # Run the tool and capture any SystemExit so we can still pause before exiting.
    exit_code = 0
    try:
        tool.run(only=args.only)
    except SystemExit as e:
        # Preserve exit code (could be None or int)
        try:
            exit_code = int(e.code) if e.code is not None else 1
        except Exception:
            exit_code = 1

    # If requested, pause at end so double-clicked EXE windows don't close immediately
    if args.pause:
        print("\nİşlem tamamlandı. Çıkmak için Enter'a bas...")
        try:
            input()
        except Exception:
            # In non-interactive environments input() may fail; ignore
            pass

    # Exit with the same code the tool intended
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
