Advanced Workflows
==================

This guide covers advanced patterns and techniques for implementing complex wave modeling workflows with rompy-oceanum. Learn how to automate model execution, implement batch processing, ensemble modeling, and operational forecasting systems.

Overview
--------

Advanced workflows in rompy-oceanum enable sophisticated modeling patterns including:

* **Batch Processing**: Execute multiple model configurations in parallel or sequence
* **Ensemble Modeling**: Run multiple model variants with different parameters
* **Operational Forecasting**: Automated model execution for real-time forecasting
* **Data Pipeline Integration**: Seamless integration with data processing workflows
* **Conditional Execution**: Dynamic workflow control based on results and conditions

Batch Processing
----------------

Execute multiple wave models efficiently using batch processing patterns.

Basic Batch Execution
~~~~~~~~~~~~~~~~~~~~~

Process multiple configurations in parallel:

.. code-block:: python

   import asyncio
   from rompy_oceanum import BatchProcessor
   from rompy_oceanum.backends import PraxConfig

   async def run_batch_models():
       # Define multiple model configurations
       configs = [
           {"grid": "north_sea", "forcing": "era5"},
           {"grid": "atlantic", "forcing": "gfs"},
           {"grid": "pacific", "forcing": "ecmwf"}
       ]

       # Configure batch processor
       batch_processor = BatchProcessor(
           backend="prax",
           backend_config=PraxConfig(
               org="your-org",
               project="wave-forecasting",
               stage="prod"
           ),
           max_concurrent=3
       )

       # Execute batch
       results = await batch_processor.run_batch(configs)

       # Process results
       for config, result in zip(configs, results):
           if result.is_successful():
               print(f"✓ {config['grid']} completed successfully")
           else:
               print(f"✗ {config['grid']} failed: {result.error_message}")

   # Run the batch
   asyncio.run(run_batch_models())

Sequential Processing
~~~~~~~~~~~~~~~~~~~~~

When models depend on each other or resources are limited:

.. code-block:: python

   from rompy_oceanum import SequentialProcessor

   def run_sequential_workflow():
       # Define workflow stages
       stages = [
           {
               "name": "preprocessing",
               "config": preprocess_config,
               "dependencies": []
           },
           {
               "name": "coarse_grid",
               "config": coarse_grid_config,
               "dependencies": ["preprocessing"]
           },
           {
               "name": "fine_grid",
               "config": fine_grid_config,
               "dependencies": ["coarse_grid"]
           }
       ]

       processor = SequentialProcessor(backend="prax")
       results = processor.run_workflow(stages)

       return results

Conditional Batch Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Execute batches based on conditions:

.. code-block:: python

   from rompy_oceanum import ConditionalBatch
   from datetime import datetime, timedelta

   def run_conditional_forecast():
       # Check if new forcing data is available
       forcing_check = check_latest_forcing_data()

       if forcing_check.is_updated():
           # Define forecast ensemble
           ensemble_configs = generate_ensemble_configs(
               base_config=operational_config,
               perturbations=[
                   {"wind_speed_factor": 1.1},
                   {"wind_speed_factor": 0.9},
                   {"wave_height_bias": 0.1},
                   {"wave_height_bias": -0.1}
               ]
           )

           # Execute ensemble
           batch = ConditionalBatch(
               condition=lambda: forcing_check.is_updated(),
               retry_interval=timedelta(hours=6),
               max_retries=4
           )

           results = batch.execute(ensemble_configs)
           return results

Ensemble Modeling
-----------------

Implement ensemble modeling for uncertainty quantification and improved forecasts.

Parameter Ensemble
~~~~~~~~~~~~~~~~~~

Vary model parameters systematically:

