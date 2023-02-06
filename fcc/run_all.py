import os

import click
import extract_state_feature as esf
import fabric_scraper as fs

STATES = [
    ("al", "Alabama"),
    ("az", "Arizona"),
    ("ar", "Arkansas"),
    ("ca", "California"),
    ("co", "Colorado"),
    ("ct", "Connecticut"),
    ("de", "Delaware"),
    ("fl", "Florida"),
    ("ga", "Georgia"),
    ("hi", "Hawaii"),
    ("id", "Idaho"),
    ("il", "Illinois"),
    ("in", "Indiana"),
    ("ia", "Iowa"),
    ("la", "Louisiana"),
    ("ks", "Kansas"),
    ("ky", "Kentucky"),
    ("me", "Maine"),
    ("md", "Maryland"),
    ("ma", "Massachusetts"),
    ("mi", "Michigan"),
    ("mn", "Minnesota"),
    ("ms", "Mississippi"),
    ("mo", "Missouri"),
    ("mt", "Montana"),
    ("nc", "North Carolina"),
    ("nd", "North Dakota"),
    ("ne", "Nebraska"),
    ("nv", "Nevada"),
    ("nh", "New Hampshire"),
    ("nj", "New Jersey"),
    ("nm", "New Mexico"),
    ("ny", "New York"),
    ("oh", "Ohio"),
    ("ok", "Oklahoma"),
    ("or", "Oregon"),
    ("pa", "Pennsylvania"),
    ("ri", "Rhode Island"),
    ("sc", "South Carolina"),
    ("sd", "South Dakota"),
    ("tn", "Tennessee"),
    ("tx", "Texas"),
    ("ut", "Utah"),
    ("vt", "Vermont"),
    ("va", "Virginia"),
    ("wa", "Washington"),
    ("wv", "West Virginia"),
    ("wi", "Wisconsin"),
    ("wy", "Wyoming"),
    ("ak", "Alaska"),  # Last because it's enormous.
]


@click.command()
@click.pass_context
def run(ctx):
    i = 1
    for abbr, name in STATES:
        print(f"State {i} out of {len(STATES)}: {name}")
        i += 1
        print(f"Extracting feature data for {name} ...")
        ctx.invoke(esf.extract, abbreviation=abbr, name=name)
        print(f"Scraping address tiles for {name} ...")
        ctx.invoke(
            fs.run,
            tile_dir=os.path.join("..", "data", "tiles"),
            feature=os.path.join("..", "data", "shapes", f"{abbr}.geojson"),
            strict=True,
            concurrency=3,
            rate=12,
        )


if __name__ == "__main__":
    run()
