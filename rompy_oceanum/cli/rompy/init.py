"""Init command for creating new rompy configurations."""

import json
from pathlib import Path
from typing import Optional

import click
import yaml
from oceanum.cli.models import ContextObject

# Template configurations for different model types
SWAN_TEMPLATE = {
    "run_id": "swan_example_run",  # This has to be run_id for now - fix coming
    "output_dir": "/tmp/rompy",
    "run_id_subdir": "True",
    # Time period configuration
    "period": {
        "start": "20240101T000000",  # Format: YYYYMMDDTHHMMSS
        "duration": "1d",  # Duration: 1 day
        "interval": "1h",  # Output every hour
    },
    # SWAN model configuration
    "config": {
        "model_type": "swanconfig",
        # Startup configuration
        "startup": {
            # Project metadata
            "project": {
                "model_type": "project",
                "name": "Swan Example",  # Project name
                "nr": "run1",  # Run number
                "title1": "Rompy Swan configuration",  # Title
            },
            # General settings
            "set": {
                "model_type": "set",
                "level": 0.0,  # Water level
                "depmin": 0.05,  # Minimum water depth (m)
                "direction_convention": "nautical",  # Direction convention (nautical/cartesian)
            },
            # Computation mode
            "mode": {
                "model_type": "mode",
                "kind": "nonstationary",  # Stationary or nonstationary computation
                "dim": "twodimensional",  # 1D or 2D computation
            },
            # Coordinate system
            "coordinates": {
                "model_type": "coordinates",
                "kind": {
                    "model_type": "spherical"  # Spherical (lat/lon) or cartesian coordinates
                },
            },
        },
        # Computational grid definition
        "cgrid": {
            "model_type": "regular",  # Regular rectangular grid
            "spectrum": {
                "mdc": 36,  # Number of directional bins
                "flow": 0.04,  # Lowest frequency (Hz)
                "fhigh": 1.0,  # Highest frequency (Hz)
            },
            "grid": {
                "xp": 110.0,  # Origin x-coordinate (longitude)
                "yp": -35.2,  # Origin y-coordinate (latitude)
                "alp": 4.0,  # Grid rotation angle (degrees)
                "xlen": 7.5,  # Grid width (degrees)
                "ylen": 12.5,  # Grid height (degrees)
                "mx": 14,  # Number of grid cells in x-direction
                "my": 24,  # Number of grid cells in y-direction
            },
        },
        # Input data grids
        "inpgrid": {
            "model_type": "data_interface",
            # Bathymetry data
            "bottom": {
                "var": "bottom",  # Variable name
                "source": {
                    "model_type": "datamesh",
                    "datasource": "our-changing-coast-gebco_1_degree_for_testing",  # Bathymetry source
                    "token": None,  # API token (if needed)
                },
                "fac": -1.0,  # Scaling factor (negative for depth)
                "buffer": 1.0,  # Buffer around domain (degrees)
                "z1": "elevation",  # Variable name in data source
                "coords": {
                    "x": "lon",  # X-coordinate name in data source
                    "y": "lat",  # Y-coordinate name in data source
                },
            },
            # Input forcing data
            "input": [
                {
                    "var": "wind",  # Wind input
                    "source": {
                        "model_type": "datamesh",
                        "datasource": "era5_wind10m",  # ERA5 wind data
                        "token": None,  # API token (if needed)
                    },
                    "buffer": 2.0,  # Buffer around domain (degrees)
                    "filter": {
                        "sort": {
                            "coords": ["latitude"],
                        },
                    },
                    "z1": "u10",  # U-component variable name
                    "z2": "v10",  # V-component variable name
                    "coords": {
                        "x": "longitude",  # X-coordinate name in data source
                        "y": "latitude",  # Y-coordinate name in data source
                    },
                }
            ],
        },
        # Boundary conditions
        "boundary": {
            "model_type": "boundspec",
            "shapespec": {
                "model_type": "shapespec",
                "per_type": "peak",  # Period specification type
                "dspr_type": "degrees",  # Directional spread units
                "shape": {
                    "model_type": "tma",  # TMA spectral shape
                    "gamma": 3.3,  # Peak enhancement factor
                    "d": 12.0,  # Water depth (m)
                },
            },
            "location": {
                "model_type": "side",  # Boundary location type
                "side": "west",  # Side of model domain (north/east/south/west)
            },
            "data": {
                "model_type": "constantpar",  # Constant parameters
                "hs": 2.0,  # Significant wave height (m)
                "per": 12.0,  # Peak period (s)
                "dir": 255.0,  # Mean direction (degrees)
                "dd": 25.0,  # Directional spread (degrees)
            },
        },
        # Initial conditions
        "initial": {
            "kind": {"model_type": "default"}  # Default initial conditions (cold start)
        },
        # Physics parameters
        "physics": {
            "gen": {
                "model_type": "gen3",  # Third-generation physics
                "source_terms": {
                    "model_type": "westhuysen"  # Source terms formulation
                },
            },
            "quadrupl": {"iquad": 2},  # Quadruplet interactions method
            "breaking": {
                "model_type": "constant",  # Depth-induced breaking
                "gamma": 0.73,  # Breaking parameter
            },
            "friction": {
                "model_type": "madsen",  # Bottom friction formulation
                "kn": 0.05,  # Bottom roughness length (m)
            },
            "triad": {"model_type": "triad"},  # Triad wave-wave interactions
        },
        # Numerical propagation scheme
        "prop": {"scheme": {"model_type": "bsbt"}},  # BSBT propagation scheme
        # Numerical parameters
        "numeric": {
            "stop": {
                "model_type": "stopc",  # Stopping criteria
                "dabs": 0.05,  # Absolute Hs difference threshold (m)
                "drel": 0.05,  # Relative Hs difference threshold (fraction)
                "curvat": 0.05,  # Curvature threshold
                "npnts": 95,  # Percentage of points that must converge
                "mode": {
                    "model_type": "nonstat",  # Non-stationary convergence
                    "mxitns": 3,  # Maximum iterations per timestep
                },
            }
        },
        # Output configuration
        "output": {
            # Output locations (points)
            "points": {
                "model_type": "points",
                "sname": "pts",  # Name of output location set
                "xp": [114.0, 112.5, 115.0],  # X-coordinates (longitude)
                "yp": [-34.0, -26.0, -30.0],  # Y-coordinates (latitude)
            },
            # Output quantities definition
            "quantity": {
                "model_type": "quantities",
                "quantities": [
                    {
                        "output": [
                            "depth",
                            "hsign",
                            "tps",
                            "dir",
                            "tm01",
                        ],  # Main wave parameters
                        "excv": -9,  # Exception value for missing data
                    },
                    {
                        "output": ["hswell"],  # Swell component
                        "fswell": 0.125,  # Swell frequency threshold (Hz)
                    },
                ],
            },
            # Grid output file
            "block": {
                "model_type": "block",
                "sname": "COMPGRID",  # Special frame name for computational grid
                "fname": "swangrid.nc",  # Output filename (NetCDF format)
                "output": ["depth", "wind", "hsign", "tps", "dir"],  # Grid variables
                "times": {"dfmt": "hr"},  # Time format (hours)
            },
            # Tabular output file
            "table": {
                "sname": "pts",  # Output location set name
                "format": "header",  # Include header in output
                "fname": "swantable.txt",  # Output filename
                "output": [
                    "time",
                    "hsign",
                    "hswell",
                    "dir",
                    "tps",
                    "tm01",
                ],  # Variables
                "times": {"dfmt": "hr"},  # Time format (hours)
            },
        },
        "lockup": {
            "compute": {
                "model_type": "nonstat",
                "initstat": True,
                "times": {"model_type": "nonstationary", "tfmt": 1, "dfmt": "hr"},
                "hotfile": {"fname": "hotfile.txt", "format": "free"},
                "hottimes": [-1],
            }
        },
    },
}

