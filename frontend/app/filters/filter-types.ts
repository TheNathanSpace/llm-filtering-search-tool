import { InputModality, OutputModality } from "@/app/client";

export type NumberRange = [number, number];

export type ModelFiltersState = {
    includeMissing: boolean;
    creators: string[];
    intelligenceIndex: NumberRange | undefined;
    codingIndex: NumberRange | undefined;
    agenticIndex: NumberRange | undefined;
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
    inputModalities: InputModality[];
    outputModalities: OutputModality[];
};

/** User-edited filter fields; unset range fields fall back to bounds when resolved. */
export type UserFilterChoices = {
    includeMissing: boolean;
    creators: string[];
    intelligenceIndex: NumberRange | undefined;
    codingIndex: NumberRange | undefined;
    agenticIndex: NumberRange | undefined;
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
    inputModalities: InputModality[];
    outputModalities: OutputModality[];
};

export type FilterBounds = {
    creators: string[];
    intelligenceIndex: NumberRange | undefined;
    codingIndex: NumberRange | undefined;
    agenticIndex: NumberRange | undefined;
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
};

export function createInitialUserChoices(): UserFilterChoices {
    return {
        includeMissing: true,
        creators: [],
        intelligenceIndex: undefined,
        codingIndex: undefined,
        agenticIndex: undefined,
        creationDate: undefined,
        knowledgeCutoff: undefined,
        contextLength: undefined,
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
        creators: choices.creators,
        intelligenceIndex: resolveRange(
            choices.intelligenceIndex,
            bounds.intelligenceIndex,
        ),
        codingIndex: resolveRange(choices.codingIndex, bounds.codingIndex),
        agenticIndex: resolveRange(choices.agenticIndex, bounds.agenticIndex),
        creationDate: resolveRange(choices.creationDate, bounds.creationDate),
        knowledgeCutoff: resolveRange(
            choices.knowledgeCutoff,
            bounds.knowledgeCutoff,
        ),
        contextLength: resolveRange(
            choices.contextLength,
            bounds.contextLength,
        ),
        inputModalities: choices.inputModalities,
        outputModalities: choices.outputModalities,
    };
}
