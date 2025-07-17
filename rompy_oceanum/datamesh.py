import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Union

import typer
import xarray as xr
from cloudpathlib import AnyPath
from oceanum.datamesh import Connector
from oceanum.datamesh.connection import DatameshWriteError
from oceanum.datamesh.datasource import Coordinates
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from wavespectra import read_ncswan, read_ww3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class DatameshWriter(BaseModel):
    datasource_id: str
    name: str
    description: str
    tags: list[str] = []
    labels: list[str] = []
    _connector: None

    @property
    def connector(self):
        if not hasattr(self, "_connector"):
            self._connector = Connector()
        return self._connector

    # @retry(
    #     stop=stop_after_attempt(3),
    #     wait=wait_fixed(2),
    #     retry=retry_if_exception_type(DatameshWriteError),
    #     reraise=True,
    # )
    def write_dataset(
        self,
        ds: xr.Dataset,
        coordinates: dict = {"t": "time", "x": "longitude", "y": "latitude"},
        additional_tags: list = [],
        dataset_id_postfix: list = [],
        name_postfix: list = [],
        description_postfix: list = [],
    ):
        times = ds[coordinates["t"]].to_pandas()
        datasource_id = "-".join([self.datasource_id] + dataset_id_postfix)
        logger.info(f"\t -- writing to datamesh datasource_id {datasource_id}")
        datasource = self.connector.write_datasource(
            datasource_id=datasource_id,
            name=" ".join([self.name] + name_postfix),
            description=" ".join([self.description] + description_postfix),
            data=ds,
            coordinates=coordinates,
            tags=self.tags + additional_tags,
            # labels=self.labels,
            tstart=times[0],
            tend=times[-1],
            geom={
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            ds[coordinates["x"]].min(),
                            ds[coordinates["y"]].min(),
                        ],
                        [
                            ds[coordinates["x"]].max(),
                            ds[coordinates["y"]].min(),
                        ],
                        [
                            ds[coordinates["x"]].max(),
                            ds[coordinates["y"]].max(),
                        ],
                        [
                            ds[coordinates["x"]].min(),
                            ds[coordinates["y"]].max(),
                        ],
                    ]
                ],
            },
            # append=coordinates["t"],  # Commented for now as this causes error in datamesh if data doesn't exist
        )
        return datasource

    def write_grid(self, nc: AnyPath):
        dataset = xr.open_dataset(nc)
        logger.info(f"Writing grid from {nc}")
        #    dataset.drop_vars(["MAPSTA"]),
        # drop MAPSTA because if it exists
        # it will cause the write to fail
        if "MAPSTA" in dataset:
            dataset = dataset.drop_vars(["MAPSTA"])
        self.write_dataset(
            ds=dataset,
            coordinates={"t": "time", "x": "longitude", "y": "latitude"},
            additional_tags=["grid"],
            dataset_id_postfix=["grid"],
            name_postfix=[" parameters"],
            description_postfix=["- Gridded Parameters"],
        )

    def write_spectra(self, nc: AnyPath):
        dataset = read_ncswan(nc)
        logger.info(f"Writing spectra from {nc}")
        self.write_dataset(
            dataset,
            coordinates={"t": "time", "x": "lon", "y": "lat"},
            additional_tags=["spectra"],
            dataset_id_postfix=["spectra"],
            name_postfix=[" spectra"],
            description_postfix=["- Spectra"],
        )


# Create typer apps
app = typer.Typer(
    help="DataMesh CLI for working with grid and spectra data",
    rich_markup_mode="none",  # Disable rich markup to avoid terminal characters
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
)
write_app = typer.Typer(help="Write data to DataMesh")
app.add_typer(write_app, name="write")


@app.callback()
def callback(
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug mode with detailed logging"
    )
):
    """DataMesh CLI with debugging options."""
    if debug:
        # Set logging level to DEBUG for more verbose output
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        logger.setLevel(logging.DEBUG)
        print("Debug mode enabled")


@write_app.command("grid")
def write_grid(
    file: Path = typer.Argument(..., help="Path to the NetCDF file", exists=True),
    datasource_id: str = typer.Option("rompy", help="DataMesh datasource ID"),
    name: str = typer.Option("ROMPY Data", help="Name for the dataset"),
    description: str = typer.Option(
        "ROMPY generated dataset", help="Description for the dataset"
    ),
    tags: Optional[List[str]] = typer.Option(None, help="Tags for the dataset"),
    labels: Optional[List[str]] = typer.Option(None, help="Labels for the dataset"),
):
    """Write grid data to DataMesh."""
    tags = tags or []
    try:
        writer = DatameshWriter(
            datasource_id=datasource_id,
            name=name,
            description=description,
            tags=tags,
            # labels=labels,
        )

        print(f"Writing grid data from file: {file}")
        writer.write_grid(file)
        print("✓ Grid data written successfully")
    except Exception as e:
        print(f"Error: {str(e)}")
        if logger.level <= logging.DEBUG:  # Only show traceback in debug mode
            print("Debug traceback:")
            traceback.print_exc()
        raise typer.Exit(code=1)


