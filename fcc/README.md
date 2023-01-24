# FCC Fabric Scraper

Scrape addresses used on the [FCC's Broadband Map](https://broadbandmap.fcc.gov/home).

These come from a third-party vendor in a product called Fabric.

Our scraper downloads the Mapbox tiles provided by Fabric, decodes them, and stores data in CSV files.
The scraped data directory structure mimics the tile server's, with directories like `./{zoom}/{x}/{y}/`.

## Data

The FCC's address data come from a project called `Fabric` compiled by a company called CostQuest.
The dataset purports to represent all addresses in the US which are candidates for broadband service.
(This includes satellite services such as Starlink.)
Detailed information about how they compiled the data are [here](https://www.costquest.com/wp-content/uploads/2022/11/BroadbandServiceableLocationFabricMethodsManualPublic11022022-2.pdf).

## Usage

Here's an example that downloads all the addresses in San Francisco,
assuming we have a GeoJSON feature called `sf.geojson` that contains the bounds
of the city:

```py
poetry run python fabric_scraper.py --feature sf.geojson --tile_dir ../data/tiles --strict
```

We will generate the minimal set of tiles covering the given geometry and scrape them from the FCC website.

If tiles have been downloaded already, they are not attempted again unless they appear incomplete (e.g., an error occurred during the download).

Scraping puts an unnatural load on the source server, and they have some anti-scraping messages in place.
The `rate` and `concurrency` flags have defaults that are tuned to maximize speed while flying under the radar.
Change them at your own risk!

### Args

- `--feature <path>` GeoJSON Feature or FeatureCollection
- `--tile_dir <dir>` Directory that contains downloaded tiles, with metadata
- `--strict` Flag to force strict checking of metadata associated with previously downloaded files. If this is not used, we will skip downloading any tile that seems to exist. If `--strict` is passed, we will verify that the download of that tile actually succeeded and that the content is correct. If the tile data is invalid, we will re-download it.
- `--rate <n>` Max number of queries per second to make. The FCC website seems to ban you if you query at a sustained rate of 20 QPS, so the default is set to 15.
- `--concurrency <n>` Number of concurrent download requests to make. This can speed up downloading, but risks getting temporarily banned from the site. The FCC website seems to ban you quickly if you make 4 or more concurrent requests.

## Completeness

It's a good idea to run the scraper multiple times for a given feature with `--strict` mode enabled, until it declares that every tile is downloaded.
Otherwise you may have missing data, since some requests will inevitably fail when you're downloading tens of thousands of tiles.
