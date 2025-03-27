import logging
***REMOVED***
from pathlib import Path
from typing import List, Optional

import typer
import xarray as xr
from cloudpathlib import AnyPath
from oceanum.datamesh import Connector
from oceanum.datamesh.connection import DatameshWriteError
from oceanum.datamesh.datasource import Coordinates
from pydantic import BaseModel
from rich.console import Console
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)
from wavespectra import read_ncswan, read_ww3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

console = Console()


class DatameshWriter(BaseModel):
    datasource_id: str
    name: str
    description: str
    tags: list[str] = []
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
        datasource_id = "_".join([self.datasource_id] + dataset_id_postfix)
        logger.info(f"\t -- writing to datamesh datasource_id {datasource_id}")
        datasource = self.connector.write_datasource(
            datasource_id=datasource_id,
            name=" ".join([self.name] + name_postfix),
            description=" ".join([self.description] + description_postfix),
            data=ds,
            coordinates=coordinates,
            tags=self.tags + additional_tags,
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
            append=coordinates["t"],
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
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,  # Show full tracebacks instead of simplified errors
    pretty_exceptions_show_locals=True,  # Show local variables in tracebacks
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
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        console.print("[bold yellow]Debug mode enabled[/]")


@write_app.command("grid")
def write_grid(
    file: Path = typer.Argument(..., help="Path to the NetCDF file", exists=True),
    datasource_id: str = typer.Option("rompy", help="DataMesh datasource ID"),
    name: str = typer.Option("ROMPY Data", help="Name for the dataset"),
    description: str = typer.Option(
        "ROMPY generated dataset", help="Description for the dataset"
    ),
    tags: Optional[List[str]] = typer.Option(None, help="Tags for the dataset"),
):
    """Write grid data to DataMesh."""
    tags = tags or []
    try:
        writer = DatameshWriter(
            datasource_id=datasource_id, name=name, description=description, tags=tags
        )

        console.print(f"[bold blue]Writing grid data from file:[/] {file}")
        writer.write_grid(file)
        console.print("[bold green]✓[/] Grid data written successfully")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if logger.level <= logging.DEBUG:  # Only show traceback in debug mode
            console.print("[bold yellow]Debug traceback:[/]")
            console.print_exception(show_locals=True)
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

        console.print(f"[bold blue]Writing spectra data from file:[/] {file}")
        writer.write_spectra(file)
        console.print("[bold green]✓[/] Spectra data written successfully")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if logger.level <= logging.DEBUG:  # Only show traceback in debug mode
            console.print("[bold yellow]Debug traceback:[/]")
            console.print_exception(show_locals=True)
        raise typer.Exit(code=1)


def main():
    """Main entry point for the CLI."""
    try:
        app()
    except Exception as e:
        console.print("[bold red]Error:[/]")
        console.print_exception(
            show_locals=True
        )  # Show detailed exception info with local variables
        sys.exit(1)


if __name__ == "__main__":
    main()
