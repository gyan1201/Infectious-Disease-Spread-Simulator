// Engine.ts
import { Agent } from './Agent';
import type { Demographics, Income, Education, Age, Race, Gender } from './DecisionBank';
import { defaultConfig } from './DiseaseModel';

export class SimulationEngine {
  agents: Agent[] = [];
  width: number = 1000;
  height: number = 1000;
  scenario: 'Independent' | 'Household' | 'MessageFraming' = 'Independent';
  contactRadius: number = 15;
  infectionRateMult: number = 1.0;
  
  constructor(numAgents: number) {
    this.initializeAgents(numAgents);
  }

  initializeAgents(numAgents: number) {
    this.agents = [];
    const incomes: Income[] = ['Above $70k', 'Below $70k'];
    const educations: Education[] = ['Bachelor or more', 'Some college', 'High school or less'];
    const ages: Age[] = ['Over 50', 'Under 50'];
    const races: Race[] = ['Asian', 'Black', 'White', 'Other'];
    const genders: Gender[] = ['Male', 'Female'];

    for (let i = 0; i < numAgents; i++) {
      const demo: Demographics = {
        income: incomes[Math.floor(Math.random() * incomes.length)],
        education: educations[Math.floor(Math.random() * educations.length)],
        age: ages[Math.floor(Math.random() * ages.length)],
        race: races[Math.floor(Math.random() * races.length)],
        gender: genders[Math.floor(Math.random() * genders.length)],
      };

      const x = Math.random() * this.width;
      const y = Math.random() * this.height;
      this.agents.push(new Agent(i.toString(), x, y, demo));
    }

    // Infect patient zero
    if (this.agents.length > 0) {
      this.agents[0].expose();
    }
  }

  setScenario(scen: 'Independent' | 'Household' | 'MessageFraming') {
    this.scenario = scen;
  }

  setInfectionRateMultiplier(mult: number) {
    this.infectionRateMult = mult;
  }

  tick() {
    // Spatial hashing could optimize this, but O(N^2) is fine for N=500
    for (const agent of this.agents) {
      agent.tick(this.scenario);
    }

    // Process infections
    const infectious = this.agents.filter(a => a.state === 'Infectious');
    const susceptible = this.agents.filter(a => a.state === 'Susceptible');

    const prob = defaultConfig.infectionProbability * this.infectionRateMult;

    for (const inf of infectious) {
      for (const sus of susceptible) {
        const dx = inf.x - sus.x;
        const dy = inf.y - sus.y;
        if (dx*dx + dy*dy < this.contactRadius * this.contactRadius) {
          if (Math.random() < prob) {
            sus.expose();
          }
        }
      }
    }
  }

  getStats() {
    return {
      total: this.agents.length,
      susceptible: this.agents.filter(a => a.state === 'Susceptible').length,
      exposed: this.agents.filter(a => a.state === 'Exposed').length,
      infectious: this.agents.filter(a => a.state === 'Infectious').length,
      isolated: this.agents.filter(a => a.state === 'Isolated').length, // These are the "Reported" cases
      recovered: this.agents.filter(a => a.state === 'Recovered').length,
    };
  }
}
