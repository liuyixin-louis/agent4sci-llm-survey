#!/usr/bin/env python
"""
Create publication-ready figures for the paper.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set publication style
try:
    plt.style.use('seaborn-whitegrid')
except:
    plt.style.use('default')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

def create_comparison_figure():
    """Create main comparison figure."""
    
    # Load demo results
    with open('outputs/demo/demo_results.json', 'r') as f:
        data = json.load(f)
    
    methods = ['AutoSurvey', 'AutoSurvey+LCE', 'Global Iterative\n(Ours)']
    
    # Extract scores
    scores = data['methods']
    metrics = ['coverage', 'coherence', 'structure', 'citations']
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left plot: Overall scores
    ax1 = axes[0]
    overall_scores = [
        scores['autosurvey']['overall'],
        scores['autosurvey_lce']['overall'],
        scores['iterative']['overall']
    ]
    
    bars = ax1.bar(methods, overall_scores, color=['#ff7f0e', '#2ca02c', '#1f77b4'])
    ax1.set_ylabel('Overall Quality Score (1-5)')
    ax1.set_title('Overall Survey Quality Comparison')
    ax1.set_ylim([0, 5])
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, score in zip(bars, overall_scores):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{score:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # Add improvement percentages
    baseline = overall_scores[0]
    for i, (bar, score) in enumerate(zip(bars[1:], overall_scores[1:]), 1):
        improvement = ((score - baseline) / baseline) * 100
        ax1.text(bar.get_x() + bar.get_width()/2., 0.5,
                f'+{improvement:.1f}%', ha='center', va='bottom',
                color='darkgreen', fontsize=10)
    
    # Right plot: Individual metrics
    ax2 = axes[1]
    x = np.arange(len(metrics))
    width = 0.25
    
    autosurvey_vals = [scores['autosurvey'][m] for m in metrics]
    lce_vals = [scores['autosurvey_lce'][m] for m in metrics]
    iter_vals = [scores['iterative'][m] for m in metrics]
    
    ax2.bar(x - width, autosurvey_vals, width, label='AutoSurvey', color='#ff7f0e')
    ax2.bar(x, lce_vals, width, label='AutoSurvey+LCE', color='#2ca02c')
    ax2.bar(x + width, iter_vals, width, label='Global Iterative (Ours)', color='#1f77b4')
    
    ax2.set_ylabel('Score (1-5)')
    ax2.set_title('Detailed Quality Metrics')
    ax2.set_xticks(x)
    ax2.set_xticklabels([m.capitalize() for m in metrics])
    ax2.legend(loc='upper left')
    ax2.set_ylim([0, 5])
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path('outputs/figures')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig.savefig(output_dir / 'comparison.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_dir / 'comparison.pdf', bbox_inches='tight')
    print(f"Saved comparison figure to {output_dir}")
    
    return fig


def create_convergence_figure():
    """Create convergence plot."""
    
    # Load demo results
    with open('outputs/demo/demo_results.json', 'r') as f:
        data = json.load(f)
    
    iterations = list(range(len(data['convergence']['iterations'])))
    scores = data['convergence']['iterations']
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Plot convergence curve
    ax.plot(iterations, scores, 'o-', linewidth=2.5, markersize=10, 
            color='#1f77b4', label='Global Iterative System')
    
    # Add convergence threshold
    ax.axhline(y=4.0, color='red', linestyle='--', linewidth=1.5,
               label='Convergence Threshold (4.0)')
    
    # Mark convergence point
    conv_iter = data['convergence']['converged_at']
    ax.plot(conv_iter, scores[conv_iter], 'r*', markersize=20, 
            label=f'Converged (Iteration {conv_iter})')
    
    # Annotations
    for i, score in enumerate(scores):
        if i == conv_iter:
            ax.annotate(f'Converged\n{score:.1f}', 
                       xy=(i, score), xytext=(i+0.3, score-0.3),
                       arrowprops=dict(arrowstyle='->', color='red'),
                       fontsize=10, ha='left')
        else:
            ax.text(i, score + 0.05, f'{score:.1f}', 
                   ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Iteration Number')
    ax.set_ylabel('Overall Quality Score')
    ax.set_title('Global Iterative System Convergence')
    ax.set_xlim([-0.2, len(iterations)-0.8])
    ax.set_ylim([3.0, 4.5])
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')
    
    # Save figure
    output_dir = Path('outputs/figures')
    fig.savefig(output_dir / 'convergence.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_dir / 'convergence.pdf', bbox_inches='tight')
    print(f"Saved convergence figure to {output_dir}")
    
    return fig


def create_architecture_diagram():
    """Create system architecture diagram."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # AutoSurvey + LCE (left)
    ax1.set_title('AutoSurvey with Local Coherence Enhancement', fontsize=12)
    ax1.set_xlim([0, 10])
    ax1.set_ylim([0, 10])
    ax1.axis('off')
    
    # Draw boxes for AutoSurvey
    boxes = [
        {'xy': (1, 8), 'width': 3, 'height': 1, 'label': 'Papers'},
        {'xy': (1, 6), 'width': 3, 'height': 1, 'label': 'Chunk\nOutline'},
        {'xy': (1, 4), 'width': 3, 'height': 1, 'label': 'Parallel\nWriting'},
        {'xy': (1, 2), 'width': 3, 'height': 1, 'label': 'Survey'},
        {'xy': (5, 2), 'width': 3, 'height': 1, 'label': 'LCE\n2-pass'},
        {'xy': (5, 0.5), 'width': 3, 'height': 1, 'label': 'Final\nSurvey'},
    ]
    
    for box in boxes:
        rect = plt.Rectangle(box['xy'], box['width'], box['height'], 
                            fill=True, facecolor='lightblue', 
                            edgecolor='black', linewidth=1.5)
        ax1.add_patch(rect)
        ax1.text(box['xy'][0] + box['width']/2, 
                box['xy'][1] + box['height']/2,
                box['label'], ha='center', va='center', fontsize=10)
    
    # Draw arrows
    arrows = [
        ((2.5, 8), (2.5, 7)),
        ((2.5, 6), (2.5, 5)),
        ((2.5, 4), (2.5, 3)),
        ((4, 2.5), (5, 2.5)),
        ((6.5, 2), (6.5, 1.5)),
    ]
    
    for start, end in arrows:
        ax1.arrow(start[0], start[1], end[0]-start[0], end[1]-start[1],
                 head_width=0.2, head_length=0.15, fc='black', ec='black')
    
    # Add LOCAL annotation
    ax1.text(6.5, 3.5, 'LOCAL\nCoherence\nOnly', ha='center', 
            fontsize=10, color='red', fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3))
    
    # Our Global Iterative (right)
    ax2.set_title('Our Global Iterative System', fontsize=12)
    ax2.set_xlim([0, 10])
    ax2.set_ylim([0, 10])
    ax2.axis('off')
    
    # Draw boxes for our system
    boxes2 = [
        {'xy': (1, 8), 'width': 3, 'height': 1, 'label': 'Papers'},
        {'xy': (1, 6), 'width': 3, 'height': 1, 'label': 'Initial\nSurvey'},
        {'xy': (5, 6), 'width': 3, 'height': 1, 'label': 'Global\nVerification'},
        {'xy': (5, 4), 'width': 3, 'height': 1, 'label': 'Targeted\nImprovement'},
        {'xy': (5, 2), 'width': 3, 'height': 1, 'label': 'Updated\nSurvey'},
        {'xy': (1, 0.5), 'width': 3, 'height': 1, 'label': 'Final\nSurvey'},
    ]
    
    for box in boxes2:
        color = 'lightgreen' if 'Global' in box['label'] or 'Targeted' in box['label'] else 'lightblue'
        rect = plt.Rectangle(box['xy'], box['width'], box['height'], 
                            fill=True, facecolor=color, 
                            edgecolor='black', linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(box['xy'][0] + box['width']/2, 
                box['xy'][1] + box['height']/2,
                box['label'], ha='center', va='center', fontsize=10)
    
    # Draw arrows with iteration loop
    arrows2 = [
        ((2.5, 8), (2.5, 7)),
        ((4, 6.5), (5, 6.5)),
        ((6.5, 6), (6.5, 5)),
        ((6.5, 4), (6.5, 3)),
    ]
    
    for start, end in arrows2:
        ax2.arrow(start[0], start[1], end[0]-start[0], end[1]-start[1],
                 head_width=0.2, head_length=0.15, fc='black', ec='black')
    
    # Iteration loop
    ax2.arrow(5, 2.5, -3, 3, head_width=0.2, head_length=0.15, 
             fc='red', ec='red', linestyle='--', linewidth=2)
    ax2.text(3, 4, 'Iterate until\nconverged', ha='center', 
            fontsize=9, color='red', fontweight='bold')
    
    # Convergence arrow
    ax2.arrow(6.5, 2, -3.5, -1, head_width=0.2, head_length=0.15,
             fc='green', ec='green', linewidth=2)
    ax2.text(4.5, 1.2, 'Converged', ha='center', 
            fontsize=9, color='green', fontweight='bold')
    
    # Add GLOBAL annotation
    ax2.text(6.5, 7.5, 'GLOBAL\nView', ha='center', 
            fontsize=10, color='green', fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.3))
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path('outputs/figures')
    fig.savefig(output_dir / 'architecture.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_dir / 'architecture.pdf', bbox_inches='tight')
    print(f"Saved architecture diagram to {output_dir}")
    
    return fig


if __name__ == "__main__":
    print("Creating paper figures...")
    
    # Create all figures
    fig1 = create_comparison_figure()
    fig2 = create_convergence_figure()
    fig3 = create_architecture_diagram()
    
    print("\nAll figures created successfully!")
    print("Figures saved in outputs/figures/")
    
    # Show figures (optional)
    # plt.show()