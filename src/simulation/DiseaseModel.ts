// DiseaseModel.ts
export type DiseaseState = 'Susceptible' | 'Exposed' | 'Infectious' | 'Recovered' | 'Isolated';

export interface DiseaseConfig {
  infectionProbability: number; // Probability of infection per contact
  incubationPeriodDays: [number, number]; // Min/Max days in Exposed state
  infectiousPeriodDays: [number, number]; // Min/Max days in Infectious state
  recoveryPeriodDays: [number, number]; // Min/Max days in Recovered state
}

export const defaultConfig: DiseaseConfig = {
  infectionProbability: 0.07, // From the paper p_I = 0.07
  incubationPeriodDays: [1, 5], // d_E = 1 to 5 days
  infectiousPeriodDays: [5, 8], // d_I = 5 to 8 days
  recoveryPeriodDays: [30, 180] // d_R = 30 to 180 days
};

export function getRandomInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
