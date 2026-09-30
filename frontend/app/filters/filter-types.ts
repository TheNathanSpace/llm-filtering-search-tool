import { InputModality, OutputModality } from "@/app/client";

export type NumberRange = [number, number];

export type ModelFiltersState = {
    includeMissing: boolean;
    openWeightsOnly: boolean;
    nameQuery: string;
    creators: string[];
    intelligenceIndex: NumberRange | undefined;
    codingIndex: NumberRange | undefined;
    agenticIndex: NumberRange | undefined;
    pricingInput: NumberRange | undefined;
    pricingOutput: NumberRange | undefined;
    providers: string[];
    throughput: NumberRange | undefined;
    latencyMs: NumberRange | undefined;
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
    parametersB: NumberRange | undefined;
    inputModalities: InputModality[];
    outputModalities: OutputModality[];
};

/** User-edited filter fields; unset range fields fall back to bounds when resolved. */
export type UserFilterChoices = {
    includeMissing: boolean;
    openWeightsOnly: boolean;
    nameQuery: string;
    creators: string[];
    intelligenceIndex: NumberRange | undefined;
    codingIndex: NumberRange | undefined;
    agenticIndex: NumberRange | undefined;
    pricingInput: NumberRange | undefined;
    pricingOutput: NumberRange | undefined;
    providers: string[];
    throughput: NumberRange | undefined;
    latencyMs: NumberRange | undefined;
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
    parametersB: NumberRange | undefined;
    inputModalities: InputModality[];
    outputModalities: OutputModality[];
};

export type FilterBounds = {
    creators: string[];
    intelligenceIndex: NumberRange | undefined;
    codingIndex: NumberRange | undefined;
    agenticIndex: NumberRange | undefined;
    pricingInput: NumberRange | undefined;
    pricingOutput: NumberRange | undefined;
    providers: string[];
    throughput: NumberRange | undefined;
    latencyMs: NumberRange | undefined;
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
    parametersB: NumberRange | undefined;
};

export function createInitialUserChoices(): UserFilterChoices {
    return {
        includeMissing: true,
        openWeightsOnly: false,
        nameQuery: "",
        creators: [],
        intelligenceIndex: undefined,
        codingIndex: undefined,
        agenticIndex: undefined,
        pricingInput: undefined,
        pricingOutput: undefined,
        providers: [],
        throughput: undefined,
        latencyMs: undefined,
        creationDate: undefined,
        knowledgeCutoff: undefined,
        contextLength: undefined,
        parametersB: undefined,
        inputModalities: [],
        outputModalities: [],
    };
}

function resolveRange(
    choice: NumberRange | undefined,
    bounds: NumberRange | undefined,
): NumberRange | undefined {
    if (!bounds) {
        return undefined;
    }
    return choice ?? [bounds[0], bounds[1]];
}

export function resolveFilters(
    choices: UserFilterChoices,
    bounds: FilterBounds,
): ModelFiltersState {
    return {
        includeMissing: choices.includeMissing,
        openWeightsOnly: choices.openWeightsOnly,
        nameQuery: choices.nameQuery,
        creators: choices.creators,
        intelligenceIndex: resolveRange(
            choices.intelligenceIndex,
            bounds.intelligenceIndex,
        ),
        codingIndex: resolveRange(choices.codingIndex, bounds.codingIndex),
        agenticIndex: resolveRange(choices.agenticIndex, bounds.agenticIndex),
        pricingInput: resolveRange(choices.pricingInput, bounds.pricingInput),
        pricingOutput: resolveRange(
            choices.pricingOutput,
            bounds.pricingOutput,
        ),
        providers: choices.providers,
        throughput: resolveRange(choices.throughput, bounds.throughput),
        latencyMs: resolveRange(choices.latencyMs, bounds.latencyMs),
        creationDate: resolveRange(choices.creationDate, bounds.creationDate),
        knowledgeCutoff: resolveRange(
            choices.knowledgeCutoff,
            bounds.knowledgeCutoff,
        ),
        contextLength: resolveRange(
            choices.contextLength,
            bounds.contextLength,
        ),
        parametersB: resolveRange(choices.parametersB, bounds.parametersB),
        inputModalities: choices.inputModalities,
        outputModalities: choices.outputModalities,
    };
}
