#!/usr/bin/env python3
"""
Streaming Catalog Parser

Parses and displays fields from Hulu & Disney+ catalog CSV files.
Handles complex nested JSON data and provides readable output.

Usage:
    python streaming_catalog_parser.py --file data/hulu_disneyplus_us.csv --limit 5
    python streaming_catalog_parser.py --file data/hulu_disneyplus_us.csv --id 1243341
"""

import json
import argparse
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path


class StreamingCatalogParser:
    """Parser for streaming service catalog CSV files."""
    
    def __init__(self, csv_file: str):
        """Initialize parser with CSV file path."""
        self.csv_file = Path(csv_file)
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load CSV data into pandas DataFrame."""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        print(f"📖 Loading catalog data from {self.csv_file}...")
        self.df = pd.read_csv(self.csv_file)
        print(f"✅ Loaded {len(self.df)} entries")
    
    def get_entry_by_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific entry by TMDB ID."""
        entry = self.df[self.df['tmdb_id'] == tmdb_id]
        if entry.empty:
            return None
        return entry.iloc[0].to_dict()
    
    def get_sample_entries(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample entries from the catalog."""
        return self.df.head(limit).to_dict('records')
    
    def parse_json_field(self, field_value: str) -> Any:
        """Safely parse JSON field values."""
        if pd.isna(field_value) or field_value == '':
            return None
        try:
            parsed = json.loads(field_value)
            # Remove "results:" prefix if it exists in the string
            if isinstance(parsed, dict) and 'results' in parsed:
                return parsed['results']
            return parsed
        except (json.JSONDecodeError, TypeError):
            return field_value
    
    def format_field_value(self, field_name: str, value: Any, max_length: int = 200) -> str:
        """Format field value for display."""
        if pd.isna(value) or value is None:
            return "None"
        
        # Handle JSON fields
        if isinstance(value, str) and (field_name in ['genres', 'credits', 'watch_providers', 
                                                     'external_ids', 'keywords', 'videos', 
                                                     'images', 'translations', 'release_dates', 
                                                     'content_ratings'] or value.startswith('{')):
            parsed = self.parse_json_field(value)
            if isinstance(parsed, (dict, list)):
                return f"[JSON Data - {len(str(parsed))} chars]"
        
        # Truncate long strings
        if isinstance(value, str) and len(value) > max_length:
            return f"{value[:max_length]}... [truncated]"
        
        return str(value)
    
    def display_entry(self, entry: Dict[str, Any], show_json_details: bool = False):
        """Display a single catalog entry in a formatted way."""
        print("\n" + "="*80)
        print(f"🎬 {entry.get('title', entry.get('name', 'Unknown Title'))}")
        print("="*80)
        
        # Basic info section
        print("\n📋 BASIC INFORMATION:")
        print("-" * 40)
        basic_fields = [
            'service', 'media_type', 'tmdb_id', 'title', 'name', 
            'original_title', 'original_name', 'overview', 'tagline',
            'status', 'release_date', 'first_air_date', 'last_air_date'
        ]
        
        for field in basic_fields:
            if field in entry:
                value = self.format_field_value(field, entry[field])
                print(f"{field:20}: {value}")
        
        # Technical details section
        print("\n🔧 TECHNICAL DETAILS:")
        print("-" * 40)
        tech_fields = [
            'runtime', 'episode_run_time', 'number_of_seasons', 
            'number_of_episodes', 'in_production', 'original_language',
            'homepage', 'popularity', 'vote_average', 'vote_count',
            'budget', 'revenue'
        ]
        
        for field in tech_fields:
            if field in entry:
                value = self.format_field_value(field, entry[field])
                print(f"{field:20}: {value}")
        
        # Lists and arrays section
        print("\n📝 LISTS & ARRAYS:")
        print("-" * 40)
        list_fields = [
            'genres', 'spoken_languages', 'production_companies',
            'production_countries', 'origin_country', 'languages'
        ]
        
        for field in list_fields:
            if field in entry:
                value = entry[field]
                parsed = self.parse_json_field(value)
                if isinstance(parsed, list):
                    print(f"{field:20}: {len(parsed)} items")
                    if parsed:
                        for i, item in enumerate(parsed):
                            if isinstance(item, dict):
                                # Handle dictionary items (like genres with id and name)
                                if 'name' in item:
                                    print(f"{'':20}  {i+1}. {item['name']}")
                                elif 'iso_639_1' in item:
                                    print(f"{'':20}  {i+1}. {item.get('name', item['iso_639_1'])}")
                                else:
                                    print(f"{'':20}  {i+1}. {item}")
                            else:
                                print(f"{'':20}  {i+1}. {item}")
                else:
                    print(f"{field:20}: {self.format_field_value(field, value)}")
        
        # Complex JSON fields section
        print("\n🔗 COMPLEX DATA:")
        print("-" * 40)
        json_fields = [
            'external_ids', 'keywords', 'watch_providers', 'credits',
            'videos', 'images', 'translations', 'release_dates', 'content_ratings'
        ]
        
        for field in json_fields:
            if field in entry:
                value = entry[field]
                parsed = self.parse_json_field(value)
                if isinstance(parsed, dict):
                    # Only show external_ids as they're usually simple
                    if field == 'external_ids' and parsed:
                        print(f"{field:20}: {len(parsed)} keys")
                        for key, val in parsed.items():
                            print(f"{'':20}  {key}: {val}")
                    else:
                        # Hide other complex dict fields
                        print(f"{field:20}: [Complex data - {len(parsed)} keys]")
                elif isinstance(parsed, list):
                    # Hide complex list fields
                    print(f"{field:20}: [Complex data - {len(parsed)} items]")
                else:
                    print(f"{field:20}: {self.format_field_value(field, value)}")
    
    def display_sample_entries(self, limit: int = 3, show_json_details: bool = False):
        """Display sample entries from the catalog."""
        print(f"\n🎯 DISPLAYING {limit} SAMPLE ENTRIES:")
        print("="*80)
        
        entries = self.get_sample_entries(limit)
        for i, entry in enumerate(entries, 1):
            print(f"\n📺 ENTRY #{i}")
            self.display_entry(entry, show_json_details)
    
    def display_entry_by_id(self, tmdb_id: int, show_json_details: bool = False):
        """Display a specific entry by TMDB ID."""
        entry = self.get_entry_by_id(tmdb_id)
        if entry is None:
            print(f"❌ No entry found with TMDB ID: {tmdb_id}")
            return
        
        print(f"\n🎯 DISPLAYING ENTRY WITH TMDB ID: {tmdb_id}")
        self.display_entry(entry, show_json_details)
    
    def get_catalog_stats(self):
        """Display catalog statistics."""
        print("\n📊 CATALOG STATISTICS:")
        print("="*50)
        
        print(f"Total entries: {len(self.df)}")
        print(f"Services: {self.df['service'].unique()}")
        print(f"Media types: {self.df['media_type'].unique()}")
        
        # Service breakdown
        print("\nService breakdown:")
        service_counts = self.df['service'].value_counts()
        for service, count in service_counts.items():
            print(f"  {service}: {count} entries")
        
        # Media type breakdown
        print("\nMedia type breakdown:")
        media_counts = self.df['media_type'].value_counts()
        for media_type, count in media_counts.items():
            print(f"  {media_type}: {count} entries")
        
        # Top genres (if available)
        if 'genres' in self.df.columns:
            print("\nTop genres (first 10):")
            all_genres = []
            for genres_str in self.df['genres'].dropna():
                try:
                    genres = json.loads(genres_str)
                    if isinstance(genres, list):
                        all_genres.extend([g.get('name', 'Unknown') for g in genres])
                except:
                    continue
            
            if all_genres:
                from collections import Counter
                genre_counts = Counter(all_genres)
                for genre, count in genre_counts.most_common(10):
                    print(f"  {genre}: {count} entries")


def main():
    parser = argparse.ArgumentParser(description="Parse streaming catalog CSV files")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--limit", type=int, default=3, help="Number of sample entries to display")
    parser.add_argument("--id", type=int, help="Display specific entry by TMDB ID")
    parser.add_argument("--stats", action="store_true", help="Show catalog statistics")
    parser.add_argument("--json-details", action="store_true", help="Show detailed JSON content")
    
    args = parser.parse_args()
    
    try:
        catalog_parser = StreamingCatalogParser(args.file)
        
        if args.stats:
            catalog_parser.get_catalog_stats()
        
        if args.id:
            catalog_parser.display_entry_by_id(args.id, args.json_details)
        else:
            catalog_parser.display_sample_entries(args.limit, args.json_details)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 