import unittest

from solace.benchmark import BenchmarkReport, BenchmarkResult, format_benchmark
from solace.llm import InferenceMetrics
from solace.ollama import RunningModelInfo
from solace.status import MemoryUsage


class BenchmarkTests(unittest.TestCase):
    def test_ollama_metrics_are_parsed_and_rates_are_calculated(self):
        metrics = InferenceMetrics.from_payload(
            {
                "total_duration": 2_500_000_000,
                "load_duration": 500_000_000,
                "prompt_eval_count": 100,
                "prompt_eval_duration": 1_000_000_000,
                "eval_count": 50,
                "eval_duration": 2_000_000_000,
                "done_reason": "stop",
            },
            wall_seconds=2.6,
            first_content_seconds=0.9,
        )
        self.assertEqual(metrics.total_seconds, 2.5)
        self.assertEqual(metrics.load_seconds, 0.5)
        self.assertEqual(metrics.prompt_tokens_per_second, 100.0)
        self.assertEqual(metrics.generation_tokens_per_second, 25.0)
        self.assertEqual(metrics.first_content_seconds, 0.9)

    def test_benchmark_output_distinguishes_cold_and_warm_metrics(self):
        metrics = InferenceMetrics.from_payload(
            {
                "total_duration": 2_000_000_000,
                "load_duration": 100_000_000,
                "prompt_eval_count": 20,
                "prompt_eval_duration": 500_000_000,
                "eval_count": 10,
                "eval_duration": 1_000_000_000,
                "done_reason": "stop",
            },
            wall_seconds=2.1,
            first_content_seconds=0.8,
        )
        report = BenchmarkReport(
            model="qwen3:4b",
            thinking_disabled=True,
            context_window=4096,
            response_limit=128,
            results=(
                BenchmarkResult("Cold simple", metrics),
                BenchmarkResult("Warm simple", metrics),
                BenchmarkResult("Warm medium", metrics),
            ),
            thinking_only_artifact=False,
            memory_before=MemoryUsage(4 * 1024**3, 16 * 1024**3),
            memory_loaded=MemoryUsage(7 * 1024**3, 16 * 1024**3),
            running_model=RunningModelInfo(
                "qwen3:4b", 3 * 1024**3, 0, 4096, None
            ),
        )
        output = format_benchmark(report)
        self.assertIn("Cold simple:", output)
        self.assertIn("Warm simple:", output)
        self.assertIn("First content: 0.800 s", output)
        self.assertIn("Generation: 10.0 tok/s", output)
        self.assertIn("100% CPU", output)


if __name__ == "__main__":
    unittest.main()