@write_app.command("spectra")
def write_spectra(
    file: Path = typer.Argument(..., help="Path to the NetCDF file", exists=True),
    datasource_id: str = typer.Option("rompy", help="DataMesh datasource ID"),
    name: str = typer.Option("ROMPY Data", help="Name for the dataset"),
    description: str = typer.Option(
        "ROMPY generated dataset", help="Description for the dataset"
    ),
    tags: Optional[List[str]] = typer.Option(None, help="Tags for the dataset"),
):
    """Write spectra data to DataMesh."""
    tags = tags or []
    try:
        writer = DatameshWriter(
            datasource_id=datasource_id, name=name, description=description, tags=tags
        )

        print(f"Writing spectra data from file: {file}")
        writer.write_spectra(file)
        print("✓ Spectra data written successfully")
    except Exception as e:
        print(f"Error: {str(e)}")
        if logger.level <= logging.DEBUG:  # Only show traceback in debug mode
            print("Debug traceback:")
            traceback.print_exc()
        raise typer.Exit(code=1)


def load_rompy_config(config_path: Optional[str] = None) -> Dict:
    """
    Load a rompy configuration from a file or environment variable.

    Args:
        config_path: Path to the config file, if None will try to use ROMPY_CONFIG environment variable

    Returns:
        Parsed configuration as a dictionary
    """
    if config_path is None:
        file_content = os.getenv("ROMPY_CONFIG")
        if not file_content:
            raise ValueError(
                "No config path provided and ROMPY_CONFIG environment variable not set"
            )
    else:
        with open(config_path, "r") as f:
            file_content = f.read()

    try:
        # The example model_config.json contains an escaped JSON string, not a raw JSON object
        # Handle this special case by checking if it starts and ends with quotes
        if file_content.startswith('"') and file_content.endswith('"'):
            # This is a JSON string that needs to be parsed twice
            # First, parse the outer string to get the inner content
            inner_json_string = json.loads(file_content)
            # Then parse the inner content as JSON
            config = json.loads(inner_json_string)
        else:
            # Regular JSON file - parse directly
            config = json.loads(file_content)

        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse config file: {e}")
    except FileNotFoundError:
        raise ValueError(f"Config file not found: {config_path}")


@write_app.command("from-config")
def write_from_config(
    config_path: Optional[str] = typer.Argument(
        None,
        help="Path to rompy config file, if not provided will use ROMPY_CONFIG env var",
    ),
    org: str = typer.Option("", help="Organisation name for dataset naming"),
    tags: Optional[List[str]] = typer.Option(
        None, help="Additional tags for the datasets"
    ),
):
    """
    Write both grid and spectra data to DataMesh based on a rompy config file.

    This command will:
    1. Read configuration from a file or ROMPY_CONFIG environment variable
    2. Load the model configuration data
    3. Register the grid and spectra data with DataMesh
    """
    tags = tags or []

    try:
        # Load config from file or environment variable
        config = load_rompy_config(config_path)

        # Extract basic info from config
        run_id = config.get('run_id', 'unknown')
        output_dir = Path(config.get('output_dir', '/app'))

        # Set up DataMesh configuration
        org = org or os.environ.get("DATAMESH_ORGANISATION", "oceanum")

        # Display summary of what will be processed
        print("=" * 60)
        print("Processing model output for: ROMPY Model Run")
        print(f"Run ID: {run_id}")
        print(f"Output directory: {output_dir}")
        print(f"Organisation: {org}")
        print("=" * 60)

        # Determine correct file paths based on run_id_subdir configuration
        run_id_subdir = config.get('run_id_subdir', True)

        if run_id_subdir:
            # Traditional path with run_id subdirectory
            base_path = output_dir / run_id
        else:
            # Direct path without run_id subdirectory (Prax pipeline context)
            base_path = output_dir

        print(f"Looking for output files in: {base_path}")

        # Create DataMesh writer for this run
        datasource_base = f"{org}-rompy-{run_id}"

        # Process grid file if it exists
        grid_file = base_path / "swangrid.nc"
        if grid_file.exists():
            print(f"Registering grid data with DataMesh: {grid_file}")
            grid_writer = DatameshWriter(
                datasource_id=f"{datasource_base}-grid",
                name=f"{org} ROMPY Grid Data",
                description=f"ROMPY generated grid data for run {run_id}",
                tags=tags + ["rompy", "swan", "grid", org]
            )
            grid_writer.write_grid(grid_file)
            print(f"✓ Grid data registered successfully as '{datasource_base}-grid'")
        else:
            error_msg = f"Error: Grid file not found at {grid_file}"
            print(error_msg)
            raise FileNotFoundError(error_msg)

        # Process spectra file if it exists
        spectra_file = base_path / "swanspec.nc"
        if spectra_file.exists():
            print(f"Registering spectra data with DataMesh: {spectra_file}")
            spectra_writer = DatameshWriter(
                datasource_id=f"{datasource_base}-spectra",
                name=f"{org} ROMPY Spectra Data",
                description=f"ROMPY generated spectra data for run {run_id}",
                tags=tags + ["rompy", "swan", "spectra", org]
            )
            spectra_writer.write_spectra(spectra_file)
            print(f"✓ Spectra data registered successfully as '{datasource_base}-spectra'")
        else:
            error_msg = f"Error: Spectra file not found at {spectra_file}"
            print(error_msg)
            raise FileNotFoundError(error_msg)

        print("✓ Processing complete")

    except Exception as e:
        print(f"Error: {str(e)}")
        if logger.level <= logging.DEBUG:  # Only show traceback in debug mode
            print("Debug traceback:")
            traceback.print_exc()
        raise typer.Exit(code=1)


def main():
    """Main entry point for the CLI."""
    try:
        app(prog_name="datamesh")
    except Exception as e:
        # Simplified error output
        if logger.level <= logging.DEBUG:
            print("Error:")
            traceback.print_exc()
        else:
            print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
