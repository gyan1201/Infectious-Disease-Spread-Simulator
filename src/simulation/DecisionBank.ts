// DecisionBank.ts
export type Income = 'Above $70k' | 'Below $70k';
export type Education = 'Bachelor or more' | 'Some college' | 'High school or less';
export type Age = 'Over 50' | 'Under 50';
export type Race = 'Asian' | 'Black' | 'White' | 'Other';
export type Gender = 'Male' | 'Female';

export interface Demographics {
  income: Income;
  education: Education;
  age: Age;
  race: Race;
  gender: Gender;
}

// These values mirror the findings from Table 4 in the paper
export function getReportingProbability(demo: Demographics, scenario: 'Independent' | 'Household' | 'MessageFraming'): number {
  let baseProb = 0.5; // default 50%
  
  // Income effect (strongest)
  if (demo.income === 'Above $70k') baseProb += 0.2;
  else baseProb -= 0.1;

  // Education effect
  if (demo.education === 'Bachelor or more') baseProb += 0.15;
  else if (demo.education === 'Some college') baseProb += 0.05;
  else baseProb -= 0.1;

  // Age effect
  if (demo.age === 'Under 50') baseProb += 0.05;

  // Race effect (minor based on paper, but kept for completion)
  if (demo.race === 'White') baseProb += 0.02;
  else if (demo.race === 'Asian') baseProb += 0.01;
  else if (demo.race === 'Black') baseProb -= 0.02;

  // Scenario effect
  if (scenario === 'Household') {
    // Household influence normalizes towards lower average in paper (63% vs 65%)
    baseProb = (baseProb + 0.5) / 2;
  } else if (scenario === 'MessageFraming') {
    // Message framing generally increases reporting across the board
    baseProb += 0.1;
  }

  // Clamp between 0 and 1
  return Math.max(0, Math.min(1, baseProb));
}
