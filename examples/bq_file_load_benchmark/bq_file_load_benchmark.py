# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import logging

from generic_benchmark_tools import schema_creator
from generic_benchmark_tools import staging_table_generator
from generic_benchmark_tools import table_util
from load_benchmark_tools import load_file_generator
from load_benchmark_tools import load_file_parameters
from load_benchmark_tools import load_tables_processor


BENCHMARK_NAME = 'FILE LOADER'


def parse_args(argv):
    """Parses arguments from command line.

    Args:
        argv: list of arguments.

    Returns:
        parsed_args: parsed arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--create_results_table',
        help='Flag to initiate the process of creating results table to'
             'store the results of the benchmark loads. '
             'load_file_parameters.py.',
        action='store_true'
    )
    parser.add_argument(
        '--create_benchmark_schemas',
        help='Flag to initiate the process of creating schemas for the '
             'benchmarked tables based off of parameters in '
             'load_file_parameters.py.',
        action='store_true'
    )
    parser.add_argument(
        '--benchmark_table_schemas_directory',
        default='json_schemas/benchmark_table_schemas',
        help='Directory that stores the JSON files that hold the schemas for '
             'the benchmark tables.'
    )
    parser.add_argument(
        '--create_staging_tables',
        help='Flag to initiate process of creating staging tables using '
             'file parameters, which will be used to create files for '
             'loaing into benchmarked tables.',
        action='store_true'
    )
    parser.add_argument(
        '--create_files',
        help='Flag to initiate process of creating files for loading '
             'into benchmarked tables.',
        action='store_true'
    )
    parser.add_argument(
        '--restart_file',
        help='File to start with when creating files if program failed in '
             'the middle of file creation. Can only be used with '
             '--create_files flag.'
    )
    parser.add_argument(
        '--create_benchmark_tables',
        help='Flag to initiate process of creating benchmarked tables '
             'from files and storing results for comparison.',
        action='store_true'
    )
    parser.add_argument(
        '--duplicate_benchmark_tables',
        help='Flag that will create new benchmark tables from files that '
             'have already been used to create benchmark tables. Without '
             'this flag, tables will only be created from files that have not '
             'yet been loaded into benchmark tables. Can only be used with '
             '--create_benchmark_tables flag.',
        action='store_true'
    )
    parser.add_argument(
        '--bq_project_id',
        help='Project ID that contains bigquery resources for running '
             'the benchmark.'
    )
    parser.add_argument(
        '--benchmark_dataset_id',
        help='Dataset ID that benchmarked tables will be loaded to. '
    )
    parser.add_argument(
        '--staging_project_id',
        help='Name of the project that will hold resources for staging tables.'
    )
    parser.add_argument(
        '--staging_dataset_id',
        help='Dataset ID that staging tables will be loaded to.'
    )
    parser.add_argument(
        '--resized_staging_dataset_id',
        help='Dataset ID that resized staging tables will be loaded to.'
    )
    parser.add_argument(
        '--results_table_name',
        help='Name of table that will store results of '
             'benchmark loads.'
    )
    parser.add_argument(
        '--results_dataset_id',
        help='Name of the dataset that will hold the results table.'
    )
    parser.add_argument(
        '--results_table_schema_path',
        default='json_schemas/results_table_schema.json',
        help='Path of JSON file that holds the schema for the table '
             'that the benchmark results will be loaded into. '
    )
    parser.add_argument(
        '--gcs_project_id',
        help='Project ID that contains GCS resources for running '
             'the benchmark.'
    )
    parser.add_argument(
        '--bucket_name',
        help='Name of bucket that will contain files for loading into '
             'benchmarked tables.'
    )
    parser.add_argument(
        '--dataflow_temp_location',
        help='Temporary location for Dataflow jobs on GCS.'
    )
    parser.add_argument(
        '--dataflow_staging_location',
        help='Staging location for Dataflow jobs on GCS.'
    )
    parser.add_argument(
        '--bq_logs_dataset',
        help='Dataset that holds the table storing logs for BQ jobs '
             'in --bq_project_id'
    )
    args = parser.parse_args(args=argv)

    # Only certain args are required depending on the command. Rather than
    # making each arg required, raise an error when a command is missing an
    # accompanying arg.

    missing_args_error = ('Missing arg: {0:s} is required with the ' 
                          '{1:s} command.')

    if args.create_results_table:
        if not args.results_table_name:
            parser.error(missing_args_error.format(
                '--results_table_name',
                '--create_results_table'
            ))
        if not args.results_dataset_id:
            parser.error(missing_args_error.format(
                '--results_dataset_id',
                '--create_results_table'
            ))

    if args.create_staging_tables:
        if not args.bq_project_id:
            parser.error(missing_args_error.format(
                '--bq_project_id',
                '--create_staging_tables'
            ))
        if not args.staging_dataset_id:
            parser.error(missing_args_error.format(
                '--staging_dataset_id',
                '--create_staging_tables'
            ))
        if not args.resized_staging_dataset_id:
            parser.error(missing_args_error.format(
                '--resized_staging_dataset_id',
                '--create_staging_tables'
            ))
        if not args.dataflow_staging_location:
            parser.error(missing_args_error.format(
                '--dataflow_staging_location',
                '--create_staging_tables'
            ))
        if not args.dataflow_temp_location:
            parser.error(missing_args_error.format(
                '--dataflow_temp_location',
                '--create_staging_tables'
            ))

    if args.create_files:
        if not args.gcs_project_id:
            parser.error(missing_args_error.format(
                '--gcs_project_id',
                '--create_files'
            ))
        if not args.resized_staging_dataset_id:
            parser.error(missing_args_error.format(
                '--resized_staging_dataset_id',
                '--create_files'
            ))
        if not args.bucket_name:
            parser.error(missing_args_error.format(
                '--bucket_name',
                '--create_files'
            ))
        if not args.dataflow_staging_location:
            parser.error(missing_args_error.format(
                '--dataflow_staging_location',
                '--create_files'
            ))
        if not args.dataflow_temp_location:
            parser.error(missing_args_error.format(
                '--dataflow_temp_location',
                '--create_files'
            ))

    if args.restart_file:
        if not args.create_files:
            parser.error(missing_args_error.format(
                '--create_files',
                '--restart_file'
            ))

    if args.create_benchmark_tables:
        if not args.bq_project_id:
            parser.error(missing_args_error.format(
                '--bq_project_id',
                '--create_benchmark_tables'
            ))
        if not args.bq_project_id:
            parser.error(missing_args_error.format(
                '--gcs_project_id',
                '--create_benchmark_tables'
            ))
        if not args.staging_project_id:
            parser.error(missing_args_error.format(
                '--staging_project_id',
                '--create_benchmark_tables'
            ))
        if not args.staging_dataset_id:
            parser.error(missing_args_error.format(
                '--staging_dataset_id',
                '--create_benchmark_tables'
            ))
        if not args.benchmark_dataset_id:
            parser.error(missing_args_error.format(
                '--benchmark_dataset_id',
                '--create_benchmark_tables'
            ))
        if not args.bucket_name:
            parser.error(missing_args_error.format(
                '--bucket_name',
                '--create_benchmark_tables'
            ))
        if not args.results_table_name:
            parser.error(missing_args_error.format(
                '--results_table_name',
                '--create_benchmark_tables'
            ))
        if not args.results_dataset_id:
            parser.error(missing_args_error.format(
                '--results_dataset_id',
                '--create_benchmark_tables'
            ))
        if not args.bq_logs_dataset:
            parser.error(missing_args_error.format(
                '--bq_logs_dataset',
                '--create_benchmark_tables'
            ))

    return args


def main(argv=None):
    args = parse_args(argv)

    create_results_table = args.create_results_table
    create_benchmark_schemas = args.create_benchmark_schemas
    benchmark_table_schemas_dir = args.benchmark_table_schemas_directory
    create_staging_tables = args.create_staging_tables
    create_files = args.create_files
    restart_file = args.restart_file
    create_benchmark_tables = args.create_benchmark_tables
    duplicate_benchmark_tables = args.duplicate_benchmark_tables
    bq_project_id = args.bq_project_id
    benchmark_dataset_id = args.benchmark_dataset_id
    staging_project_id=args.staging_project_id
    staging_dataset_id = args.staging_dataset_id
    resized_staging_dataset_id = args.resized_staging_dataset_id
    results_table_name = args.results_table_name
    results_dataset_id=args.results_dataset_id
    results_table_schema_path = args.results_table_schema_path
    gcs_project_id = args.gcs_project_id
    bucket_name = args.bucket_name
    dataflow_temp_location = args.dataflow_temp_location
    dataflow_staging_location = args.dataflow_temp_location
    bq_logs_dataset = args.bq_logs_dataset

    file_params = load_file_parameters.FILE_PARAMETERS

    # Run provided commands
    if create_results_table:
        logging.info('Creating results table {0:s} from schema in '
                     '{1:s}.'.format(
                         results_table_name,
                         results_table_schema_path,
                     )
        )
        results_table_util = table_util.TableUtil(
            table_id=results_table_name,
            dataset_id=results_dataset_id,
            json_schema_filename=results_table_schema_path,
        )
        results_table_util.create_table()
        logging.info('Done creating results table.')

    if create_benchmark_schemas:
        benchmark_schema_creator = schema_creator.SchemaCreator(
            schemas_dir=benchmark_table_schemas_dir,
            file_params=file_params
        )
        benchmark_schema_creator.create_schemas()

    if create_staging_tables:
        benchmark_staging_table_generator = (
            staging_table_generator.StagingTableGenerator(
                project=bq_project_id,
                staging_dataset_id=staging_dataset_id,
                resized_dataset_id=resized_staging_dataset_id,
                json_schema_path=benchmark_table_schemas_dir,
                file_params=file_params,
                num_rows=500
            )
        )
        benchmark_staging_table_generator.create_staging_tables(
            dataflow_staging_location=dataflow_staging_location,
            dataflow_temp_location=dataflow_staging_location,
        )
        benchmark_staging_table_generator.create_resized_tables()

    if create_files:
        benchmark_load_file_generator = load_file_generator.FileGenerator(
            project_id=gcs_project_id,
            primitive_staging_dataset_id=resized_staging_dataset_id,
            bucket_name=bucket_name,
            file_params=file_params,
            dataflow_staging_location=dataflow_staging_location,
            dataflow_temp_location=dataflow_temp_location,
        )
        if restart_file:
            benchmark_load_file_generator.restart_incomplete_combination(
                restart_file
            )
        benchmark_load_file_generator.create_files()

    if create_benchmark_tables:
        benchmark_tables_processor = load_tables_processor.LoadTablesProcessor(
            benchmark_name=BENCHMARK_NAME,
            bq_project=bq_project_id,
            gcs_project=gcs_project_id,
            staging_project=staging_project_id,
            staging_dataset_id=staging_dataset_id,
            dataset_id=benchmark_dataset_id,
            bucket_name=bucket_name,
            results_table_name=results_table_name,
            results_table_dataset_id=results_dataset_id,
            duplicate_benchmark_tables=duplicate_benchmark_tables,
            file_params=file_params,
            bq_logs_dataset=bq_logs_dataset,
        )
        benchmark_tables_processor.create_benchmark_tables()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    main()
