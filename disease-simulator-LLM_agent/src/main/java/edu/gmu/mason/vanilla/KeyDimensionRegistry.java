package edu.gmu.mason.vanilla;

import sim.field.network.Edge;
import sim.util.Bag;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Registry of all key dimensions used to build the LLM decision bank lookup key.
 *
 * Built-in dimensions (matching the 5-digit demographic baseline key):
 *   Vulnerability, Race, Gender, Income, Household Income, Hispanic, Education
 *
 * Built-in event dimensions (the +1 or more digits for context-aware scenarios):
 *   Family  — encodes whether a family member is infected and has/hasn't reported
 *   News    — encodes regional news context (region id mod 3)
 *
 * Adding a new dimension at runtime (no recompile needed):
 *   KeyDimensionRegistry.register("MyDim", agent -> agent.someField() > threshold ? "1" : "0");
 *   Then add "MyDim" to biasConsideration in bias.config and regenerate the decision bank CSV.
 */
public class KeyDimensionRegistry {

    private static final Map<String, KeyDimension> registry = new LinkedHashMap<>();

    static {
        // --- Demographic dimensions (5-digit baseline key) ---

        register("Vulnerability", agent ->
                agent.getAge() >= 50 ? "1" : "0");

        register("Race", agent -> {
            switch (agent.getRace()) {
                case WhiteOnly: return "1";
                case BlackOnly: return "2";
                case AsianOnly: return "3";
                default:        return "2";
            }
        });

        register("Gender", agent ->
                agent.getIsMale() ? "1" : "0");

        register("Income", agent ->
                agent.getIndivCensusIncome() > 70000 ? "1" : "0");

        register("Household Income", agent ->
                agent.getHhCensusIncome() > 100000 ? "1" : "0");

        register("Hispanic", agent ->
                agent.getIsHispanic() ? "1" : "0");

        register("Education", agent -> {
            switch (agent.getEducationLevel()) {
                case Bachelors:
                case Graduate:          return "2";
                case HighSchoolOrCollege: return "1";
                default:                return "0";
            }
        });

        // --- Event dimensions (extend the key beyond 5 digits) ---

        // Family: 0 = infected family member who reported, 1 = infected but not reported, 2 = no infected family
        register("Family", agent -> {
            if (!agent.hasFamily()) return "2";
            Bag edges = agent.getModel().getFriendFamilyNetwork().getEdgesOut(agent.getAgentId());
            String result = "2";
            for (Object obj : edges) {
                Edge edge = (Edge) obj;
                long familyId = (long) edge.getTo();
                Person member = agent.getModel().getAgent(familyId);
                if (member.getInfectiousDisease().getStatus() == InfectionStatus.Infectious) {
                    result = "1";
                    if (member.getInfectiousDisease().getIsreport()) return "0";
                }
            }
            return result;
        });

        // News: proxy for regional news context (0, 1, or 2)
        register("News", agent ->
                String.valueOf(agent.getOriginRegionId() % 3));

        // --- Example event dimensions: case-count awareness ---
        // These show how to encode simulation state into the key.
        // To use: add "RegionCases" and/or "TotalCases" to biasConsideration in bias.config,
        // then regenerate the decision bank CSV with the extra digit(s).
        //
        // Encoding: 0 = no cases, 1 = 1–9 cases, 2 = 10–100 cases, 3 = >100 cases

        // RegionCases: number of new reported cases in the agent's home region today.
        // WorldModel.numNewCasesRegion keeps a rolling 2-entry list [yesterday, today];
        // get(size-1) is the current day's running count.
        register("RegionCases", agent -> {
            int regionId = agent.getOriginRegionId();
            java.util.List<Integer> regionCounts = WorldModel.numNewCasesRegion.get(regionId);
            int cases = (regionCounts != null && !regionCounts.isEmpty())
                    ? regionCounts.get(regionCounts.size() - 1) : 0;
            if (cases == 0)          return "0";
            else if (cases < 10)     return "1";
            else if (cases <= 100)   return "2";
            else                     return "3";
        });

        // TotalCases: number of new reported cases across the entire simulation today.
        // WorldModel.numNewCases keeps a rolling 2-entry list [yesterday, today];
        // get(size-1) is the current day's running count.
        register("TotalCases", agent -> {
            java.util.List<Integer> counts = WorldModel.numNewCases;
            int cases = counts.isEmpty() ? 0 : counts.get(counts.size() - 1);
            if (cases == 0)          return "0";
            else if (cases < 10)     return "1";
            else if (cases <= 100)   return "2";
            else                     return "3";
        });
    }

    public static void register(String name, KeyDimension dimension) {
        registry.put(name, dimension);
    }

    /**
     * Builds the full lookup key for an agent by encoding each dimension listed
     * in biasConsideration (slash-separated) in order.
     *
     * @param agent            the agent
     * @param biasConsideration slash-separated dimension names, e.g. "Vulnerability/Gender/Race/Income/Education"
     * @return the concatenated key string, e.g. "00100"
     */
    public static String buildKey(Person agent, String biasConsideration) {
        StringBuilder key = new StringBuilder();
        for (String name : biasConsideration.split("/")) {
            String trimmed = name.trim();
            KeyDimension dim = registry.get(trimmed);
            if (dim != null) {
                key.append(dim.encode(agent));
            } else {
                agent.getModel().logger_o.warn("KeyDimensionRegistry: unknown dimension '{}' — skipped", trimmed);
            }
        }
        return key.toString();
    }
}