.. code-block:: python

   from rompy_oceanum import EnsembleManager
   from itertools import product

   def create_parameter_ensemble():
       # Define parameter ranges
       wind_factors = [0.8, 0.9, 1.0, 1.1, 1.2]
       friction_coeffs = [0.01, 0.015, 0.02, 0.025, 0.03]

       # Generate all combinations
       ensemble_configs = []
       for wind_factor, friction in product(wind_factors, friction_coeffs):
           config = base_config.copy()
           config.update({
               "physics": {
                   "wind_drag_coefficient": wind_factor * base_wind_drag,
                   "bottom_friction": friction
               },
               "ensemble_member": f"wind_{wind_factor}_friction_{friction}"
           })
           ensemble_configs.append(config)

       # Execute ensemble
       ensemble = EnsembleManager(
           backend="prax",
           ensemble_name="parameter_sensitivity",
           max_concurrent=10
       )

       results = ensemble.run(ensemble_configs)
       return ensemble.analyze_results(results)

Forcing Ensemble
~~~~~~~~~~~~~~~~

Use multiple forcing datasets:

.. code-block:: python

   def create_forcing_ensemble():
       forcing_sources = [
           {"name": "era5", "source": "era5_winds.nc"},
           {"name": "gfs", "source": "gfs_winds.nc"},
           {"name": "ecmwf", "source": "ecmwf_winds.nc"}
       ]

       ensemble_configs = []
       for forcing in forcing_sources:
           config = base_config.copy()
           config["forcing"]["wind_file"] = forcing["source"]
           config["ensemble_member"] = forcing["name"]
           ensemble_configs.append(config)

       return ensemble_configs

Multi-Model Ensemble
~~~~~~~~~~~~~~~~~~~~

Combine different wave models:

.. code-block:: python

   def create_multi_model_ensemble():
       models = [
           {"type": "swan", "config": swan_config},
           {"type": "wavewatch3", "config": ww3_config},
           {"type": "mike21", "config": mike_config}
       ]

       ensemble_results = {}
       for model in models:
           result = run_model(
               config=model["config"],
               backend="prax",
               pipeline_name=f"ensemble_{model['type']}"
           )
           ensemble_results[model["type"]] = result

       # Combine results
       combined_forecast = combine_ensemble_results(ensemble_results)
       return combined_forecast

Operational Forecasting
-----------------------

Implement automated operational forecasting systems.

Scheduled Execution
~~~~~~~~~~~~~~~~~~~

Set up automated model runs:

.. code-block:: python

   from rompy_oceanum import ScheduledForecaster
   from crontab import CronTab

   class OperationalForecaster:
       def __init__(self):
           self.forecaster = ScheduledForecaster(
               schedule="0 */6 * * *",  # Every 6 hours
               backend="prax",
               backend_config=PraxConfig(
                   org="operational",
                   project="wave-forecast",
                   stage="prod"
               )
           )

       def setup_operational_forecast(self):
           # Configure forecast chain
           forecast_chain = [
               {
                   "name": "data_ingestion",
                   "task": self.ingest_latest_forcing,
                   "timeout": 1800  # 30 minutes
               },
               {
                   "name": "quality_control",
                   "task": self.validate_forcing_data,
                   "dependencies": ["data_ingestion"]
               },
               {
                   "name": "wave_forecast",
                   "task": self.run_wave_model,
                   "dependencies": ["quality_control"]
               },
               {
                   "name": "post_processing",
                   "task": self.process_outputs,
                   "dependencies": ["wave_forecast"]
               },
               {
                   "name": "dissemination",
                   "task": self.publish_results,
                   "dependencies": ["post_processing"]
               }
           ]

           self.forecaster.register_workflow(forecast_chain)

       def ingest_latest_forcing(self):
           """Download latest forcing data."""
           # Implementation for data ingestion
           pass

       def validate_forcing_data(self):
           """Validate forcing data quality."""
           # Implementation for QC
           pass

       def run_wave_model(self):
           """Execute wave model forecast."""
           config = self.generate_forecast_config()
           result = self.forecaster.submit_model(config)
           return result

       def process_outputs(self):
           """Post-process model outputs."""
           # Implementation for post-processing
           pass

       def publish_results(self):
           """Publish results to stakeholders."""
           # Implementation for dissemination
           pass

Real-time Monitoring
~~~~~~~~~~~~~~~~~~~~

Monitor operational forecasts in real-time:

.. code-block:: python

   from rompy_oceanum import ForecastMonitor
   import logging

   class OperationalMonitor:
       def __init__(self):
           self.monitor = ForecastMonitor(
               check_interval=300,  # 5 minutes
               alert_channels=["email", "slack"]
           )

       def setup_monitoring(self):
           # Define monitoring rules
           rules = [
               {
                   "name": "forecast_delay",
                   "condition": lambda run: run.age_hours > 12,
                   "severity": "critical",
                   "action": self.alert_forecast_delay
               },
               {
                   "name": "model_failure",
                   "condition": lambda run: run.status == "failed",
                   "severity": "high",
                   "action": self.handle_model_failure
               },
               {
                   "name": "resource_usage",
                   "condition": lambda run: run.cpu_usage > 0.9,
                   "severity": "medium",
                   "action": self.scale_resources
               }
           ]

           self.monitor.add_rules(rules)

       def alert_forecast_delay(self, run):
           """Handle forecast delays."""
           message = f"Forecast {run.id} delayed by {run.age_hours} hours"
           self.monitor.send_alert(message, severity="critical")

       def handle_model_failure(self, run):
           """Handle model execution failures."""
           # Attempt automatic recovery
           if run.retry_count < 3:
               run.retry()
           else:
               self.monitor.send_alert(
                   f"Model {run.id} failed after 3 retries",
                   severity="high"
               )

       def scale_resources(self, run):
           """Scale resources for high-usage runs."""
           run.scale_resources(cpu="8000m", memory="16Gi")

Data Pipeline Integration
-------------------------

Integrate wave modeling with broader data processing pipelines.

Apache Airflow Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use Airflow for complex workflow orchestration:

.. code-block:: python

   from airflow import DAG
   from airflow.operators.python_operator import PythonOperator
   from rompy_oceanum.integrations.airflow import RompyOperator
   from datetime import datetime, timedelta

   # Define DAG
   dag = DAG(
       'wave_forecast_pipeline',
       default_args={
           'owner': 'wave-team',
           'depends_on_past': False,
           'start_date': datetime(2025, 1, 1),
           'retries': 2,
           'retry_delay': timedelta(minutes=30)
       },
       schedule_interval='0 */6 * * *',  # Every 6 hours
       catchup=False
   )

   # Data ingestion task
   ingest_forcing = PythonOperator(
       task_id='ingest_forcing_data',
       python_callable=download_forcing_data,
       dag=dag
   )

   # Wave model execution
   run_wave_model = RompyOperator(
       task_id='run_wave_forecast',
       config_template='templates/operational_forecast.yml',
       backend='prax',
       pipeline_name='airflow_wave_forecast',
       dag=dag
   )

   # Post-processing
   process_results = PythonOperator(
       task_id='process_results',
       python_callable=process_wave_outputs,
       dag=dag
   )

   # Set dependencies
   ingest_forcing >> run_wave_model >> process_results

Prefect Integration
~~~~~~~~~~~~~~~~~~~

Use Prefect for modern workflow orchestration:

.. code-block:: python

   import prefect
   from prefect import Flow, task
   from rompy_oceanum.integrations.prefect import rompy_task

   @task
   def prepare_forcing_data():
       """Prepare forcing data for wave model."""
       # Data preparation logic
       return forcing_config

   @rompy_task
   def run_wave_forecast(forcing_config):
       """Execute wave forecast model."""
       config = generate_model_config(forcing_config)
       return config

   @task
   def validate_outputs(model_result):
       """Validate model outputs."""
       if not model_result.is_successful():
           raise ValueError("Model execution failed")

       # Validation logic
       return model_result

   # Create flow
   with Flow("Wave Forecast Pipeline") as flow:
       forcing = prepare_forcing_data()
       forecast = run_wave_forecast(forcing)
       validated = validate_outputs(forecast)

   # Register and run
   flow.register(project_name="wave-forecasting")

Error Handling and Recovery
---------------------------

Implement robust error handling for production workflows.

Retry Strategies
~~~~~~~~~~~~~~~~