SCHISM_TEMPLATE = {
    "run_id": "schism_example_run",
    "model_type": "schism",
    "period": {
        "start": "2024-01-01T00:00:00",
        "end": "2024-01-02T00:00:00",
        "dt": 150,
        "nspool": 360,
        "ihfskip": 720,
    },
    "grid": {
        "hgrid_file": "hgrid.gr3",
        "vgrid_file": "vgrid.in",
        "min_depth": 0.5,
        "coordinate_system": "geographic",
    },
    "physics": {
        "baroclinic": True,
        "temperature": True,
        "salinity": True,
        "turbulence": "gotm",
        "bottom_friction": "drag",
        "atmospheric_pressure": True,
        "tides": True,
    },
    "forcing": {
        "atmospheric": {
            "source": "gfs",
            "variables": [
                "wind",
                "pressure",
                "air_temperature",
                "humidity",
                "precipitation",
                "radiation",
            ],
        },
        "ocean_boundary": {
            "source": "hycom",
            "variables": ["elevation", "velocity", "temperature", "salinity"],
        },
        "rivers": {"source": "usgs", "temperature": 15.0},
    },
    "output": {
        "stations": {
            "file": "station.in",
            "variables": ["elevation", "velocity", "temperature", "salinity"],
        },
        "global": {
            "variables": [
                "elevation",
                "velocity",
                "temperature",
                "salinity",
                "turbulence",
            ],
            "format": "netcdf",
        },
    },
}

