#!/usr/bin/env python3
"""
Stock and Price Comparison Tool

Compares original and cloned XML files to ensure stock/price fields
were not modified during the cloning process.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from lxml import etree


class StockPriceComparator:
    """Compare stock and price fields between original and cloned XML."""
    
    def __init__(self, feed_type: str):
        """Initialize comparator for specific feed type."""
        self.feed_type = feed_type
        
        if feed_type == 'ebi':
            self.root_tag = 'Urunler'
            self.item_tag = 'Urun'
            self.key_field = 'product_id'  # Will look for this or use stok_kodu
            self.stock_field = 'miktar'
            self.price_fields = ['fiyat', 'bayi_fiyati']
        elif feed_type == 'tkt':
            self.root_tag = 'data'
            self.item_tag = 'post'
            self.key_field = 'ID'
            self.stock_field = 'Stock'
            self.price_fields = ['Price']
        else:
            raise ValueError(f"Unknown feed type: {feed_type}")
    
    def _extract_key(self, item: etree.Element) -> Optional[str]:
        """Extract unique key from item."""
        if self.feed_type == 'ebi':
            # Try product_id first, fallback to stok_kodu
            key_elem = item.find('product_id')
            if key_elem is None or key_elem.text is None:
                key_elem = item.find('stok_kodu')
            if key_elem is not None and key_elem.text:
                return key_elem.text.strip()
        elif self.feed_type == 'tkt':
            key_elem = item.find(self.key_field)
            if key_elem is not None and key_elem.text:
                return key_elem.text.strip()
        return None
    
    def _extract_stock(self, item: etree.Element) -> Optional[str]:
        """Extract stock value from item."""
        stock_elem = item.find(self.stock_field)
        if stock_elem is not None:
            return stock_elem.text.strip() if stock_elem.text else None
        return None
    
    def _extract_price(self, item: etree.Element) -> Optional[str]:
        """Extract price value from item (tries all price fields)."""
        for price_field in self.price_fields:
            price_elem = item.find(price_field)
            if price_elem is not None and price_elem.text:
                return price_elem.text.strip()
        return None
    
    def _load_xml(self, file_path: Path) -> Optional[etree.ElementTree]:
        """Load XML file."""
        try:
            parser = etree.XMLParser(strip_cdata=False, recover=True)
            tree = etree.parse(str(file_path), parser=parser)
            return tree
        except Exception as e:
            print(f"Error loading {file_path}: {e}", file=sys.stderr)
            return None
    
    def _parse_items(self, tree: etree.ElementTree) -> Dict[str, Dict]:
        """Parse items from XML tree into dictionary keyed by item key."""
        items = {}
        root = tree.getroot()
        
        # Find all item nodes
        item_nodes = root.xpath(f'//{self.item_tag}')
        
        for item in item_nodes:
            key = self._extract_key(item)
            if key is None:
                continue
            
            items[key] = {
                'stock': self._extract_stock(item),
                'price': self._extract_price(item),
                'element': item
            }
        
        return items
    
    def compare(self, original_path: Path, cloned_path: Path) -> Dict:
        """
        Compare original and cloned XML files.
        
        Returns dictionary with comparison results.
        """
        # Load XML files
        orig_tree = self._load_xml(original_path)
        clone_tree = self._load_xml(cloned_path)
        
        if orig_tree is None or clone_tree is None:
            return {'error': 'Failed to load XML files'}
        
        # Parse items
        orig_items = self._parse_items(orig_tree)
        clone_items = self._parse_items(clone_tree)
        
        # Compare
        orig_keys = set(orig_items.keys())
        clone_keys = set(clone_items.keys())
        
        missing_keys = orig_keys - clone_keys
        extra_keys = clone_keys - orig_keys
        common_keys = orig_keys & clone_keys
        
        # Find differences in stock/price
        stock_diffs = []
        price_diffs = []
        
        for key in common_keys:
            orig_item = orig_items[key]
            clone_item = clone_items[key]
            
            # Compare stock
            orig_stock = orig_item['stock']
            clone_stock = clone_item['stock']
            if orig_stock != clone_stock:
                stock_diffs.append({
                    'key': key,
                    'original': orig_stock,
                    'cloned': clone_stock
                })
            
            # Compare price
            orig_price = orig_item['price']
            clone_price = clone_item['price']
            if orig_price != clone_price:
                price_diffs.append({
                    'key': key,
                    'original': orig_price,
                    'cloned': clone_price
                })
        
        return {
            'original_count': len(orig_items),
            'cloned_count': len(clone_items),
            'missing_keys': list(missing_keys),
            'extra_keys': list(extra_keys),
            'stock_diffs': stock_diffs,
            'price_diffs': price_diffs,
            'total_diffs': len(stock_diffs) + len(price_diffs)
        }
    
    def print_report(self, results: Dict):
        """Print comparison report."""
        if 'error' in results:
            print(f"Error: {results['error']}", file=sys.stderr)
            return
        
        print("="*60)
        print("STOCK & PRICE COMPARISON REPORT")
        print("="*60)
        print(f"\nFeed Type: {self.feed_type.upper()}")
        print(f"\nItem Counts:")
        print(f"  Original: {results['original_count']}")
        print(f"  Cloned:   {results['cloned_count']}")
        
        print(f"\nKey Comparison:")
        print(f"  Missing keys (in original but not cloned): {len(results['missing_keys'])}")
        if results['missing_keys']:
            print(f"    First 10: {results['missing_keys'][:10]}")
        
        print(f"  Extra keys (in cloned but not original): {len(results['extra_keys'])}")
        if results['extra_keys']:
            print(f"    First 10: {results['extra_keys'][:10]}")
        
        print(f"\nDifferences:")
        print(f"  Stock differences: {len(results['stock_diffs'])}")
        print(f"  Price differences: {len(results['price_diffs'])}")
        print(f"  Total differences: {results['total_diffs']}")
        
        # Print first 10 diffs
        all_diffs = []
        for diff in results['stock_diffs']:
            all_diffs.append(('stock', diff))
        for diff in results['price_diffs']:
            all_diffs.append(('price', diff))
        
        if all_diffs:
            print(f"\nFirst 10 Differences:")
            for field_type, diff in all_diffs[:10]:
                print(f"  [{field_type.upper()}] Key: {diff['key']}")
                print(f"    Original: {diff['original']}")
                print(f"    Cloned:   {diff['cloned']}")
        else:
            print("\n✓ No differences found - stock and price fields preserved correctly!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compare stock and price fields between original and cloned XML',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'feed_type',
        choices=['ebi', 'tkt'],
        help='Feed type: ebi (eBijuteri) or tkt (TeknoTok)'
    )
    
    parser.add_argument(
        'original',
        type=Path,
        help='Path to original XML file'
    )
    
    parser.add_argument(
        'cloned',
        type=Path,
        help='Path to cloned XML file'
    )
    
    args = parser.parse_args()
    
    # Check files exist
    if not args.original.exists():
        print(f"Error: Original file not found: {args.original}", file=sys.stderr)
        sys.exit(1)
    
    if not args.cloned.exists():
        print(f"Error: Cloned file not found: {args.cloned}", file=sys.stderr)
        sys.exit(1)
    
    # Run comparison
    comparator = StockPriceComparator(args.feed_type)
    results = comparator.compare(args.original, args.cloned)
    comparator.print_report(results)
    
    # Exit with error if differences found
    if results.get('total_diffs', 0) > 0:
        sys.exit(1)