Configure intelligent retry mechanisms:

.. code-block:: python

   from rompy_oceanum import RetryManager
   from tenacity import retry, stop_after_attempt, wait_exponential

   class RobustWorkflow:
       def __init__(self):
           self.retry_manager = RetryManager(
               max_attempts=3,
               backoff_strategy="exponential",
               base_delay=60  # 1 minute
           )

       @retry(
           stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=4, max=10)
       )
       def execute_with_retry(self, config):
           """Execute model with automatic retry."""
           try:
               result = self.run_model(config)
               if not result.is_successful():
                   raise ModelExecutionError(f"Model failed: {result.error}")
               return result
           except Exception as e:
               logging.error(f"Model execution failed: {e}")
               raise

Circuit Breaker Pattern
~~~~~~~~~~~~~~~~~~~~~~~

Prevent cascade failures:

.. code-block:: python

   from rompy_oceanum import CircuitBreaker

   class ProtectedWorkflow:
       def __init__(self):
           self.circuit_breaker = CircuitBreaker(
               failure_threshold=5,
               recovery_timeout=300,  # 5 minutes
               expected_exception=ModelExecutionError
           )

       def execute_protected(self, config):
           """Execute with circuit breaker protection."""
           with self.circuit_breaker:
               return self.run_model(config)

Performance Optimization
------------------------

Optimize workflow performance for production use.

Resource Management
~~~~~~~~~~~~~~~~~~~

Optimize resource allocation:

.. code-block:: python

   from rompy_oceanum import ResourceOptimizer

   class OptimizedWorkflow:
       def __init__(self):
           self.optimizer = ResourceOptimizer()

       def optimize_batch_resources(self, configs):
           """Optimize resource allocation for batch processing."""
           # Analyze configurations
           resource_requirements = []
           for config in configs:
               req = self.optimizer.estimate_resources(config)
               resource_requirements.append(req)

           # Optimize scheduling
           schedule = self.optimizer.optimize_schedule(
               configs, resource_requirements
           )

           return schedule

Caching Strategies
~~~~~~~~~~~~~~~~~~

Implement intelligent caching:

.. code-block:: python

   from rompy_oceanum import ResultCache
   import hashlib

   class CachedWorkflow:
       def __init__(self):
           self.cache = ResultCache(
               backend="redis",  # or "memory", "file"
               ttl=3600  # 1 hour
           )

       def execute_with_cache(self, config):
           """Execute with result caching."""
           # Generate cache key
           config_hash = hashlib.md5(
               str(sorted(config.items())).encode()
           ).hexdigest()

           cache_key = f"model_result_{config_hash}"

           # Check cache
           cached_result = self.cache.get(cache_key)
           if cached_result:
               return cached_result

           # Execute and cache
           result = self.run_model(config)
           self.cache.set(cache_key, result)

           return result

Best Practices
--------------

Guidelines for implementing robust advanced workflows:

Workflow Design
~~~~~~~~~~~~~~~

* **Modularity**: Design workflows as composable components
* **Idempotency**: Ensure workflows can be safely re-executed
* **Observability**: Include comprehensive logging and monitoring
* **Error Boundaries**: Isolate failures to prevent cascade effects

Resource Management
~~~~~~~~~~~~~~~~~~~

* **Right-sizing**: Monitor and optimize resource allocation
* **Scaling**: Implement auto-scaling for variable workloads
* **Cost Control**: Monitor and control computational costs
* **Efficiency**: Optimize workflow scheduling and execution

Monitoring and Alerting
~~~~~~~~~~~~~~~~~~~~~~~

* **Health Checks**: Implement comprehensive health monitoring
* **Performance Metrics**: Track key performance indicators
* **Alert Fatigue**: Configure meaningful, actionable alerts
* **Documentation**: Maintain runbooks for incident response

See Also
--------

* :doc:`basic-usage` - Getting started with rompy-oceanum
* :doc:`pipeline-backends` - Understanding execution backends
* :doc:`troubleshooting` - Debugging workflow issues
* :doc:`../api/index` - API reference documentation
