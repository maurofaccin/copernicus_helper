"""Use this to download Copernicus data."""

import argparse
from pathlib import Path
from typing import Literal

import cdsapi
import country_bounding_boxes as countries


def get_data_from_copernicus(
    filename: str | Path,
    year: int = 2011,
    variable: str = "instantaneous_10m_wind_gust",
    area: list[float] = [1, -1, -1, 1],  # This should be [north, west, south, east].
    dataset: str = "single-levels",
):
    """Retrieve data from Copernicus and save locally as `.nc` file.

    `variable` can be any of the following:
    ```
    [
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "2m_dewpoint_temperature",
        "2m_temperature",
        "mean_sea_level_pressure",
        "total_precipitation",
        "instantaneous_10m_wind_gust"
    ],
    ```
    Go [here](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download) to find the other names
    """
    if Path(filename).is_file():
        # do not download the same data multiple times
        return

    dataset = "reanalysis-era5-" + dataset
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
    for k, v in request.items():
        print(f"{k:20s} : {v}")

    client = cdsapi.Client()
    client.retrieve(dataset, request).download(filename)


def get_projections_from_copernicus(
    filename: str | Path,
    resolution: Literal["daily", "monthly"] = "monthly",
    experiment: Literal["historical", "ssp1_2_6", "ssp2_4_5", "ssp3_7_0"] = "historical",
    year: int | str = 2000,
    variable: str = "daily_maximum_near_surface_air_temperature",
    area: list[float] = [90, -180, -90, 180],  # This should be [north, west, south, east].
):
    """Retrieve data from Copernicus and save locally as `.nc` file.

    ```
    Go [here](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download) to find the other names
    """
    if Path(filename).is_file():
        # do not download the same data multiple times
        return

    dataset = "projections-cmip6"
    request = {
        "variable": variable,
        "temporal_resolution": resolution,
        "experiment": experiment,
        "year": [str(year)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": area,
    }
    if resolution == "daily":
        request |= {"day": [f"{d:02d}" for d in range(1, 32)]}

    for k, v in request.items():
        print(f"{k:20s} : {v}")

    client = cdsapi.Client(url=None, key=None)
    client.retrieve(dataset, request).download(filename)


def get_country(
    code2: str,
    subunit: str | None = None,
    padding: float | None = 0.1,  # ~10Km
) -> list[float]:
    """Get country bounding box.

    If only `code2` is provided, the smaller box including all subunits is returned.
    Data from https://www.naturalearthdata.com/

    The box is [north, west, south, east] as required by copernicus.

    Arguments
    ---------
    code2 : str
        Country code (2 chars)
    subunit: str
        Name of the subunit
    padding: float
        Padding to apply to the box

    Returns
    -------
    box : list[float]
        The box
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

    return [box[-1]] + box[:-1]


def cache_location(default: str | None = None) -> Path:
    """Return the right location to save data."""
    if default is None:
        location = Path("/dataNfs")
        if location.is_dir():
            return location

        location = Path("~/copernicus_data").expanduser()

    else:
        location = Path(default).expanduser()

    location.mkdir(parents=True, exist_ok=True)
    return location


def args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Helper to download Copernicus data.")
    parser.add_argument(
        "--variable",
        "-v",
        default="total_precipitation",
        help="variable name (default: total_precipitation)",
    )
    parser.add_argument(
        "--country",
        "-c",
        default="IT",
        help="Country to restrict (2chars code, default: IT, you can also select a subunit as in ES:Spain)",
    )
    parser.add_argument(
        "--dataset",
        "--ds",
        action="store",
        default=None,
        choices=["single-levels", "land", "pressure-levels"],
        help="Dataset: single-levels (default), land, …, for ERA5.",
    )
    parser.add_argument(
        "--experiment",
        "-x",
        action="store",
        default=None,
        choices=["historical", "ssp1_2_6", "ssp2_4_5", "ssp3_7_0"],
        help="Download the given expariment from CMIP6.",
    )
    parser.add_argument(
        "--folder",
        "-o",
        help="Output folder. (default: check if /dataNfs is present, else ~/copernicus_data)",
    )
    parser.add_argument("--time-range", "-y", default="2000-2100")
    return parser


def main() -> None:
    """Do the main.

    Command line arguments:
        Variable location
    Example:
        copernicus.py instantaneous_10m_wind_gust IT
    """
    arguments = args().parse_args()

    # Check arguments:
    if arguments.experiment is None and arguments.dataset is None:
        raise ValueError("Arguments: you should supply either the experiment or the dataset.")
    if arguments.experiment is not None:
        print(f"Experiment:  {arguments.experiment}")
    elif arguments.dataset is not None:
        print(f"Dataset:     {arguments.dataset}")

    variable = arguments.variable
    print(f"Variable:    {variable}")
    country = arguments.country
    if ":" in country:
        country, subunit = country.split(":")
    else:
        subunit = None
    print(f"Country:     {country}, {subunit}")
    year1, year2 = map(int, arguments.time_range.split("-"))
    print(f"Year:        {year1} - {year2}")

    location = cache_location(arguments.folder) / f"{country}_{variable}_{arguments.dataset}"
    location.mkdir(parents=True, exist_ok=True)
    print(f"Folder:      {location}")

    for year in range(year1, year2 + 1):
        print(f"Downloading {year}")

        if arguments.experiment is not None:
            # Get CMIP6 projection data from Copernicus.
            fname = location / f"{variable}_{arguments.experiment}_{country}_{year}.nc"
            if fname.is_file():
                print("Already downloaded", fname)
                continue
            get_projections_from_copernicus(
                filename=fname,
                resolution="monthly",
                experiment=arguments.experiment,
                year=year,
                variable=variable,
                area=get_country(country, subunit=subunit),
            )
        elif arguments.dataset is not None:
            # Get re-projection ERA5 data from Copernicus.
            fname = location / f"{variable}_{arguments.dataset}_{country}_{year}.nc"
            if fname.is_file():
                print("Already downloaded", fname)
                continue
            get_data_from_copernicus(
                filename=fname,
                year=year,
                variable=variable,
                area=get_country(country, subunit=subunit),
                dataset=arguments.dataset,
            )


if __name__ == "__main__":
    main()
