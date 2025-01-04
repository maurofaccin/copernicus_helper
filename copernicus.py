"""Use this to download copernicus data."""

import sys
from pathlib import Path

import cdsapi
import country_bounding_boxes as countries


def get_data_from_copernicus(
    filename: str | Path,
    year: int = 2011,
    variable: str = "instantaneous_10m_wind_gust",
    area: list[int] = [1, -1, -1, 1],  # this should be [north, west, south, east]
):
    """Retrieve data from Copernicus and save locally as nc file.

    variable can be any of the following:
        [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "2m_dewpoint_temperature",
            "2m_temperature",
            "mean_sea_level_pressure",
            "total_precipitation",
            "instantaneous_10m_wind_gust"
        ],
        Go [here](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download) to find the other names
    """
    if Path(filename).is_file():
        # do not download the same data multiple times
        return

    dataset = "reanalysis-era5-single-levels"
    request = {
        "product_type": "reanalysis",
        "variable": variable,
        "year": [str(year)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": area,
    }

    client = cdsapi.Client()
    client.retrieve(dataset, request).download(filename)


def get_country(
    code2: str,
    subunit: str | None = None,
    ndigits: int | None = 2,  # ~1km
    padding: float | None = 0.1,  # ~10Km
):
    """Get country bounding box.

    If only `code2` is provided, the smaller box including all subunits is returned.
    Data from https://www.naturalearthdata.com/

    The box is [north, west, south, east] as required by copernicus.
    """
    print("Checking", code2)
    units = countries.country_subunits_by_iso_code(code2)
    if subunit is None:
        boxes = [unit.bbox for unit in units]
    else:
        boxes = [unit.bbox for unit in units if unit.name == subunit]

    # transpose
    boxes = list(zip(*boxes))
    print(boxes)
    box = [min(boxes[0]), min(boxes[1]), max(boxes[2]), max(boxes[3])]

    if padding is not None:
        box = [box[0] - padding, box[1] - padding, box[2] + padding, box[3] + padding]

    if ndigits is not None:
        box = [round(x, ndigits=ndigits) for x in box]

    return [box[-1]] + box[:-1]


def main() -> None:
    """Do the main.

    Command line arguments:
        Variable location
    Example:
        copernicus.py instantaneous_10m_wind_gust IT
    """
    variable = sys.argv[-2]
    country = sys.argv[-1]
    location = Path("/dataNfs") / f"{variable}_{country}"
    location.mkdir(parents=True, exist_ok=True)

    for year in range(2000, 2101):
        get_data_from_copernicus(
            filename=location / f"{variable}_{country}_{year}.nc",
            year=year,
            variable=variable,
            area=get_country(country),
        )


if __name__ == "__main__":
    main()
