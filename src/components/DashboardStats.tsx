import React from 'react';
import { Activity, ShieldAlert, AlertTriangle, UserCheck, ShieldCheck } from 'lucide-react';

interface StatsProps {
  stats: {
    total: number;
    susceptible: number;
    exposed: number;
    infectious: number;
    isolated: number;
    recovered: number;
  };
}

export const DashboardStats: React.FC<StatsProps> = ({ stats }) => {
  const reportedRate = stats.infectious + stats.isolated > 0 
    ? ((stats.isolated / (stats.infectious + stats.isolated)) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="stats-grid">
      <div className="stat-card glass-panel">
        <div className="stat-header">
          <Activity size={20} className="text-blue" />
          <span>Susceptible</span>
        </div>
        <div className="stat-value">{stats.susceptible}</div>
      </div>
      
      <div className="stat-card glass-panel">
        <div className="stat-header">
          <AlertTriangle size={20} className="text-yellow" />
          <span>Exposed</span>
        </div>
        <div className="stat-value">{stats.exposed}</div>
      </div>

      <div className="stat-card glass-panel">
        <div className="stat-header">
          <ShieldAlert size={20} className="text-red" />
          <span>Infectious (Hidden)</span>
        </div>
        <div className="stat-value">{stats.infectious}</div>
      </div>

      <div className="stat-card glass-panel">
        <div className="stat-header">
          <UserCheck size={20} className="text-purple" />
          <span>Reported (Isolated)</span>
        </div>
        <div className="stat-value">{stats.isolated}</div>
        <div className="stat-sub">Reporting Rate: {reportedRate}%</div>
      </div>

      <div className="stat-card glass-panel">
        <div className="stat-header">
          <ShieldCheck size={20} className="text-green" />
          <span>Recovered</span>
        </div>
        <div className="stat-value">{stats.recovered}</div>
      </div>
    </div>
  );
};