WW3_TEMPLATE = {
    "run_id": "ww3_example_run",
    "model_type": "ww3",
    "period": {
        "start": "2024-01-01T00:00:00",
        "end": "2024-01-02T00:00:00",
        "dt": 3600,
    },
    "grid": {
        "name": "global_grid",
        "type": "regular",
        "lon_min": -180,
        "lon_max": 180,
        "lat_min": -90,
        "lat_max": 90,
        "resolution": 0.5,
        "closure": "global",
    },
    "physics": {
        "source_terms": {
            "input": "st4",
            "dissipation": "st4",
            "nonlinear": "nl1",
            "bottom": "bt4",
        },
        "propagation": {"scheme": "umb", "refraction": True, "diffraction": False},
        "numerics": {
            "time_step_global": 1800,
            "time_step_spatial": 600,
            "time_step_spectral": 300,
        },
    },
    "forcing": {
        "winds": {"source": "gfs", "format": "grib2", "resolution": 0.25},
        "ice": {"source": "nsidc", "concentration_threshold": 0.5},
        "currents": {"source": "hycom", "resolution": 0.08},
    },
    "output": {
        "fields": {
            "variables": ["hs", "tp", "dp", "tm01", "tm02", "spr", "fp"],
            "interval": 3600,
            "format": "netcdf",
        },
        "spectra": {"points": "spec_points.txt", "interval": 3600, "format": "netcdf"},
        "restart": {"interval": 21600},
    },
}

TEMPLATES = {"swan": SWAN_TEMPLATE, "schism": SCHISM_TEMPLATE, "ww3": WW3_TEMPLATE}


