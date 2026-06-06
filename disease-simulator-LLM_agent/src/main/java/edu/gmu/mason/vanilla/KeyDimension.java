package edu.gmu.mason.vanilla;

/**
 * Encodes one dimension of an agent's demographic or event context into a
 * single digit (or short string) for use as part of the LLM decision bank key.
 *
 * To add a new dimension without recompiling Person.java:
 *   1. Implement this interface (as a lambda or class).
 *   2. Register it via KeyDimensionRegistry.register("MyDim", impl).
 *   3. Add "MyDim" to biasConsideration in bias.config.
 *   4. Re-generate the decision bank CSV with the new key format.
 */
@FunctionalInterface
public interface KeyDimension {
    /**
     * @param agent the agent being evaluated
     * @return a short string (typically one digit) representing this dimension
     */
    String encode(Person agent);
}
