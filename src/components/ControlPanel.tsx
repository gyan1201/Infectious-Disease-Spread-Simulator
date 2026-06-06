import React from 'react';
import { Play, Pause, RotateCcw, Settings } from 'lucide-react';

interface ControlProps {
  running: boolean;
  onTogglePlay: () => void;
  onReset: () => void;
  scenario: 'Independent' | 'Household' | 'MessageFraming';
  onChangeScenario: (s: 'Independent' | 'Household' | 'MessageFraming') => void;
  infectionRateMult: number;
  onChangeInfectionRate: (r: number) => void;
}

export const ControlPanel: React.FC<ControlProps> = ({
  running,
  onTogglePlay,
  onReset,
  scenario,
  onChangeScenario,
  infectionRateMult,
  onChangeInfectionRate
}) => {
  return (
    <div className="control-panel glass-panel">
      <div className="control-header">
        <Settings size={20} />
        <h2>Simulation Controls</h2>
      </div>

      <div className="control-group">
        <div className="button-group">
          <button className={`btn ${running ? 'btn-danger' : 'btn-primary'}`} onClick={onTogglePlay}>
            {running ? <><Pause size={16}/> Pause</> : <><Play size={16}/> Play</>}
          </button>
          <button className="btn btn-secondary" onClick={onReset}>
            <RotateCcw size={16}/> Reset
          </button>
        </div>
      </div>

      <div className="control-group">
        <label>Decision Scenario</label>
        <select 
          value={scenario} 
          onChange={(e) => onChangeScenario(e.target.value as any)}
          className="select-input"
        >
          <option value="Independent">Independent Reasoning</option>
          <option value="Household">Household Influence</option>
          <option value="MessageFraming">Message Framing (Pro-Social)</option>
        </select>
        <p className="helper-text">
          {scenario === 'Independent' && "Agents decide purely based on demographics."}
          {scenario === 'Household' && "Agents are influenced by household reporting rates."}
          {scenario === 'MessageFraming' && "Pro-social message framing increases reporting."}
        </p>
      </div>

      <div className="control-group">
        <label>Infection Rate Multiplier ({infectionRateMult.toFixed(1)}x)</label>
        <input 
          type="range" 
          min="0.1" 
          max="3.0" 
          step="0.1" 
          value={infectionRateMult}
          onChange={(e) => onChangeInfectionRate(parseFloat(e.target.value))}
          className="range-input"
        />
      </div>
    </div>
  );
};
