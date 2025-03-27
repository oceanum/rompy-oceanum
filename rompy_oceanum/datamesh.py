import json
import logging
import os
***REMOVED***
from pathlib import Path
from typing import Dict, List, Optional, Union

import typer
import xarray as xr
from cloudpathlib import AnyPath
from oceanum.datamesh import Connector
from oceanum.datamesh.connection import DatameshWriteError
from oceanum.datamesh.datasource import Coordinates
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
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


def load_rompy_config(config_path: Optional[str] = None) -> Dict:
    """
    Load a rompy configuration from a file or environment variable.
    
    Args:
        config_path: Path to the config file, if None will try to use ROMPY_CONFIG environment variable
        
    Returns:
        Parsed configuration as a dictionary
    """
    if config_path is None:
        config_path = os.environ.get("ROMPY_CONFIG")
        if not config_path:
            raise ValueError("No config path provided and ROMPY_CONFIG environment variable not set")
    
    try:
        with open(config_path, "r") as f:
            file_content = f.read()
        
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
        None, help="Path to rompy config file, if not provided will use ROMPY_CONFIG env var"
    ),
    datasource_id: str = typer.Option("rompy", help="Base DataMesh datasource ID"),
    tags: Optional[List[str]] = typer.Option(None, help="Additional tags for the datasets"),
):
    """
    Write both grid and spectra data to DataMesh based on a rompy config file.
    
    This command will:
    1. Read configuration from a file or ROMPY_CONFIG environment variable
    2. Extract name and description from the config
    3. Find and process swangrid.nc and swanspec.nc files from output_dir/run_id/
    """
    tags = tags or []
    
    try:
        # Load config from file or environment variable
        config = load_rompy_config(config_path)
        
        # Extract required information from config
        run_id = config.get("run_id")
        output_dir = config.get("output_dir")
        
        if not run_id or not output_dir:
            raise ValueError("Config must contain 'run_id' and 'output_dir' fields")
        
        # Construct the output path
        output_path = Path(output_dir) / run_id
        
        # Look for required files
        grid_file = output_path / "swangrid.nc"
        spectra_file = output_path / "swanspec.nc"
        
        # Extract name and description
        name = "ROMPY Model Run"
        description = "ROMPY generated dataset"
        
        # Try to get more descriptive name and description from config
        if "config" in config and "startup" in config["config"]:
            if "project" in config["config"]["startup"]:
                project = config["config"]["startup"]["project"]
                if "name" in project:
                    name = project["name"]
                if "title1" in project:
                    description = project["title1"]
        
        # Display summary of what will be processed
        console.print(Panel(
            f"[bold]Processing model output for:[/] {name}\n"
            f"[bold]Description:[/] {description}\n"
            f"[bold]Run ID:[/] {run_id}\n"
            f"[bold]Output directory:[/] {output_path}"
        ))
        
        # Create the writer
        writer = DatameshWriter(
            datasource_id=f"{datasource_id}_{run_id}", 
            name=name, 
            description=description, 
            tags=["rompy", "model-output"] + tags
        )
        
        # Process grid file if it exists
        if grid_file.exists():
            console.print(f"[bold blue]Writing grid data from:[/] {grid_file}")
            writer.write_grid(grid_file)
            console.print("[bold green]✓[/] Grid data written successfully")
        else:
            console.print(f"[bold yellow]Warning:[/] Grid file not found at {grid_file}")
        
        # Process spectra file if it exists
        if spectra_file.exists():
            console.print(f"[bold blue]Writing spectra data from:[/] {spectra_file}")
            writer.write_spectra(spectra_file)
            console.print("[bold green]✓[/] Spectra data written successfully")
        else:
            console.print(f"[bold yellow]Warning:[/] Spectra file not found at {spectra_file}")
            
        console.print("[bold green]✓[/] Processing complete")
        
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