@click.command()
@click.option(
    "--type",
    "model_type",
    type=click.Choice(["swan", "schism", "ww3"]),
    prompt="Which model type would you like to configure",
    help="Ocean/wave model type",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: <model>_config.yml)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@click.option(
    "--interactive", is_flag=True, help="Interactive mode to customize configuration"
)
@click.pass_obj
def init(
    obj: ContextObject,
    model_type: str,
    output: Optional[str],
    output_format: str,
    interactive: bool,
):
    """Initialize a new rompy model configuration.

    Creates a template configuration file for the specified ocean/wave model
    that can be customized and run with 'oceanum rompy run'.

    Examples:
        oceanum rompy init --type swan
        oceanum rompy init --type schism --output my_model.yml
        oceanum rompy init --type ww3 --interactive
    """
    # Get the template
    template = TEMPLATES[model_type].copy()

    # Interactive customization if requested
    if interactive:
        click.echo(f"\n🔧 Customizing {model_type.upper()} configuration...\n")

        # Run ID
        template["run_id"] = click.prompt(
            "Run ID", default=template["run_id"], type=str
        )

        # Time period
        click.echo("\n📅 Time Period Configuration:")
        template["period"]["start"] = click.prompt(
            "  Start time (ISO format)", default=template["period"]["start"], type=str
        )
        template["period"]["end"] = click.prompt(
            "  End time (ISO format)", default=template["period"]["end"], type=str
        )

        # Model-specific customization
        if model_type == "swan":
            click.echo("\n🌊 SWAN Grid Configuration:")
            # Domain configuration
            template["config"]["cgrid"]["grid"]["xp"] = click.prompt(
                "  Longitude origin (left edge)",
                default=template["config"]["cgrid"]["grid"]["xp"],
                type=float,
            )
            template["config"]["cgrid"]["grid"]["yp"] = click.prompt(
                "  Latitude origin",
                default=template["config"]["cgrid"]["grid"]["yp"],
                type=float,
            )
            template["config"]["cgrid"]["grid"]["xlen"] = click.prompt(
                "  Domain width (degrees)",
                default=template["config"]["cgrid"]["grid"]["xlen"],
                type=float,
            )
            template["config"]["cgrid"]["grid"]["ylen"] = click.prompt(
                "  Domain height (degrees)",
                default=template["config"]["cgrid"]["grid"]["ylen"],
                type=float,
            )
            template["config"]["cgrid"]["grid"]["mx"] = click.prompt(
                "  Number of grid cells in x-direction",
                default=template["config"]["cgrid"]["grid"]["mx"],
                type=int,
            )
            template["config"]["cgrid"]["grid"]["my"] = click.prompt(
                "  Number of grid cells in y-direction",
                default=template["config"]["cgrid"]["grid"]["my"],
                type=int,
            )

        elif model_type == "schism":
            click.echo("\n🌊 SCHISM Configuration:")
            template["grid"]["hgrid_file"] = click.prompt(
                "  Horizontal grid file",
                default=template["grid"]["hgrid_file"],
                type=str,
            )
            template["grid"]["vgrid_file"] = click.prompt(
                "  Vertical grid file", default=template["grid"]["vgrid_file"], type=str
            )
            template["physics"]["baroclinic"] = click.confirm(
                "  Enable baroclinic mode?", default=template["physics"]["baroclinic"]
            )

        elif model_type == "ww3":
            click.echo("\n🌊 WW3 Grid Configuration:")
            template["grid"]["resolution"] = click.prompt(
                "  Grid resolution (degrees)",
                default=template["grid"]["resolution"],
                type=float,
            )
            template["grid"]["closure"] = click.prompt(
                "  Grid closure",
                default=template["grid"]["closure"],
                type=click.Choice(["global", "regional"]),
            )

    # Determine output file
    if not output:
        output = f"{model_type}_config.{output_format}"

    output_path = Path(output)

    # Check if file exists
    if output_path.exists():
        if not click.confirm(f"\n⚠️  File '{output}' already exists. Overwrite?"):
            click.echo("Aborted.")
            return

    # Write configuration
    try:
        with open(output_path, "w") as f:
            if output_format == "yaml":
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(template, f, indent=2)

        click.echo(f"\n✅ Created {model_type.upper()} configuration: {output}")

        # Show next steps
        click.echo("\n📝 Next steps:")
        click.echo(f"1. Edit the configuration file: {output}")
        click.echo("2. Prepare your input files (grids, forcing data, etc.)")
        click.echo("3. List available pipelines:")
        click.echo("   oceanum rompy list pipelines")
        click.echo("4. Run the model:")
        click.echo(
            f"   oceanum rompy run {output} --pipeline-name {model_type}-from-rompy"
        )

        # Model-specific tips
        if model_type == "swan":
            click.echo("\n💡 SWAN Tips:")
            click.echo(
                "   - Set appropriate grid resolution based on your domain (typically 0.5-5km)"
            )
            click.echo(
                "   - Adjust spectral resolution (mdc and flow/fhigh) based on your wave conditions"
            )
            click.echo(
                "   - For oceanic applications, add boundary conditions on all exposed sides"
            )
            click.echo(
                "   - For deep water, enable quadruplets; for shallow water, enable triads"
            )
            click.echo(
                "   - Ensure bathymetry data covers your entire domain plus buffer"
            )

        elif model_type == "schism":
            click.echo("\n💡 SCHISM Tips:")
            click.echo("   - Prepare hgrid.gr3 and vgrid.in files for your domain")
            click.echo("   - Configure atmospheric forcing for accurate results")
            click.echo("   - Set appropriate time steps based on grid resolution")

        elif model_type == "ww3":
            click.echo("\n💡 WW3 Tips:")
            click.echo("   - Use 'st4' source terms for latest physics")
            click.echo("   - Configure ice forcing for polar regions")
            click.echo("   - Set spectral resolution based on application")

    except Exception as e:
        raise click.ClickException(f"Failed to write configuration: {e}")


# Export the command
__all__ = ["init"]
