#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os
from src.extractor import SourceCodeExtractor

async def main():
    target_url = "https://target_here"
    download_dir = "downloaded_sources"
    
    extractor = SourceCodeExtractor(target_url, download_dir)
    await extractor.extract()

if __name__ == "__main__":
    asyncio.run(main())

