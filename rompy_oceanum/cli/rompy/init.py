"""Init command for creating new rompy configurations."""

import json
from pathlib import Path
from typing import Optional

import click
import yaml
from oceanum.cli.common.models import ContextObject


# Template configurations for different model types
SWAN_TEMPLATE = {
    "run_id": "swan_example_run",
    "model_type": "swan",
    "period": {
        "start": "2024-01-01T00:00:00",
        "end": "2024-01-02T00:00:00",
        "interval": "1H"
    },
    "output": {
        "grid": {
            "type": "regular",
            "lon_min": -180,
            "lon_max": -170,
            "lat_min": 20,
            "lat_max": 30,
            "resolution": 0.1
        },
        "variables": ["hs", "tp", "dir", "tm01"],
        "format": "netcdf"
    },
    "physics": {
        "gen": 3,
        "whitecapping": "komen",
        "quadruplets": True,
        "triads": True,
        "breaking": True,
        "friction": "jonswap",
        "diffraction": False
    },
    "forcing": {
        "winds": {
            "source": "gfs",
            "resolution": 0.25
        },
        "waves": {
            "source": "ww3",
            "resolution": 0.5
        },
        "currents": {
            "source": "hycom",
            "resolution": 0.08
        }
    },
    "computational": {
        "dt": 600,
        "npnts": 95,
        "cgrid": {
            "resolution": 0.05,
            "ntheta": 36,
            "nfreq": 35
        }
    }
}

SCHISM_TEMPLATE = {
    "run_id": "schism_example_run",
    "model_type": "schism",
    "period": {
        "start": "2024-01-01T00:00:00",
        "end": "2024-01-02T00:00:00",
        "dt": 150,
        "nspool": 360,
        "ihfskip": 720
    },
    "grid": {
        "hgrid_file": "hgrid.gr3",
        "vgrid_file": "vgrid.in",
        "min_depth": 0.5,
        "coordinate_system": "geographic"
    },
    "physics": {
        "baroclinic": True,
        "temperature": True,
        "salinity": True,
        "turbulence": "gotm",
        "bottom_friction": "drag",
        "atmospheric_pressure": True,
        "tides": True
    },
    "forcing": {
        "atmospheric": {
            "source": "gfs",
            "variables": ["wind", "pressure", "air_temperature", "humidity", "precipitation", "radiation"]
        },
        "ocean_boundary": {
            "source": "hycom",
            "variables": ["elevation", "velocity", "temperature", "salinity"]
        },
        "rivers": {
            "source": "usgs",
            "temperature": 15.0
        }
    },
    "output": {
        "stations": {
            "file": "station.in",
            "variables": ["elevation", "velocity", "temperature", "salinity"]
        },
        "global": {
            "variables": ["elevation", "velocity", "temperature", "salinity", "turbulence"],
            "format": "netcdf"
        }
    }
}

WW3_TEMPLATE = {
    "run_id": "ww3_example_run",
    "model_type": "ww3",
    "period": {
        "start": "2024-01-01T00:00:00",
        "end": "2024-01-02T00:00:00",
        "dt": 3600
    },
    "grid": {
        "name": "global_grid",
        "type": "regular",
        "lon_min": -180,
        "lon_max": 180,
        "lat_min": -90,
        "lat_max": 90,
        "resolution": 0.5,
        "closure": "global"
    },
    "physics": {
        "source_terms": {
            "input": "st4",
            "dissipation": "st4",
            "nonlinear": "nl1",
            "bottom": "bt4"
        },
        "propagation": {
            "scheme": "umb",
            "refraction": True,
            "diffraction": False
        },
        "numerics": {
            "time_step_global": 1800,
            "time_step_spatial": 600,
            "time_step_spectral": 300
        }
    },
    "forcing": {
        "winds": {
            "source": "gfs",
            "format": "grib2",
            "resolution": 0.25
        },
        "ice": {
            "source": "nsidc",
            "concentration_threshold": 0.5
        },
        "currents": {
            "source": "hycom",
            "resolution": 0.08
        }
    },
    "output": {
        "fields": {
            "variables": ["hs", "tp", "dp", "tm01", "tm02", "spr", "fp"],
            "interval": 3600,
            "format": "netcdf"
        },
        "spectra": {
            "points": "spec_points.txt",
            "interval": 3600,
            "format": "netcdf"
        },
        "restart": {
            "interval": 21600
        }
    }
}

