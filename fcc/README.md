# FCC Fabric Scraper

Scrape addresses used on the [FCC's Broadband Map](https://broadbandmap.fcc.gov/home).

These come from a third-party vendor in a product called Fabric.

Our scraper downloads the Mapbox tiles provided by Fabric, decodes them, and stores data in CSV files.

## Usage

Here's an example that downloads all the addresses in San Francisco.

```py
poetry run python fabric_scraper.py --ul '37.819800770375664, -122.56455476579843' --lr '37.702835718277555, -122.34388077023986' --tile_dir ../data/tiles
```

If tiles have been downloaded already, they are not attempted again.

## TODO

- Pass in custom GeoJSON geometry to download addresses for.
