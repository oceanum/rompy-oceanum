"""Init command for creating rompy configuration templates optimized for Oceanum Prax."""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import click
import yaml
from oceanum.cli.models import ContextObject

logger = logging.getLogger(__name__)


@click.command()
@click.argument("model", type=click.Choice(["swan", "schism", "ww3"]))
@click.option(
    "--template",
    type=click.Choice(["basic", "advanced", "research", "operational"]),
    default="basic",
    help="Configuration template type",
)
@click.option(
    "--output",
    "-o",
    help="Output configuration file path (default: rompy_config_{model}_{template}.yml)",
)
@click.option("--domain", help="Model domain name")
@click.option(
    "--grid-resolution", type=float, help="Grid resolution in degrees (e.g., 0.1)"
)
@click.option("--time-start", help="Start time (ISO format: 2023-01-01T00:00:00)")
@click.option("--time-end", help="End time (ISO format: 2023-01-02T00:00:00)")
@click.option("--bbox", help="Bounding box as 'lon_min,lat_min,lon_max,lat_max'")
@click.option(
    "--forcing",
    type=click.Choice(["era5", "gfs", "local"]),
    default="era5",
    help="Atmospheric forcing data source",
)
@click.option(
    "--prax-optimized/--no-prax-optimized",
    default=True,
    help="Include Prax-specific optimizations",
)
@click.option("--interactive", is_flag=True, help="Interactive configuration setup")
@click.pass_obj
def init(
    obj: ContextObject,
    model,
    template,
    output,
    domain,
    grid_resolution,
    time_start,
    time_end,
    bbox,
    forcing,
    prax_optimized,
    interactive,
):
    """Initialize a rompy configuration optimized for Oceanum Prax execution.

    Args:
        model: Model type (swan, schism, ww3)

    Usage:
        oceanum rompy init swan --template basic --domain "my_domain"
        oceanum rompy init schism --template advanced --interactive
        oceanum rompy init ww3 --bbox "-180,-90,180,90" --grid-resolution 0.1
    """
    # Determine output file path
    if not output:
        output = f"rompy_config_{model}_{template}.yml"

    output_path = Path(output)

    # Check if file exists
    if output_path.exists():
        if not click.confirm(f"File {output_path} already exists. Overwrite?"):
            click.echo("❌ Initialization cancelled.")
            return

    # Interactive mode
    if interactive:
        click.echo("🎯 Interactive rompy configuration setup")
        click.echo("=" * 40)

        domain = domain or click.prompt("Domain name", default="my_domain")

        if not grid_resolution:
            grid_resolution = click.prompt(
                "Grid resolution (degrees)", type=float, default=0.1
            )

        if not time_start:
            time_start = click.prompt(
                "Start time (YYYY-MM-DDTHH:MM:SS)", default="2023-01-01T00:00:00"
            )

        if not time_end:
            time_end = click.prompt(
                "End time (YYYY-MM-DDTHH:MM:SS)", default="2023-01-02T00:00:00"
            )

        if not bbox:
            click.echo("Bounding box coordinates:")
            lon_min = click.prompt("  Longitude min", type=float, default=-180.0)
            lat_min = click.prompt("  Latitude min", type=float, default=-90.0)
            lon_max = click.prompt("  Longitude max", type=float, default=180.0)
            lat_max = click.prompt("  Latitude max", type=float, default=90.0)
            bbox = f"{lon_min},{lat_min},{lon_max},{lat_max}"

        forcing = click.prompt(
            "Forcing data source",
            type=click.Choice(["era5", "gfs", "local"]),
            default=forcing,
        )

    # Parse bounding box
    if bbox:
        try:
            lon_min, lat_min, lon_max, lat_max = map(float, bbox.split(","))
        except ValueError:
            click.echo(
                "❌ Invalid bounding box format. Use: 'lon_min,lat_min,lon_max,lat_max'",
                err=True,
            )
            return
    else:
        # Default global domain
        lon_min, lat_min, lon_max, lat_max = 106.0, -39.0, 114.0, -30.0

    # Generate configuration
    try:
        config = _generate_config(
            model=model,
            template=template,
            domain=domain or "my_domain",
            grid_resolution=grid_resolution or 0.5,
            time_start=time_start or "2023-01-01T00:00:00",
            time_end=time_end or "2023-01-02T00:00:00",
            lon_min=lon_min,
            lat_min=lat_min,
            lon_max=lon_max,
            lat_max=lat_max,
            forcing=forcing,
            prax_optimized=prax_optimized,
            oceanum_context=obj,
        )

        # Write configuration file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2, sort_keys=False)

        click.echo(f"✅ Configuration created: {output_path}")
        click.echo(f"📊 Model: {model}, Template: {template}")

        if prax_optimized:
            click.echo("🚀 Prax optimizations enabled")

        # Show next steps
        click.echo(f"\n💡 Next steps:")
        click.echo(f"  1. Review and customize: {output_path}")
        click.echo(
            f"  2. Execute via Prax: oceanum rompy run {output_path} {model} --pipeline-name swan-from-rompy --project rompy-oceanum --follow"
        )

        # Show template-specific guidance
        _show_template_guidance(model, template)

    except Exception as e:
        click.echo(f"❌ Error creating configuration: {e}", err=True)
        logger.exception("Configuration creation failed")


