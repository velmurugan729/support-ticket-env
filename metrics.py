import json
import os
from datetime import datetime

class PerformanceReporter:
    """
    Generates professional performance reports for the ticket routing agent.
    """
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def add_result(self, task_name, success, score, steps, rewards):
        self.results.append({
            "task": task_name,
            "success": success,
            "score": score,
            "steps": steps,
            "rewards": rewards
        })
        
    def generate_summary(self):
        total_tasks = len(self.results)
        successes = sum(1 for r in self.results if r["success"])
        avg_score = sum(r["score"] for r in self.results) / total_tasks if total_tasks > 0 else 0
        
        report = f"""
==================================================
🚀 OPENENV PERFORMANCE REPORT - {self.timestamp}
==================================================
Model: {self.model_name}
Total Tasks: {total_tasks}
Success Rate: {(successes/total_tasks)*100:.1f}% ({successes}/{total_tasks})
Average Score: {avg_score:.3f}

DETAILED BREAKDOWN:
--------------------------------------------------
"""
        for r in self.results:
            status = "✅ SUCCESS" if r["success"] else "❌ FAILED"
            report += f"Task: {r['task']:<15} | Status: {status:<10} | Score: {r['score']:.3f} | Steps: {r['steps']}\n"
            report += f"  Rewards: {r['rewards']}\n"
            
        report += "==================================================\n"
        
        # Save to file
        os.makedirs("results", exist_ok=True)
        filename = f"results/report_{self.timestamp}.txt"
        with open(filename, "w") as f:
            f.write(report)
            
        print(report)
        print(f"Detailed report saved to {filename}")
        return report
