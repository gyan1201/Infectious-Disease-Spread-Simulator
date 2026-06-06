import React, { useRef, useEffect } from 'react';
import { Agent } from '../simulation/Agent';

interface SimulationCanvasProps {
  agents: Agent[];
}

const colorMap = {
  Susceptible: '#3b82f6', // Blue
  Exposed: '#facc15', // Yellow
  Infectious: '#ef4444', // Red
  Isolated: '#a855f7', // Purple (Reported)
  Recovered: '#22c55e', // Green
};

export const SimulationCanvas: React.FC<SimulationCanvasProps> = ({ agents }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear background
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let i = 0; i < canvas.width; i += 50) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, canvas.height);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(canvas.width, i);
      ctx.stroke();
    }

    // Draw agents
    agents.forEach(agent => {
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = colorMap[agent.state] || '#fff';
      
      // Add glow effect for infectious and exposed
      if (agent.state === 'Infectious' || agent.state === 'Exposed') {
        ctx.shadowBlur = 10;
        ctx.shadowColor = ctx.fillStyle;
      } else {
        ctx.shadowBlur = 0;
      }

      ctx.fill();
    });
  }, [agents]); // Will re-render whenever agents array reference or contents change (handled by parent passing a clone or forcing render)

  return (
    <div className="canvas-container glass-panel">
      <canvas
        ref={canvasRef}
        width={1000}
        height={1000}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};
