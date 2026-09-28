import { InputModality, OutputModality } from "@/app/client";

export type NumberRange = [number, number];

export type ModelFiltersState = {
    includeMissing: boolean;
    creators: string[];
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
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
    inputModalities: InputModality[];
    outputModalities: OutputModality[];
};

export type FilterBounds = {
    creators: string[];
    creationDate: NumberRange | undefined;
    knowledgeCutoff: NumberRange | undefined;
    contextLength: NumberRange | undefined;
};

export function createInitialUserChoices(): UserFilterChoices {
    return {
        includeMissing: true,
        creators: [],
        creationDate: undefined,
        knowledgeCutoff: undefined,
        contextLength: undefined,
        inputModalities: [],
        outputModalities: [],
    };
}

export function resolveFilters(
    choices: UserFilterChoices,
    bounds: FilterBounds,
): ModelFiltersState {
    return {
        includeMissing: choices.includeMissing,
        creators: choices.creators,
        creationDate: bounds.creationDate
            ? (choices.creationDate ?? [
                  bounds.creationDate[0],
                  bounds.creationDate[1],
              ])
            : undefined,
        knowledgeCutoff: bounds.knowledgeCutoff
            ? (choices.knowledgeCutoff ?? [
                  bounds.knowledgeCutoff[0],
                  bounds.knowledgeCutoff[1],
              ])
            : undefined,
        contextLength: bounds.contextLength
            ? (choices.contextLength ?? [
                  bounds.contextLength[0],
                  bounds.contextLength[1],
              ])
            : undefined,
        inputModalities: choices.inputModalities,
        outputModalities: choices.outputModalities,
    };
}
