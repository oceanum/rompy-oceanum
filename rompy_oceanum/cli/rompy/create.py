"""Create command for rompy-oceanum CLI."""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from oceanum.cli.models import ContextObject
from oceanum.cli.prax.client import PRAXClient
from oceanum.cli.prax.models import ProjectSpec



logger = logging.getLogger(__name__)

# Common options for create commands
project_option = click.option(
    "--project",
    default="rompy-oceanum",
    help="Prax project name (default: rompy-oceanum)",
)
org_option = click.option(
    "--org",
    help="Prax organization name (overrides oceanum context)",
)
user_option = click.option(
    "--user",
    help="Prax user email (overrides oceanum context)",
)
stage_option = click.option(
    "--stage",
    default="dev",
    help="Prax stage name (default: dev)",
)
name_option = click.option(
    "--name",
    help="Resource name (defaults to filename without extension)",
)


@click.command(name="create", help="Create resources in Prax")
@click.argument("resource_type", type=click.Choice(["project", "pipeline"]))
@click.argument("spec_file", type=click.Path(exists=True), required=False)
@name_option
@project_option
@org_option
@user_option
@stage_option
@click.option(
    "--wait", help="Wait for resource to be deployed", default=True, type=bool
)
@click.pass_context
def create_resource(
    ctx: click.Context,
    resource_type: str,
    spec_file: Optional[str],
    name: Optional[str],
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
    wait: bool,
):
    """Create resources in Prax.

    RESOURCE_TYPE: Type of resource to create (project or pipeline)
    SPEC_FILE: Path to specification file (required for project, optional for pipeline)
    """
    try:
        if resource_type == "project":
            if not spec_file:
                click.echo("❌ Spec file is required for creating projects", err=True)
                sys.exit(1)

            # Load spec
            with open(spec_file, "r") as f:
                spec_data = yaml.safe_load(f)

            # Use provided name or derive from filename
            if not name:
                name = Path(spec_file).stem

            # Set name in spec if not already set
            if "name" not in spec_data:
                spec_data["name"] = name

            # Create PRAXClient with context
            client = PRAXClient(ctx)

            # Convert dict to ProjectSpec and submit project spec
            spec = ProjectSpec(**spec_data)
            result = client.deploy_project(spec)

            click.echo(f"✅ Project '{name}' created successfully")
            click.echo(f"📝 Project details: {result}")

        elif resource_type == "pipeline":
            if spec_file:
                # Deploy pipeline from spec file
                with open(spec_file, "r") as f:
                    spec_data = yaml.safe_load(f)

                # Use provided name or derive from filename
                if not name:
                    name = Path(spec_file).stem

                # Set name in spec if not already set
                if "name" not in spec_data:
                    spec_data["name"] = name

                # Create PRAXClient with oceanum context for proper URL construction
                client = PRAXClient(ctx)

                # Convert dict to ProjectSpec
                spec = ProjectSpec(**spec_data)
                # Submit pipeline template
                result = client.deploy_project(spec)

                click.echo(
                    f"✅ Pipeline '{name}' created successfully in project '{project}'"
                )
                click.echo(f"📝 Pipeline details: {result}")
            else:
                # Deploy default pipeline
                click.echo(
                    f"🚀 Deploying default pipeline template to project: {project}"
                )

                # Get the path to the default template
                template_path = (
                    Path(__file__).parent.parent.parent
                    / "pipeline_templates"
                    / "swan.yaml"
                )

                if not template_path.exists():
                    click.echo(
                        f"❌ Default template not found at {template_path}", err=True
                    )
                    sys.exit(1)

                # Load template
                with open(template_path, "r") as f:
                    spec_data = yaml.safe_load(f)

                # Create PRAXClient with oceanum context for proper URL construction
                client = PRAXClient(ctx)

                # Convert dict to ProjectSpec
                spec = ProjectSpec(**spec_data)
                # Submit pipeline template
                result = client.deploy_project(spec)

                # Check for error response
                if hasattr(result, "detail") and "Not Found" in str(result.detail):
                    click.echo(f"❌ Failed to deploy pipeline: {result.detail}", err=True)
                    sys.exit(1)

                click.echo("✅ Default pipeline template deployed successfully!")
                click.echo(
                    f"💡 You can now run models using: oceanum rompy run config.yml swan --pipeline-name swan-from-rompy --project {project}"
                )

    except Exception as e:
        click.echo(f"❌ Failed to create {resource_type}: {e}", err=True)
        sys.exit(1)
