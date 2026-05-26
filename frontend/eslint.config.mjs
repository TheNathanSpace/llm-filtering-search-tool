import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import eslintPluginUnicorn from "eslint-plugin-unicorn";
import unusedImports from "eslint-plugin-unused-imports";

const eslintConfig = defineConfig([
    ...nextVitals,
    ...nextTs,
    // Override default ignores of eslint-config-next.
    globalIgnores([
        // Default ignores of eslint-config-next:
        ".next/**",
        "out/**",
        "build/**",
        "next-env.d.ts",
    ]),
    eslintPluginUnicorn.configs.recommended,
    {
        plugins: {
            "unused-imports": unusedImports,
            unicorn: eslintPluginUnicorn,
        },
        rules: {
            "unicorn/no-abusive-eslint-disable": "off",
            "unused-imports/no-unused-imports": "warn",
        },
    },
]);

export default eslintConfig;
