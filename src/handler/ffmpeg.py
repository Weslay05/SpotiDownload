import subprocess
import json

class FFMPEG:
    """Analyses Processes Audio"""

    def __init__(self,
                 logger: object,
                 output_loudness_lufs:str = "-14",
                 loudness_peak_dbfs:str = "-1.5",
                 loudness_range_lra:str = "14",
                 ) -> None:
        self.logging = logger
        self.loudness = output_loudness_lufs
        self.peak = loudness_peak_dbfs
        self.lra = loudness_range_lra

    def analyze_audio(self, file) -> dict[str, str]:
        """First audio normalization pass, returns a json with all relevant info"""
        log = self.logging
        settings = (
            f"loudnorm=I={self.loudness}:"
            f"TP={self.peak}:"
            f"LRA={self.lra}:"
            f"print_format=json"
        )
        cmd = [ "ffmpeg", "-i", file, "-af", settings, "-f", "null", "-" ]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, check=False, text=True)

            # : Grab that json outta there
        output = result.stderr
        json_start = output.find("{")
        json_end = output.rfind("}") + 1
        log.debug("Analysed audio and return loudnorm input values")
        return json.loads(output[json_start:json_end])

    def normalize_audio(self, input_file: str, output_file: str, analysis_results: dict[str, str]):
        """Takes a Dict of already analyzed audio, uses it to perfect Loudness normalization."""
        log = self.logging
        filter_settings = (
            f"loudnorm=I={self.loudness}:" f"measured_I={analysis_results['input_i']}:"
            f"TP={self.peak}:" f"measured_TP={analysis_results['input_tp']}:"
            f"LRA={self.lra}:" f"measured_LRA={analysis_results['input_lra']}:"
            f"measured_thresh={analysis_results['input_thresh']}:"
            f"offset={analysis_results['target_offset']}:"
            f"linear=true:print_format=summary"
        )
        cmd = ["ffmpeg", "-i", input_file, "-af", filter_settings, output_file]
        subprocess.run(cmd, check=False)
        log.debug("Applying Loudness...")
