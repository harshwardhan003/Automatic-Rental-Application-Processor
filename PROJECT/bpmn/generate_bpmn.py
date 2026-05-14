"""
DRAP BPMN Generator
Programmatically generates As-Is and To-Be BPMN diagrams as PNGs.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def draw_diagram(title, steps, filename):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    x = 5
    y = 50
    width = 15
    height = 10
    spacing = 20

    for i, step in enumerate(steps):
        # Draw box
        rect = patches.Rectangle((x, y - height/2), width, height, linewidth=2, edgecolor='black', facecolor='lightblue')
        ax.add_patch(rect)
        
        # Add text
        ax.text(x + width/2, y, step, ha='center', va='center', wrap=True, fontsize=10)
        
        # Draw arrow to next
        if i < len(steps) - 1:
            ax.arrow(x + width, y, spacing - width - 2, 0, head_width=2, head_length=2, fc='black', ec='black')
        
        x += spacing

    output_path = Path("bpmn") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"[BPMN] Generated {output_path}")

if __name__ == "__main__":
    as_is_steps = ["Email Received", "Manual Check", "Arithmetics", "Read Refs", "Manual Score", "Mental Shortlist"]
    to_be_steps = ["Structured Intake", "RPA Validation", "AI Scoring", "Auto-Rank", "Dashboard Review", "Agent Decision"]
    
    draw_diagram("As-Is Process (Manual)", as_is_steps, "as_is_bpmn.png")
    draw_diagram("To-Be Process (DRAP Automated)", to_be_steps, "to_be_bpmn.png")
