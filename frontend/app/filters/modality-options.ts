import { InputModality, OutputModality } from "@/app/client";

export const INPUT_MODALITY_OPTIONS: readonly InputModality[] = [
    "text",
    "image",
    "file",
    "audio",
    "video",
];

export const OUTPUT_MODALITY_OPTIONS: readonly OutputModality[] = [
    "text",
    "image",
    "embeddings",
    "audio",
    "video",
    "rerank",
    "speech",
    "transcription",
];
