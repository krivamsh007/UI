import json
from transformations import apply_transformations_with_summary, apply_advanced_excel_transformations

class PipelineManager:
    def __init__(self):
        # Holds pipeline steps as a list of dicts: {"order": int, "transformation": str, "parameters": dict}
        self.pipeline_steps = []

    def add_step(self, trans_name, parameters):
        """Remove any previous step with the same transformation name and add new step."""
        self.pipeline_steps = [step for step in self.pipeline_steps if step["transformation"] != trans_name]
        order = len(self.pipeline_steps) + 1
        self.pipeline_steps.append({"order": order, "transformation": trans_name, "parameters": parameters})

    def clear(self):
        """Clears all pipeline steps."""
        self.pipeline_steps = []

    def get_pipeline(self):
        """Return a dict mapping transformation keys to parameters (ordered by step)."""
        pipeline = {}
        for step in sorted(self.pipeline_steps, key=lambda x: x["order"]):
            pipeline[step["transformation"]] = step["parameters"]
        return pipeline

    def apply_pipeline(self, df, header_row, filter_conditions, advanced_excel_config, transformation_params):
        """
        Given an original DataFrame and the current configuration,
        merge the pipeline steps (if any) with the direct transformation parameters,
        then apply filters, transformations and advanced Excel functions.
        Returns the transformed DataFrame and a transformation summary.
        """
        # If pipeline is loaded, use its steps; otherwise use direct transformation params.
        if self.pipeline_steps:
            transformations = self.get_pipeline()
        else:
            transformations = transformation_params

        config = {
            "Header Row": header_row,
            "Filters": filter_conditions,
            "Transformations": transformations,
            "Advanced Excel Functions": advanced_excel_config,
        }
        df_transformed, summary_list = apply_transformations_with_summary(df, config)
        df_transformed = apply_advanced_excel_transformations(df_transformed, config["Advanced Excel Functions"])
        return df_transformed, summary_list

    def save_pipeline_config(self, header_row, filter_conditions, advanced_excel_config, transformation_params, column_registry, filepath):
        """
        Save the pipeline configuration to a JSON file.
        If pipeline steps exist, they are saved; otherwise direct transformation params are saved.
        """
        if self.pipeline_steps:
            config = {
                "Header Row": header_row,
                "Filters": filter_conditions,
                "Pipeline Steps": self.pipeline_steps,
                "Advanced Excel Functions": advanced_excel_config,
                "Column Registry": column_registry
            }
        else:
            config = {
                "Header Row": header_row,
                "Filters": filter_conditions,
                "Transformations": transformation_params,
                "Advanced Excel Functions": advanced_excel_config,
                "Column Registry": column_registry
            }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def load_pipeline_config(self, filepath):
        """
        Load a pipeline configuration from a JSON file.
        Returns the configuration dictionary.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
