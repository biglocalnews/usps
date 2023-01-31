import click
import geojson

with open("../data/shapes/usa_500k.geojson") as fh:
    states = geojson.load(fh)


@click.command()
@click.argument("abbreviation")
@click.argument("name")
def extract(abbreviation: str, name: str):
    with open(f"../data/shapes/{abbreviation}.geojson", "w") as fh:
        geojson.dump(
            [
                x
                for x in states.features
                if x.properties["NAME"].lower() == name.lower()
            ][0],
            fh,
        )


if __name__ == "__main__":
    extract()