TEMPLATES = {
    "swan": SWAN_TEMPLATE,
    "schism": SCHISM_TEMPLATE,
    "ww3": WW3_TEMPLATE
}


@click.command()
@click.option(
    "--type",
    "model_type",
    type=click.Choice(["swan", "schism", "ww3"]),
    prompt="Which model type would you like to configure",
    help="Ocean/wave model type"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: <model>_config.yml)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format"
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Interactive mode to customize configuration"
)
@click.pass_obj
def init(
    obj: ContextObject,
    model_type: str,
    output: Optional[str],
    output_format: str,
    interactive: bool
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
            "Run ID",
            default=template["run_id"],
            type=str
        )

        # Time period
        click.echo("\n📅 Time Period Configuration:")
        template["period"]["start"] = click.prompt(
            "  Start time (ISO format)",
            default=template["period"]["start"],
            type=str
        )
        template["period"]["end"] = click.prompt(
            "  End time (ISO format)",
            default=template["period"]["end"],
            type=str
        )

        # Model-specific customization
        if model_type == "swan":
            click.echo("\n🌊 SWAN Grid Configuration:")
            template["output"]["grid"]["lon_min"] = click.prompt(
                "  Longitude min",
                default=template["output"]["grid"]["lon_min"],
                type=float
            )
            template["output"]["grid"]["lon_max"] = click.prompt(
                "  Longitude max",
                default=template["output"]["grid"]["lon_max"],
                type=float
            )
            template["output"]["grid"]["lat_min"] = click.prompt(
                "  Latitude min",
                default=template["output"]["grid"]["lat_min"],
                type=float
            )
            template["output"]["grid"]["lat_max"] = click.prompt(
                "  Latitude max",
                default=template["output"]["grid"]["lat_max"],
                type=float
            )
            template["output"]["grid"]["resolution"] = click.prompt(
                "  Resolution (degrees)",
                default=template["output"]["grid"]["resolution"],
                type=float
            )

        elif model_type == "schism":
            click.echo("\n🌊 SCHISM Configuration:")
            template["grid"]["hgrid_file"] = click.prompt(
                "  Horizontal grid file",
                default=template["grid"]["hgrid_file"],
                type=str
            )
            template["grid"]["vgrid_file"] = click.prompt(
                "  Vertical grid file",
                default=template["grid"]["vgrid_file"],
                type=str
            )
            template["physics"]["baroclinic"] = click.confirm(
                "  Enable baroclinic mode?",
                default=template["physics"]["baroclinic"]
            )

        elif model_type == "ww3":
            click.echo("\n🌊 WW3 Grid Configuration:")
            template["grid"]["resolution"] = click.prompt(
                "  Grid resolution (degrees)",
                default=template["grid"]["resolution"],
                type=float
            )
            template["grid"]["closure"] = click.prompt(
                "  Grid closure",
                default=template["grid"]["closure"],
                type=click.Choice(["global", "regional"])
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
        with open(output_path, 'w') as f:
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
        click.echo(f"   oceanum rompy run {output} --pipeline-name {model_type}-from-rompy")

        # Model-specific tips
        if model_type == "swan":
            click.echo("\n💡 SWAN Tips:")
            click.echo("   - Use 'gen: 3' for third-generation mode")
            click.echo("   - Enable 'quadruplets' for deep water applications")
            click.echo("   - Set appropriate grid resolution based on your domain")

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
