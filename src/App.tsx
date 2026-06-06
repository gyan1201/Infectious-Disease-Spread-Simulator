import { useEffect, useState, useRef } from 'react';
import { SimulationEngine } from './simulation/Engine';
import { SimulationCanvas } from './components/SimulationCanvas';
import { DashboardStats } from './components/DashboardStats';
import { ControlPanel } from './components/ControlPanel';

function App() {
  const engineRef = useRef<SimulationEngine | null>(null);
  const [running, setRunning] = useState(true);
  const requestRef = useRef<number>(0);
  const [stats, setStats] = useState({
    total: 0, susceptible: 0, exposed: 0, infectious: 0, isolated: 0, recovered: 0
  });
  const [agents, setAgents] = useState<any[]>([]);

  // Controls state
  const [scenario, setScenario] = useState<'Independent' | 'Household' | 'MessageFraming'>('Independent');
  const [infectionRateMult, setInfectionRateMult] = useState(1.0);

  const initSimulation = () => {
    engineRef.current = new SimulationEngine(800); // 800 agents
    engineRef.current.setScenario(scenario);
    engineRef.current.setInfectionRateMultiplier(infectionRateMult);
    setStats(engineRef.current.getStats());
    setAgents([...engineRef.current.agents]);
  };

  useEffect(() => {
    initSimulation();
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, []);

  const update = () => {
    if (engineRef.current && running) {
      engineRef.current.tick();
      setStats(engineRef.current.getStats());
      // We pass a shallow copy so React detects the change, but this might be heavy.
      // Alternatively, the canvas can just draw the mutable array directly.
      setAgents([...engineRef.current.agents]);
    }
    requestRef.current = requestAnimationFrame(update);
  };

  useEffect(() => {
    requestRef.current = requestAnimationFrame(update);
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [running]);

  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.setScenario(scenario);
    }
  }, [scenario]);

  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.setInfectionRateMultiplier(infectionRateMult);
    }
  }, [infectionRateMult]);

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="app-header glass-panel">
          <h1>Epidemic ABS</h1>
          <p>LLM-Driven Agent Behavior</p>
        </div>
        
        <DashboardStats stats={stats} />
        
        <ControlPanel 
          running={running}
          onTogglePlay={() => setRunning(!running)}
          onReset={initSimulation}
          scenario={scenario}
          onChangeScenario={setScenario}
          infectionRateMult={infectionRateMult}
          onChangeInfectionRate={setInfectionRateMult}
        />
      </div>
      
      <div className="main-content">
        <SimulationCanvas agents={agents} />
      </div>
    </div>
  );
}

export default App;
