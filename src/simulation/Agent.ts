// Agent.ts
import type { DiseaseState } from './DiseaseModel';
import { getRandomInt, defaultConfig } from './DiseaseModel';
import type { Demographics } from './DecisionBank';
import { getReportingProbability } from './DecisionBank';

export class Agent {
  id: string;
  x: number;
  y: number;
  homeX: number;
  homeY: number;
  demographics: Demographics;
  
  state: DiseaseState = 'Susceptible';
  daysInState: number = 0;
  targetDaysInState: number = 0;
  symptomatic: boolean = false;
  
  constructor(id: string, x: number, y: number, demographics: Demographics) {
    this.id = id;
    this.x = x;
    this.y = y;
    this.homeX = x;
    this.homeY = y;
    this.demographics = demographics;
  }

  expose() {
    if (this.state === 'Susceptible') {
      this.state = 'Exposed';
      this.daysInState = 0;
      this.targetDaysInState = getRandomInt(defaultConfig.incubationPeriodDays[0], defaultConfig.incubationPeriodDays[1]);
    }
  }

  tick(scenario: 'Independent' | 'Household' | 'MessageFraming') {
    this.daysInState++;

    // Random walk movement for simplicity in "town" unless isolated
    if (this.state !== 'Isolated') {
      this.x += (Math.random() - 0.5) * 8;
      this.y += (Math.random() - 0.5) * 8;
      
      // keep within bounds 0-1000
      this.x = Math.max(0, Math.min(1000, this.x));
      this.y = Math.max(0, Math.min(1000, this.y));
    }

    if (this.state === 'Exposed' && this.daysInState >= this.targetDaysInState) {
      this.state = 'Infectious';
      this.daysInState = 0;
      this.targetDaysInState = getRandomInt(defaultConfig.infectiousPeriodDays[0], defaultConfig.infectiousPeriodDays[1]);
      
      // Probability of being symptomatic (from paper, let's say 60% for simplicity)
      this.symptomatic = Math.random() < 0.6;
    }

    if (this.state === 'Infectious') {
      // If symptomatic, make a decision to report and isolate based on LLM decision bank
      if (this.symptomatic && this.daysInState === 1) {
         const reportProb = getReportingProbability(this.demographics, scenario);
         if (Math.random() < reportProb) {
            this.state = 'Isolated'; // Self-reporting leads to isolation
            this.daysInState = 0;
            // Isolation lasts same as remaining infectious period roughly
         }
      }
      
      if (this.state !== 'Isolated' && this.daysInState >= this.targetDaysInState) {
        this.state = 'Recovered';
        this.daysInState = 0;
        this.targetDaysInState = getRandomInt(defaultConfig.recoveryPeriodDays[0], defaultConfig.recoveryPeriodDays[1]);
      }
    }

    if (this.state === 'Isolated' && this.daysInState >= this.targetDaysInState) {
       this.state = 'Recovered';
       this.daysInState = 0;
       this.targetDaysInState = getRandomInt(defaultConfig.recoveryPeriodDays[0], defaultConfig.recoveryPeriodDays[1]);
    }

    if (this.state === 'Recovered' && this.daysInState >= this.targetDaysInState) {
      this.state = 'Susceptible';
      this.daysInState = 0;
    }
  }
}