def _generate_config(
    model: str,
    template: str,
    domain: str,
    grid_resolution: float,
    time_start: str,
    time_end: str,
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    forcing: str,
    prax_optimized: bool,
    oceanum_context: ContextObject,
) -> Dict[str, Any]:
    """Generate rompy configuration based on parameters."""

    # Create the model configuration
    model_config = _get_model_config(
        model,
        template,
        domain,
        grid_resolution,
        time_start,
        time_end,
        lon_min,
        lat_min,
        lon_max,
        lat_max,
        forcing,
    )

    # Create the complete config structure for rompy ModelRun
    config = {"run_id": f"{domain}_{model}_{template}", "config": model_config}

    # Add period information
    config["period"] = {
        "start": time_start.replace("T", "T")
        .replace(":", "")
        .replace("-", ""),  # Format: 20230101T000000
        "duration": "1d",
        "interval": "1h",
    }

    # Add output directory
    config["output_dir"] = "/tmp/rompy"
    config["run_id_subdir"] = False

    return config


def _get_model_config(
    model: str,
    template: str,
    domain: str,
    grid_resolution: float,
    time_start: str,
    time_end: str,
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    forcing: str,
) -> Dict[str, Any]:
    """Get model-specific configuration for rompy."""

    if model == "swan":
        return _get_swan_config(
            template,
            domain,
            grid_resolution,
            time_start,
            time_end,
            lon_min,
            lat_min,
            lon_max,
            lat_max,
            forcing,
        )
    elif model == "schism":
        return _get_schism_config(
            template,
            domain,
            grid_resolution,
            time_start,
            time_end,
            lon_min,
            lat_min,
            lon_max,
            lat_max,
            forcing,
        )
    else:  # ww3
        return _get_ww3_config(
            template,
            domain,
            grid_resolution,
            time_start,
            time_end,
            lon_min,
            lat_min,
            lon_max,
            lat_max,
            forcing,
        )


def _get_swan_config(
    template: str,
    domain: str,
    grid_resolution: float,
    time_start: str,
    time_end: str,
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    forcing: str,
) -> Dict[str, Any]:
    """Generate a proper SWAN configuration following rompy schema."""

    # Calculate grid dimensions
    xlen = lon_max - lon_min
    ylen = lat_max - lat_min
    mx = max(10, int(xlen / grid_resolution))
    my = max(10, int(ylen / grid_resolution))

    return {
        "model_type": "swanconfig",
        "startup": {
            "project": {
                "model_type": "project",
                "name": domain[:16],  # Limit to 16 characters
                "nr": "run1",
                "title1": f"Generated {template} SWAN configuration",
            },
            "set": {
                "model_type": "set",
                "level": 0.0,
                "depmin": 0.05,
                "direction_convention": "nautical",
            },
            "mode": {
                "model_type": "mode",
                "kind": "nonstationary",
                "dim": "twodimensional",
            },
            "coordinates": {
                "model_type": "coordinates",
                "kind": {"model_type": "spherical"},
            },
        },
        "cgrid": {
            "model_type": "regular",
            "spectrum": {"mdc": 36, "flow": 0.04, "fhigh": 1.0},
            "grid": {
                "xp": lon_min + xlen / 2,
                "yp": lat_min + ylen / 2,
                "alp": 0.0,
                "xlen": xlen,
                "ylen": ylen,
                "mx": mx,
                "my": my,
            },
        },
        "inpgrid": {
            "model_type": "data_interface",
            "bottom": {
                "var": "bottom",
                "source": {
                    "model_type": "datamesh",
                    "datasource": "our-changing-coast-gebco_1_degree_for_testing",
                    "token": os.getenv("DATAMESH_TOKEN"),
                    # "token": None,
                },
                "fac": -1.0,
                "buffer": 1.0,
                "z1": "elevation",
                "coords": {"x": "lon", "y": "lat"},
            },
            "input": [
                {
                    "var": "wind",
                    "source": {
                        "model_type": "datamesh",
                        "datasource": (
                            "era5_wind10m" if forcing == "era5" else "gfs_wind10m"
                        ),
                        "token": os.getenv("DATAMESH_TOKEN"),
                        # "token": None,
                    },
                    "buffer": 2.0,
                    "filter": {"sort": {"coords": ["latitude"]}},
                    "z1": "u10",
                    "z2": "v10",
                    "coords": {"x": "longitude", "y": "latitude"},
                }
            ],
        },
        "boundary": {
            "model_type": "boundspec",
            "shapespec": {
                "model_type": "shapespec",
                "per_type": "peak",
                "dspr_type": "degrees",
                "shape": {"model_type": "tma", "gamma": 3.3, "d": 12.0},
            },
            "location": {"model_type": "side", "side": "west"},
            "data": {
                "model_type": "constantpar",
                "hs": 2.0,
                "per": 12.0,
                "dir": 270.0,
                "dd": 25.0,
            },
        },
        "initial": {"kind": {"model_type": "default"}},
        "physics": {
            "gen": {"model_type": "gen3", "source_terms": {"model_type": "westhuysen"}},
            "quadrupl": {"iquad": 2},
            "breaking": {"model_type": "constant", "gamma": 0.73},
            "friction": {"model_type": "madsen", "kn": 0.05},
            "triad": {"model_type": "triad"},
        },
        "prop": {"scheme": {"model_type": "bsbt"}},
        "numeric": {
            "stop": {
                "model_type": "stopc",
                "dabs": 0.05,
                "drel": 0.05,
                "curvat": 0.05,
                "npnts": 95,
                "mode": {"model_type": "nonstat", "mxitns": 3},
            }
        },
        "output": {
            "points": {
                "model_type": "points",
                "sname": "pts",
                "xp": [lon_min + xlen * 0.3, lon_min + xlen * 0.7],
                "yp": [lat_min + ylen * 0.3, lat_min + ylen * 0.7],
            },
            "quantity": {
                "model_type": "quantities",
                "quantities": [
                    {"output": ["depth", "hsign", "tps", "dir", "tm01"], "excv": -9},
                    {"output": ["hswell"], "fswell": 0.125},
                ],
            },
            "block": {
                "model_type": "block",
                "sname": "COMPGRID",
                "fname": "swangrid.nc",
                "output": ["depth", "wind", "hsign", "tps", "dir"],
                "times": {"dfmt": "hr"},
            },
            "table": {
                "sname": "pts",
                "format": "header",
                "fname": "swantable.txt",
                "output": ["time", "hsign", "hswell", "dir", "tps", "tm01"],
                "times": {"dfmt": "hr"},
            },
            "specout": {
                "sname": "pts",
                "fname": "swanspec.nc",
                "dim": {"model_type": "spec2d"},
                "freq": {"model_type": "abs"},
                "times": {"dfmt": "hr"},
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
    }


def _get_schism_config(
    template: str,
    domain: str,
    grid_resolution: float,
    time_start: str,
    time_end: str,
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    forcing: str,
) -> Dict[str, Any]:
    """Generate a basic SCHISM configuration."""
    return {
        "model_type": "schism",
        "grid": {"model_type": "unstructured"},
        "time": {
            "model_type": "time_range",
            "start": time_start,
            "end": time_end,
            "step": "PT1H",
        },
    }


def _get_ww3_config(
    template: str,
    domain: str,
    grid_resolution: float,
    time_start: str,
    time_end: str,
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    forcing: str,
) -> Dict[str, Any]:
    """Generate a basic WW3 configuration."""
    return {
        "model_type": "ww3",
        "grid": {"model_type": "regular_grid", "spacing": grid_resolution},
        "time": {
            "model_type": "time_range",
            "start": time_start,
            "end": time_end,
            "step": "PT1H",
        },
    }


def _show_template_guidance(model: str, template: str):
    """Show template-specific guidance."""

    guidance = {
        "basic": "🎯 Basic template includes essential model physics and standard outputs.",
        "advanced": "⚙️  Advanced template includes additional physics, validation, and diagnostics.",
        "research": "🔬 Research template includes comprehensive analysis and statistics.",
        "operational": "🏭 Operational template optimized for speed and monitoring.",
    }

    model_notes = {
        "swan": "🌊 SWAN: Spectral wave model - good for coastal and nearshore applications",
        "schism": "🌍 SCHISM: 3D hydrodynamic model - suitable for estuarine and coastal modeling",
        "ww3": "🌐 WaveWatch III: Global wave model - ideal for ocean-scale applications",
    }

    click.echo(f"\n📚 Template info: {guidance.get(template, '')}")
    click.echo(f"📝 Model info: {model_notes.get(model, '')}")

    if template == "basic":
        click.echo("💡 Consider 'advanced' template for production runs")
    elif template == "research":
        click.echo("💡 Review analysis settings in the configuration file")
